#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate the Beacon technical-whitepaper source and rendered artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_HEADINGS = (
    "Executive summary",
    "Problem and context",
    "Evidence and claims",
    "System model",
    "Limitations",
    "Reproducibility",
    "Version history",
)
REQUIRED_REVIEWS = ("editorial", "technical", "evidence", "accessibility")
ALLOWED_CLAIM_STATES = {"proposed", "supported", "contested", "retired"}
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME|REPLACE ME)\b", re.IGNORECASE)
MARKDOWN_LINK = re.compile(r"!?\[([^\]]*)\]\(([^)\s]+)(?:\s+[\"'][^\"']*[\"'])?\)")
EXTERNAL_URL = re.compile(r"https?://[^\s<>{}\[\]\\\"']+")


def load_toml(path: Path) -> dict:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def contrast_ratio(first: str, second: str = "FFFFFF") -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def bibliography_keys(text: str) -> set[str]:
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", text, re.IGNORECASE))


def cited_keys(text: str) -> set[str]:
    return set(re.findall(r"(?<![\w.])@([A-Za-z0-9_:.+/-]+)", text))


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
        errors.append("whitepaper.pdf must use US Letter pages")
    if re.search(r"^Encrypted:\s+yes", info, re.MULTILINE):
        errors.append("whitepaper.pdf must not be encrypted")
    if re.search(r"^JavaScript:\s+yes", info, re.MULTILINE):
        errors.append("whitepaper.pdf must not contain JavaScript")
    rows = [line for line in fonts.splitlines()[2:] if line.strip()]
    if not rows or any(re.search(r"\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", row) for row in rows):
        errors.append("whitepaper.pdf must contain only embedded fonts")


def live_link_checks(urls: set[str], errors: list[str]) -> None:
    for url in sorted(urls):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Beacon-whitepaper-link-check/0.1"},
            method="HEAD",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.status >= 400:
                    errors.append(f"external link returned HTTP {response.status}: {url}")
        except urllib.error.HTTPError as error:
            if error.code in {403, 405}:
                try:
                    fallback = urllib.request.Request(
                        url,
                        headers={"User-Agent": "Beacon-whitepaper-link-check/0.1"},
                        method="GET",
                    )
                    with urllib.request.urlopen(fallback, timeout=15) as response:
                        if response.status >= 400:
                            errors.append(f"external link returned HTTP {response.status}: {url}")
                except (urllib.error.URLError, TimeoutError) as fallback_error:
                    errors.append(f"external link failed: {url} ({fallback_error})")
            else:
                errors.append(f"external link returned HTTP {error.code}: {url}")
        except (urllib.error.URLError, TimeoutError) as error:
            errors.append(f"external link failed: {url} ({error})")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--theme", default="themes/organization.json")
    parser.add_argument("--check-external-links", action="store_true")
    arguments = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    build = Path(arguments.build_dir)
    if not build.is_absolute():
        build = ROOT / build
    theme_path = Path(arguments.theme)
    if not theme_path.is_absolute():
        theme_path = ROOT / theme_path

    manifest = load_toml(ROOT / "beacon-template.toml")
    config = load_toml(ROOT / "whitepaper.toml")
    claims_data = load_toml(ROOT / "evidence" / "claims.toml")
    sources_data = load_toml(ROOT / "evidence" / "sources.toml")
    metadata = json.loads((ROOT / "metadata" / "whitepaper.json").read_text(encoding="utf-8"))
    theme = json.loads(theme_path.read_text(encoding="utf-8"))
    manuscript = (ROOT / "manuscript" / "whitepaper.md").read_text(encoding="utf-8")
    bibliography = (ROOT / "manuscript" / "references.bib").read_text(encoding="utf-8")

    if manifest.get("id") != "technical-whitepaper":
        errors.append("manifest id must be technical-whitepaper")
    if manifest.get("version") != config.get("document_version"):
        errors.append("manifest and whitepaper.toml versions differ")
    if metadata.get("version") != config.get("document_version"):
        errors.append("metadata and whitepaper.toml versions differ")

    for field in manifest["metadata"]["required"]:
        metadata_field = "author" if field == "authors" else "lang" if field == "language" else field
        if not metadata.get(metadata_field):
            errors.append(f"required metadata is empty: {field}")

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^#\s+{re.escape(heading)}\s*$", manuscript, re.MULTILINE):
            errors.append(f"required section is missing: {heading}")

    sources = {source["id"]: source for source in sources_data.get("sources", [])}
    source_citations = {source.get("citation_key") for source in sources.values()}
    claims = claims_data.get("claims", [])
    claim_ids = [claim.get("id") for claim in claims]
    if len(claim_ids) != len(set(claim_ids)):
        errors.append("claim IDs must be unique")
    for claim in claims:
        claim_id = claim.get("id", "<missing>")
        if claim.get("status") not in ALLOWED_CLAIM_STATES:
            errors.append(f"{claim_id}: invalid claim status")
        if not claim.get("statement") or not claim.get("limitations"):
            errors.append(f"{claim_id}: statement and limitations are required")
        if claim_id not in manuscript:
            errors.append(f"{claim_id}: claim ID is not visible in manuscript")
        for evidence_id in claim.get("evidence_ids", []):
            if evidence_id not in sources:
                errors.append(f"{claim_id}: unknown evidence ID {evidence_id}")
        for citation_key in claim.get("citation_keys", []):
            if citation_key not in source_citations:
                errors.append(f"{claim_id}: citation key has no source record: {citation_key}")

    bib_keys = bibliography_keys(bibliography)
    manuscript_citations = cited_keys(manuscript)
    for citation_key in sorted(manuscript_citations - bib_keys):
        errors.append(f"citation missing from bibliography: {citation_key}")
    for citation_key in sorted((source_citations - {None}) - bib_keys):
        errors.append(f"source citation missing from bibliography: {citation_key}")

    links: set[str] = set()
    for text_path in (ROOT / "README.md", ROOT / "PUBLISHING.md", ROOT / "manuscript" / "whitepaper.md"):
        text = text_path.read_text(encoding="utf-8")
        for label, target in MARKDOWN_LINK.findall(text):
            if target.startswith(("http://", "https://")):
                links.add(target)
            elif not target.startswith(("#", "mailto:")):
                candidate = (text_path.parent / target).resolve()
                if not candidate.exists():
                    errors.append(f"broken internal link in {text_path.relative_to(ROOT)}: {target}")
            if text[text.find(f"![{label}]") :].startswith(f"![{label}]") and not label.strip():
                errors.append(f"image has empty alternative text in {text_path.relative_to(ROOT)}")
        links.update(EXTERNAL_URL.findall(text))
    links.update(source["url"] for source in sources.values())
    for url in links:
        parsed = urlparse(url.rstrip(".,);"))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append(f"invalid external URL: {url}")

    for field in ("identity_mode", "identity_name", "identity_product", "identity_primary", "identity_accent", "identity_surface"):
        if not theme.get(field):
            errors.append(f"theme field is missing: {field}")
    for color_field in ("identity_primary", "identity_accent", "identity_surface"):
        value = str(theme.get(color_field, ""))
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
            errors.append(f"theme color must be six hexadecimal digits: {color_field}")
    minimum_contrast = float(config["quality"]["minimum_external_contrast"])
    for color_field in ("identity_primary", "identity_accent"):
        value = str(theme.get(color_field, "000000"))
        if re.fullmatch(r"[0-9A-Fa-f]{6}", value) and contrast_ratio(value) < minimum_contrast:
            errors.append(f"{color_field} contrast against white is below {minimum_contrast}:1")

    html_path = build / "web" / "index.html"
    if not html_path.is_file() or html_path.stat().st_size == 0:
        errors.append(f"missing or empty HTML: {html_path}")
    else:
        html = html_path.read_text(encoding="utf-8")
        for marker in ('<html lang="', '<main id="content"', 'aria-label="Table of contents"', 'class="skip-link"', '<figcaption'):
            if marker not in html:
                errors.append(f"web accessibility marker is missing: {marker}")

    pdf_checks(build / "whitepaper.pdf", errors)

    stage = config.get("stage")
    if stage not in {"draft", "publication-ready"}:
        errors.append("stage must be draft or publication-ready")
    placeholders = sum(
        len(PLACEHOLDER.findall(path.read_text(encoding="utf-8")))
        for path in (ROOT / "manuscript" / "whitepaper.md", ROOT / "metadata" / "whitepaper.json")
    )
    if stage == "publication-ready":
        revision = str(metadata.get("source_revision", ""))
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            errors.append("publication-ready source_revision must be a full commit SHA")
        for review in REQUIRED_REVIEWS:
            if config["review"].get(review) != "complete":
                errors.append(f"publication-ready review is incomplete: {review}")
        if not config["publication"].get("enabled"):
            errors.append("publication-ready mode requires Relay publication to be enabled")
        if placeholders:
            errors.append(f"publication-ready source contains {placeholders} placeholder(s)")
        if not arguments.check_external_links:
            errors.append("publication-ready mode requires --check-external-links")
    else:
        pending = [review for review in REQUIRED_REVIEWS if config["review"].get(review) != "complete"]
        if pending:
            warnings.append("draft mode; pending reviews: " + ", ".join(pending))
        if not re.fullmatch(r"[0-9a-f]{40}", str(metadata.get("source_revision", ""))):
            warnings.append("draft mode; source_revision is not immutable")

    if arguments.check_external_links:
        live_link_checks({url.rstrip(".,);") for url in links}, errors)

    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"PASS technical whitepaper checks ({stage} mode, {theme['identity_mode']} theme).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
