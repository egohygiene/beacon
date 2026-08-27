# Beacon CLI

The Beacon CLI is the deterministic registry, initialization, and execution
layer shared by the active publication profiles. It consumes each profile's
`beacon-template.toml`; initialized projects own the Python execution adapter,
Makefile, Taskfile, rendering assets, and document-specific checks.

## Discover and inspect profiles

```bash
cargo run --locked -- list
cargo run --locked -- inspect magazine
cargo run --locked -- validate
cargo run --locked -- validate technical-whitepaper
cargo run --locked -- inspect publication-hub
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

Publication-hub initialization creates an independently buildable draft site
with honest paper and magazine placeholders:

```bash
cargo run --locked -- init publication-hub "../publication-site" \
  --title "Publication Site" \
  --author "Publication Author" \
  --project-id "publication-site" \
  --theme "egohygiene"
```

The initializer:

1. validates the selected profile manifest;
2. rejects files, symbolic links, protected paths, and non-empty destinations;
3. materializes the profile through a temporary sibling workspace;
4. materializes the project-local Make, Task, adapter, renderer, and profile
   contract files;
5. requires a common `beacon-project.toml` envelope;
6. renames the completed workspace into place only after initialization passes.

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

## Diagnose, plan, build, and package

Check every tool required by the active registry, or limit the check to one
profile:

```bash
cargo run --locked -- doctor
cargo run --locked -- doctor research-paper
```

An initialized project's `[beacon]` envelope pins the profile and version.
Beacon resolves that pin before it executes anything:

```bash
cargo run --locked -- plan "../antidote-paper"
cargo run --locked -- build "../antidote-paper" \
  --theme "egohygiene" \
  --output-directory "build/publication"
cargo run --locked -- package "../antidote-paper" \
  --theme "egohygiene" \
  --output-directory "build/publication" \
  --package-directory "dist/antidote-draft"
```

Relative output and package paths resolve from the project directory. `plan` is
non-executing and prints the resolved profile, version, theme, paths, command,
and artifacts. `build` then:

1. renders into a temporary sibling directory;
2. runs the profile's checks as part of the adapter command;
3. verifies every artifact declared by the profile;
4. replaces only output previously marked as Beacon-owned;
5. atomically finalizes the verified output.

`package` performs the same verified build and stages declared files under
`artifacts/`. It writes a deterministic `beacon-package.json` plus
`SHA256SUMS`. It does not publish, upload, or submit anything, and it refuses a
non-empty package destination.

The package manifest is documented by
[`contracts/package-manifest.schema.json`](../contracts/package-manifest.schema.json).

The execution adapter is declarative: a bare program, argument templates,
required host tools (including explicit alternatives), supported theme values,
default output, and artifact paths. Built-in profiles execute the initialized
project's local `scripts/tasks.py`; Beacon does not require Make or Task and does
not reach back into profile assets after initialization.
External registries may be inspected and planned without trust. `doctor`,
`build`, and `package` require `--allow-executable-adapter` because those
commands execute programs declared by the registry.

For direct project use and Make/Task command parity, see the
[`standalone project task contract`](project-task-contract.md).

The publication-hub profile produces a host-neutral `site/` artifact. Its
versioned public catalog, required routes, lifecycle states, and deployment
boundary are documented in the
[`publication-hub contract`](../templates/publication-hub/CONTRACT.md).

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
