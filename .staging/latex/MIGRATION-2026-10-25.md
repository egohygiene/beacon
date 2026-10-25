# LaTeX reference intake — October 25, 2026

This change extends governed reference intake and discoverability. It does not
register new active publication profiles or change runtime behavior.

## Dispositions

- Fifty incoming book-template files matched existing Git blobs at base commit
  `ec32528be133d51cf047d228bff51cd667a34c99`: Kaobook 22,
  Legrand Orange Book 9, Tufte Book 16, and ebook-book 3.
  Existing canonical files were retained without duplicate imports.
- Six PracTeX Journal files were imported with their original bytes and names.
  The class license and the sample's separate permission notice are preserved.
  `PROVENANCE.json` records all six hashes; GPL version 2 is included as `COPYING`.
- Two original neutral starter examples were added for IEEE conference papers
  and IEEEtran BibTeX. Complete upstream dependencies must be installed
  separately; the historical provider bundles are not partially vendored.
- Historical Wiley, IEEE, and flyer source bundles remain privately preserved
  for dependency and distribution-term review. No personal records or private
  storage links are published here.

## Validation

| Example | Verification | Result |
| --- | --- | --- |
| PracTeX Journal | Generate class from original `.ins`/`.dtx`; run pdfLaTeX twice, including documented preview job name | Pass; 3 pages |
| IEEE conference | Run pdfLaTeX twice using retained IEEEtran 1.8b in an isolated build directory | Pass; 1 page |
| IEEEtran bibliography | pdfLaTeX, BibTeX, pdfLaTeX twice using retained IEEEtran.bst 1.12 | Pass; 1 page; citation resolved |

All commands disabled shell escape. Final sample logs contain no undefined
references or missing-character warnings. All five rendered pages were
visually inspected. The two new preview PDFs correspond to the new examples.
The bundled PracTeX PDF remains the upstream original.

Original source hashes, generated preview checksums, local link checks, and
the absence of private Drive links were checked before publication. The
existing 119 reference families were inventoried, not rebuilt. Current
publisher compliance, accessibility conformance, and active-profile support
are not established by these smoke builds.

## Follow-ups

The Wiley bundle has missing `p01.tex` and `p02.tex` references and
case-sensitive package/bibliography filename mismatches. The historical
Practical TeX 2005 flyer lacks `p2005.png`. Their originals remain intact;
neither bundle is represented here as a build-ready template.

Retain separate upstream terms. Beacon's root MIT license applies to the new
original examples and documentation, not as a replacement for imported notices.
