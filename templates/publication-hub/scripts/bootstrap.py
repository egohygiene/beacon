#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Create a standalone publication-hub project from the canonical scaffold."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_KIT_ENTRIES = (
    "CONTRACT.md",
    "MIGRATION.md",
    "Makefile",
    "OWNERSHIP.md",
    "Taskfile.yml",
    "UPGRADING.md",
    "beacon-template.toml",
    "contracts",
    "fixtures",
    "scripts",
    "tests",
)


def reject_json_constant(value: str) -> None:
    """Reject JavaScript's non-finite numeric extensions to JSON."""
    raise ValueError(f"non-finite JSON number: {value}")


def slugify(value: str) -> str:
    """Return a stable lowercase identifier for human-supplied text."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "publication-hub"


def copy_entry(relative_path: str, destination: Path) -> None:
    """Copy one project-owned build-kit entry into an initialized workspace."""
    source = ROOT / relative_path
    target = destination / relative_path
    if source.is_dir():
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns("build", "dist", "__pycache__", "*.pyc"),
        )
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> int:
    """Initialize one safe, self-contained draft publication hub."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--publisher")
    parser.add_argument("--project-id")
    parser.add_argument("--theme", choices=("neutral", "egohygiene"), default="neutral")
    arguments = parser.parse_args()

    destination = Path(arguments.destination).expanduser().resolve()
    if destination.exists():
        raise SystemExit(f"destination already exists: {destination}")
    if destination in {Path("/"), ROOT} or destination in ROOT.parents:
        raise SystemExit(f"refusing unsafe destination: {destination}")

    shutil.copytree(
        ROOT / "scaffold",
        destination,
        ignore=shutil.ignore_patterns("build", "dist", "__pycache__", "*.pyc"),
    )
    for relative_path in BUILD_KIT_ENTRIES:
        copy_entry(relative_path, destination)

    project_id = slugify(arguments.project_id or arguments.title)
    publisher = arguments.publisher or arguments.author
    catalog_path = destination / "publication-hub.json"
    catalog = json.loads(
        catalog_path.read_text(encoding="utf-8"),
        parse_constant=reject_json_constant,
    )
    catalog["site"]["id"] = project_id
    catalog["site"]["title"] = arguments.title
    catalog["site"]["description"] = (
        f"The canonical publication hub for {arguments.title}."
    )
    catalog["site"]["publisher"] = publisher
    catalog["site"]["theme"] = arguments.theme
    catalog["site"]["copy"]["heading"] = arguments.title
    catalog["site"]["copy"]["introduction"] = (
        f"Follow the paper, magazine, and verified releases for {arguments.title}."
    )
    catalog["site"]["brand"]["logo"]["alt"] = arguments.title
    catalog_path.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    manifest_path = destination / "beacon-project.toml"
    manifest = manifest_path.read_text(encoding="utf-8")
    manifest = manifest.replace('theme = "neutral"', f'theme = "{arguments.theme}"')
    manifest_path.write_text(manifest, encoding="utf-8")
    print(f"Created publication-hub project at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
