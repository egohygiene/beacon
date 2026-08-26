# Standards baseline

Verified 2026-08-26. These sources define behavior and review expectations; no
source code or sample prose was copied from them.

- [arXiv: Submit TeX/LaTeX](https://info.arxiv.org/help/submit_tex.html) - arXiv
  compiles from the submission root, requires needed style and figure files,
  accepts PDF figures for PDFLaTeX, does not convert figures during processing,
  supports BibTeX, and can consume a matching generated `.bbl`. It also advises
  against `\today`, hidden files, JavaScript, and extraneous build products.
- [Pandoc User's Guide](https://pandoc.org/MANUAL.html) - informs the standalone
  HTML, table of contents, section wrappers, citation processing, and MathML
  projection.
- [CRediT](https://credit.niso.org/) - supplies the optional standardized
  contributor-role vocabulary. Roles describe contributions; they do not decide
  authorship.
- [ORCID registry search guidance](https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/)
  - supports the rule that Beacon never guesses or assigns an ORCID identifier.
  A project records one only when the author supplies or authenticates it.
- [Reproducible Builds: SOURCE_DATE_EPOCH](https://reproducible-builds.org/docs/source-date-epoch/)
  - supplies the build-time convention used for deterministic artifact checks.

arXiv's submission system and TeX Live versions change over time. Re-verify the
official guidance before a public submission and visually inspect the server's
generated PDF.
