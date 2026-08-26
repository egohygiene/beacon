# Beacon Template Registry

This directory contains Beacon's active, first-party template packages. Every
package is independently buildable, versioned, documented, and described by a
`beacon-template.toml` manifest.

Each manifest also declares the profile's executable adapter: required host
tools, supported theme values, a tokenized build/check command, default output,
and artifacts eligible for publication packaging. Initializers copy the
profile's complete build kit into the project. The root CLI validates and
orchestrates that project-owned contract without becoming a runtime dependency.

Every initialized package offers equivalent Make and Task entrypoints over its
local `scripts/tasks.py`. See the
[`standalone project task contract`](../docs/project-task-contract.md).

## Active packages

| Package | Status | Purpose |
| --- | --- | --- |
| [`nih-nimh-rpg`](nih-nimh-rpg/) | experimental | NIH/NIMH research-project-grant concept and attachment authoring |
| [`magazine`](magazine/) | experimental | Browser-compatible editorial magazines with digital, print, and accessible web outputs |
| [`research-paper`](research-paper/) | experimental | Neutral academic papers with PDF, accessible web, and arXiv-source outputs |
| [`technical-whitepaper`](technical-whitepaper/) | experimental | Evidence-led technical whitepapers with PDF and accessible web outputs |

Content under `.staging/` is governed reference intake, not part of this
registry. Useful visual behavior will be transformed into original publication
profiles or reusable LaTeX components with consistent override contracts. A
staged source is removed only after its provenance and transformation,
supersession, or retention decision is recorded; staged files are never
promoted by bulk copy.

See the [LaTeX component-library direction](../docs/latex-component-library.md).
