#!/usr/bin/env python3
# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Validate publication-hub source and a previously staged public tree."""

from __future__ import annotations

import argparse
from pathlib import Path

from build import ContractError, load_catalog, validate_output


def main() -> int:
    """Validate one product-owned hub catalog and output directory."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--build-dir", required=True)
    parser.add_argument("--theme", choices=("neutral", "egohygiene"), default="neutral")
    parser.add_argument("--source-revision")
    parser.add_argument(
        "--revision-policy", choices=("local", "deployment"), default="local"
    )
    arguments = parser.parse_args()
    project = Path(arguments.project).resolve()
    output = Path(arguments.build_dir)
    if not output.is_absolute():
        output = project / output
    require_deployable = arguments.revision_policy == "deployment"
    catalog = load_catalog(
        project,
        arguments.theme,
        arguments.source_revision,
        require_deployable_revision=require_deployable,
    )
    validate_output(
        output,
        require_deployable_revision=require_deployable,
        expected_catalog=catalog,
    )
    print(f"Validated publication hub at {output / 'site'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as error:
        raise SystemExit(f"ERROR: {error}") from error
