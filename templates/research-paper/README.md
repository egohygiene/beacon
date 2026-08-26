# Research Paper

This package gives a standalone research project one canonical LaTeX manuscript
and three synchronized outputs: a publication-quality PDF, an accessible web
projection, and a clean arXiv source archive. The manuscript, bibliography,
figures, notes, source records, and complete build kit remain owned by the paper
repository. Beacon provides the versioned profile and optional orchestration.

## Start a paper

From the Beacon repository root, use the shared safe initializer:

```bash
cargo run --locked -- init research-paper "../antidote" \
  --title "Antidote" \
  --author "Alan Szmyt" \
  --project-id "antidote" \
  --theme "egohygiene"
```

The profile-owned adapter remains independently callable from this directory:

```sh
python3 scripts/bootstrap.py \
  --destination="../../../../antidote" \
  --title="Antidote" \
  --author="Alan Szmyt" \
  --project-id="antidote" \
  --theme="egohygiene"
```

The initializer copies the governed runner, styles, themes, templates, and
checks into the paper repository. Build there through either developer
interface:

```bash
cd "../antidote"
make check THEME="egohygiene"
task check THEME="egohygiene"
```

The result is:

- `build/paper.pdf`
- `build/web/index.html`
- `build/arxiv/<paper-id>-<version>.tar.gz`
- `build/provenance.json`

Make and Task both delegate to the initialized project's `scripts/tasks.py`.
Set `THEME="egohygiene"` to exercise the organization projection. Run
`make check-links` or `task check-links` before a submission or release to
verify external links.

## Project contract

- `beacon-project.toml` owns title, authors, affiliations, optional authenticated
  ORCID identifiers, CRediT roles, version, stage, theme, and provenance.
- `paper/paper.tex` is the canonical manuscript entrypoint.
- `paper/sections/*.tex` keeps long manuscripts navigable without introducing a
  second canonical source.
- `paper/references.bib` owns bibliography records.
- `paper/figures/*.svg` owns editable figures. The build converts them to PDF
  before LaTeX and arXiv packaging, while HTML retains the SVG.
- `notes/` and `sources/` are project-owned working areas and are never included
  in publication artifacts.

Use `\BeaconFigure{slug}{caption}{description}` for a synchronized figure. The
caption is visible in both outputs; the description supplies a nearby text
equivalent for readers who cannot interpret the graphic. Tables, equations,
citations, cross-references, appendices, and ordinary LaTeX section hierarchy
remain standard LaTeX.

## Readiness model

The checker accepts `draft`, `submission-ready`, and `published` stages. Drafts
may retain visible placeholders and mutable provenance, but they report
warnings. Submission-ready and published manuscripts reject placeholders,
missing references, incomplete artifact sets, unsafe PDFs, inaccessible web
landmarks, and arXiv bundles that cannot compile independently.

The arXiv archive is intentionally conservative: PDFLaTeX, BibTeX, bundled
Beacon styles, a generated `.bbl`, converted PDF figures, no hidden files, and
no intermediate build products. Always inspect arXiv's rendered PDF during the
actual submission process; local validation cannot reproduce every server-side
policy or TeX Live transition.

See [`ANTIDOTE_MIGRATION.md`](ANTIDOTE_MIGRATION.md) for the first consumer
handoff and [`SOURCES.md`](SOURCES.md) for the standards baseline.
