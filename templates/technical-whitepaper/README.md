# Technical Whitepaper

This package turns one evidence-led Markdown source into a polished PDF and an
accessible, responsive web document. It is the first-party implementation for
Beacon issue #1 and is deliberately usable before the organization-wide
Identity and Relay contracts are finished.

## Start writing

From the Beacon repository root, initialize a customized project safely:

```bash
cargo run --locked -- init technical-whitepaper "../my-whitepaper" \
  --title "Evidence-led System Design" \
  --author "Author Name" \
  --project-id "evidence-led-system-design" \
  --theme "egohygiene"
```

Then:

1. Review `metadata/whitepaper.json` and the selected theme.
2. Replace the reference manuscript in `manuscript/whitepaper.md`.
3. Record each important assertion in `evidence/claims.toml` and each supporting
   source in `evidence/sources.toml`.
4. Add real bibliography records to `manuscript/references.bib` and cite them in
   the manuscript.
5. Build and validate:

   ```bash
   make check
   ```

Outputs are written to `build/whitepaper.pdf` and `build/web/index.html`.

For the canonical Beacon handoff, run the shared doctor and package commands
from the Beacon repository root:

```bash
cargo run --locked -- doctor technical-whitepaper
cargo run --locked -- package "../my-whitepaper"
```

The package command validates the project before staging only the declared PDF
and web artifacts under `dist/technical-whitepaper-0.1.0/artifacts/`. The bundle
also contains `beacon-package.json` and `SHA256SUMS`; downstream publishers use
those files instead of collecting mutable files directly from `build/`.

To preview the product theme:

```sh
make clean
make check THEME="themes/product.json"
```

`make check` validates the document contract, claim/source relationships,
citation keys, internal links, image alternatives, theme contrast, PDF safety,
embedded fonts, web landmarks, and byte-for-byte reproducibility. Run the live
network check separately when preparing a release:

```sh
make check-links
```

## Publication stages

`whitepaper.toml` starts in `draft` mode. Drafts may use a branch name as the
source revision and may have pending reviews. `publication-ready` mode rejects
mutable revisions, incomplete reviews, placeholder text, unchecked live links,
and disabled publication.

The `publication` table and verified Beacon package form the input boundary for
the future Relay `document-site` profile. Beacon owns production of the local,
checksummed bundle; Relay and fleet consumers own live routes, deployment,
rollback, and release evidence. The theme JSON files are fallback projections
for the future document-style output from `egohygiene/identity#2`; consumers can
already provide another compatible file through `THEME`.

## Source contract

- `metadata/whitepaper.json`: title, abstract, authorship, version, language,
  keywords, and source provenance.
- `manuscript/whitepaper.md`: semantic narrative, citations, accessible diagram
  equivalents, limitations, reproducibility notes, and document history.
- `evidence/claims.toml`: reviewable claims with status, section, evidence IDs,
  citation keys, and claim-specific limitations.
- `evidence/sources.toml`: first-party and external evidence inventory.
- `themes/*.json`: Identity-compatible fallback projections.
- `VERSION_HISTORY.md`: changes to the reusable template package itself.

The reference manuscript describes the template instead of inventing product
results. Initialize a project for a real whitepaper, then replace the example
claims with evidence from that product.
