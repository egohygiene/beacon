#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Create a standalone evidence-first technical-whitepaper workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPY_ENTRIES = (
    ".gitignore",
    "Makefile",
    "PROVENANCE.md",
    "PUBLISHING.md",
    "README.md",
    "Taskfile.yml",
    "VERSION_HISTORY.md",
    "beacon-template.toml",
    "evidence",
    "manuscript",
    "metadata",
    "scripts/check.py",
    "scripts/tasks.py",
    "templates",
    "themes",
    "whitepaper.toml",
)
THEMES = {
    "egohygiene": ("product", "themes/product.json"),
    "neutral": ("organization", "themes/organization.json"),
    "organization": ("organization", "themes/organization.json"),
    "product": ("product", "themes/product.json"),
}


def slugify(value: str) -> str:
    """Return a stable lowercase project identifier."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "whitepaper"


def copy_entry(relative_path: str, destination: Path) -> None:
    """Copy one governed profile entry into a project workspace."""
    source = ROOT / relative_path
    target = destination / relative_path
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def main() -> int:
    """Parse arguments and materialize a customized whitepaper workspace."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--project-id")
    parser.add_argument("--theme", choices=tuple(THEMES))
    arguments = parser.parse_args()

    destination = Path(arguments.destination).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for relative_path in COPY_ENTRIES:
        copy_entry(relative_path, destination)

    today = dt.date.today()
    epoch = int(
        dt.datetime.combine(today, dt.time(), tzinfo=dt.timezone.utc).timestamp()
    )
    theme_id, theme_path = THEMES[arguments.theme or "organization"]
    project_id = arguments.project_id or slugify(arguments.title)

    metadata_path = destination / "metadata" / "whitepaper.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(
        {
            "title": arguments.title,
            "author": [arguments.author],
            "date": today.isoformat(),
            "source_repository": "https://github.com/OWNER/REPOSITORY",
            "source_revision": "working-tree",
            "contact": arguments.author,
        }
    )
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    config_path = destination / "whitepaper.toml"
    config = config_path.read_text(encoding="utf-8")
    config = re.sub(
        r'(?m)^default_theme = ".*"$',
        f'default_theme = "{theme_path}"',
        config,
    )
    config = re.sub(
        r"(?m)^source_date_epoch = [0-9]+$",
        f"source_date_epoch = {epoch}",
        config,
    )
    config_path.write_text(config, encoding="utf-8")

    manifest = f"""[beacon]
schema_version = 1
profile = "technical-whitepaper"
profile_version = "0.1.0"
theme = {json.dumps(theme_id)}

[project]
id = {json.dumps(project_id, ensure_ascii=False)}
title = {json.dumps(arguments.title, ensure_ascii=False)}
author = {json.dumps(arguments.author, ensure_ascii=False)}
stage = "draft"

[provenance]
source_repository = "https://github.com/egohygiene/beacon"
source_path = "templates/technical-whitepaper"
source_revision = "working-tree"
source_date_epoch = {epoch}
"""
    (destination / "beacon-project.toml").write_text(manifest, encoding="utf-8")
    print(f"Created technical-whitepaper project at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
