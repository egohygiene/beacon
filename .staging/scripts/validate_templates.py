#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate Beacon template packages using only the Python standard library."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "id",
    "name",
    "version",
    "description",
    "outputs",
    "metadata",
    "capabilities",
}

ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def validate_package(package_directory: Path) -> list[str]:
    """Return validation errors for one Beacon template package."""

    errors: list[str] = []
    manifest_path = package_directory / "beacon-template.toml"

    if not manifest_path.is_file():
        return [f"missing manifest: {manifest_path}"]

    with manifest_path.open("rb") as manifest_file:
        manifest = tomllib.load(manifest_file)

    missing_keys = sorted(REQUIRED_TOP_LEVEL_KEYS.difference(manifest))
    if missing_keys:
        errors.append(f"{manifest_path}: missing keys: {', '.join(missing_keys)}")
        return errors

    if manifest["schema_version"] != 1:
        errors.append(f"{manifest_path}: schema_version must be 1")

    template_id = manifest["id"]
    if not isinstance(template_id, str) or not ID_PATTERN.fullmatch(template_id):
        errors.append(f"{manifest_path}: id must be lowercase kebab-case")
    elif package_directory.name != template_id:
        errors.append(
            f"{manifest_path}: id '{template_id}' must match directory "
            f"'{package_directory.name}'"
        )

    version = manifest["version"]
    if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
        errors.append(f"{manifest_path}: version must use x.y.z semantic versioning")

    outputs = manifest["outputs"]
    if not isinstance(outputs, list) or not outputs:
        errors.append(f"{manifest_path}: outputs must contain at least one entry")
        return errors

    renderers: set[str] = set()
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            errors.append(f"{manifest_path}: outputs[{index}] must be a table")
            continue

        for key in ("format", "renderer", "template"):
            if not isinstance(output.get(key), str) or not output[key].strip():
                errors.append(f"{manifest_path}: outputs[{index}].{key} is required")

        template_name = output.get("template")
        renderer = output.get("renderer")
        if isinstance(renderer, str):
            renderers.add(renderer)

        if isinstance(template_name, str) and template_name:
            candidate = (package_directory / template_name).resolve()
            package_root = package_directory.resolve()
            if package_root not in candidate.parents:
                errors.append(
                    f"{manifest_path}: output template escapes package: {template_name}"
                )
            elif not candidate.is_file():
                errors.append(
                    f"{manifest_path}: output template does not exist: {template_name}"
                )

    metadata = manifest["metadata"]
    if not isinstance(metadata, dict):
        errors.append(f"{manifest_path}: metadata must be a table")
    else:
        for key in ("required", "optional"):
            values = metadata.get(key)
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value for value in values
            ):
                errors.append(f"{manifest_path}: metadata.{key} must be a string array")

    tex_path = package_directory / "template.tex"
    if "pandoc" in renderers and tex_path.is_file():
        tex = tex_path.read_text(encoding="utf-8")
        for placeholder in ("$title$", "$author$", "$body$"):
            if placeholder not in tex:
                errors.append(f"{tex_path}: missing Pandoc placeholder {placeholder}")
        if "\\begin{document}" not in tex or "\\end{document}" not in tex:
            errors.append(f"{tex_path}: incomplete LaTeX document boundary")

    html_path = package_directory / "template.html"
    if "tera" in renderers and html_path.is_file():
        html = html_path.read_text(encoding="utf-8")
        for placeholder in ("{{ title", "{{ body"):
            if placeholder not in html:
                errors.append(f"{html_path}: missing Tera placeholder {placeholder}")

    return errors


def validate_repository(repository_root: Path) -> list[str]:
    """Validate every built-in Beacon template package."""

    templates_directory = repository_root / "beacon" / "templates"
    if not templates_directory.is_dir():
        return [f"missing Beacon templates directory: {templates_directory}"]

    package_directories = sorted(
        path for path in templates_directory.iterdir() if path.is_dir()
    )
    if not package_directories:
        return [f"no Beacon template packages found in {templates_directory}"]

    errors: list[str] = []
    for package_directory in package_directories:
        errors.extend(validate_package(package_directory))
    return errors


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-root",
        default=".",
        help="Empathy repository root containing beacon/",
    )
    return parser.parse_args()


def main() -> int:
    """Run Beacon template validation and return a process exit code."""

    arguments = parse_arguments()
    errors = validate_repository(Path(arguments.repository_root).resolve())

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Beacon template validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
