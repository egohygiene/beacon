# Beacon core provenance

## Origin

Beacon's first registry and CLI vertical slice was incubated under
`egohygiene/empathy/beacon` and later preserved in this repository's
`.staging/` intake. That prototype established several durable behaviors:

- renderer-aware `beacon-template.toml` packages;
- deterministic profile discovery;
- `list`, `inspect`, `validate`, and `init` commands;
- project ownership recorded through `beacon-project.toml`;
- refusal to overwrite non-empty destinations;
- Rust unit and binary smoke coverage.

The original research-template work was informed by Renderflow's research
templates and renderer behavior. Renderflow remains the historical rendering
reference; Beacon owns the generalized publication profile and initialization
contracts.

## Standalone promotion

Roadmap step `BEA-Q02` and Beacon issue `#12` promoted and adapted the staged
core rather than copying it unchanged. The standalone implementation:

- corrects Empathy-era repository metadata and paths;
- separates reusable registry behavior into `src/lib.rs` from the CLI in
  `src/main.rs`;
- supports the five active heterogeneous profiles;
- adds a common project-manifest envelope and profile initializer contract;
- materializes projects through temporary sibling workspaces;
- protects built-in and external executable-initializer trust boundaries;
- commits the Rust lockfile and pinned toolchain;
- uses Rust as the single canonical manifest validator;
- runs the same contract locally and in CI.

The staged standard-library Python validator was retired because maintaining a
second implementation would allow schema and path-safety behavior to diverge.
Profile-owned Python initializer adapters remain deliberately small and handle
only document-specific source customization.

## Preserved intake boundary

The staged LaTeX reference tree was not part of the core promotion. It remains
recoverable design input for original Beacon profiles and a future composable
LaTeX component library. Its migration and disposition rules are documented in
[`latex-component-library.md`](latex-component-library.md).
