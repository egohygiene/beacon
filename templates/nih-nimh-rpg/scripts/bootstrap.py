#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Create a standalone NIH/NIMH concept-proposal workspace."""

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
    "CHECKLIST.md",
    "Makefile",
    "PROVENANCE.md",
    "README.md",
    "SOURCES.md",
    "VERSION_HISTORY.md",
    "attachments",
    "beacon-template.toml",
    "common",
    "latexmkrc",
    "proposal.toml",
    "references.bib",
    "scripts/check.py",
    "sections",
    "styles",
)


def slugify(value: str) -> str:
    """Return a stable lowercase project identifier."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "nimh-proposal"


def latex_escape(value: str) -> str:
    """Escape plain user input for a LaTeX command value."""
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
    return "".join(replacements.get(character, character) for character in value)


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
    """Parse arguments and materialize a customized proposal workspace."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--project-id")
    arguments = parser.parse_args()

    destination = Path(arguments.destination).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    for relative_path in COPY_ENTRIES:
        copy_entry(relative_path, destination)

    metadata_path = destination / "common" / "metadata.tex"
    metadata = metadata_path.read_text(encoding="utf-8")
    replacements = {
        "ProjectTitle": latex_escape(arguments.title),
        "PrincipalInvestigator": latex_escape(arguments.author),
    }
    for command, value in replacements.items():
        metadata = re.sub(
            rf"(?m)^\\newcommand\{{\\{command}\}}\{{.*\}}$",
            lambda _match, command=command, value=value: (
                rf"\newcommand{{\{command}}}{{{value}}}"
            ),
            metadata,
        )
    metadata_path.write_text(metadata, encoding="utf-8")

    project_id = arguments.project_id or slugify(arguments.title)
    manifest = f"""[beacon]
schema_version = 1
profile = "nih-nimh-rpg"
profile_version = "0.1.0"

[project]
id = {json.dumps(project_id, ensure_ascii=False)}
title = {json.dumps(arguments.title, ensure_ascii=False)}
principal_investigator = {json.dumps(arguments.author, ensure_ascii=False)}
stage = "concept"

[provenance]
source_repository = "https://github.com/egohygiene/beacon"
source_path = "templates/nih-nimh-rpg"
source_revision = "working-tree"
initialized_on = "{dt.date.today().isoformat()}"
"""
    (destination / "beacon-project.toml").write_text(manifest, encoding="utf-8")
    print(f"Created NIH/NIMH proposal project at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
