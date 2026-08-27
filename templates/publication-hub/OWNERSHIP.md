# Publication Hub ownership

The publication hub is a product artifact, not a centralized website runtime.
The generated project remains independently buildable even if Beacon, Relay,
GitHub Actions, or GitHub Pages is unavailable.

| Concern | Canonical owner | Boundary |
| --- | --- | --- |
| Manuscript, magazine, and publication artifacts | Product repository | Beacon never rewrites publication source |
| Catalog, slot state, copy, artwork, logo, ordering, aliases, and style overrides | Product repository | Authored in `publication-hub.json` and local assets |
| Source and public JSON schemas, lifecycle invariants, deterministic renderer contract | Beacon `publication-hub` profile | Copied into an initialized project and pinned by profile version |
| Local site build and validation | Initialized product build kit | Python implementation shared by Make, Task, and Beacon adapters |
| Deployment workflow, environment protection, artifact transport, and Pages activation | Relay or product repository | Consumes a validated static directory; does not reinterpret slot truth |
| DNS records, custom-domain verification, certificate issuance, and HTTPS enforcement | Domain owner and hosting provider | Never inferred or mutated by the build |
| Brand-system defaults | Identity, when explicitly consumed | Product overrides remain local and optional |

The public catalog is renderer- and host-neutral. A consumer may deploy it to a
custom domain, a repository subpath, or another static host as long as the
declared canonical/fallback URL contract remains true.

Deployment must not change a planned slot to available, synthesize download
metadata, invent a DOI or release, or alter checksums. Those are product-source
changes that must be reviewed and rebuilt before deployment.
