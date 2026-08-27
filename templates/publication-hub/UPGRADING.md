# Publication Hub upgrades

An initialized project pins both the Beacon profile version and the source/public
catalog schema version. Upgrades are explicit repository changes; no build may
silently mutate authored content.

## Compatibility policy

- Patch profile changes may fix rendering, validation, documentation, or tests
  without changing a valid v1 catalog's meaning.
- Minor profile changes may add optional capabilities or generated evidence.
- A required authored field, removed state, changed route meaning, or changed
  public JSON shape requires a new schema major version and migration guidance.
- Unknown core fields remain errors. Forward-looking product data belongs in
  namespaced `extensions` and still must respect lifecycle restrictions.

## Upgrade procedure

1. Read the profile release notes and compare both JSON schemas.
2. Update the project-owned kit on a branch while preserving
   `publication-hub.json`, product assets, custom CSS, and supplied landing
   pages.
3. Preview any catalog migration as a reviewable diff.
4. Run Make and Task through clean outputs for every supported theme.
5. Compare `site.json`, route inventory, aliases, HTML metadata, and
   `SHA256SUMS` with the previous build.
6. Run the repository's non-deploying Relay canary.
7. Update the pinned `profile_version` only when the new evidence is accepted.

If an upgrade changes a public route or removes an alias, keep the prior
artifact deployable until redirects and consumer links have been reviewed. A
schema rollback restores the previous project-owned kit and catalog together;
it does not depend on a live Beacon checkout.
