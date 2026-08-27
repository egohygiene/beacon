#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Expose the product-owned publication-hub contract to Make, Task, and Beacon."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from build import (
    ContractError,
    build_project,
    clean_output,
    load_catalog,
    validate_output,
)

ROOT = Path(__file__).resolve().parents[1]


def resolve(value: str) -> Path:
    """Resolve a path relative to the project-owned build-kit root."""
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def resolve_project(value: str) -> Path:
    """Resolve an initialized project or the profile's Antidote-style fixture."""
    if value != "auto":
        return resolve(value)
    if (ROOT / "publication-hub.json").is_file():
        return ROOT
    return ROOT / "fixtures" / "antidote-planned-magazine"


def tree_digest(root: Path) -> list[tuple[str, bytes]]:
    """Return stable path-and-byte records for one built public tree."""
    return [
        (path.relative_to(root).as_posix(), path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def verify_reproducibility(
    project: Path,
    theme: str,
    source_revision: str | None,
    require_deployable_revision: bool,
) -> None:
    """Build twice under the project and compare every governed output byte."""
    with tempfile.TemporaryDirectory(prefix=".hub-repro-", dir=project) as temporary:
        temporary_root = Path(temporary)
        first = build_project(
            project,
            temporary_root / "first",
            theme,
            source_revision,
            require_deployable_revision=require_deployable_revision,
        )
        second = build_project(
            project,
            temporary_root / "second",
            theme,
            source_revision,
            require_deployable_revision=require_deployable_revision,
        )
        if tree_digest(first) != tree_digest(second):
            raise ContractError("publication-hub reproducibility mismatch")
    print("PASS deterministic publication hub and checksum inventory.")


def run_tests(python: str) -> None:
    """Run only standard-library publication-hub contract tests."""
    environment = os.environ.copy()
    environment.pop("SOURCE_REVISION", None)
    subprocess.run(
        [
            python,
            "-m",
            "unittest",
            "discover",
            "--start-directory",
            str(ROOT / "tests"),
            "--pattern",
            "test_*.py",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )


def bootstrap_check(theme: str, python: str, source_revision: str | None) -> None:
    """Prove the initializer emits a complete standalone build kit."""
    initializer = ROOT / "scripts" / "bootstrap.py"
    if not (ROOT / "scaffold").is_dir() or not initializer.is_file():
        print("SKIP bootstrap-check is only applicable to the Beacon profile checkout.")
        return
    with tempfile.TemporaryDirectory(prefix="beacon-publication-hub-") as temporary:
        project = Path(temporary) / "project"
        subprocess.run(
            [
                python,
                str(initializer),
                f"--destination={project}",
                "--title=Standalone publication hub",
                "--author=Beacon Maintainers",
                f"--theme={theme}",
            ],
            cwd=ROOT,
            check=True,
        )
        build_project(project, project / "build", theme, source_revision)
        validate_output(project / "build")
        for required in (
            "CONTRACT.md",
            "MIGRATION.md",
            "Makefile",
            "OWNERSHIP.md",
            "Taskfile.yml",
            "UPGRADING.md",
            "beacon-template.toml",
            "contracts/publication-hub.schema.json",
            "contracts/publication-site.schema.json",
            "scripts/build.py",
            "scripts/check.py",
            "scripts/tasks.py",
            "tests/test_publication_hub.py",
        ):
            if not (project / required).is_file():
                raise ContractError(f"standalone bootstrap is missing {required}")
    print("PASS standalone publication-hub bootstrap.")


def parse_arguments() -> argparse.Namespace:
    """Parse the stable standalone project task interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "bootstrap-check",
            "build",
            "check",
            "check-content",
            "clean",
            "reproducibility",
            "test",
            "validate",
        ),
    )
    parser.add_argument("--project", default="auto")
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--theme", choices=("neutral", "egohygiene"), default="neutral")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--source-revision", default=os.environ.get("SOURCE_REVISION") or None)
    parser.add_argument(
        "--revision-policy", choices=("local", "deployment"), default="local"
    )
    return parser.parse_args()


def main() -> int:
    """Dispatch one publication-hub task without requiring Beacon."""
    arguments = parse_arguments()
    project = resolve_project(arguments.project)
    output = Path(arguments.build_dir).expanduser()
    if not output.is_absolute():
        output = project / output
    source_revision = (arguments.source_revision or "").strip() or None
    require_deployable = arguments.revision_policy == "deployment"

    if arguments.command == "build":
        build_project(
            project,
            output,
            arguments.theme,
            source_revision,
            require_deployable_revision=require_deployable,
        )
    elif arguments.command == "validate":
        catalog = load_catalog(
            project,
            arguments.theme,
            source_revision,
            require_deployable_revision=require_deployable,
        )
        validate_output(
            output,
            require_deployable_revision=require_deployable,
            expected_catalog=catalog,
        )
    elif arguments.command == "check-content":
        build_project(
            project,
            output,
            arguments.theme,
            source_revision,
            require_deployable_revision=require_deployable,
        )
        catalog = load_catalog(
            project,
            arguments.theme,
            source_revision,
            require_deployable_revision=require_deployable,
        )
        validate_output(
            output,
            require_deployable_revision=require_deployable,
            expected_catalog=catalog,
        )
    elif arguments.command == "reproducibility":
        verify_reproducibility(
            project, arguments.theme, source_revision, require_deployable
        )
    elif arguments.command == "test":
        run_tests(arguments.python)
    elif arguments.command == "bootstrap-check":
        bootstrap_check(arguments.theme, arguments.python, source_revision)
    elif arguments.command == "check":
        run_tests(arguments.python)
        build_project(
            project,
            output,
            arguments.theme,
            source_revision,
            require_deployable_revision=require_deployable,
        )
        catalog = load_catalog(
            project,
            arguments.theme,
            source_revision,
            require_deployable_revision=require_deployable,
        )
        validate_output(
            output,
            require_deployable_revision=require_deployable,
            expected_catalog=catalog,
        )
        verify_reproducibility(
            project, arguments.theme, source_revision, require_deployable
        )
    elif arguments.command == "clean":
        clean_output(project, output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as error:
        raise SystemExit(f"ERROR: {error}") from error
