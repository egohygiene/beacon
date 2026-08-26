# Beacon CLI

The Beacon CLI is the deterministic registry and initialization layer shared by
the active publication profiles. It consumes each profile's
`beacon-template.toml`; it does not replace that profile's build or validation
pipeline.

## Discover and inspect profiles

```bash
cargo run --locked -- list
cargo run --locked -- inspect magazine
cargo run --locked -- validate
cargo run --locked -- validate technical-whitepaper
```

The built-in registry defaults to `templates/`. A separate registry can be
inspected without executing it:

```bash
cargo run --locked -- \
  --templates-directory "../publication-profiles" \
  list
```

## Initialize a project

Every built-in profile accepts a common minimum identity:

```bash
cargo run --locked -- init research-paper "../antidote-paper" \
  --title "Antidote" \
  --author "Alan Szmyt" \
  --project-id "antidote" \
  --theme "egohygiene"
```

Magazine initialization maps `--author` to the publisher when `--publisher` is
not supplied and defaults `--edition` to `1`:

```bash
cargo run --locked -- init magazine "../field-notes" \
  --title "Field Notes" \
  --author "Ego Hygiene" \
  --publisher "Ego Hygiene" \
  --edition "01"
```

The initializer:

1. validates the selected profile manifest;
2. rejects files, symbolic links, protected paths, and non-empty destinations;
3. materializes the profile through a temporary sibling workspace;
4. requires a common `beacon-project.toml` envelope;
5. renames the completed workspace into place only after initialization passes.

## Executable initializer trust

Profiles currently retain small Python standard-library initializer adapters so
their document-specific JSON, TOML, Markdown, and LaTeX sources can be
customized safely. Beacon executes those adapters automatically only for its
built-in registry.

For a custom registry, `list`, `inspect`, and `validate` remain non-executing.
Initialization requires explicit acknowledgement:

```bash
cargo run --locked -- \
  --templates-directory "../reviewed-profiles" \
  init reviewed-profile "../new-project" \
  --title "Reviewed Project" \
  --author "Author Name" \
  --allow-executable-initializer
```

Do not enable this flag for an unreviewed template package.

## Project manifest envelope

Every initialized project begins with:

```toml
[beacon]
schema_version = 1
profile = "research-paper"
profile_version = "0.1.0"
```

Profiles may add theme, project, publication, provenance, and document-specific
tables. The shared envelope is documented by
[`contracts/project-manifest.schema.json`](../contracts/project-manifest.schema.json).
