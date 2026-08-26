# Beacon Template Registry

This directory contains Beacon's active, first-party template packages. Every
package is independently buildable, versioned, documented, and described by a
`beacon-template.toml` manifest.

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
