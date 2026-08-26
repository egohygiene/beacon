#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Create a standalone project-owned research-paper workspace."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "scaffold"


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "research-paper"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--author", required=True)
    parser.add_argument("--project-id")
    parser.add_argument("--theme", choices=("neutral", "egohygiene"), default="neutral")
    arguments = parser.parse_args()

    destination = Path(arguments.destination).expanduser().resolve()
    if destination.exists() and any(destination.iterdir()):
        raise SystemExit(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SCAFFOLD, destination, dirs_exist_ok=True)

    today = dt.date.today()
    raw_replacements = {
        "@@TITLE@@": arguments.title,
        "@@AUTHOR@@": arguments.author,
        "@@PROJECT_ID@@": arguments.project_id or slug(arguments.title),
        "@@THEME@@": arguments.theme,
        "@@DATE@@": today.isoformat(),
        "@@SOURCE_DATE_EPOCH@@": str(int(dt.datetime.combine(today, dt.time(), tzinfo=dt.timezone.utc).timestamp())),
    }
    for path in sorted(destination.rglob("*")):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            replacements = raw_replacements
            if path.name == "beacon-project.toml":
                replacements = {
                    marker: json.dumps(value, ensure_ascii=False)[1:-1]
                    for marker, value in raw_replacements.items()
                }
            text = text.replace(
                'source_date_epoch = "@@SOURCE_DATE_EPOCH@@"',
                f"source_date_epoch = {raw_replacements['@@SOURCE_DATE_EPOCH@@']}",
            )
            for marker, value in replacements.items():
                text = text.replace(marker, value)
            path.write_text(text, encoding="utf-8")
    print(f"Created research-paper project at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
