# Migrating an existing publication site

Migration is incremental. Keep the existing site and deployment workflow
authoritative until the generated artifact has been compared and approved.

## 1. Inventory without moving content

Record the current canonical and fallback bases, repository subpath, paper and
magazine routes, artifact filenames, root aliases, DOI/release metadata,
manifests, provenance files, custom landing pages, and deployment source. Do
not rename a published artifact merely to match a starter convention.

## 2. Initialize the standalone build kit

```bash
beacon init publication-hub "../publication-site-canary" \
  --title "Product publication site" \
  --author "Publisher"
```

Copy the resulting build kit into the product repository or use it as a review
workspace. Replace the starter catalog with product-owned declarations. A
publication without a real release remains `planned` or `draft`; do not add
placeholder checksums or identifiers.

## 3. Map physical resources and public routes

Declare each real resource with its local source, media type, public route, and
required integrity data. Preserve compatibility filenames through explicit
aliases. Use resource landing mode when an existing product page must remain
the slot landing page.

Reflector-style root aliases and Antidote-style draft/planned states have
dedicated fixtures under `fixtures/`.

## 4. Prove the product-owned build

```bash
make test
make check-content SOURCE_REVISION="$(git rev-parse HEAD)" REVISION_POLICY=deployment
make reproducibility SOURCE_REVISION="$(git rev-parse HEAD)" REVISION_POLICY=deployment
make clean
task test
task check-content SOURCE_REVISION="$(git rev-parse HEAD)" REVISION_POLICY=deployment
task reproducibility SOURCE_REVISION="$(git rev-parse HEAD)" REVISION_POLICY=deployment
task clean
```

Compare routes, visible copy, files, media types, byte counts, digests,
canonical URLs, and fallback URLs against the existing site. Review both
neutral and Ego Hygiene themes when the product supports them.

## 5. Add a non-deploying canary

CI should initialize or use the project-owned kit, build outside the Beacon
checkout, validate `site.json`, and verify both checksum inventories. Uploading
a review artifact is safe; changing the live Pages source is a separate,
human-approved step.

## 6. Hand the artifact to deployment

Only after parity is accepted should Relay or a product workflow deploy the
validated `site/` tree. Keep rollback to the previous site artifact available.
Custom-domain and HTTPS configuration remain host administration, not catalog
migration.
