# Beacon

🔦 A local-first publication toolkit for discovering, initializing, validating,
assembling, and packaging polished research, grant, whitepaper, editorial, and
publication-site projects.

Beacon owns reusable publication profiles and their contracts. Projects own
their manuscripts, evidence, bibliography, artwork, configuration, and release
history. Profile-specific renderers remain independently usable; the Beacon core
provides one deterministic registry, initialization, build, and packaging
surface over them.

## Active profiles

- `magazine`: structured digital, print, and accessible web magazines;
- `nih-nimh-rpg`: separately rendered NIH/NIMH grant attachments;
- `publication-hub`: host-neutral publication catalogs and accessible static sites;
- `research-paper`: PDF, accessible web, and arXiv-source research papers;
- `technical-whitepaper`: evidence-led PDF and web whitepapers.

Inspect the full registry in [`templates/README.md`](templates/README.md).

## Core commands

The repository pins its Rust toolchain. From a clean checkout:

```bash
cargo run --locked -- list
cargo run --locked -- inspect research-paper
cargo run --locked -- inspect publication-hub
cargo run --locked -- validate
cargo run --locked -- init research-paper "../my-paper" \
  --title "My Research Paper" \
  --author "Author Name"
cargo run --locked -- doctor research-paper
cargo run --locked -- plan "../my-paper"
cargo run --locked -- package "../my-paper"
```

Every initializer writes through a temporary sibling workspace and refuses to
overwrite a non-empty destination. Executable initializers from a custom
registry are denied unless the caller explicitly supplies
`--allow-executable-initializer` after inspecting that package.

Initialized projects contain their own Makefile, Taskfile, build/check adapter,
styles, templates, themes, and profile manifest. They continue to build without
a Beacon checkout:

```bash
make check
task check
```

Both developer entrypoints call the same project-owned implementation. See the
[`standalone project task contract`](docs/project-task-contract.md) for command
parity, overrides, and profile-specific capabilities.

Builds are transactional and profile-checked. Packages contain only the
profile's declared artifacts, a machine-readable manifest, and SHA-256
checksums. See [`docs/cli.md`](docs/cli.md) for the command, output-safety, and
trust contracts.

## Validation

Run the root contract locally with:

```bash
task check
```

The same formatting, Clippy, Rust tests, five-profile initialization smoke test,
and registry validation run in GitHub Actions. Each profile also retains its own
document build and quality workflow.

## LaTeX component direction

The remaining `.staging/latex` tree is governed design reference intake, not
disposable bulk and not an active runtime registry. Beacon will progressively
transform useful patterns into original, composable LaTeX components with a
documented override cascade for Identity themes, publication profiles, project
art direction, and page-specific composition.

See [`docs/latex-component-library.md`](docs/latex-component-library.md).

## Boundaries

- Beacon owns profile discovery, manifest validation, safe initialization,
  execution planning, transactional builds, and artifact packaging.
- Profiles own document-specific source, build, check, and renderer adapters.
- Projects own authored content and selected style overrides.
- Initialized projects own the complete local build kit; Beacon invokes it but
  is not required by it.
- Publication products own their catalog, copy, artwork, URL policy, and
  generated static tree; Relay or another host owns deployment and DNS.
- Renderflow, Relay, Identity, Dreamscape, and organization synchronization are
  optional integrations rather than local runtime requirements.
- External publication and grant submission remain human-approved actions.
