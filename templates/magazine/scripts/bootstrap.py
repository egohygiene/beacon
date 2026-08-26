#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Create a standalone magazine project from Beacon's canonical scaffold."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    """Return a stable lowercase identifier for human-supplied text."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "magazine"


def toml_string(value: str) -> str:
    """Encode a human-supplied value as a TOML basic string."""
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--edition", required=True)
    arguments = parser.parse_args()

    destination = Path(arguments.destination).expanduser().resolve()
    if destination.exists():
        raise SystemExit(f"destination already exists: {destination}")
    if destination in {Path("/"), ROOT} or destination in ROOT.parents:
        raise SystemExit(f"refusing unsafe destination: {destination}")

    shutil.copytree(ROOT / "scaffold", destination)
    edition_path = destination / "magazine" / "edition.json"
    edition = json.loads(edition_path.read_text(encoding="utf-8"))
    edition["id"] = f"{slugify(arguments.title)}-{slugify(arguments.edition)}"
    edition["title"] = arguments.title
    edition["subtitle"] = f"A magazine published by {arguments.publisher}"
    edition["edition_number"] = arguments.edition
    edition["description"] = (
        f"{arguments.title}, issue {arguments.edition}, published by "
        f"{arguments.publisher}."
    )
    edition["creators"] = [
        {
            "name": arguments.publisher,
            "roles": ["publisher", "editorial direction"],
        }
    ]
    edition["rights"]["copyright"] = f"Copyright 2026 {arguments.publisher}"
    edition_path.write_text(
        json.dumps(edition, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    cover_path = destination / "magazine" / "pages" / "01-cover" / "page.json"
    cover = json.loads(cover_path.read_text(encoding="utf-8"))
    cover["kicker"] = f"Issue {arguments.edition} / {edition.get('edition_name', 'Edition')}"
    cover["title"] = arguments.title
    cover_path.write_text(
        json.dumps(cover, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    back_cover_path = (
        destination / "magazine" / "pages" / "08-back-cover" / "page.json"
    )
    back_cover_page = json.loads(back_cover_path.read_text(encoding="utf-8"))
    back_cover = back_cover_page["back_cover"]
    back_cover["description"] = edition["description"]
    back_cover["creator"] = arguments.publisher
    back_cover["copyright"] = f"Copyright 2026 {arguments.publisher}"
    back_cover_path.write_text(
        json.dumps(back_cover_page, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    credits_path = destination / "magazine" / "pages" / "07-credits" / "content.md"
    credits = credits_path.read_text(encoding="utf-8").replace(
        "**Publisher and editorial direction:** Ego Hygiene",
        f"**Publisher and editorial direction:** {arguments.publisher}",
    )
    credits_path.write_text(credits, encoding="utf-8")

    config_path = destination / "beacon-project.toml"
    config = config_path.read_text(encoding="utf-8")
    config = re.sub(
        r'(?m)^id = "[^"]+"$', f'id = "{slugify(arguments.title)}"', config, count=1
    )
    config = re.sub(
        r'(?m)^publisher = "[^"]+"$',
        lambda _: f"publisher = {toml_string(arguments.publisher)}",
        config,
        count=1,
    )
    config = re.sub(
        r'(?m)^product = "[^"]+"$',
        lambda _: f"product = {toml_string(arguments.title)}",
        config,
        count=1,
    )
    config = re.sub(
        r'(?m)^source_repository = "[^"]+"$',
        'source_repository = "https://github.com/OWNER/REPOSITORY"',
        config,
        count=1,
    )
    config = re.sub(
        r'(?m)^source_path = "[^"]+"$', 'source_path = "."', config, count=1
    )
    config_path.write_text(config, encoding="utf-8")

    print(f"Created magazine project at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
