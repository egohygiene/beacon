# Beacon Provenance

## Origin

Beacon's initial `research-paper` template package is extracted from the
research template implementation in `egohygiene/renderflow`.

Reference sources at extraction time:

- `templates/research/research.tex`
- `templates/research/research.html`
- `.github/agents/research-paper.agent.md`
- `crates/renderflow-core/src/template.rs`

The source repository established a practical vertical slice: structured
research Markdown, renderer templates, metadata interpolation, and explicit
template validation. Beacon generalizes that working implementation into a
renderer-agnostic package contract.

## What was preserved

- Pandoc-compatible LaTeX variables for title, author, date, abstract, body,
  table of contents, geometry, paper size, font size, and header includes;
- academic typography, tables, mathematics, code, figures, hyperlinks, and
  print-friendly structure;
- the HTML research presentation as a second renderer example;
- deterministic expectations around template existence and required variables;
- compatibility with structured Markdown research documents.

## What changed

- template identity and capabilities are now declared in
  `beacon-template.toml`;
- renderer-specific outputs are explicit rather than implicit;
- template files are package-local and checked against path traversal;
- validation is owned by Beacon rather than Renderflow;
- research-writing agent behavior is treated as authoring guidance, not as a
  runtime requirement or part of the template manifest.

## Ownership rule

Renderflow remains the historical source and rendering reference. Beacon is the
canonical home for the generalized template-package abstraction developed from
that source.
