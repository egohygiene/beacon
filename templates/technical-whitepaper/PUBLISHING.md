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

## Relay output

REL-04 is expected to consume:

| Artifact | Media type | Stable local path |
| --- | --- | --- |
| Whitepaper PDF | `application/pdf` | `build/whitepaper.pdf` |
| Whitepaper web entrypoint | `text/html` | `build/web/index.html` |

Before enabling `[publication]` in `whitepaper.toml`, the Relay profile must pin
its own version, publish both artifacts from the same immutable source revision,
and emit checksums, provenance, rollback instructions, and the live-link report.
The local GitHub workflow is a validation producer, not a substitute publisher.
