# IEEEtran BibTeX example

An original minimal bibliography starter, outside Beacon's active registry.
Both starter files use Beacon's MIT license. Install the complete IEEEtran
bibliography package through your TeX distribution; the dependency retains
its own LPPL terms. Upstream: <https://ctan.org/pkg/ieeetran>.

From this directory:

```sh
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape example.tex
bibtex example
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape example.tex
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape example.tex
```

The example entry is intentionally fictional and must be replaced.
The historical 1.12 bibliography bundle remains privately preserved; this
directory does not vendor a partial copy. Validation uses that retained
dependency in an isolated build directory. See
`../../MIGRATION-2026-10-25.md`.

[Rendered example](preview.pdf) — generated during the October 25 validation.
