# Beacon reference intake

This directory contains governed source references that have not yet been
transformed into active Beacon profiles or components. Nothing below
`.staging/` participates in the runtime registry, normal builds, or releases.

## Current contents

The remaining `latex/` tree spans books, title pages, newsletters, conference
materials, journal classes, and other document families. It is design and
implementation research—not a collection to publish unchanged and not
disposable bulk.

Useful patterns will be transformed into original Beacon components or
profile-specific adapters with:

- recorded source, license, checksum, and disposition;
- stable semantic APIs instead of copied theme internals;
- accessible defaults and deterministic fixtures;
- Identity, profile, project, and page-level style overrides;
- artwork slots appropriate for projects such as the Ego Hygiene book;
- representative digital and print build evidence.

See [`../docs/latex-component-library.md`](../docs/latex-component-library.md)
for the intended architecture and intake workflow.

## Removal rule

A staged source may be removed only after its useful behavior and provenance
have been reviewed and its transformation, supersession, rejection, or later
retention decision is recorded. Git history remains the recoverable source of
removed intake.

The former staged Beacon CLI, contracts, tests, toolchain, and validator were
promoted and adapted at the repository root through issue `#12`. Their history
is summarized in [`../docs/core-provenance.md`](../docs/core-provenance.md).
