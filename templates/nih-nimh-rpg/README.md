# NIH/NIMH Research Project Grant

An original Beacon authoring workspace for rapidly developing an NIH/NIMH
research-project-grant concept as separate, uploadable PDF attachments. It is
not an NIH form, does not submit an application, and does not replace the
selected Notice of Funding Opportunity (NOFO), the current NIH Application
Guide, or institutional review.

The package starts in `concept` mode so writing can begin before the mechanism
is final. `submission-ready` mode is intentionally gated on the activity code,
NOFO, due date, applicant organization, institutional submission contact,
program officer, and mechanism-specific Research Strategy page limit.

## Start writing

```bash
cp -R templates/nih-nimh-rpg my-nimh-proposal
cd my-nimh-proposal
$EDITOR common/metadata.tex proposal.toml
$EDITOR attachments/specific-aims.tex
$EDITOR sections/research-strategy/*.tex
make check
```

Built PDFs are written to `build/`:

- `project-summary-abstract.pdf`
- `project-narrative.pdf`
- `specific-aims.pdf`
- `research-strategy.pdf`
- `bibliography-references.pdf`

The workspace deliberately does not produce one monolithic grant PDF. NIH
submission systems assemble separately uploaded attachments into the
application image.

## Design defaults

- US Letter paper and 0.6-inch margins, leaving a small safety buffer above
  NIH's one-half-inch minimum;
- 11-point Helvetica-compatible body text with approximately 13-point leading;
- no applicant-created headers, footers, page numbers, or active hyperlinks;
- restrained, high-contrast typography optimized for reviewer scanning;
- numbered citations backed by one BibTeX source of truth;
- separate Significance, Innovation, and Approach source files;
- warnings during concept drafting and hard failures for unresolved readiness
  gates in `submission-ready` mode.

## External official-format artifacts

Do not recreate these in LaTeX:

- Biographical Sketch Common Form, NIH Biographical Sketch Supplement, and
  Current and Pending (Other) Support: prepare and certify them in SciENcv.
- Data Management and Sharing Plan: use NIH's required 2026 DMS Plan format
  page and follow the selected NOFO and institute-specific expectations.
- SF424 and other system forms: complete them through the applicant
  organization's authorized ASSIST, Grants.gov, or system-to-system workflow.

See [SOURCES.md](SOURCES.md), [CHECKLIST.md](CHECKLIST.md), and
[PROVENANCE.md](PROVENANCE.md) before treating an attachment bundle as final.

## Requirements

- a current TeX Live distribution with `latexmk`, `pdflatex`, `natbib`,
  `bibentry`, `microtype`, and the standard PostScript fonts;
- Python 3.11 or newer;
- Poppler's `pdfinfo` for the structural checks.

## Commands

```bash
make          # build all five authored attachments
make check    # build, inspect PDF structure, and evaluate readiness gates
make clean    # remove generated files
```
