# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

VALIDATOR_PATH = Path(__file__).parents[1] / "scripts" / "validate_templates.py"
SPEC = importlib.util.spec_from_file_location("beacon_validate_templates", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class BeaconTemplateValidationTests(unittest.TestCase):
    def test_builtin_templates_validate(self) -> None:
        repository_root = Path(__file__).parents[2]
        self.assertEqual([], VALIDATOR.validate_repository(repository_root))

    def test_missing_manifest_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_directory = Path(temporary_directory) / "example"
            package_directory.mkdir()
            errors = VALIDATOR.validate_package(package_directory)
            self.assertEqual(1, len(errors))
            self.assertIn("missing manifest", errors[0])

    def test_manifest_id_must_match_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            package_directory = Path(temporary_directory) / "wrong-name"
            package_directory.mkdir()
            (package_directory / "template.tex").write_text(
                "$title$ $author$ $body$ \\begin{document} \\end{document}",
                encoding="utf-8",
            )
            (package_directory / "beacon-template.toml").write_text(
                """schema_version = 1
id = \"research-paper\"
name = \"Research Paper\"
version = \"0.1.0\"
description = \"Example\"

[[outputs]]
format = \"pdf\"
renderer = \"pandoc\"
template = \"template.tex\"

[metadata]
required = [\"title\", \"author\"]
optional = []

[capabilities]
pdf = true
""",
                encoding="utf-8",
            )
            errors = VALIDATOR.validate_package(package_directory)
            self.assertTrue(any("must match directory" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
