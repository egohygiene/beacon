# Research Paper Template

This is Beacon's canonical first template package. It is derived from the
working research templates in `egohygiene/renderflow` and exists to prove the
Beacon package contract before the CLI is introduced.

## Outputs

- `template.tex` — Pandoc-compatible LaTeX template for PDF generation.
- `template.html` — Tera-compatible HTML presentation template.

## Required metadata

- `title`
- `author`

## Optional metadata

- `date`
- `abstract`
- `toc`
- `fontsize`
- `papersize`
- `geometry`
- `header-includes`

## Example

`example/paper.md` demonstrates the intended Markdown/front-matter shape.

A future Beacon CLI will materialize a complete project around this package;
this PR intentionally defines and validates the package before implementing
project generation.
