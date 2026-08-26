# Provenance

The active package is an original Beacon implementation. No class file, font,
logo, image, sample prose, or bibliography record was copied from the staged
references.

## Dispositioned staging references

Two visual-layout references were reviewed and removed in the migration that
introduced this package:

- `.staging/latex/Business Reports/makoto-technical-report` at tree
  `81f51da91e95c627ea03267d41ef79f8de02df5c`
- `.staging/latex/Business Reports/sullivan-business-report` at tree
  `54074d0f4965181674dfb02ecbd044ba30b15971`

Both originated from LaTeXTemplates.com, identified Vel as the author, and were
licensed CC BY-NC-SA 4.0. They were useful as examples of hierarchy, title
treatment, figures, citations, and business-report navigation, but their
noncommercial share-alike terms and bundled third-party assets made them poor
foundations for Beacon's reusable first-party package.

The deleted files remain recoverable from Git history using the tree IDs above.
This document records influence and disposition without importing the staged
license into the active implementation.

## Standards and tool references

The reference manuscript cites the official Pandoc manual, WCAG 2.2, and the
SOURCE_DATE_EPOCH specification. Those references inform the output and
validation contract; they are not template source code.
