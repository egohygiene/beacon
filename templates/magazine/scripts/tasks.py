#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Expose the project-owned magazine build contract to any task runner."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPRODUCIBLE_ARTIFACTS = (
    Path("magazine.pdf"),
    Path("magazine-print.pdf"),
    Path("web/index.html"),
    Path("publication-manifest.json"),
    Path("provenance.json"),
)


def run(command: list[str], *, capture_output: bool = False) -> str:
    """Run one checked command from the project build-kit root."""
    print("+ " + " ".join(command))
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        capture_output=capture_output,
        text=capture_output,
    )
    return completed.stdout if capture_output else ""


def resolve(value: str) -> Path:
    """Resolve a user path relative to the build-kit root."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def resolve_project(value: str) -> Path:
    """Resolve the initialized project or the profile reference scaffold."""
    if value != "auto":
        return resolve(value)
    if (ROOT / "magazine" / "edition.json").is_file():
        return ROOT
    return ROOT / "scaffold"


def build(project: Path, output: Path, theme: str, python: str) -> None:
    """Build synchronized digital, print, web, and provenance artifacts."""
    run(
        [
            python,
            str(ROOT / "scripts" / "build.py"),
            f"--project={project}",
            f"--output={output}",
            f"--theme={theme}",
        ]
    )


def validate(project: Path, output: Path, theme: str, python: str) -> None:
    """Validate the structured source and all rendered magazine artifacts."""
    run(
        [
            python,
            str(ROOT / "scripts" / "check.py"),
            f"--project={project}",
            f"--build={output}",
            f"--theme={theme}",
        ]
    )


def compare_file(first: Path, second: Path) -> None:
    """Fail when two expected deterministic artifacts differ."""
    if first.read_bytes() != second.read_bytes():
        raise RuntimeError(f"reproducibility mismatch: {first.name}")


def verify_reproducibility(
    project: Path, theme: str, python: str
) -> None:
    """Build twice in clean directories and compare governed artifacts."""
    with tempfile.TemporaryDirectory(prefix="beacon-magazine-") as temporary:
        temporary_root = Path(temporary)
        first = temporary_root / "first"
        second = temporary_root / "second"
        build(project, first, theme, python)
        build(project, second, theme, python)
        for relative in REPRODUCIBLE_ARTIFACTS:
            compare_file(first / relative, second / relative)
    print("PASS reproducible magazine artifact bundle.")


def bootstrap_check(python: str) -> None:
    """Prove the profile initializer emits a self-contained project."""
    initializer = ROOT / "scripts" / "bootstrap.py"
    if not initializer.is_file() or not (ROOT / "scaffold").is_dir():
        print("SKIP bootstrap-check is only applicable to the Beacon profile checkout.")
        return
    with tempfile.TemporaryDirectory(prefix="beacon-magazine-bootstrap-") as temporary:
        temporary_root = Path(temporary)
        project = temporary_root / "project"
        output = temporary_root / "build"
        run(
            [
                python,
                str(initializer),
                f"--destination={project}",
                "--title=Bootstrap Magazine",
                "--publisher=Bootstrap Publisher",
                "--edition=07",
            ]
        )
        build(project, output, "neutral", python)
        validate(project, output, "neutral", python)
        pdf_text = run(
            ["pdftotext", str(output / "magazine.pdf"), "-"],
            capture_output=True,
        )
        if "Bootstrap Magazine" not in pdf_text:
            raise RuntimeError("bootstrap title is missing from the rendered PDF")
        html = (output / "web" / "index.html").read_text(encoding="utf-8")
        if "Bootstrap Publisher" not in html:
            raise RuntimeError("bootstrap publisher is missing from the web output")
    print("PASS bootstrap customization evidence.")


def check_all(project: Path, python: str) -> None:
    """Verify both fallback themes and the standalone initializer."""
    for theme in ("neutral", "egohygiene"):
        output = ROOT / "build" / theme
        build(project, output, theme, python)
        validate(project, output, theme, python)
        verify_reproducibility(project, theme, python)
    bootstrap_check(python)


def clean(output: Path) -> None:
    """Remove only the selected generated output directory."""
    if output in {Path("/"), ROOT} or ROOT not in output.parents:
        raise RuntimeError(f"refusing unsafe clean target: {output}")
    shutil.rmtree(output, ignore_errors=True)


def parse_arguments() -> argparse.Namespace:
    """Parse the stable magazine project task interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "bootstrap-check",
            "build",
            "check",
            "check-all",
            "clean",
            "reproducibility",
        ),
    )
    parser.add_argument("--project", default="auto")
    parser.add_argument("--build-dir", default="build/neutral")
    parser.add_argument("--theme", choices=("neutral", "egohygiene"), default="neutral")
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    """Dispatch one magazine project task."""
    arguments = parse_arguments()
    project = resolve_project(arguments.project)
    output = resolve(arguments.build_dir)

    if arguments.command == "build":
        build(project, output, arguments.theme, arguments.python)
    elif arguments.command == "check":
        build(project, output, arguments.theme, arguments.python)
        validate(project, output, arguments.theme, arguments.python)
    elif arguments.command == "reproducibility":
        verify_reproducibility(project, arguments.theme, arguments.python)
    elif arguments.command == "bootstrap-check":
        bootstrap_check(arguments.python)
    elif arguments.command == "check-all":
        check_all(project, arguments.python)
    elif arguments.command == "clean":
        clean(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
