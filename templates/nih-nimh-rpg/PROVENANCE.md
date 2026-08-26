# Provenance

## Authorship

This package is a newly authored Beacon implementation licensed under MIT. Its
policy notes are paraphrased from the official NIH and NIMH sources recorded in
`SOURCES.md`; those sources remain authoritative.

## Staged reference disposition

Two byte-identical copies of a 2019 third-party template were reviewed as
reference intake and removed during this package's introduction:

- `.staging/latex/nih-grant-proposal/`
- `.staging/latex/Miscellaneous/nih-grant-proposal/`

The reference was version 1.1, dated December 26, 2019, and marked CC
BY-NC-SA 3.0. Its prose, sample bibliography, images, bibliography style, and
source code were not copied into this MIT-licensed package. Git history retains
the intake for audit and recovery.

## Design lineage

The legacy reference demonstrated the usefulness of compact NIH-oriented
typography, but it also combined many application components into one document
and embedded guidance that had become stale. Beacon replaces it with:

- original source and neutral placeholders;
- a multi-attachment project structure;
- current official-source links with verification dates;
- explicit external-form boundaries;
- concept and submission-readiness states;
- reproducible build and structural validation.
