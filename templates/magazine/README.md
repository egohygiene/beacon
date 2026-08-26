# Magazine Publication

This package turns structured edition and page JSON plus granular Markdown into
three synchronized artifacts:

- `magazine.pdf` - trim-size digital review PDF;
- `magazine-print.pdf` - bleed-size print PDF with trim boxes and crop marks;
- `web/index.html` - responsive, accessible reading experience suitable for a
  product-owned `/magazine` route.

It is the first-party implementation for Beacon issue #3. Reflector supplies
the compatibility evidence; the package does not copy Reflector's manuscript,
artwork, prompts, or product identity.

## Build the reference scaffold

```sh
make check-all
task check-all
```

That command builds and validates the neutral and Ego Hygiene fallback themes.
Artifacts are written below `build/<theme>/`.

## Start a product magazine

From the Beacon repository root, use the shared safe initializer:

```bash
cargo run --locked -- init magazine "../my-product-magazine" \
  --title "My Product Magazine" \
  --author "My Product" \
  --publisher "My Product" \
  --edition "01"
```

The profile-owned adapter remains independently callable from this directory:

```sh
python3 scripts/bootstrap.py \
  --destination="../../../../my-product-magazine" \
  --title="My Product Magazine" \
  --publisher="My Product" \
  --edition="01"
```

Then edit:

- `beacon-project.toml` for the Beacon pin, theme, print geometry, route,
  provenance, review state, and publication gate;
- `magazine/edition.json` for edition-level identity, creators, rights, and
  explicit page order;
- each `magazine/pages/*/page.json` for page identity, role, layout, and
  optional artwork/prompt/animation references;
- each page's `content.md` for semantic prose.

The initializer copies the renderer, checks, styles, themes, templates,
Makefile, and Taskfile into the product repository. Build there through either
developer interface:

```bash
cd "../my-product-magazine"
make check THEME="neutral"
task check THEME="neutral"
```

Both entrypoints delegate to the project-owned `scripts/tasks.py`; Beacon is not
required for either command.

## Source-of-truth boundary

The canonical authoring surface is deliberately browser-friendly:

1. TOML owns the Beacon project/build relationship.
2. Edition JSON owns publication metadata and ordered page references.
3. Page JSON owns stable IDs, semantic roles, layouts, and asset provenance.
4. Markdown owns page prose.
5. LaTeX, HTML, PDFs, and generated manifests are outputs.

This lets a future browser editor manipulate explicit objects and commit small,
reviewable files to a branch without round-tripping arbitrary LaTeX. Generated
output is never canonical. The generated publication manifest records hashes
for the project, edition, page, prose, and declared asset sources; it also
distinguishes the configured revision from the observed Git revision and dirty
state.

## Supported page contracts

Every issue must contain one `cover`, at least one `article`, one `credits`, and
one final `back-cover`. `inside-cover` is optional. The first release supports:

- `cover`, `opener`, `feature`, `diagram`, `split`, `quote`, `credits`, and
  `back-cover` layouts;
- optional full-page PNG, JPEG, or PDF artwork with required alternative text;
- optional prompt and animation provenance that remain source assets rather
  than PDF requirements;
- explicit back-cover publishing metadata, including optional ISBN, rendered
  barcode/QR assets, and an HTTPS QR destination.

The reference issue has eight pages so its print artifact satisfies the common
four-page signature constraint. Beacon does not impose printer imposition,
CMYK conversion, PDF/X certification, ISBN assignment, or vendor approval.
Those remain human- and vendor-gated publication steps.

## Publication boundary

`publication.stage = "draft"` is usable locally. `publication-ready` mode
requires an immutable source revision, completed editorial/accessibility/rights
reviews, a completed physical print proof, and enabled publication. The stable
artifact paths are the future Relay handoff; publication remains disabled until
the versioned upstream contract is available.

See [PUBLISHING.md](PUBLISHING.md), [CONSUMERS.md](CONSUMERS.md), and the JSON
schemas under `contracts/` for the durable integration boundaries.
