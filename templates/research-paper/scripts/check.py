#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate a Beacon research-paper project and its rendered artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SECTIONS = (
    "Introduction",
    "Methods",
    "Results",
    "Discussion",
    "Limitations",
    "Ethics statement",
    "Data and code availability",
    "Acknowledgements",
    "Contributor statement",
)
ALLOWED_THEMES = {"neutral", "egohygiene"}
ALLOWED_STAGES = {"draft", "submission-ready", "published"}
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME|REPLACE ME)\b", re.IGNORECASE)
INPUT = re.compile(r"\\input\{([^}]+)\}")
FIGURE = re.compile(r"\\BeaconFigure\{([^{}]+)\}\{([^{}]+)\}\{([^{}]+)\}", re.DOTALL)
URL = re.compile(r"https?://[^\s<>{}\[\]\\\"']+")


def load_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def resolve_from_cwd(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()


def collect_tex(path: Path, project: Path, seen: set[Path] | None = None) -> str:
    seen = set() if seen is None else seen
    resolved = path.resolve()
    if resolved in seen:
        return ""
    seen.add(resolved)
    text = resolved.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        target = match.group(1)
        if target.startswith("beacon-generated-"):
            return ""
        candidate = (project / target).with_suffix(".tex")
        if not candidate.exists():
            candidate = (resolved.parent / target).with_suffix(".tex")
        candidate = candidate.resolve()
        if project not in candidate.parents:
            raise ValueError(f"LaTeX input escapes project: {target}")
        return collect_tex(candidate, project, seen)

    return INPUT.sub(replace, text)


def bibliography_keys(text: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", text, re.IGNORECASE))


def citation_keys(text: str) -> set[str]:
    citations: set[str] = set()
    pattern = re.compile(r"\\cite\w*\*?(?:\[[^\]]*\]){0,2}\{([^}]+)\}")
    for group in pattern.findall(text):
        citations.update(key.strip() for key in group.split(","))
    return citations


def pdf_checks(path: Path, errors: list[str]) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f"missing or empty PDF: {path}")
        return
    try:
        info = subprocess.run(
            ["pdfinfo", str(path)], check=True, capture_output=True, text=True
        ).stdout
        fonts = subprocess.run(
            ["pdffonts", str(path)], check=True, capture_output=True, text=True
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        errors.append(f"PDF inspection failed: {error}")
        return
    size = re.search(r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts", info, re.MULTILINE)
    if size is None or not (611 <= float(size.group(1)) <= 613 and 791 <= float(size.group(2)) <= 793):
        errors.append("paper.pdf must use US Letter pages")
    if re.search(r"^Encrypted:\s+yes", info, re.MULTILINE):
        errors.append("paper.pdf must not be encrypted")
    if re.search(r"^JavaScript:\s+yes", info, re.MULTILINE):
        errors.append("paper.pdf must not contain JavaScript")
    rows = [line for line in fonts.splitlines()[2:] if line.strip()]
    if not rows or any(re.search(r"\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", row) for row in rows):
        errors.append("paper.pdf must contain only embedded fonts")


def archive_checks(path: Path, errors: list[str], compile_archive: bool) -> None:
    if not path.is_file():
        errors.append(f"missing arXiv source archive: {path}")
        return
    with tarfile.open(path, "r:gz") as archive:
        names = archive.getnames()
        required = {
            "main.tex",
            "main.bbl",
            "beacon-research-paper.sty",
            "beacon-generated-metadata.tex",
            "beacon-generated-provenance.tex",
        }
        for missing in sorted(required - set(names)):
            errors.append(f"arXiv archive missing: {missing}")
        forbidden_suffixes = {".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".svg"}
        for name in names:
            path_parts = Path(name).parts
            if name.startswith("/") or ".." in path_parts or any(part.startswith(".") for part in path_parts):
                errors.append(f"unsafe or hidden arXiv archive member: {name}")
            if Path(name).suffix in forbidden_suffixes:
                errors.append(f"intermediate or unsupported arXiv archive member: {name}")
        if compile_archive and not errors:
            with tempfile.TemporaryDirectory() as temporary:
                destination = Path(temporary)
                archive.extractall(destination, filter="data")
                try:
                    subprocess.run(
                        [
                            "latexmk",
                            "-pdf",
                            "-interaction=nonstopmode",
                            "-halt-on-error",
                            "-file-line-error",
                            "main.tex",
                        ],
                        cwd=destination,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                except (OSError, subprocess.CalledProcessError) as error:
                    details = error.stderr[-2000:] if isinstance(error, subprocess.CalledProcessError) else str(error)
                    errors.append(f"arXiv archive did not compile independently: {details}")


def live_link_checks(urls: set[str], errors: list[str]) -> None:
    for url in sorted(urls):
        request = urllib.request.Request(url, headers={"User-Agent": "Beacon-research-paper/0.1"}, method="HEAD")
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status >= 400:
                    errors.append(f"external link returned HTTP {response.status}: {url}")
        except urllib.error.HTTPError as error:
            if error.code not in {403, 405}:
                errors.append(f"external link returned HTTP {error.code}: {url}")
        except (urllib.error.URLError, TimeoutError) as error:
            errors.append(f"external link failed: {url} ({error})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--build-dir", required=True)
    parser.add_argument("--theme")
    parser.add_argument("--compile-arxiv", action="store_true")
    parser.add_argument("--check-external-links", action="store_true")
    arguments = parser.parse_args()

    project = resolve_from_cwd(arguments.project)
    build = resolve_from_cwd(arguments.build_dir)
    errors: list[str] = []
    warnings: list[str] = []
    manifest = load_toml(ROOT / "beacon-template.toml")
    config = load_toml(project / "beacon-project.toml")
    paper = config.get("paper", {})
    beacon = config.get("beacon", {})
    provenance = config.get("provenance", {})
    theme = arguments.theme or beacon.get("theme")

    if manifest.get("id") != "research-paper":
        errors.append("manifest id must be research-paper")
    if beacon.get("profile") != manifest.get("id"):
        errors.append("project profile does not match manifest")
    if beacon.get("template_version") != manifest.get("version"):
        errors.append("project template version does not match manifest")
    if theme not in ALLOWED_THEMES:
        errors.append(f"unsupported theme: {theme}")
    if paper.get("stage") not in ALLOWED_STAGES:
        errors.append("paper stage must be draft, submission-ready, or published")
    for field in ("id", "title", "version", "date", "language", "abstract", "keywords", "authors", "entrypoint", "bibliography"):
        if not paper.get(field):
            errors.append(f"required paper metadata is empty: {field}")
    if not provenance.get("source_repository"):
        errors.append("provenance.source_repository is required")
    if not isinstance(provenance.get("source_date_epoch"), int):
        errors.append("provenance.source_date_epoch must be an integer")

    entrypoint = project / paper.get("entrypoint", "paper/paper.tex")
    bibliography = project / paper.get("bibliography", "paper/references.bib")
    if not entrypoint.is_file():
        errors.append(f"missing entrypoint: {entrypoint}")
        tex = ""
    else:
        try:
            tex = collect_tex(entrypoint, project)
        except (OSError, ValueError) as error:
            errors.append(str(error))
            tex = ""
    bibliography_text = bibliography.read_text(encoding="utf-8") if bibliography.is_file() else ""
    if not bibliography.is_file():
        errors.append(f"missing bibliography: {bibliography}")

    for section in REQUIRED_SECTIONS:
        if not re.search(rf"\\section\*?\{{{re.escape(section)}\}}", tex, re.IGNORECASE):
            errors.append(f"required section is missing: {section}")
    if r"\appendix" not in tex:
        errors.append("paper must include an appendix boundary")
    for key in sorted(citation_keys(tex) - bibliography_keys(bibliography_text)):
        errors.append(f"citation missing from bibliography: {key}")
    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    labels.update(f"fig:{slug}" for slug, _, _ in FIGURE.findall(tex))
    references = set(re.findall(r"\\(?:ref|eqref|autoref)\{([^}]+)\}", tex))
    for label in sorted(references - labels):
        errors.append(f"reference target is missing: {label}")
    figures = FIGURE.findall(tex)
    if not figures:
        errors.append("paper must exercise at least one BeaconFigure")
    for slug, caption, description in figures:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            errors.append(f"figure slug must use lowercase letters, digits, and hyphens: {slug}")
        if not (project / "paper" / "figures" / f"{slug}.svg").is_file():
            errors.append(f"figure source is missing: {slug}.svg")
        if not caption.strip() or not description.strip():
            errors.append(f"figure requires caption and description: {slug}")

    log_path = build / "paper.log"
    if not log_path.is_file():
        errors.append(f"missing LaTeX log: {log_path}")
    else:
        log = log_path.read_text(encoding="utf-8", errors="replace")
        for pattern in ("undefined references", "Citation `", "There were undefined"):
            if pattern.lower() in log.lower():
                errors.append(f"LaTeX log contains unresolved references: {pattern}")
    pdf_checks(build / "paper.pdf", errors)

    html_path = build / "web" / "index.html"
    if not html_path.is_file() or html_path.stat().st_size == 0:
        errors.append(f"missing or empty HTML: {html_path}")
    else:
        html = html_path.read_text(encoding="utf-8")
        for marker in ('<html lang="', 'class="skip-link"', '<main id="content"', 'aria-label="Table of contents"', '<figcaption'):
            if marker not in html:
                errors.append(f"web accessibility marker is missing: {marker}")
        for image in re.findall(r"<img\b[^>]*>", html):
            if not re.search(r'\balt="[^"]+"', image):
                errors.append("web image is missing non-empty alternative text")
        if "Figure description:" not in html:
            errors.append("web figure description is missing")

    provenance_path = build / "provenance.json"
    if not provenance_path.is_file():
        errors.append(f"missing provenance record: {provenance_path}")
    else:
        record = json.loads(provenance_path.read_text(encoding="utf-8"))
        if record.get("template_version") != manifest.get("version"):
            errors.append("provenance template version does not match manifest")
        revision = str(record.get("source_revision", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            if paper.get("stage") in {"submission-ready", "published"}:
                errors.append("submission-ready source revision must be a full Git commit")
            else:
                warnings.append("source revision is not an immutable Git commit")

    archives = sorted((build / "arxiv").glob("*.tar.gz")) if (build / "arxiv").exists() else []
    if len(archives) != 1:
        errors.append("build must contain exactly one arXiv source archive")
    else:
        archive_checks(archives[0], errors, arguments.compile_arxiv)

    placeholders = len(PLACEHOLDER.findall(tex)) + len(PLACEHOLDER.findall((project / "beacon-project.toml").read_text(encoding="utf-8")))
    if paper.get("stage") in {"submission-ready", "published"} and placeholders:
        errors.append(f"submission-ready source contains {placeholders} placeholder(s)")
    elif placeholders:
        warnings.append(f"draft source contains {placeholders} placeholder(s)")
    authors = paper.get("authors", [])
    for author in authors:
        orcid = author.get("orcid")
        if orcid and not re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", orcid):
            errors.append(f"invalid ORCID format for {author.get('name', '<unknown>')}")
        if not author.get("credit_roles"):
            warnings.append(f"CRediT roles are not assigned for {author.get('name', '<unknown>')}")

    urls: set[str] = set()
    for path in (ROOT / "README.md", ROOT / "SOURCES.md", project / "beacon-project.toml"):
        urls.update(url.rstrip(".,);") for url in URL.findall(path.read_text(encoding="utf-8")))
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"invalid external URL: {url}")
    if arguments.check_external_links:
        live_link_checks(urls, errors)
    elif paper.get("stage") in {"submission-ready", "published"}:
        errors.append("submission-ready validation requires --check-external-links")

    for warning in sorted(set(warnings)):
        print(f"WARN {warning}")
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1
    print(f"PASS research-paper project and {theme} artifacts are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
