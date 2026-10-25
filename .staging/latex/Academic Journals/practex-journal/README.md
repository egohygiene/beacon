# PracTeX Journal reference package

Historical PracTeX Journal class and sample, retained as a complete local intake
bundle. This is governed reference material, outside Beacon's active registry.

## Contents and provenance

The six original files are preserved byte-for-byte. `pracjourn.dtx` declares
class v0.4n dated 2007-08-25; its supplied PDF reports 2007-08-13 v0.4n.
The separate v0.4o manual is a different retained edition.
See `PROVENANCE.json` for checksums and per-file licensing evidence.

The class sources are GPL-2.0-or-later; `COPYING` supplies GPL version 2.
The sample has its own permission notice allowing verbatim or modified
distribution while retaining that notice. Those source terms remain in force;
Beacon's root MIT license does not replace them. Preserve upstream names,
credits, and notices. This collection does not imply current venue support.

Upstream: <http://tug.org/pracjourn>.

## Build locally

Run these commands from this package directory with a TeX distribution
providing the packages named by the class:

```sh
latex --interaction=nonstopmode --halt-on-error --no-shell-escape pracjourn.ins
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape --jobname=pjsample-preview pjsample.ltx
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape --jobname=pjsample-preview pjsample.ltx
```

The generated class and build outputs are local artifacts. The supplied
`pjsample.pdf` is an upstream preview, not evidence of a new build.
Current verification is recorded in `../../MIGRATION-2026-10-25.md`.
