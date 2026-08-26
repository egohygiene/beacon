# Publishing and print handoff

## Artifact contract

The build emits stable paths:

| Artifact | Purpose |
| --- | --- |
| `magazine.pdf` | Trim-size digital review and download |
| `magazine-print.pdf` | Bleed-size printer review with crop marks and PDF trim/bleed boxes |
| `web/index.html` | Accessible web reading surface for `/magazine` |
| `publication-manifest.json` | Ordered source/page/editor contract |
| `provenance.json` | Source revision and SHA-256 artifact evidence |

## Print interpretation

The default trim is 8 by 12 inches to preserve Reflector compatibility. The
print PDF adds 0.125 inch bleed on every edge. Artwork intended to bleed must
already contain meaningful image content through that region; Beacon does not
invent missing pixels.

The output remains in reader order. A printer or print-on-demand vendor owns
binding-specific imposition. Before release, confirm the vendor's trim, bleed,
safe-area, color-space, ink-coverage, barcode, spine, and PDF requirements.

`print-ready` in this profile means structurally prepared for a vendor proof;
it does not claim PDF/X conformance, CMYK conversion, archival certification,
or acceptance by a specific printer. The completed physical proof gate records
that a human reviewed an actual sample.

## Digital and web review

The digital PDF intentionally omits printer marks. The web artifact preserves
semantic text even when a page also uses raster artwork, so the publication can
remain readable by assistive technology and indexable on a product site.

## Relay handoff

Relay should consume these exact artifact paths, attach immutable checksums and
source provenance, and publish only when `publication.enabled = true`. Local
authoring and validation do not depend on GitHub Actions or Relay.
