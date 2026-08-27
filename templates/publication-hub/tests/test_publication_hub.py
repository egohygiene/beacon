# Copyright 2026 Ego Hygiene
# SPDX-License-Identifier: MIT

"""Adversarial stdlib tests for the standalone publication-hub contract."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402

FULL_REVISION = "0123456789abcdef0123456789abcdef01234567"


class PublicationHubContractTests(unittest.TestCase):
    """Prove source honesty, deterministic output, and deployment safety."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="publication-hub-test-")
        self.root = Path(self.temporary.name)
        self.fixture_counter = 0

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def fixture(self, name: str) -> Path:
        self.fixture_counter += 1
        destination = self.root / f"{name}-{self.fixture_counter}"
        shutil.copytree(
            ROOT / "fixtures" / name,
            destination,
            ignore=shutil.ignore_patterns("build", "dist", "__pycache__", "*.pyc"),
        )
        return destination

    def catalog(self, project: Path) -> dict:
        return json.loads((project / "publication-hub.json").read_text(encoding="utf-8"))

    def write_catalog(self, project: Path, catalog: dict) -> None:
        (project / "publication-hub.json").write_text(
            json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
        )

    def build(self, name: str, *, theme: str = "neutral") -> tuple[Path, dict]:
        project = self.fixture(name)
        output = build.build_project(project, project / "build", theme)
        build.validate_output(output)
        public = json.loads((output / "site" / "site.json").read_text(encoding="utf-8"))
        return output, public

    def test_all_reference_fixtures_build_and_validate(self) -> None:
        for name in (
            "antidote-planned-magazine",
            "combined",
            "magazine-only",
            "no-fallback",
            "paper-only",
            "reflector-root-aliases",
        ):
            with self.subTest(name=name):
                output, public = self.build(name)
                self.assertEqual(public["schema"], build.SITE_SCHEMA)
                self.assertEqual(public["schema_version"], build.SCHEMA_VERSION)
                self.assertTrue((output / "site" / "manifest.webmanifest").is_file())
                self.assertTrue((output / "site" / build.CHECKSUM_FILE).is_file())

    def test_antidote_keeps_publication_stage_separate_from_slot_state(self) -> None:
        output, public = self.build("antidote-planned-magazine")
        slots = {slot["id"]: slot for slot in public["slots"]}
        self.assertEqual(public["site"]["stage"], "draft")
        self.assertEqual(slots["paper"]["status"], "available")
        self.assertEqual(slots["magazine"]["status"], "planned")
        for forbidden in build.FORBIDDEN_PLANNED_FIELDS:
            self.assertNotIn(forbidden, slots["magazine"])
        source = ROOT / "fixtures/antidote-planned-magazine/artifacts/paper.html"
        self.assertEqual((output / "site/paper/index.html").read_bytes(), source.read_bytes())
        paper_resource = slots["paper"]["artifacts"][0]
        self.assertEqual(paper_resource["path"], "paper/index.html")
        self.assertEqual(paper_resource["route"], "paper/")
        self.assertEqual(paper_resource["url"], "https://antidote.egohygiene.io/paper/")

    def test_reflector_root_aliases_preserve_artifact_bytes(self) -> None:
        output, public = self.build("reflector-root-aliases")
        aliases = [
            alias
            for slot in public["slots"]
            for resource in slot.get("artifacts", [])
            for alias in resource["aliases"]
        ]
        self.assertEqual(len(aliases), 3)
        self.assertEqual(
            sorted(alias["path"] for alias in aliases),
            ["reflector-magazine-print.pdf", "reflector-magazine.pdf", "reflector.pdf"],
        )
        self.assertEqual(public["site"]["stage"], "draft")
        self.assertTrue(all(slot["status"] == "available" for slot in public["slots"]))
        route_paths = {route["path"] for route in public["routes"]}
        self.assertTrue(
            {
                "paper/",
                "magazine/",
                "magazine/print/",
                "publication.json",
                "reflector.pdf",
                "reflector-magazine.pdf",
                "reflector-magazine-print.pdf",
            }.issubset(route_paths)
        )
        paper = next(slot for slot in public["slots"] if slot["id"] == "paper")
        self.assertEqual(paper["identifiers"][0]["scheme"], "doi")
        self.assertEqual(
            paper["release"]["url"],
            "https://github.com/egohygiene/reflector/releases/tag/v0.1.2",
        )
        for slot in public["slots"]:
            for resource in slot.get("artifacts", []):
                artifact = output / "site" / resource["path"]
                for alias in resource["aliases"]:
                    self.assertEqual(
                        artifact.read_bytes(), (output / "site" / alias["path"]).read_bytes()
                    )

    def test_repository_subpath_can_omit_fallback(self) -> None:
        _, public = self.build("no-fallback")
        self.assertIsNone(public["site"]["fallback_base_url"])
        self.assertEqual(public["slots"], [])
        self.assertTrue(all(route["fallback_url"] is None for route in public["routes"]))
        self.assertEqual(public["site"]["canonical_base_url"], "https://example.github.io/no-fallback/")

    def test_repeated_builds_are_byte_identical(self) -> None:
        project = self.fixture("combined")
        first = build.build_project(project, project / "first")
        second = build.build_project(project, project / "second")
        first_files = {
            path.relative_to(first).as_posix(): path.read_bytes()
            for path in first.rglob("*")
            if path.is_file()
        }
        second_files = {
            path.relative_to(second).as_posix(): path.read_bytes()
            for path in second.rglob("*")
            if path.is_file()
        }
        self.assertEqual(first_files, second_files)

    def test_theme_and_product_token_overrides_are_deterministic(self) -> None:
        project = self.fixture("no-fallback")
        catalog = self.catalog(project)
        catalog["site"]["styles"] = {"tokens": {"--hub-radius": "2rem"}}
        self.write_catalog(project, catalog)
        output = build.build_project(project, project / "build", "egohygiene")
        css = (output / "site/assets/site.css").read_text(encoding="utf-8")
        self.assertIn("--hub-radius: 2rem;", css)
        self.assertIn("--hub-background: #100c17;", css)

    def test_magazine_only_fixture_owns_brand_artwork_copy_and_custom_css(self) -> None:
        output, public = self.build("magazine-only")
        site = output / "site"
        self.assertEqual([slot["kind"] for slot in public["slots"]], ["magazine"])
        self.assertTrue((site / "assets/brand/logo.svg").is_file())
        self.assertTrue((site / "assets/brand/artwork.svg").is_file())
        self.assertTrue((site / "assets/slots/magazine/artwork.svg").is_file())
        self.assertEqual(
            (site / "assets/custom.css").read_text(encoding="utf-8"),
            (ROOT / "fixtures/magazine-only/assets/custom.css").read_text(encoding="utf-8"),
        )
        css = (site / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn("--hub-accent: #6f42c1;", css)
        self.assertIn("Product-owned copy", (site / "index.html").read_text(encoding="utf-8"))

    def test_planned_slots_reject_release_fields_and_nested_extension_lies(self) -> None:
        reserved_fields = (
            "artifacts",
            "cover_url",
            "doi",
            "identifiers",
            "issue_number",
            "manifests",
            "preview",
            "provenance",
            "release",
            "sha256",
            "source",
            "version",
            "zenodo",
        )
        for reserved in reserved_fields:
            with self.subTest(reserved=reserved):
                project = self.fixture("antidote-planned-magazine")
                catalog = self.catalog(project)
                planned = catalog["slots"][1]
                planned["extensions"] = {"consumer": {reserved.replace("_", "-"): "fake"}}
                self.write_catalog(project, catalog)
                with self.assertRaises(build.ContractError):
                    build.load_catalog(project)
                shutil.rmtree(project)

    def test_planned_slot_rejects_top_level_publication_data_before_paths(self) -> None:
        project = self.fixture("antidote-planned-magazine")
        catalog = self.catalog(project)
        catalog["slots"][1]["artifacts"] = []
        self.write_catalog(project, catalog)
        with self.assertRaises(build.ContractError):
            build.load_catalog(project)

    def test_unsafe_public_hosts_are_rejected(self) -> None:
        unsafe = (
            "https://localhost/",
            "https://service.localhost/path/",
            "https://127.0.0.1/",
            "https://[::1]/",
            "https://example.org:8443/",
            "https://bad host.example/",
            "https://single-label/",
            "https://example.org/\nattack/",
        )
        for value in unsafe:
            with self.subTest(value=value):
                with self.assertRaises(build.ContractError):
                    build.normalize_base_url(value, "test URL")

    def test_repository_subpaths_are_normalized_and_distinct(self) -> None:
        self.assertEqual(
            build.normalize_base_url("https://EXAMPLE.org/project", "base"),
            "https://example.org/project/",
        )
        project = self.fixture("no-fallback")
        catalog = self.catalog(project)
        catalog["site"]["fallback_base_url"] = catalog["site"]["canonical_base_url"]
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "must be distinct"):
            build.load_catalog(project)

    def test_available_and_deployment_builds_require_full_revision(self) -> None:
        project = self.fixture("paper-only")
        catalog = self.catalog(project)
        catalog["site"]["revision"] = "WORKING_TREE"
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "full lowercase source revision"):
            build.load_catalog(project)
        loaded = build.load_catalog(project, source_revision_override=FULL_REVISION)
        self.assertEqual(loaded["site"]["revision"], FULL_REVISION)

        draft_project = self.fixture("no-fallback")
        build.load_catalog(draft_project)
        with self.assertRaisesRegex(build.ContractError, "full lowercase source revision"):
            build.load_catalog(draft_project, require_deployable_revision=True)
        deployable = build.load_catalog(
            draft_project,
            source_revision_override=FULL_REVISION,
            require_deployable_revision=True,
        )
        self.assertEqual(deployable["site"]["revision"], FULL_REVISION)

    def test_source_revision_override_beats_catalog_and_is_public(self) -> None:
        project = self.fixture("no-fallback")
        output = build.build_project(
            project,
            project / "build",
            source_revision=FULL_REVISION,
            require_deployable_revision=True,
        )
        public = json.loads((output / "site/site.json").read_text(encoding="utf-8"))
        self.assertEqual(public["source"]["revision"], FULL_REVISION)
        self.assertEqual(public["site"]["revision"], FULL_REVISION)

    def test_output_path_and_public_route_collisions_fail(self) -> None:
        project = self.fixture("combined")
        catalog = self.catalog(project)
        catalog["slots"][1]["artifacts"][0]["path"] = "downloads/combined-paper.pdf"
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "output collision"):
            build.load_catalog(project)

        shutil.rmtree(project)
        project = self.fixture("combined")
        catalog = self.catalog(project)
        catalog["slots"][1]["artifacts"][0]["path"] = "downloads/index.html"
        catalog["slots"][1]["artifacts"][0]["route"] = "downloads/"
        catalog["slots"][1]["artifacts"][0]["media_type"] = "text/html"
        self.write_catalog(project, catalog)
        with self.assertRaises(build.ContractError):
            build.load_catalog(project)

        project = self.fixture("combined")
        catalog = self.catalog(project)
        catalog["slots"][1]["artifacts"][0]["route"] = catalog["slots"][0][
            "artifacts"
        ][0].get("route", catalog["slots"][0]["artifacts"][0]["path"])
        self.write_catalog(project, catalog)
        with self.assertRaises(build.ContractError):
            build.load_catalog(project)

    def test_artifact_and_manifest_ids_share_one_slot_namespace(self) -> None:
        project = self.fixture("paper-only")
        catalog = self.catalog(project)
        catalog["slots"][0]["manifests"][0]["id"] = catalog["slots"][0][
            "artifacts"
        ][0]["id"]
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "repeats resource id"):
            build.load_catalog(project)

    def test_manifests_cannot_alias_or_own_slot_landings(self) -> None:
        project = self.fixture("antidote-planned-magazine")
        catalog = self.catalog(project)
        manifest = catalog["slots"][0]["manifests"][0]
        manifest.update(
            {
                "media_type": "text/html",
                "path": "paper/index.html",
                "route": "paper/",
            }
        )
        catalog["slots"][0]["landing"]["resource_id"] = manifest["id"]
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "artifact, not a manifest"):
            build.load_catalog(project)

        output, public = self.build("paper-only")
        public["slots"][0]["manifests"][0]["aliases"] = [
            {
                "path": "provenance.json",
                "url": "https://paper.example.org/research/provenance.json",
                "fallback_url": "https://example.github.io/paper-only/provenance.json",
            }
        ]
        with self.assertRaisesRegex(build.ContractError, "too many items"):
            build.validate_schema_document(
                public, build.PUBLIC_SCHEMA_PATH, "mutated public catalog"
            )
        (output / "site/site.json").write_text(
            json.dumps(public, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaises(build.ContractError):
            build.validate_public_catalog(output / "site")

    def test_available_and_draft_slot_resource_invariants(self) -> None:
        project = self.fixture("paper-only")
        catalog = self.catalog(project)
        catalog["slots"][0].pop("artifacts")
        self.write_catalog(project, catalog)
        with self.assertRaises(build.ContractError):
            build.load_catalog(project)

        project = self.fixture("paper-only")
        catalog = self.catalog(project)
        catalog["slots"][0]["status"] = "draft"
        catalog["slots"][0].pop("version")
        catalog["slots"][0].pop("source")
        self.write_catalog(project, catalog)
        with self.assertRaises(build.ContractError):
            build.load_catalog(project)

    def test_escaping_symlink_and_empty_sources_fail(self) -> None:
        project = self.fixture("paper-only")
        catalog = self.catalog(project)
        catalog["slots"][0]["artifacts"][0]["source"] = "../outside.pdf"
        self.write_catalog(project, catalog)
        with self.assertRaises(build.ContractError):
            build.load_catalog(project)

        project = self.fixture("paper-only")
        artifact = project / "artifacts/paper.pdf"
        artifact.write_bytes(b"")
        with self.assertRaisesRegex(build.ContractError, "empty file"):
            build.load_catalog(project)

        shutil.rmtree(project)
        project = self.fixture("paper-only")
        artifact = project / "artifacts/paper.pdf"
        artifact.unlink()
        artifact.symlink_to(self.root / "outside.pdf")
        (self.root / "outside.pdf").write_bytes(b"outside")
        with self.assertRaisesRegex(build.ContractError, "symlink"):
            build.load_catalog(project)

    def test_symlinked_source_catalog_fails(self) -> None:
        project = self.fixture("no-fallback")
        catalog = project / "publication-hub.json"
        outside = self.root / "catalog.json"
        outside.write_bytes(catalog.read_bytes())
        catalog.unlink()
        catalog.symlink_to(outside)
        with self.assertRaisesRegex(build.ContractError, "cannot be a symlink"):
            build.load_catalog(project)

    def test_existing_outside_link_target_still_fails_containment(self) -> None:
        output, _ = self.build("no-fallback")
        outside = output / "outside.html"
        outside.write_text("outside", encoding="utf-8")
        page = output / "site/index.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "</main>", '<a href="../../outside.html">escape</a></main>'
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(build.ContractError, "escapes the site"):
            build.validate_html_links(output / "site")

    def test_tampered_catalog_paths_cannot_escape_validation(self) -> None:
        output, public = self.build("no-fallback")
        public["routes"][0]["path"] = "../../sentinel.txt"
        public["routes"][0]["url"] = "https://example.github.io/sentinel.txt"
        (output / "site/site.json").write_text(
            json.dumps(public, indent=2) + "\n", encoding="utf-8"
        )
        (output / "sentinel.txt").write_text("outside", encoding="utf-8")
        with self.assertRaises(build.ContractError):
            build.validate_public_catalog(output / "site")

    def test_public_schema_and_route_order_reject_tampering(self) -> None:
        output, public = self.build("no-fallback")
        public["site"]["unexpected"] = True
        (output / "site/site.json").write_text(
            json.dumps(public, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaises(build.ContractError):
            build.validate_public_catalog(output / "site")

        output, public = self.build("no-fallback")
        public["source"].pop("catalog_sha256")
        (output / "site/site.json").write_text(
            json.dumps(public, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaises(build.ContractError):
            build.validate_public_catalog(output / "site")

        output, public = self.build("no-fallback")
        public["routes"].reverse()
        (output / "site/site.json").write_text(
            json.dumps(public, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(build.ContractError, "deterministic"):
            build.validate_public_catalog(output / "site")

    def test_canonical_open_graph_and_json_ld_must_equal_catalog(self) -> None:
        output, _ = self.build("no-fallback")
        page = output / "site/index.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                'rel="canonical" href="https://example.github.io/no-fallback/"',
                'rel="canonical" href="https://wrong.example.org/"',
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(build.ContractError, "canonical URL disagrees"):
            build.validate_html_links(output / "site")

    def test_checksum_tampering_and_incomplete_inventory_fail(self) -> None:
        output, _ = self.build("paper-only")
        artifact = output / "site/downloads/reference-paper.pdf"
        artifact.write_bytes(artifact.read_bytes() + b"tamper")
        with self.assertRaises(build.ContractError):
            build.validate_output(output)

        output, _ = self.build("no-fallback")
        checksum = output / "site/SHA256SUMS"
        checksum.write_text("\n".join(checksum.read_text().splitlines()[:-1]) + "\n")
        with self.assertRaisesRegex(build.ContractError, "does not exactly cover"):
            build.validate_output(output)

    def test_unowned_output_is_never_replaced_or_cleaned(self) -> None:
        project = self.fixture("no-fallback")
        output = project / "build"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_text("preserve", encoding="utf-8")
        with self.assertRaisesRegex(build.ContractError, "unowned"):
            build.build_project(project, output)
        with self.assertRaisesRegex(build.ContractError, "unowned"):
            build.clean_output(project, output)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_failed_rebuild_preserves_prior_owned_output(self) -> None:
        project = self.fixture("no-fallback")
        output = build.build_project(project, project / "build")
        before = {
            path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*")
            if path.is_file()
        }
        with mock.patch.object(
            build, "validate_output", side_effect=build.ContractError("forced failure")
        ):
            with self.assertRaisesRegex(build.ContractError, "forced failure"):
                build.build_project(project, output)
        after = {
            path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)

    def test_sources_cannot_depend_on_prior_output(self) -> None:
        project = self.fixture("paper-only")
        output = build.build_project(project, project / "build")
        catalog = self.catalog(project)
        catalog["slots"][0]["artifacts"][0]["source"] = (
            "build/site/downloads/reference-paper.pdf"
        )
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "cannot depend on generated output"):
            build.build_project(project, output)

    def test_staged_output_is_bound_to_current_source_and_effective_theme(self) -> None:
        project = self.fixture("no-fallback")
        output = build.build_project(project, project / "build")
        catalog = self.catalog(project)
        catalog["site"]["title"] = "Changed after staging"
        self.write_catalog(project, catalog)
        expected = build.load_catalog(project)
        with self.assertRaisesRegex(build.ContractError, "does not match the current source"):
            build.validate_output(output, expected_catalog=expected)

    def test_reserved_route_ids_fail_before_rendering(self) -> None:
        project = self.fixture("no-fallback")
        catalog = self.catalog(project)
        catalog["slots"] = [
            {
                "id": "home",
                "kind": "paper",
                "title": "Reserved",
                "summary": "This cannot shadow the built-in route identifier.",
                "status": "planned",
            }
        ]
        self.write_catalog(project, catalog)
        with self.assertRaisesRegex(build.ContractError, "reserved"):
            build.load_catalog(project)

    def test_hidden_slots_do_not_leak_into_public_projection(self) -> None:
        project = self.fixture("antidote-planned-magazine")
        catalog = self.catalog(project)
        catalog["slots"][1]["visible"] = False
        self.write_catalog(project, catalog)
        output = build.build_project(project, project / "build")
        public = json.loads((output / "site/site.json").read_text(encoding="utf-8"))
        self.assertEqual([slot["id"] for slot in public["slots"]], ["paper"])
        self.assertFalse((output / "site/magazine/index.html").exists())

    def test_manifest_and_checksum_inventory_are_complete_and_sorted(self) -> None:
        output, public = self.build("paper-only")
        site = output / "site"
        manifest = json.loads((site / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["start_url"], "./")
        self.assertEqual(manifest["scope"], "./")
        listed = [line.split("  ", 1)[1] for line in (site / "SHA256SUMS").read_text().splitlines()]
        actual = sorted(
            path.relative_to(site).as_posix()
            for path in site.rglob("*")
            if path.is_file() and path.name != "SHA256SUMS"
        )
        self.assertEqual(listed, actual)
        self.assertIn("manifest.webmanifest", listed)
        core = {
            route["path"]: (route["kind"], route["id"])
            for route in public["routes"]
            if route["path"] in build.CORE_ROUTES
        }
        self.assertEqual(
            core,
            {
                path: (kind, route_id)
                for path, (kind, route_id, _physical) in build.CORE_ROUTES.items()
            },
        )

    def test_every_fixture_matches_both_formal_schemas(self) -> None:
        for name in (
            "antidote-planned-magazine",
            "combined",
            "magazine-only",
            "no-fallback",
            "paper-only",
            "reflector-root-aliases",
        ):
            with self.subTest(name=name):
                project = self.fixture(name)
                source = build.read_json(project / "publication-hub.json")
                build.validate_schema_document(
                    source, build.SOURCE_SCHEMA_PATH, f"{name} source"
                )
                output = build.build_project(project, project / "build")
                public = build.read_json(output / "site/site.json")
                build.validate_schema_document(
                    public, build.PUBLIC_SCHEMA_PATH, f"{name} public"
                )

    def test_non_finite_json_is_rejected_in_source_and_public_catalogs(self) -> None:
        project = self.fixture("no-fallback")
        source_path = project / "publication-hub.json"
        text = source_path.read_text(encoding="utf-8")
        source_path.write_text(
            text.replace('"slots": []', '"extensions": {"bad": NaN},\n  "slots": []'),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(build.ContractError, "non-finite"):
            build.load_catalog(project)

        output, _ = self.build("no-fallback")
        public_path = output / "site/site.json"
        text = public_path.read_text(encoding="utf-8")
        public_path.write_text(
            text.replace('"routes": [', '"extensions": {"bad": Infinity},\n  "routes": ['),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(build.ContractError, "non-finite"):
            build.validate_public_catalog(output / "site")

    def test_schema_documents_pin_runtime_literals_and_resource_mapping(self) -> None:
        source_schema = json.loads(
            (ROOT / "contracts/publication-hub.schema.json").read_text(encoding="utf-8")
        )
        public_schema = json.loads(
            (ROOT / "contracts/publication-site.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            source_schema["properties"]["schema"]["const"], build.SOURCE_CATALOG_SCHEMA
        )
        self.assertEqual(public_schema["properties"]["schema"]["const"], build.SITE_SCHEMA)
        self.assertEqual(
            public_schema["properties"]["schema_version"]["const"], build.SCHEMA_VERSION
        )
        required = public_schema["$defs"]["resource"]["required"]
        for key in ("path", "route", "bytes", "sha256", "url", "fallback_url"):
            self.assertIn(key, required)
        self.assertTrue(source_schema["$defs"]["slot"]["allOf"])


if __name__ == "__main__":
    unittest.main()
