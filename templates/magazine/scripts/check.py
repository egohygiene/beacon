#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate Beacon magazine source contracts and rendered artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
HEX = re.compile(r"^[0-9A-Fa-f]{6}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME|REPLACE ME)\b", re.IGNORECASE)
RAW_RENDERER = re.compile(
    r"(?:\\(?:documentclass|usepackage|begin\{|end\{|input\{|include\{)|<[A-Za-z][^>]*>)"
)
ALLOWED_KINDS = {"cover", "inside-cover", "article", "credits", "back-cover"}
ALLOWED_LAYOUTS = {
    "cover",
    "opener",
    "feature",
    "diagram",
    "split",
    "quote",
    "credits",
    "back-cover",
    "full-bleed-artwork",
}
REQUIRED_REVIEWS = ("editorial", "accessibility", "rights", "print_proof")


def load_toml(path: Path) -> dict:
    """Load TOML from disk."""
    with path.open("rb") as stream:
        return tomllib.load(stream)


def load_json(path: Path) -> dict:
    """Load JSON from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_from_cwd(value: str) -> Path:
    """Resolve a command-line path from the caller's working directory."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()


def safe_path(base: Path, value: object, errors: list[str], context: str) -> Path | None:
    """Resolve a declared path and report absolute/traversal failures."""
    if not isinstance(value, str) or not value:
        errors.append(f"{context}: path must be a non-empty string")
        return None
    relative = Path(value)
    if relative.is_absolute():
        errors.append(f"{context}: absolute path is not allowed: {value}")
        return None
    candidate = (base / relative).resolve()
    if candidate != base and base not in candidate.parents:
        errors.append(f"{context}: path escapes its source boundary: {value}")
        return None
    return candidate


def sha256(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def contrast_ratio(first: str, second: str) -> float:
    """Compute WCAG relative contrast for two six-digit hexadecimal colors."""
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted((luminance(first), luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def required_string(data: dict, field: str, errors: list[str], context: str) -> str:
    """Validate and return a required non-empty string."""
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{context}: required string is missing: {field}")
        return ""
    return value


def pdf_checks(
    path: Path,
    *,
    expected_pages: int,
    expected_width: float,
    expected_height: float,
    expected_trim: tuple[float, float, float, float] | None,
    errors: list[str],
) -> None:
    """Validate PDF structure, page geometry, safety, and font embedding."""
    if not path.is_file() or path.stat().st_size == 0:
        errors.append(f"missing or empty PDF: {path}")
        return
    try:
        info = subprocess.run(
            ["pdfinfo", "-box", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        fonts = subprocess.run(
            ["pdffonts", str(path)],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        errors.append(f"PDF inspection failed for {path.name}: {error}")
        return

    pages = re.search(r"^Pages:\s+(\d+)", info, re.MULTILINE)
    if pages is None or int(pages.group(1)) != expected_pages:
        observed = pages.group(1) if pages else "missing"
        errors.append(f"{path.name}: expected {expected_pages} pages, found {observed}")
    size = re.search(r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts", info, re.MULTILINE)
    if size is None:
        errors.append(f"{path.name}: page size is unavailable")
    else:
        observed_width, observed_height = float(size.group(1)), float(size.group(2))
        if abs(observed_width - expected_width) > 1 or abs(observed_height - expected_height) > 1:
            errors.append(
                f"{path.name}: expected {expected_width:.2f} x {expected_height:.2f} pt, "
                f"found {observed_width:.2f} x {observed_height:.2f} pt"
            )
    if expected_trim is not None:
        trim = re.search(
            r"^TrimBox:\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)",
            info,
            re.MULTILINE,
        )
        if trim is None:
            errors.append(f"{path.name}: PDF TrimBox is missing")
        else:
            observed = tuple(float(trim.group(index)) for index in range(1, 5))
            if any(abs(first - second) > 0.25 for first, second in zip(observed, expected_trim)):
                errors.append(f"{path.name}: unexpected TrimBox {observed}; expected {expected_trim}")
    if re.search(r"^Encrypted:\s+yes", info, re.MULTILINE):
        errors.append(f"{path.name}: PDF must not be encrypted")
    if re.search(r"^JavaScript:\s+yes", info, re.MULTILINE):
        errors.append(f"{path.name}: PDF must not contain JavaScript")
    rows = [line for line in fonts.splitlines()[2:] if line.strip()]
    if not rows:
        errors.append(f"{path.name}: no fonts were reported")
    elif any(
        re.search(r"\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", row)
        for row in rows
    ):
        errors.append(f"{path.name}: all fonts must be embedded")


def validate_theme(theme: dict, errors: list[str]) -> None:
    """Validate the Identity-compatible fallback theme projection."""
    for field in (
        "id",
        "label",
        "publisher",
        "product",
        "primary",
        "accent",
        "highlight",
        "surface",
        "paper",
        "ink",
        "muted",
    ):
        required_string(theme, field, errors, "theme")
    for field in ("primary", "accent", "highlight", "surface", "paper", "ink", "muted"):
        value = str(theme.get(field, ""))
        if not HEX.fullmatch(value):
            errors.append(f"theme: {field} must contain six hexadecimal digits")
    if all(HEX.fullmatch(str(theme.get(field, ""))) for field in ("ink", "paper")):
        if contrast_ratio(theme["ink"], theme["paper"]) < 4.5:
            errors.append("theme: ink/paper contrast must be at least 4.5:1")
    if all(HEX.fullmatch(str(theme.get(field, ""))) for field in ("primary", "paper")):
        if contrast_ratio(theme["primary"], theme["paper"]) < 4.5:
            errors.append("theme: primary/paper contrast must be at least 4.5:1")
    for foreground, background in (
        ("accent", "paper"),
        ("accent", "surface"),
        ("muted", "paper"),
        ("muted", "surface"),
    ):
        if all(
            HEX.fullmatch(str(theme.get(field, "")))
            for field in (foreground, background)
        ) and contrast_ratio(theme[foreground], theme[background]) < 4.5:
            errors.append(
                f"theme: {foreground}/{background} contrast must be at least 4.5:1"
            )
    if all(
        HEX.fullmatch(str(theme.get(field, "")))
        for field in ("highlight", "surface")
    ) and contrast_ratio(theme["highlight"], theme["surface"]) < 3:
        errors.append("theme: highlight/surface UI contrast must be at least 3:1")
    if HEX.fullmatch(str(theme.get("primary", ""))):
        if contrast_ratio(theme["primary"], "FFFFFF") < 4.5:
            errors.append("theme: white/primary contrast must be at least 4.5:1")


def validate_page(
    page: dict,
    page_path: Path,
    project: Path,
    errors: list[str],
    placeholders: list[str],
) -> dict:
    """Validate one page manifest and its declared source assets."""
    context = page_path.relative_to(project).as_posix()
    if page.get("schema_version") != 1:
        errors.append(f"{context}: schema_version must be 1")
    page_id = required_string(page, "id", errors, context)
    if page_id and not SLUG.fullmatch(page_id):
        errors.append(f"{context}: id must be a lowercase stable slug")
    kind = required_string(page, "kind", errors, context)
    layout = required_string(page, "layout", errors, context)
    if kind not in ALLOWED_KINDS:
        errors.append(f"{context}: unsupported page kind: {kind}")
    if layout not in ALLOWED_LAYOUTS:
        errors.append(f"{context}: unsupported page layout: {layout}")
    for field in ("kicker", "title", "deck"):
        required_string(page, field, errors, context)

    allowed_by_kind = {
        "cover": {"cover", "full-bleed-artwork"},
        "inside-cover": {"opener", "quote", "full-bleed-artwork"},
        "article": {"feature", "diagram", "split", "quote", "full-bleed-artwork"},
        "credits": {"credits", "full-bleed-artwork"},
        "back-cover": {"back-cover", "full-bleed-artwork"},
    }
    if kind in allowed_by_kind and layout not in allowed_by_kind[kind]:
        errors.append(f"{context}: layout {layout} is incompatible with kind {kind}")

    source_path = safe_path(page_path.parent, page.get("source"), errors, context)
    if source_path is not None:
        if source_path.suffix.lower() != ".md":
            errors.append(f"{context}: page source must be Markdown")
        elif not source_path.is_file():
            errors.append(f"{context}: missing page source: {page.get('source')}")
        else:
            source = source_path.read_text(encoding="utf-8")
            if not source.strip():
                errors.append(f"{context}: page source is empty")
            if RAW_RENDERER.search(source):
                errors.append(f"{context}: Markdown contains renderer-specific HTML or LaTeX")
            if PLACEHOLDER.search(source):
                placeholders.append(source_path.relative_to(project).as_posix())

    for optional in ("prompt_source", "animation_asset"):
        if page.get(optional):
            optional_path = safe_path(page_path.parent, page[optional], errors, context)
            if optional_path is not None and not optional_path.is_file():
                errors.append(f"{context}: missing {optional}: {page[optional]}")

    artwork = page.get("artwork")
    if layout == "full-bleed-artwork" and not isinstance(artwork, dict):
        errors.append(f"{context}: full-bleed-artwork requires structured artwork metadata")
    if artwork is not None:
        if not isinstance(artwork, dict):
            errors.append(f"{context}: artwork must be an object")
        else:
            for field in ("path", "alt", "fit", "rights"):
                required_string(artwork, field, errors, f"{context} artwork")
            if artwork.get("fit") not in {"contain", "cover"}:
                errors.append(f"{context}: artwork fit must be contain or cover")
            artwork_path = safe_path(page_path.parent, artwork.get("path"), errors, context)
            if artwork_path is not None and not artwork_path.is_file():
                errors.append(f"{context}: artwork file is missing: {artwork.get('path')}")
            if artwork_path is not None and artwork_path.suffix.lower() == ".svg" and not artwork.get("print_path"):
                errors.append(f"{context}: SVG artwork requires a print_path for PDF output")
            if artwork.get("print_path"):
                print_path = safe_path(page_path.parent, artwork["print_path"], errors, context)
                if print_path is not None and not print_path.is_file():
                    errors.append(f"{context}: print artwork is missing: {artwork['print_path']}")

    if kind == "back-cover":
        metadata = page.get("back_cover")
        if not isinstance(metadata, dict):
            errors.append(f"{context}: back-cover requires a back_cover metadata object")
        else:
            for field in ("description", "creator", "copyright", "license", "version"):
                required_string(metadata, field, errors, f"{context} back_cover")
            for nullable in ("isbn", "barcode_asset", "qr_asset", "qr_url"):
                if (
                    nullable in metadata
                    and metadata[nullable] is not None
                    and not isinstance(metadata[nullable], str)
                ):
                    errors.append(f"{context}: {nullable} must be a string or null")
            for asset_field in ("barcode_asset", "qr_asset"):
                asset_value = metadata.get(asset_field)
                if isinstance(asset_value, str) and asset_value:
                    asset_path = safe_path(
                        page_path.parent,
                        asset_value,
                        errors,
                        f"{context} back_cover.{asset_field}",
                    )
                    if Path(asset_value).suffix.lower() not in {
                        ".png",
                        ".jpg",
                        ".jpeg",
                    }:
                        errors.append(
                            f"{context}: {asset_field} must be a PNG or JPEG image"
                        )
                    if asset_path is not None and not asset_path.is_file():
                        errors.append(f"{context}: {asset_field} file is missing")
            if (
                isinstance(metadata.get("qr_url"), str)
                and not re.fullmatch(r"https://[^\s]+", metadata["qr_url"])
            ):
                errors.append(f"{context}: qr_url must be an HTTPS URL")

    return {"id": page_id, "kind": kind, "layout": layout, "path": page_path}


def validate_web(
    html_path: Path,
    pages: list[dict],
    manifest: dict,
    errors: list[str],
) -> None:
    """Validate web semantics, navigation, images, and embedded editor data."""
    if not html_path.is_file() or html_path.stat().st_size == 0:
        errors.append(f"missing or empty web artifact: {html_path}")
        return
    rendered = html_path.read_text(encoding="utf-8")
    for marker in (
        '<html lang="',
        '<main id="content"',
        '<nav class="contents" aria-label="Table of contents">',
        'class="skip-link"',
        'id="beacon-publication-manifest" type="application/json"',
    ):
        if marker not in rendered:
            errors.append(f"web accessibility/editor marker is missing: {marker}")
    if "BEACON_" in rendered:
        errors.append("web artifact contains unresolved template markers")
    for page in pages:
        page_id = page["id"]
        if f'id="page-{page_id}"' not in rendered:
            errors.append(f"web artifact is missing page: {page_id}")
        if f'data-page-id="{page_id}"' not in rendered:
            errors.append(f"web editor marker is missing page ID: {page_id}")
    for image in re.findall(r"<img\b[^>]*>", rendered):
        alt = re.search(r'\balt="([^"]*)"', image)
        if alt is None or not alt.group(1).strip():
            errors.append("web artwork image has missing or empty alternative text")
    embedded = re.search(
        r'<script id="beacon-publication-manifest" type="application/json">(.*?)</script>',
        rendered,
        re.DOTALL,
    )
    if embedded is None:
        errors.append("web artifact has no embedded publication manifest")
    else:
        try:
            embedded_manifest = json.loads(embedded.group(1))
            if embedded_manifest != manifest:
                errors.append("embedded web manifest differs from publication-manifest.json")
        except json.JSONDecodeError as error:
            errors.append(f"embedded web manifest is invalid JSON: {error}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--build", required=True)
    parser.add_argument("--theme")
    arguments = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    placeholders: list[str] = []
    project = resolve_from_cwd(arguments.project)
    build = resolve_from_cwd(arguments.build)
    config_path = project / "beacon-project.toml"
    if not config_path.is_file():
        print(f"ERROR missing project configuration: {config_path}", file=sys.stderr)
        return 1
    config = load_toml(config_path)
    template_manifest = load_toml(ROOT / "beacon-template.toml")
    theme_id = arguments.theme or config.get("beacon", {}).get("theme", "neutral")
    theme_path = ROOT / "themes" / f"{theme_id}.toml"
    if not theme_path.is_file():
        errors.append(f"unknown magazine theme: {theme_id}")
        theme = {}
    else:
        theme = load_toml(theme_path)
        validate_theme(theme, errors)

    beacon = config.get("beacon", {})
    if beacon.get("schema_version") != 1:
        errors.append("beacon.schema_version must be 1")
    if beacon.get("profile") != "magazine":
        errors.append("beacon.profile must be magazine")
    if beacon.get("profile_version") != template_manifest.get("version"):
        errors.append("project profile_version must match the template manifest")
    project_data = config.get("project", {})
    project_id = required_string(project_data, "id", errors, "project")
    if project_id and not SLUG.fullmatch(project_id):
        errors.append("project.id must be a lowercase stable slug")
    required_string(project_data, "publisher", errors, "project")
    required_string(project_data, "product", errors, "project")

    manifest_value = config.get("magazine", {}).get("edition_manifest")
    edition_path = safe_path(project, manifest_value, errors, "magazine.edition_manifest")
    edition: dict = {}
    page_records: list[dict] = []
    if edition_path is not None and not edition_path.is_file():
        errors.append(f"edition manifest is missing: {manifest_value}")
    elif edition_path is not None:
        try:
            edition = load_json(edition_path)
        except (json.JSONDecodeError, OSError) as error:
            errors.append(f"edition manifest is invalid: {error}")

    if edition:
        if edition.get("schema_version") != 1:
            errors.append("edition.schema_version must be 1")
        edition_id = required_string(edition, "id", errors, "edition")
        if edition_id and not SLUG.fullmatch(edition_id):
            errors.append("edition.id must be a lowercase stable slug")
        for field in ("title", "edition_number", "date", "version", "language", "description"):
            required_string(edition, field, errors, "edition")
        if edition.get("date") and not DATE.fullmatch(str(edition["date"])):
            errors.append("edition.date must use YYYY-MM-DD")
        if edition.get("version") and not VERSION.fullmatch(str(edition["version"])):
            errors.append("edition.version must use semantic x.y.z form")
        creators = edition.get("creators")
        if not isinstance(creators, list) or not creators:
            errors.append("edition.creators must contain at least one creator")
        else:
            for index, creator in enumerate(creators):
                if not isinstance(creator, dict):
                    errors.append(f"edition creator {index} must be an object")
                    continue
                required_string(creator, "name", errors, f"edition creator {index}")
                if not isinstance(creator.get("roles"), list) or not creator["roles"]:
                    errors.append(f"edition creator {index} must declare roles")
        rights = edition.get("rights")
        if not isinstance(rights, dict):
            errors.append("edition.rights must be an object")
        else:
            required_string(rights, "copyright", errors, "edition.rights")
            required_string(rights, "license", errors, "edition.rights")

        page_values = edition.get("pages")
        if not isinstance(page_values, list) or len(page_values) < 4:
            errors.append("edition.pages must declare at least four ordered page manifests")
        elif edition_path is not None:
            for value in page_values:
                page_path = safe_path(edition_path.parent, value, errors, "edition.pages")
                if page_path is None:
                    continue
                if not page_path.is_file():
                    errors.append(f"declared page manifest is missing: {value}")
                    continue
                try:
                    page = load_json(page_path)
                except (json.JSONDecodeError, OSError) as error:
                    errors.append(f"invalid page manifest {value}: {error}")
                    continue
                page_records.append(
                    validate_page(page, page_path, project, errors, placeholders)
                )

    page_ids = [page["id"] for page in page_records if page["id"]]
    if len(page_ids) != len(set(page_ids)):
        errors.append("page IDs must be unique within an edition")
    kinds = [page["kind"] for page in page_records]
    for kind in ("cover", "credits", "back-cover"):
        if kinds.count(kind) != 1:
            errors.append(f"edition must contain exactly one {kind} page")
    if kinds.count("article") < 1:
        errors.append("edition must contain at least one article page")
    if kinds and kinds[0] != "cover":
        errors.append("the first declared page must be the cover")
    if kinds and kinds[-1] != "back-cover":
        errors.append("the final declared page must be the back cover")
    if "credits" in kinds and "back-cover" in kinds and kinds.index("credits") > kinds.index("back-cover"):
        errors.append("credits must appear before the back cover")

    print_config = config.get("print", {})
    numeric_print: dict[str, float] = {}
    for field in ("trim_width_in", "trim_height_in", "bleed_in", "safe_margin_in"):
        value = print_config.get(field)
        if not isinstance(value, (int, float)) or value <= 0:
            errors.append(f"print.{field} must be a positive number")
        else:
            numeric_print[field] = float(value)
    if print_config.get("crop_marks") is not True:
        errors.append("print.crop_marks must be true for the print-ready artifact")
    signature_multiple = print_config.get("signature_multiple")
    if not isinstance(signature_multiple, int) or signature_multiple <= 0:
        errors.append("print.signature_multiple must be a positive integer")
    elif page_records and len(page_records) % signature_multiple != 0:
        errors.append(
            f"edition page count {len(page_records)} is not divisible by signature_multiple {signature_multiple}"
        )
    if numeric_print.get("bleed_in", 0) < 0.125:
        errors.append("print.bleed_in must be at least 0.125 inches")
    if numeric_print.get("safe_margin_in", 0) < 0.375:
        errors.append("print.safe_margin_in must be at least 0.375 inches")

    route = required_string(config.get("web", {}), "route", errors, "web")
    if route and (not route.startswith("/") or ".." in route or route.endswith("/") and route != "/"):
        errors.append("web.route must be a stable absolute route without traversal or a trailing slash")
    editor = config.get("editor", {})
    if editor.get("schema_version") != 1:
        errors.append("editor.schema_version must be 1")
    if editor.get("source_model") != "edition-json+page-json+markdown":
        errors.append("editor.source_model must preserve the canonical structured source model")
    if editor.get("round_trip_safe") is not True:
        errors.append("editor.round_trip_safe must be true")
    if editor.get("branch_sync") != "pull-request":
        errors.append("editor.branch_sync must be pull-request")

    publication = config.get("publication", {})
    stage = publication.get("stage")
    if stage not in {"draft", "publication-ready"}:
        errors.append("publication.stage must be draft or publication-ready")
    expected_artifacts = {
        "pdf_artifact": "magazine.pdf",
        "print_artifact": "magazine-print.pdf",
        "web_artifact": "web/index.html",
    }
    for field, expected in expected_artifacts.items():
        if publication.get(field) != expected:
            errors.append(f"publication.{field} must be {expected}")
    provenance_config = config.get("provenance", {})
    source_repository = required_string(
        provenance_config, "source_repository", errors, "provenance"
    )
    revision = required_string(provenance_config, "source_revision", errors, "provenance")
    if not isinstance(provenance_config.get("source_date_epoch"), int):
        errors.append("provenance.source_date_epoch must be an integer")

    if stage == "publication-ready":
        if (
            not re.fullmatch(r"https://[^\s]+", source_repository)
            or "OWNER/REPOSITORY" in source_repository
        ):
            errors.append("publication-ready source_repository must be a concrete HTTPS URL")
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            errors.append("publication-ready source_revision must be a full commit SHA")
        for review in REQUIRED_REVIEWS:
            if config.get("review", {}).get(review) != "complete":
                errors.append(f"publication-ready review is incomplete: {review}")
        if publication.get("enabled") is not True:
            errors.append("publication-ready mode requires publication.enabled = true")
        if placeholders:
            errors.append(
                "publication-ready Markdown contains placeholders: " + ", ".join(sorted(set(placeholders)))
            )
    else:
        pending = [
            review
            for review in REQUIRED_REVIEWS
            if config.get("review", {}).get(review) != "complete"
        ]
        if pending:
            warnings.append("draft mode; pending reviews: " + ", ".join(pending))
        if not re.fullmatch(r"[0-9a-f]{40}", revision):
            warnings.append("draft mode; source_revision is not immutable")

    manifest_path = build / "publication-manifest.json"
    if not manifest_path.is_file():
        errors.append(f"missing publication manifest: {manifest_path}")
        manifest = {}
    else:
        try:
            manifest = load_json(manifest_path)
        except json.JSONDecodeError as error:
            errors.append(f"publication manifest is invalid JSON: {error}")
            manifest = {}
    if manifest:
        if manifest.get("profile") != "magazine":
            errors.append("publication manifest profile must be magazine")
        if manifest.get("route") != route:
            errors.append("publication manifest route differs from project route")
        manifest_pages = manifest.get("pages")
        if not isinstance(manifest_pages, list) or any(
            not isinstance(page, dict) for page in manifest_pages
        ):
            errors.append("publication manifest pages must be an ordered object list")
            manifest_pages = []
        elif [page.get("id") for page in manifest_pages] != page_ids:
            errors.append("publication manifest page order differs from canonical edition order")
        if manifest.get("editor") != editor:
            errors.append("publication manifest editor contract differs from project configuration")
        if manifest.get("declared_source_revision") != revision:
            errors.append("publication manifest declared revision differs from project configuration")
        source_dirty = manifest.get("source_dirty")
        if source_dirty is not None and not isinstance(source_dirty, bool):
            errors.append("publication manifest source_dirty must be boolean or null")
        if stage == "publication-ready":
            if manifest.get("source_revision") != revision:
                errors.append("publication-ready build revision differs from the pinned source revision")
            if source_dirty is True:
                errors.append("publication-ready build must use a clean project worktree")
        elif source_dirty is True:
            warnings.append("draft mode; project source contains uncommitted changes")

        expected_core_sources = ["beacon-project.toml"]
        if edition_path is not None:
            expected_core_sources.append(edition_path.relative_to(project).as_posix())
        manifest_sources = manifest.get("sources")
        if not isinstance(manifest_sources, list):
            errors.append("publication manifest must contain core source records")
            manifest_sources = []
        elif [
            record.get("path") for record in manifest_sources if isinstance(record, dict)
        ] != expected_core_sources:
            errors.append("publication manifest core source records differ from the project")

        all_source_records = list(manifest_sources)
        for manifest_page in manifest_pages:
            records = manifest_page.get("sources", [])
            if isinstance(records, list):
                all_source_records.extend(records)
            else:
                errors.append("publication manifest page sources must be a list")
        for index, record in enumerate(all_source_records):
            context = f"publication manifest source {index}"
            if not isinstance(record, dict):
                errors.append(f"{context}: record must be an object")
                continue
            source_path = safe_path(project, record.get("path"), errors, context)
            digest = record.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                errors.append(f"{context}: sha256 must be a lowercase digest")
            if source_path is None:
                continue
            if not source_path.is_file():
                errors.append(f"{context}: referenced source is missing")
            elif isinstance(digest, str) and sha256(source_path) != digest:
                errors.append(f"{context}: source hash differs from the project")

    if page_records and len(numeric_print) == 4:
        trim_width = numeric_print["trim_width_in"]
        trim_height = numeric_print["trim_height_in"]
        bleed = numeric_print["bleed_in"]
        pdf_checks(
            build / "magazine.pdf",
            expected_pages=len(page_records),
            expected_width=trim_width * 72,
            expected_height=trim_height * 72,
            expected_trim=None,
            errors=errors,
        )
        pdf_checks(
            build / "magazine-print.pdf",
            expected_pages=len(page_records),
            expected_width=(trim_width + 2 * bleed) * 72,
            expected_height=(trim_height + 2 * bleed) * 72,
            expected_trim=(
                bleed * 72,
                bleed * 72,
                (bleed + trim_width) * 72,
                (bleed + trim_height) * 72,
            ),
            errors=errors,
        )

    validate_web(build / "web" / "index.html", page_records, manifest, errors)

    provenance_path = build / "provenance.json"
    if not provenance_path.is_file():
        errors.append(f"missing provenance artifact: {provenance_path}")
    else:
        try:
            provenance = load_json(provenance_path)
            if provenance.get("profile") != "magazine":
                errors.append("provenance profile must be magazine")
            if manifest:
                for field in ("source_revision", "declared_source_revision", "source_dirty"):
                    if provenance.get(field) != manifest.get(field):
                        errors.append(f"provenance {field} differs from publication manifest")
            for artifact, expected_hash in provenance.get("artifacts", {}).items():
                artifact_path = build / artifact
                if not artifact_path.is_file():
                    errors.append(f"provenance references missing artifact: {artifact}")
                elif sha256(artifact_path) != expected_hash:
                    errors.append(f"provenance hash mismatch: {artifact}")
        except json.JSONDecodeError as error:
            errors.append(f"provenance artifact is invalid JSON: {error}")

    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)
    if errors:
        return 1
    print(
        f"PASS magazine checks ({stage} mode, {theme_id} theme, "
        f"{len(page_records)} pages, route {route})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
