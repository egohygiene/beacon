# Identity and Relay boundary

Beacon owns the whitepaper source contract, templates, local build, and quality
checks. It does not copy the Identity compiler or Relay release workflows.

## Identity input

The build accepts a JSON metadata projection through `THEME`. A compatible
projection contains these strings:

- `identity_mode`: `organization` or `product`
- `identity_name`
- `identity_product`
- `identity_primary`: six-digit hexadecimal color without `#`
- `identity_accent`: six-digit hexadecimal color without `#`
- `identity_surface`: six-digit hexadecimal color without `#`

The files under `themes/` are checked-in fallbacks. When IDN-02 publishes a
versioned document-style projection, Relay or a consumer repository can pass its
pinned output to `THEME` without changing the manuscript or templates.

## Relay handoff

Run `beacon package PROJECT` (or the equivalent `cargo run --locked -- package
PROJECT` from a Beacon checkout) to produce a validated, checksummed handoff:

| Artifact | Media type | Stable local path |
| --- | --- | --- |
| Whitepaper PDF | `application/pdf` | `dist/technical-whitepaper-0.1.0/artifacts/whitepaper.pdf` |
| Whitepaper web entrypoint | `text/html` | `dist/technical-whitepaper-0.1.0/artifacts/web/index.html` |
| Package manifest | `application/json` | `dist/technical-whitepaper-0.1.0/beacon-package.json` |
| Artifact checksums | `text/plain` | `dist/technical-whitepaper-0.1.0/SHA256SUMS` |

The package manifest records the profile and profile version, selected theme,
source repository and revision, artifact paths, sizes, and SHA-256 digests. Relay
must verify `SHA256SUMS` and publish the PDF and web entrypoint from the same
package.

Before enabling `[publication]` in `whitepaper.toml`, the consumer must also pin
the Relay profile version and immutable source revision, complete every review,
run the live-link check, and define rollback and publication evidence. Beacon's
package is the publication input contract; Relay publication and stable product
routes remain owned by `egohygiene/relay#4` and `egohygiene/pace#11`.

The Reflector compatibility audit may refine the consumer adapter, but it does
not block use of this first-party whitepaper profile or its local package.
