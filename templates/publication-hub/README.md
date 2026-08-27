# Publication Hub profile

The `publication-hub` profile turns a product-owned publication catalog into an
accessible, deterministic static site. It supports papers, magazines, source
archives, provenance, manifests, and intentionally unpublished slots without
coupling the product to GitHub Pages, Relay, or any other host.

## Start locally

The checked-in profile uses the Antidote-shaped fixture by default:

```bash
make check
task check
```

An initialized project owns the same Python, Make, Task, schema, test, and
rendering kit:

```bash
cargo run --locked -- init publication-hub "../my-publication-site" \
  --title "My Publication" \
  --author "Publication Author"
cd "../my-publication-site"
make check
task check
```

Only Python 3.11 or newer is required by the generated site runtime. Make and
Task are equivalent optional developer frontends.

## Authoring surface

Edit `publication-hub.json` to declare the site identity and ordered slots.
Product repositories may own their logo, artwork, copy, token overrides,
custom CSS, artifacts, root aliases, and product-supplied slot landing pages.

The public tree is staged transactionally under `build/site/`. Its
`site.json`, `manifest.webmanifest`, and `SHA256SUMS` are deterministic. The
build ownership marker stays outside `site/` and therefore outside a deployed
artifact.

The starter intentionally contains a draft paper and a planned magazine. A
planned slot renders a truthful landing page but cannot claim an artifact,
version, identifier, release, manifest, checksum, preview, or provenance.

## Contracts and operations

- [Catalog and public-site contract](CONTRACT.md)
- [Ownership and deployment boundary](OWNERSHIP.md)
- [Migration guide](MIGRATION.md)
- [Upgrade policy](UPGRADING.md)
- [Source catalog JSON Schema](contracts/publication-hub.schema.json)
- [Public catalog JSON Schema](contracts/publication-site.schema.json)

The fixtures cover paper-only, magazine-only, combined, Antidote planned
magazine, Reflector root aliases, and an empty catalog without a fallback host.
They are contract evidence, not deployable product content.
