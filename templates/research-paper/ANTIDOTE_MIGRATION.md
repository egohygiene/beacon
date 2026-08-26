# Antidote migration contract

Antidote is the first intended consumer of `research-paper`, but its manuscript
must have exactly one writable canonical home. Beacon issue #5 establishes the
profile; Empathy issue #71 owns the later extraction from
`egohygiene/empathy/research/antidote` into `egohygiene/antidote`.

## Handoff sequence

1. Record the Empathy source commit and the tree ID for `research/antidote`.
2. Create the standalone repository from `scripts/bootstrap.py`.
3. Move authored claims, bibliography records, notes, and source files into the
   new repository. Convert the provisional Markdown manuscript into the
   project-owned `paper/paper.tex`; do not copy the old Beacon templates.
4. Set the new project's provenance fields to the Empathy repository, source
   path, and immutable extraction commit.
5. Build and run the full checker in both themes. Review the PDF, HTML, and
   extracted arXiv archive.
6. Make the standalone repository canonical, replace Empathy's writable copy
   with a pointer, and only then remove the old fixture.

The initial Antidote configuration should use this shape:

```toml
[beacon]
schema_version = 1
profile = "research-paper"
profile_version = "0.1.0"
theme = "egohygiene"

[paper]
id = "antidote"
title = "Antidote"
version = "0.1.0"
date = "2026-08-26"
language = "en-US"
stage = "draft"
entrypoint = "paper/paper.tex"
bibliography = "paper/references.bib"
keywords = ["empathy", "affect", "research software"]
abstract = "Replace with the reviewed Antidote abstract."

[[paper.authors]]
name = "Alan Szmyt"
affiliation = "Ego Hygiene"
credit_roles = ["Conceptualization", "Methodology", "Writing - original draft"]

[provenance]
source_repository = "https://github.com/egohygiene/empathy"
source_path = "research/antidote"
source_revision = "REPLACE_WITH_EXTRACTION_COMMIT"
license = "REVIEW_BEFORE_PUBLICATION"
source_date_epoch = 1787702400
```

Do not add an ORCID identifier unless it has been authenticated or supplied by
the author. Do not migrate the provisional `templates/template.tex` or
`templates/template.html`; this profile replaces them.
