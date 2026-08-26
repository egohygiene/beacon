# Beacon CLI

The Beacon CLI is the deterministic project-initialization layer for template packages.
It reads the versioned `beacon-template.toml` contract established by the template
foundation and does not depend on Renderflow at runtime.

## Commands

Run from `beacon/`:

```bash
cargo run -- --templates-directory "templates" list
cargo run -- --templates-directory "templates" inspect research-paper
cargo run -- --templates-directory "templates" validate
cargo run -- --templates-directory "templates" validate research-paper
cargo run -- --templates-directory "templates" init research-paper "../scratch/my-paper" \
  --title "My Research Paper" \
  --author "Author Name"
```

The `init` command refuses to write into a non-empty destination.

## Generated project contract

A research-paper initialization currently produces:

```text
my-paper/
├── beacon-project.toml
├── paper.md
├── references.bib
├── data/
├── figures/
├── research/
│   ├── notes/
│   └── sources/
└── templates/
    ├── template.html
    └── template.tex
```

`beacon-project.toml` records the selected template ID and version plus the initial
project title and author. Generated projects own their copied rendering templates so
they remain inspectable and reproducible even if Beacon's built-in registry evolves.

## Validation

Run the complete Beacon subproject contract with:

```bash
task --dir "beacon" check
```

The task validates the existing dependency-free Python template contract and the Rust
implementation with formatting, Clippy, and tests.

## Deliberate exclusions

This MVP does not:

- initialize Git repositories;
- create GitHub repositories;
- invoke Renderflow or Pandoc;
- call local or hosted language models;
- provide a graphical interface;
- mutate an existing non-empty project.

Those behaviors should be added only after the initializer contract is proven by real
paper projects.
