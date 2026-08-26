#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Expose the project-owned NIH/NIMH build contract to any task runner."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTACHMENTS = (
    "project-summary-abstract",
    "project-narrative",
    "specific-aims",
    "research-strategy",
    "bibliography-references",
)


def run(command: list[str], *, environment: dict[str, str] | None = None) -> None:
    """Run one checked command from the proposal root."""
    print("+ " + " ".join(command))
    subprocess.run(command, cwd=ROOT, env=environment, check=True)


def resolve_output(value: str) -> Path:
    """Resolve a generated-output path relative to the proposal root."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def latex_sources() -> list[str]:
    """Return every separately rendered grant attachment source."""
    return [f"attachments/{attachment}.tex" for attachment in ATTACHMENTS]


def build(output: Path) -> None:
    """Build all separately uploadable proposal attachments."""
    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["BEACON_BUILD_DIR"] = str(output)
    run(["latexmk", "-r", "latexmkrc", "-pdf", *latex_sources()], environment=environment)


def validate(output: Path, python: str) -> None:
    """Inspect attachment structure and proposal readiness gates."""
    run(
        [
            python,
            str(ROOT / "scripts" / "check.py"),
            f"--build-dir={output}",
        ]
    )


def clean(output: Path) -> None:
    """Clean LaTeX intermediates and remove only the selected output directory."""
    if output in {Path("/"), ROOT} or ROOT not in output.parents:
        raise RuntimeError(f"refusing unsafe clean target: {output}")
    environment = os.environ.copy()
    environment["BEACON_BUILD_DIR"] = str(output)
    run(["latexmk", "-r", "latexmkrc", "-C", *latex_sources()], environment=environment)
    shutil.rmtree(output, ignore_errors=True)


def parse_arguments() -> argparse.Namespace:
    """Parse the stable proposal task interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("build", "check", "clean"))
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    """Dispatch one NIH/NIMH proposal task."""
    arguments = parse_arguments()
    output = resolve_output(arguments.build_dir)
    if arguments.command == "build":
        build(output)
    elif arguments.command == "check":
        build(output)
        validate(output, arguments.python)
    elif arguments.command == "clean":
        clean(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
