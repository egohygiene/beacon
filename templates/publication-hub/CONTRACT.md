# Publication Hub contract

## Versioned envelopes

The authored catalog and public catalog are separate contracts:

| Surface | Schema literal | Version | Owner |
| --- | --- | --- | --- |
| `publication-hub.json` | `beacon.publication-hub-source/v1` | `1.0.0` | Product repository |
| `build/site/site.json` | `beacon.publication-hub/v1` | `1.0.0` | Generated, never hand-edited |

Both schemas reject unknown core fields. Product-specific metadata belongs in
an `extensions` object; it cannot weaken lifecycle or publication truthfulness
rules.

The public catalog's `source.catalog_sha256` is the SHA-256 digest of the exact
private, authored `publication-hub.json` bytes. Product-local build and
validation bind that digest to the source file. A downstream host such as Relay
can validate the digest's syntax and preserve it as provenance, but cannot
recompute the binding when the private source catalog is intentionally absent
from the deployment artifact.

## Two independent lifecycles

The site can be deployed before any publication is released. Its lifecycle is
independent of every publication slot:

| Surface | States | Meaning |
| --- | --- | --- |
| Site `stage` | `draft`, `published`, `archived` | State of the publication hub itself |
| Slot `status` | `planned`, `draft`, `available`, `superseded`, `withdrawn` | State of one paper, magazine, or other publication |

`planned` and `draft` slots produce honest landing pages without fake download
claims. `planned` slots may not carry artifacts, source records, versions,
manifests, identifiers, releases, checksums, previews, provenance, covers, or
issue metadata, including through nested extension data. An `available` slot
must carry real, non-empty, checksummed resources and a deployable source
revision.

## URL and file model

- `path` is the physical file beneath the staged public tree.
- `route` is the public browser URL relative to the configured base.
- A landing page may therefore use `path: paper/index.html` with
  `route: paper/`.
- `canonical_base_url` is required. `fallback_base_url` is optional and must be
  distinct when present.
- Generated public `fallback_url` fields are always present and are `null` when
  no fallback host is configured.
- Public bases must be HTTPS, use a valid public DNS hostname, and may not use
  credentials, IP literals, localhost names, control characters, or an
  explicit non-443 port.
- Repository subpaths are supported; routes may not escape their base.

Aliases are explicit copies of one governed resource at another public route.
They exist for compatibility names such as `reflector.pdf`; they do not change
the canonical resource identity or checksum.

## Required public routes

Every built site publishes these core route records:

| ID | Kind | Route |
| --- | --- | --- |
| `home` | `hub` | empty root route |
| `downloads` | `downloads` | `downloads/` |
| `site-json` | `catalog` | `site.json` |
| `web-manifest` | `web-manifest` | `manifest.webmanifest` |
| `sha256sums` | `checksum` | `SHA256SUMS` |

The hub, slot, and downloads pages use semantic HTML, canonical and Open Graph
metadata, JSON-LD, visible lifecycle language, keyboard-visible focus styles,
and structured download details. A product may supply a slot landing page as a
governed resource instead of using the generated page.

## Integrity and reproducibility

Builds stage to a temporary directory, validate the complete tree, and replace
only an output previously marked as owned by this profile. The builder rejects
route collisions, escaping paths, symlinked inputs, empty resources, broken
local links or fragments, checksum mismatches, and source/output overlap.

`SHA256SUMS` covers every public file except itself in stable path order. The
source revision is selected in this order:

1. explicit `--source-revision` / `SOURCE_REVISION` task argument;
2. the `SOURCE_REVISION` environment variable;
3. the source catalog revision;
4. `WORKING_TREE`.

Local drafts may use `WORKING_TREE`. Available publications and builds using
`REVISION_POLICY=deployment` require a full lowercase 40-character commit SHA.

## Host boundary

The artifact contract ends at the validated `site/` directory. Beacon does not
write DNS records, select a Pages source, enable HTTPS, publish a release, or
deploy the tree. Relay or another repository-owned workflow consumes the static
artifact only after its catalog and checksums pass.
