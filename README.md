# Beacon

🔦 A local-first publication toolkit for discovering, initializing, validating,
assembling, and eventually packaging polished research, grant, whitepaper, and
editorial projects.

Beacon owns reusable publication profiles and their contracts. Projects own
their manuscripts, evidence, bibliography, artwork, configuration, and release
history. Profile-specific renderers remain independently usable; the Beacon
core provides one deterministic registry and initialization surface over them.

## Active profiles

- `magazine`: structured digital, print, and accessible web magazines;
- `nih-nimh-rpg`: separately rendered NIH/NIMH grant attachments;
- `research-paper`: PDF, accessible web, and arXiv-source research papers;
- `technical-whitepaper`: evidence-led PDF and web whitepapers.

Inspect the full registry in [`templates/README.md`](templates/README.md).

## Core commands

The repository pins its Rust toolchain. From a clean checkout:

```bash
cargo run --locked -- list
cargo run --locked -- inspect research-paper
cargo run --locked -- validate
cargo run --locked -- init research-paper "../my-paper" \
  --title "My Research Paper" \
  --author "Author Name"
```

Every initializer writes through a temporary sibling workspace and refuses to
overwrite a non-empty destination. Executable initializers from a custom
registry are denied unless the caller explicitly supplies
`--allow-executable-initializer` after inspecting that package.

See [`docs/cli.md`](docs/cli.md) for the command and trust contract.

## Validation

Run the root contract locally with:

```bash
task check
```

The same formatting, Clippy, Rust tests, four-profile initialization smoke test,
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

- Beacon owns profile discovery, manifest validation, safe initialization, and
  future packaging coordination.
- Profiles own document-specific source, build, check, and renderer adapters.
- Projects own authored content and selected style overrides.
- Renderflow, Relay, Identity, Dreamscape, and organization synchronization are
  optional integrations rather than local runtime requirements.
- External publication and grant submission remain human-approved actions.
