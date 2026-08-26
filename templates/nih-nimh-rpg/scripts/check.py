#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Build-time structural and readiness checks for the NIH/NIMH profile."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ATTACHMENTS = (
    "project-summary-abstract",
    "project-narrative",
    "specific-aims",
    "research-strategy",
    "bibliography-references",
)

REQUIRED_SUBMISSION_FIELDS = (
    "activity_code",
    "funding_opportunity",
    "due_date",
    "applicant_organization",
    "authorized_submission_contact",
    "program_officer",
)


def pdf_info(path: Path) -> tuple[int, tuple[float, float], str]:
    """Return page count, first-page dimensions, and raw Poppler metadata."""

    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    pages_match = re.search(r"^Pages:\s+(\d+)$", result.stdout, re.MULTILINE)
    size_match = re.search(
        r"^Page size:\s+([0-9.]+) x ([0-9.]+) pts",
        result.stdout,
        re.MULTILINE,
    )
    if pages_match is None or size_match is None:
        raise ValueError(f"could not parse pdfinfo output for {path}")
    return (
        int(pages_match.group(1)),
        (float(size_match.group(1)), float(size_match.group(2))),
        result.stdout,
    )


def fonts_are_embedded(path: Path) -> bool:
    """Return whether Poppler reports at least one font and all are embedded."""

    result = subprocess.run(
        ["pdffonts", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    font_rows = [
        re.search(r"\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line)
        for line in result.stdout.splitlines()[2:]
    ]
    parsed_rows = [row for row in font_rows if row is not None]
    return bool(parsed_rows) and all(row.group(1) == "yes" for row in parsed_rows)


def source_files() -> list[Path]:
    """Return authored LaTeX sources that can contribute visible text."""

    roots = (ROOT / "attachments", ROOT / "sections")
    return sorted(path for directory in roots for path in directory.rglob("*.tex"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dir", default="build")
    arguments = parser.parse_args()
    build = Path(arguments.build_dir)
    if not build.is_absolute():
        build = ROOT / build

    errors: list[str] = []
    warnings: list[str] = []

    with (ROOT / "proposal.toml").open("rb") as proposal_file:
        proposal = tomllib.load(proposal_file)

    application = proposal["application"]
    limits = proposal["page_limits"]
    stage = application["stage"]
    if stage not in {"concept", "submission-ready"}:
        errors.append("proposal.toml: application.stage must be concept or submission-ready")

    page_limits = {
        "specific-aims": int(limits["specific_aims"]),
        "research-strategy": int(limits["research_strategy"]),
    }

    for attachment in ATTACHMENTS:
        pdf_path = build / f"{attachment}.pdf"
        if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            errors.append(f"missing or empty PDF: {pdf_path.relative_to(ROOT)}")
            continue
        try:
            pages, size, metadata = pdf_info(pdf_path)
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            errors.append(str(error))
            continue

        if not (611.0 <= size[0] <= 613.0 and 791.0 <= size[1] <= 793.0):
            errors.append(f"{attachment}.pdf is not US Letter: {size[0]} x {size[1]} pt")

        if re.search(r"^Encrypted:\s+yes", metadata, re.MULTILINE):
            errors.append(f"{attachment}.pdf must not be encrypted")
        if re.search(r"^JavaScript:\s+yes", metadata, re.MULTILINE):
            errors.append(f"{attachment}.pdf must not contain JavaScript")
        try:
            embedded = fonts_are_embedded(pdf_path)
        except (OSError, subprocess.CalledProcessError) as error:
            errors.append(str(error))
            embedded = False
        if not embedded:
            errors.append(f"{attachment}.pdf contains missing or unembedded fonts")

        limit = page_limits.get(attachment, 0)
        if limit > 0 and pages > limit:
            errors.append(f"{attachment}.pdf has {pages} pages; configured limit is {limit}")
        print(f"OK  {attachment}.pdf: {pages} page(s), US Letter")

    page_limited_sources = [
        ROOT / "attachments" / "specific-aims.tex",
        ROOT / "attachments" / "research-strategy.tex",
        *sorted((ROOT / "sections" / "research-strategy").glob("*.tex")),
    ]
    forbidden_link = re.compile(r"https?://|\\href\s*\{|\\url\s*\{")
    for path in page_limited_sources:
        if forbidden_link.search(path.read_text(encoding="utf-8")):
            errors.append(f"active URL or hyperlink command in {path.relative_to(ROOT)}")

    style = (ROOT / "styles" / "nih-attachment.sty").read_text(encoding="utf-8")
    for requirement in (
        r"\RequirePackage{helvet}",
        r"\RequirePackage[letterpaper,margin=0.6in]{geometry}",
        r"\pagestyle{empty}",
        r"\AtBeginDocument{\fontsize{11}{13}\selectfont}",
    ):
        if requirement not in style:
            errors.append(f"style guard missing: {requirement}")

    todo_count = sum(
        path.read_text(encoding="utf-8").count("\\TODO{") for path in source_files()
    )
    sample_reference = "SAMPLE ENTRY" in (ROOT / "references.bib").read_text(
        encoding="utf-8"
    )

    unresolved_fields = [
        field for field in REQUIRED_SUBMISSION_FIELDS if not application.get(field)
    ]
    if not application.get("program_officer_contacted"):
        unresolved_fields.append("program_officer_contacted")
    if page_limits["research-strategy"] <= 0:
        unresolved_fields.append("page_limits.research_strategy")

    if stage == "submission-ready":
        if unresolved_fields:
            errors.append("unresolved submission gates: " + ", ".join(unresolved_fields))
        if todo_count:
            errors.append(f"{todo_count} TODO marker(s) remain")
        if sample_reference:
            errors.append("sample bibliography entry remains")
    else:
        if unresolved_fields:
            warnings.append("concept mode; unresolved gates: " + ", ".join(unresolved_fields))
        if todo_count:
            warnings.append(f"concept mode; {todo_count} TODO marker(s) remain")
        if sample_reference:
            warnings.append("concept mode; sample bibliography entry remains")

    for warning in warnings:
        print(f"WARN {warning}")
    for error in errors:
        print(f"ERROR {error}", file=sys.stderr)

    if errors:
        return 1
    print(f"PASS NIH/NIMH profile structural checks ({stage} mode).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
