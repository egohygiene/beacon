#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Expose the project-owned technical-whitepaper contract to any task runner."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPRODUCIBLE_ARTIFACTS = (Path("whitepaper.pdf"), Path("web/index.html"))


def run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    """Run one checked command from the whitepaper root."""
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def resolve(value: str) -> Path:
    """Resolve a user path relative to the whitepaper root."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def source_date_epoch(override: int | None) -> int:
    """Return the requested epoch or the project-pinned value."""
    if override is not None:
        return override
    with (ROOT / "whitepaper.toml").open("rb") as stream:
        return int(tomllib.load(stream)["source_date_epoch"])


def build(
    output: Path,
    theme: Path,
    epoch: int,
    pandoc: str,
    pdf_engine: str,
) -> None:
    """Build synchronized PDF and accessible web outputs."""
    output.mkdir(parents=True, exist_ok=True)
    (output / "web").mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(epoch)
    common = [
        "manuscript/whitepaper.md",
        "--from=markdown+raw_attribute",
        "--citeproc",
        "--metadata-file=metadata/whitepaper.json",
        f"--metadata-file={theme}",
        "--bibliography=manuscript/references.bib",
        "--table-of-contents",
    ]
    run(
        [
            pandoc,
            *common,
            "--template=templates/whitepaper.tex",
            f"--pdf-engine={pdf_engine}",
            f"--output={output / 'whitepaper.pdf'}",
        ],
        environment=environment,
    )
    run(
        [
            pandoc,
            *common,
            "--template=templates/whitepaper.html",
            "--standalone",
            f"--output={output / 'web' / 'index.html'}",
        ],
        environment=environment,
    )


def validate(
    output: Path,
    theme: Path,
    python: str,
    *,
    check_external_links: bool = False,
) -> None:
    """Validate evidence, rendered output, accessibility, and readiness."""
    command = [
        python,
        str(ROOT / "scripts" / "check.py"),
        f"--build-dir={output}",
        f"--theme={theme}",
    ]
    if check_external_links:
        command.append("--check-external-links")
    run(command)


def compare_file(first: Path, second: Path) -> None:
    """Fail when two expected deterministic artifacts differ."""
    if first.read_bytes() != second.read_bytes():
        raise RuntimeError(f"reproducibility mismatch: {first.name}")


def verify_reproducibility(
    theme: Path,
    epoch: int,
    pandoc: str,
    pdf_engine: str,
) -> None:
    """Build twice in clean directories and compare governed artifacts."""
    with tempfile.TemporaryDirectory(prefix="beacon-whitepaper-") as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        build(first, theme, epoch, pandoc, pdf_engine)
        build(second, theme, epoch, pandoc, pdf_engine)
        for relative in REPRODUCIBLE_ARTIFACTS:
            compare_file(first / relative, second / relative)
    print("PASS reproducible PDF and web outputs.")


def clean(output: Path) -> None:
    """Remove only the selected generated output directory."""
    if output in {Path("/"), ROOT} or ROOT not in output.parents:
        raise RuntimeError(f"refusing unsafe clean target: {output}")
    shutil.rmtree(output, ignore_errors=True)


def parse_arguments() -> argparse.Namespace:
    """Parse the stable whitepaper task interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "build",
            "check",
            "check-content",
            "check-links",
            "clean",
            "reproducibility",
        ),
    )
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--theme", default="themes/organization.json")
    parser.add_argument("--source-date-epoch", type=int)
    parser.add_argument("--pandoc", default="pandoc")
    parser.add_argument("--pdf-engine", default="pdflatex")
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    """Dispatch one technical-whitepaper project task."""
    arguments = parse_arguments()
    output = resolve(arguments.build_dir)
    theme = resolve(arguments.theme)
    epoch = source_date_epoch(arguments.source_date_epoch)

    if arguments.command == "build":
        build(output, theme, epoch, arguments.pandoc, arguments.pdf_engine)
    elif arguments.command == "check-content":
        build(output, theme, epoch, arguments.pandoc, arguments.pdf_engine)
        validate(output, theme, arguments.python)
    elif arguments.command == "check-links":
        build(output, theme, epoch, arguments.pandoc, arguments.pdf_engine)
        validate(output, theme, arguments.python, check_external_links=True)
    elif arguments.command == "reproducibility":
        verify_reproducibility(theme, epoch, arguments.pandoc, arguments.pdf_engine)
    elif arguments.command == "check":
        build(output, theme, epoch, arguments.pandoc, arguments.pdf_engine)
        validate(output, theme, arguments.python)
        verify_reproducibility(theme, epoch, arguments.pandoc, arguments.pdf_engine)
    elif arguments.command == "clean":
        clean(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
