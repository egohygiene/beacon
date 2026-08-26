#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Build a Beacon magazine project into digital PDF, print PDF, and HTML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "beacon-template.toml"
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LAYOUT_ENVIRONMENTS = {
    "cover": "BeaconCoverPage",
    "opener": "BeaconOpenerPage",
    "feature": "BeaconFeaturePage",
    "diagram": "BeaconDiagramPage",
    "split": "BeaconSplitPage",
    "quote": "BeaconQuotePage",
    "credits": "BeaconCreditsPage",
    "back-cover": "BeaconBackCoverPage",
    "full-bleed-artwork": "BeaconArtworkPage",
}


def load_toml(path: Path) -> dict:
    """Load a TOML document."""
    with path.open("rb") as stream:
        return tomllib.load(stream)


def load_json(path: Path) -> dict:
    """Load a UTF-8 JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_from_cwd(value: str) -> Path:
    """Resolve a command-line path from the caller's working directory."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()


def safe_path(base: Path, value: str) -> Path:
    """Resolve a declared relative path without allowing traversal."""
    relative = Path(value)
    if relative.is_absolute():
        raise RuntimeError(f"absolute source paths are not allowed: {value}")
    candidate = (base / relative).resolve()
    if candidate != base and base not in candidate.parents:
        raise RuntimeError(f"source path escapes project boundary: {value}")
    return candidate


def run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    capture: bool = False,
) -> str:
    """Run a subprocess and optionally return standard output."""
    print("+ " + " ".join(command))
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=capture,
        text=capture,
    )
    return completed.stdout if capture else ""


def sha256(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tex_escape(value: object) -> str:
    """Escape plain metadata for LaTeX command arguments."""
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(character, character) for character in str(value))


def git_state(path: Path, fallback: str) -> tuple[str, bool | None]:
    """Resolve the owning Git revision and project-scoped worktree state."""
    try:
        revision = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        status = subprocess.run(
            [
                "git",
                "-C",
                str(path),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--",
                ".",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return revision, bool(status)
    except (OSError, subprocess.CalledProcessError):
        return fallback, None


def load_project(project: Path, theme_id: str) -> tuple[dict, dict, dict, list[dict]]:
    """Load the project, edition, selected theme, and ordered page records."""
    config = load_toml(project / "beacon-project.toml")
    theme_path = ROOT / "themes" / f"{theme_id}.toml"
    if not theme_path.is_file():
        raise RuntimeError(f"unknown magazine theme: {theme_id}")
    theme = load_toml(theme_path)
    edition_path = safe_path(project, config["magazine"]["edition_manifest"])
    edition = load_json(edition_path)
    edition_root = edition_path.parent
    pages: list[dict] = []
    for index, page_value in enumerate(edition["pages"], start=1):
        page_path = safe_path(edition_root, page_value)
        page = load_json(page_path)
        page["_number"] = index
        page["_manifest_path"] = page_path
        page["_manifest_relative"] = page_path.relative_to(project).as_posix()
        page["_source_path"] = safe_path(page_path.parent, page["source"])
        page["_source_relative"] = page["_source_path"].relative_to(project).as_posix()
        for optional in ("prompt_source", "animation_asset"):
            if page.get(optional):
                resolved = safe_path(page_path.parent, page[optional])
                page[f"_{optional}_path"] = resolved
                page[f"_{optional}_relative"] = resolved.relative_to(project).as_posix()
        artwork = page.get("artwork")
        if artwork:
            artwork_path = safe_path(page_path.parent, artwork["path"])
            page["_artwork_path"] = artwork_path
            page["_artwork_relative"] = artwork_path.relative_to(project).as_posix()
            if artwork.get("print_path"):
                print_path = safe_path(page_path.parent, artwork["print_path"])
                page["_print_artwork_path"] = print_path
                page["_print_artwork_relative"] = print_path.relative_to(project).as_posix()
        back_cover = page.get("back_cover", {})
        for asset_field in ("barcode_asset", "qr_asset"):
            if back_cover.get(asset_field):
                asset_path = safe_path(page_path.parent, back_cover[asset_field])
                page[f"_{asset_field}_path"] = asset_path
                page[f"_{asset_field}_relative"] = asset_path.relative_to(project).as_posix()
        pages.append(page)
    return config, edition, theme, pages


def markdown_fragment(path: Path, target: str) -> str:
    """Render canonical CommonMark content into a target fragment."""
    return run(
        [
            "pandoc",
            str(path),
            "--from=commonmark_x",
            f"--to={target}",
        ],
        cwd=path.parent,
        capture=True,
    ).strip()


def page_environment(page: dict) -> str:
    """Return the LaTeX environment for a validated page layout."""
    layout = page["layout"]
    if layout not in LAYOUT_ENVIRONMENTS:
        raise RuntimeError(f"unsupported magazine layout: {layout}")
    return LAYOUT_ENVIRONMENTS[layout]


def back_cover_tex(page: dict) -> str:
    """Render structured back-cover publishing metadata."""
    metadata = page.get("back_cover", {})
    rows = [
        ("Creator", metadata.get("creator", "")),
        ("Copyright", metadata.get("copyright", "")),
        ("License", metadata.get("license", "")),
        ("Version", metadata.get("version", "")),
        ("System", metadata.get("system_line", "")),
        ("ISBN", metadata.get("isbn", "")),
        ("QR", metadata.get("qr_url", "")),
    ]
    rendered = [r"\vspace{0.22in}{\scriptsize\begin{tabular}{@{}p{0.85in}p{3.75in}@{}}"]
    for label, value in rows:
        if value:
            rendered.append(rf"\textbf{{{tex_escape(label)}}} & {tex_escape(value)} \\")
    rendered.append(r"\end{tabular}}")
    code_assets = []
    for asset_field in ("_barcode_asset_relative", "_qr_asset_relative"):
        if page.get(asset_field):
            code_assets.append(
                rf"\includegraphics[width=1.45in,height=0.72in,keepaspectratio]"
                rf"{{\detokenize{{{page[asset_field]}}}}}"
            )
    if code_assets:
        rendered.extend(
            [
                r"\par\vspace{0.18in}\begin{center}",
                r"\hspace{0.08in}\hfill".join(code_assets),
                r"\end{center}",
            ]
        )
    return "\n".join(rendered)


def generated_preamble(
    config: dict,
    edition: dict,
    theme: dict,
    *,
    print_mode: bool,
) -> str:
    """Generate stable document metadata, colors, and page geometry."""
    trim_width = float(config["print"]["trim_width_in"])
    trim_height = float(config["print"]["trim_height_in"])
    bleed = float(config["print"]["bleed_in"])
    safe = float(config["print"]["safe_margin_in"])
    page_width = trim_width + (2 * bleed if print_mode else 0)
    page_height = trim_height + (2 * bleed if print_mode else 0)
    side_margin = safe + (bleed if print_mode else 0)
    top_margin = safe + (bleed if print_mode else 0)
    edition_name = edition.get("edition_name", "").strip()
    edition_label = f"Issue {edition['edition_number']}"
    if edition_name:
        edition_label += f" / {edition_name}"

    if print_mode:
        left = bleed * 72
        bottom = bleed * 72
        right = (bleed + trim_width) * 72
        top = (bleed + trim_height) * 72
        media_right = page_width * 72
        media_top = page_height * 72
        boxes = (
            rf"\pdfpageattr{{/TrimBox [{left:.3f} {bottom:.3f} {right:.3f} {top:.3f}] "
            rf"/BleedBox [0 0 {media_right:.3f} {media_top:.3f}]}}"
        )
    else:
        boxes = ""

    commands = {
        "BeaconMagazineTitle": edition["title"],
        "BeaconMagazineDescription": edition["description"],
        "BeaconPublisher": config["project"]["publisher"],
        "BeaconProduct": config["project"]["product"],
        "BeaconEditionLabel": edition_label,
        "BeaconVersion": edition["version"],
        "BeaconPrimaryHex": theme["primary"],
        "BeaconAccentHex": theme["accent"],
        "BeaconHighlightHex": theme["highlight"],
        "BeaconSurfaceHex": theme["surface"],
        "BeaconPaperHex": theme["paper"],
        "BeaconInkHex": theme["ink"],
        "BeaconMutedHex": theme["muted"],
    }
    lines = [
        r"\documentclass[10pt]{article}",
        r"\newif\ifBeaconPrint",
        r"\BeaconPrinttrue" if print_mode else r"\BeaconPrintfalse",
    ]
    lines.extend(
        rf"\newcommand{{\{name}}}{{{tex_escape(value)}}}" for name, value in commands.items()
    )
    lines.extend(
        [
            rf"\newcommand{{\BeaconPageWidth}}{{{page_width:.6f}in}}",
            rf"\newcommand{{\BeaconPageHeight}}{{{page_height:.6f}in}}",
            rf"\newcommand{{\BeaconSideMargin}}{{{side_margin:.6f}in}}",
            rf"\newcommand{{\BeaconTopMargin}}{{{top_margin:.6f}in}}",
            rf"\newcommand{{\BeaconBleed}}{{{bleed:.6f}in}}",
            rf"\newcommand{{\BeaconPdfBoxes}}{{{boxes}}}",
            r"\usepackage{beacon-magazine}",
            r"\begin{document}",
        ]
    )
    return "\n".join(lines)


def latex_pages(pages: list[dict], project: Path, *, print_mode: bool) -> str:
    """Render ordered page records into LaTeX environments."""
    rendered: list[str] = []
    for page in pages:
        if rendered:
            rendered.append(r"\clearpage")
        environment = page_environment(page)
        arguments = [page["kicker"], page["title"], page["deck"], str(page["_number"])]
        if page["layout"] == "full-bleed-artwork":
            asset_relative = page.get("_print_artwork_relative") if print_mode else None
            asset_relative = asset_relative or page.get("_artwork_relative")
            if not asset_relative:
                raise RuntimeError(f"{page['id']}: full-bleed artwork path is missing")
            if Path(asset_relative).suffix.lower() == ".svg":
                raise RuntimeError(
                    f"{page['id']}: SVG artwork requires a PNG, JPEG, or PDF print_path"
                )
            arguments.append(asset_relative)
            body = ""
        else:
            body = markdown_fragment(page["_source_path"], "latex")
            if page["kind"] == "back-cover":
                body = body + "\n" + back_cover_tex(page)
        argument_text = "".join("{" + tex_escape(value) + "}" for value in arguments)
        rendered.extend(
            [
                rf"\begin{{{environment}}}{argument_text}",
                body,
                rf"\end{{{environment}}}",
            ]
        )
    return "\n".join(rendered)


def build_pdf(
    work: Path,
    output: Path,
    config: dict,
    edition: dict,
    theme: dict,
    pages: list[dict],
    *,
    print_mode: bool,
    epoch: int,
) -> Path:
    """Build one PDF variant."""
    variant = "print" if print_mode else "digital"
    source_path = work / f"magazine-{variant}.tex"
    source_path.write_text(
        generated_preamble(config, edition, theme, print_mode=print_mode)
        + "\n"
        + latex_pages(pages, work, print_mode=print_mode)
        + "\n\\end{document}\n",
        encoding="utf-8",
    )
    latex_output = work / f"latex-{variant}"
    latex_output.mkdir()
    environment = os.environ.copy()
    environment.update(
        {
            "SOURCE_DATE_EPOCH": str(epoch),
            "FORCE_SOURCE_DATE": "1",
            "TZ": "UTC",
            "TEXINPUTS": f"{work}{os.pathsep}" + environment.get("TEXINPUTS", ""),
        }
    )
    run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-file-line-error",
            f"-outdir={latex_output}",
            source_path.name,
        ],
        cwd=work,
        env=environment,
    )
    destination = output / ("magazine-print.pdf" if print_mode else "magazine.pdf")
    shutil.copy2(latex_output / f"magazine-{variant}.pdf", destination)
    shutil.copy2(latex_output / f"magazine-{variant}.log", output / f"magazine-{variant}.log")
    return destination


def source_record(path: Path, project: Path) -> dict:
    """Describe one canonical source file for the publication manifest."""
    return {
        "path": path.relative_to(project).as_posix(),
        "sha256": sha256(path),
    }


def publication_manifest(
    config: dict,
    edition: dict,
    pages: list[dict],
    project: Path,
    theme_id: str,
    revision: str,
    declared_revision: str,
    source_dirty: bool | None,
) -> dict:
    """Create the browser/editor and artifact handoff manifest."""
    page_records: list[dict] = []
    for page in pages:
        sources = [
            source_record(page["_manifest_path"], project),
            source_record(page["_source_path"], project),
        ]
        for optional in ("prompt_source", "animation_asset"):
            path = page.get(f"_{optional}_path")
            if path:
                sources.append(source_record(path, project))
        if page.get("_artwork_path"):
            sources.append(source_record(page["_artwork_path"], project))
        if page.get("_print_artwork_path") and page["_print_artwork_path"] != page.get("_artwork_path"):
            sources.append(source_record(page["_print_artwork_path"], project))
        for asset_field in ("_barcode_asset_path", "_qr_asset_path"):
            if page.get(asset_field):
                sources.append(source_record(page[asset_field], project))
        page_records.append(
            {
                "id": page["id"],
                "number": page["_number"],
                "kind": page["kind"],
                "layout": page["layout"],
                "title": page["title"],
                "sources": sources,
            }
        )
    return {
        "schema_version": 1,
        "profile": "magazine",
        "profile_version": load_toml(MANIFEST_PATH)["version"],
        "edition": {
            "id": edition["id"],
            "title": edition["title"],
            "edition_number": edition["edition_number"],
            "version": edition["version"],
            "language": edition["language"],
        },
        "theme": theme_id,
        "route": config["web"]["route"],
        "source_revision": revision,
        "declared_source_revision": declared_revision,
        "source_dirty": source_dirty,
        "sources": [
            source_record(project / "beacon-project.toml", project),
            source_record(
                safe_path(project, config["magazine"]["edition_manifest"]),
                project,
            ),
        ],
        "editor": config["editor"],
        "pages": page_records,
        "artifacts": {
            "digital_pdf": "magazine.pdf",
            "print_pdf": "magazine-print.pdf",
            "web": "web/index.html",
        },
    }


def artwork_html(page: dict, web_dir: Path) -> str:
    """Copy optional artwork and return an accessible image element."""
    artwork = page.get("artwork")
    if not artwork:
        return ""
    source = page["_artwork_path"]
    assets = web_dir / "assets"
    assets.mkdir(exist_ok=True)
    destination = assets / f"{page['id']}-{source.name}"
    shutil.copy2(source, destination)
    fit_class = " artwork-contain" if artwork["fit"] == "contain" else ""
    return (
        f'<img class="artwork{fit_class}" src="assets/{html.escape(destination.name)}" '
        f'alt="{html.escape(artwork["alt"], quote=True)}">'
    )


def back_cover_html(page: dict, web_dir: Path) -> str:
    """Render structured back-cover metadata as a definition list."""
    metadata = page.get("back_cover")
    if not metadata:
        return ""
    rows: list[tuple[str, object]] = [
        ("Description", metadata.get("description")),
        ("Creator", metadata.get("creator")),
        ("Copyright", metadata.get("copyright")),
        ("License", metadata.get("license")),
        ("Version", metadata.get("version")),
        ("System", metadata.get("system_line")),
        ("ISBN", metadata.get("isbn")),
    ]
    items = "".join(
        f"<dt>{html.escape(label)}</dt><dd>{html.escape(str(value))}</dd>"
        for label, value in rows
        if value
    )
    if metadata.get("qr_url"):
        url = html.escape(str(metadata["qr_url"]), quote=True)
        items += f'<dt>QR destination</dt><dd><a href="{url}">{url}</a></dd>'
    assets_html: list[str] = []
    for asset_field, label in (
        ("barcode_asset", "Publication barcode"),
        ("qr_asset", "QR code"),
    ):
        source = page.get(f"_{asset_field}_path")
        if source:
            assets = web_dir / "assets"
            assets.mkdir(exist_ok=True)
            destination = assets / f"{page['id']}-{asset_field}-{source.name}"
            shutil.copy2(source, destination)
            assets_html.append(
                f'<img class="publication-code" src="assets/{html.escape(destination.name)}" '
                f'alt="{html.escape(label, quote=True)}">'
            )
    asset_group = (
        '<div class="publication-codes">' + "".join(assets_html) + "</div>"
        if assets_html
        else ""
    )
    return f'<dl class="back-cover-meta">{items}</dl>{asset_group}'


def build_web(
    output: Path,
    config: dict,
    edition: dict,
    theme: dict,
    pages: list[dict],
    manifest: dict,
) -> Path:
    """Build the responsive semantic web edition."""
    web_dir = output / "web"
    web_dir.mkdir()
    page_html: list[str] = []
    navigation: list[str] = []
    for page in pages:
        body = markdown_fragment(page["_source_path"], "html5")
        artwork = artwork_html(page, web_dir)
        diagram = ""
        if page["layout"] == "diagram":
            diagram = (
                '<div class="flow-diagram" role="img" aria-label="Edition and page sources flow through validation and deterministic rendering to digital PDF, print PDF, and web outputs.">'
                "<div>Edition + page sources</div><span aria-hidden=\"true\">↓</span>"
                "<div>Validate + review</div><span aria-hidden=\"true\">↓</span>"
                "<div>Deterministic render</div><span aria-hidden=\"true\">↓</span>"
                "<div>Digital PDF / Print PDF / Web edition</div></div>"
            )
        page_id = f"page-{page['id']}"
        navigation.append(
            f'<li><a href="#{page_id}">{html.escape(page["title"])}</a></li>'
        )
        edition_meta = ""
        if page["kind"] == "cover":
            edition_meta = (
                f'<p class="edition-meta">Issue {html.escape(edition["edition_number"])} / '
                f'{html.escape(edition.get("edition_name", ""))} / version {html.escape(edition["version"])}</p>'
            )
        page_html.append(
            f'<article id="{page_id}" class="magazine-page page-{html.escape(page["kind"])} layout-{html.escape(page["layout"])}" '
            f'data-page-id="{html.escape(page["id"])}" data-source="{html.escape(page["_source_relative"])}" '
            f'aria-labelledby="{page_id}-title">'
            + artwork
            + '<div class="page-overlay">'
            + f'<p class="kicker">{html.escape(page["kicker"])}</p>'
            + f'<h1 id="{page_id}-title">{html.escape(page["title"])}</h1>'
            + f'<p class="deck">{html.escape(page["deck"])}</p>'
            + f'<div class="page-body">{body}</div>'
            + diagram
            + back_cover_html(page, web_dir)
            + edition_meta
            + f'<span class="page-number" aria-label="Page {page["_number"]}">{page["_number"]:02d}</span>'
            + "</div></article>"
        )

    manifest_json = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest_json = manifest_json.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    edition_label = f"Issue {edition['edition_number']}"
    if edition.get("edition_name"):
        edition_label += f" / {edition['edition_name']}"
    replacements = {
        "BEACON_LANG": html.escape(edition["language"], quote=True),
        "BEACON_DESCRIPTION": html.escape(edition["description"], quote=True),
        "BEACON_TITLE": html.escape(edition["title"]),
        "BEACON_EDITION_LABEL": html.escape(edition_label),
        "BEACON_PUBLISHER": html.escape(config["project"]["publisher"]),
        "BEACON_PRIMARY": theme["primary"],
        "BEACON_ACCENT": theme["accent"],
        "BEACON_HIGHLIGHT": theme["highlight"],
        "BEACON_SURFACE": theme["surface"],
        "BEACON_PAPER": theme["paper"],
        "BEACON_INK": theme["ink"],
        "BEACON_MUTED": theme["muted"],
        "BEACON_NAVIGATION": "".join(navigation),
        "BEACON_PAGES": "".join(page_html),
        "BEACON_ROUTE": html.escape(config["web"]["route"]),
        "BEACON_MANIFEST": manifest_json,
    }
    rendered = (ROOT / "web" / "magazine.html").read_text(encoding="utf-8")
    for marker, value in replacements.items():
        rendered = rendered.replace(marker, value)
    destination = web_dir / "index.html"
    destination.write_text(rendered, encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--theme")
    arguments = parser.parse_args()

    project = resolve_from_cwd(arguments.project)
    output = resolve_from_cwd(arguments.output)
    if output in {Path("/"), project, ROOT} or output in project.parents:
        raise SystemExit(f"refusing unsafe output directory: {output}")
    if not (project / "beacon-project.toml").is_file():
        raise SystemExit(f"missing magazine project: {project}")

    initial_config = load_toml(project / "beacon-project.toml")
    theme_id = arguments.theme or initial_config["beacon"]["theme"]
    config, edition, theme, pages = load_project(project, theme_id)
    epoch = int(config["provenance"]["source_date_epoch"])
    declared_revision = config["provenance"].get("source_revision", "working-tree")
    revision, source_dirty = git_state(project, declared_revision)

    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    work = output / "source"
    work.mkdir()
    shutil.copy2(project / "beacon-project.toml", work / "beacon-project.toml")
    shutil.copytree(project / "magazine", work / "magazine")
    shutil.copy2(ROOT / "latex" / "beacon-magazine.sty", work / "beacon-magazine.sty")

    work_config, work_edition, work_theme, work_pages = load_project(work, theme_id)
    manifest = publication_manifest(
        config,
        edition,
        pages,
        project,
        theme_id,
        revision,
        declared_revision,
        source_dirty,
    )
    (output / "publication-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    digital_pdf = build_pdf(
        work,
        output,
        work_config,
        work_edition,
        work_theme,
        work_pages,
        print_mode=False,
        epoch=epoch,
    )
    print_pdf = build_pdf(
        work,
        output,
        work_config,
        work_edition,
        work_theme,
        work_pages,
        print_mode=True,
        epoch=epoch,
    )
    web = build_web(output, config, edition, theme, pages, manifest)

    provenance = {
        "schema_version": 1,
        "profile": "magazine",
        "profile_version": load_toml(MANIFEST_PATH)["version"],
        "theme": theme_id,
        "edition_id": edition["id"],
        "edition_version": edition["version"],
        "source_repository": config["provenance"]["source_repository"],
        "source_path": config["provenance"].get("source_path", "."),
        "source_revision": revision,
        "declared_source_revision": declared_revision,
        "source_dirty": source_dirty,
        "source_date_epoch": epoch,
        "artifacts": {
            "magazine.pdf": sha256(digital_pdf),
            "magazine-print.pdf": sha256(print_pdf),
            "web/index.html": sha256(web),
            "publication-manifest.json": sha256(output / "publication-manifest.json"),
        },
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Built {digital_pdf}")
    print(f"Built {print_pdf}")
    print(f"Built {web}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
