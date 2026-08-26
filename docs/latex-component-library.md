# LaTeX component-library direction

Beacon's staged LaTeX intake contains useful composition ideas across books,
title pages, newsletters, conference materials, reports, and other document
families. The goal is not to publish those packages unchanged or discard their
design knowledge. Beacon will use them as governed references while creating an
original component system with consistent APIs, accessibility, provenance, and
override behavior.

## Intended layers

| Layer | Owns | Example |
| --- | --- | --- |
| Tokens | Named visual decisions | color, type scale, spacing, rules, radii |
| Primitives | Small semantic components | art frame, pull quote, folio, callout |
| Compositions | Reusable page structures | chapter opener, title spread, back matter |
| Profiles | Publication semantics and defaults | book, magazine, paper, grant |
| Projects | Authored content and art direction | Ego Hygiene book or magazine edition |

The intended override cascade is:

1. accessible Beacon defaults;
2. optional Identity theme tokens;
3. publication-profile defaults;
4. project-level art direction;
5. deliberate component or page overrides.

Later layers may override presentation without mutating semantic content or
breaking the component API. Components should expose named slots for original
art, full-bleed images, captions, accessible descriptions, background textures,
ornaments, and alternate print/web behavior rather than forcing projects to
fork implementation files.

## Reference-intake workflow

Each staged family will be handled independently:

1. inventory sources, licenses, checksums, and useful design behaviors;
2. identify primitives and compositions rather than copying a complete theme;
3. re-author the behavior behind stable, documented component interfaces;
4. add neutral and Ego Hygiene examples plus override fixtures;
5. compile and visually inspect representative digital and print outputs;
6. record whether each reference was transformed, retained for later study, or
   superseded;
7. remove the staged source only after its disposition is recoverable in Git
   history and provenance records.

## Initial families

The first likely component-extraction candidates are title pages, book/chapter
structures, professional newsletters, three-column editorial layouts, and the
conference booklet. Publisher-specific journal classes remain venue-adapter
references rather than universal components.

This direction supports an art-heavy Ego Hygiene book without making that book
the canonical implementation. It also leaves a clean future seam for
Dreamscape to edit component selections and overrides in a browser while Git
branches remain the synchronization and review boundary.
