# Beacon Architecture

## System overview

Beacon is an incubated Empathy holon for discovering, validating, and
instantiating reusable document-project templates. The architecture deliberately
separates template semantics from rendering engines so Beacon can support
multiple LaTeX and document toolchains without owning all rendering behavior.

## Components

### Template contract

`contracts/template-manifest.schema.json` documents the stable metadata shape
shared by every Beacon template package.

### Template registry

`templates/` is the built-in registry. Each direct child is an independently
versioned template package containing a `beacon-template.toml` manifest and all
files needed by that template.

### Validator

`scripts/validate_templates.py` performs dependency-free structural validation
for the incubated contract. It verifies manifest identity, required metadata,
output declarations, package-local paths, and required renderer placeholders.

### Future CLI

A Rust CLI will replace shell-level/manual initialization with deterministic
commands for listing, inspecting, validating, and initializing templates. The
CLI must consume the same package contract rather than introducing a second
configuration model.

## Data flow

```text
built-in / external template package
              |
              v
      template manifest
              |
              v
       Beacon validation
              |
              v
     project initialization
              |
              v
 generated project workspace
              |
       +------+------+
       |             |
       v             v
    Pandoc         Tera / future renderers
       |             |
       +------+------+
              v
        publication artifacts
```

## Boundaries

- Beacon owns template metadata, discovery, validation, and initialization.
- Template packages own presentation files and project bootstrap content.
- Generated projects own research content and publication state.
- Renderflow may render Beacon-generated projects but is not a required Beacon
  runtime dependency.
- AI systems may assist authoring but are not required to instantiate or
  validate a template.

## Extraction invariant

Everything required to extract `beacon/` into a standalone repository should
remain inside `beacon/` except optional Empathy integration such as root
Taskfile wiring and root documentation links.
