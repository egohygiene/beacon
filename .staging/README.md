# beacon

🔭 A local-first project bootstrapper and template library for reproducible
research and technical documents.

`beacon` is currently incubated inside Empathy as an independently extractable
holon. It owns reusable template contracts, template packages, deterministic
project generation, and the CLI surface used to inspect, validate, and
instantiate those packages.

## Boundary

`beacon/` owns reusable project-template contracts, template packages,
validation rules, the Beacon CLI, and eventually a lightweight local authoring
experience. A generated project owns its manuscript, bibliography, figures,
data, research notes, build configuration, and publication history.

Renderflow remains a rendering engine and reference implementation. Beacon owns
how a project template is described, discovered, validated, and instantiated.

## Current vertical slice

The current foundation provides:

- a versioned, renderer-aware template manifest contract;
- a canonical `research-paper` package derived from Renderflow's research
  templates;
- explicit provenance and extraction notes;
- deterministic template validation using Python's standard library;
- a Rust CLI with `list`, `inspect`, `validate`, and `init` commands;
- generated-project provenance through `beacon-project.toml`;
- safe initialization that refuses non-empty destinations;
- unit and binary-level smoke coverage for the built-in research template;
- first-class integration with Empathy's root `task check` contract.

Git/GitHub repository creation, local LLM assistance, graphical authoring, and
additional template-library ingestion intentionally remain future work.

## Commands

From `beacon/`:

```bash
cargo run --quiet -- --templates-directory "templates" list
cargo run --quiet -- --templates-directory "templates" inspect research-paper
cargo run --quiet -- --templates-directory "templates" validate research-paper
cargo run --quiet -- --templates-directory "templates" init research-paper ./paper \
  --title "Research Paper" \
  --author "Author"
```

## Generated research workspace

The canonical research-paper template currently produces:

```text
paper/
├── beacon-project.toml
├── paper.md
├── references.bib
├── templates/
│   ├── template.html
│   └── template.tex
├── figures/
├── data/
└── research/
    ├── notes/
    └── sources/
```

## Validation

From the Empathy repository root:

```bash
task beacon:check
task beacon:smoke
task check
```

`beacon:check` validates template packages, formatting, Clippy, and the full
Rust test suite. `beacon:smoke` exercises project generation through the compiled
CLI against the real built-in research template. Root `task check` includes the
complete Beacon check as part of Empathy's repository contract.

## Design principle

Beacon templates are packages, not loose files. Every template package must be
self-describing, versioned, renderer-aware, independently validatable, and safe
to copy into a generated project without hidden repository-relative state.
