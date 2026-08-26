# Beacon Extraction Notes

Beacon is intentionally incubated under `empathy/beacon/` so it can inherit the
repository's evolving agent, lint, security, and automation baseline while its
product boundary stabilizes.

## Standalone extraction target

A future extraction should be able to move `beacon/` to `egohygiene/beacon`
with minimal semantic change.

Expected extraction work:

1. move the contents of `beacon/` to the standalone repository root;
2. promote Beacon validation tasks into the standalone root Taskfile;
3. add the standard Empathy-derived repository foundation around the extracted
   project;
4. update relative documentation links and package paths;
5. preserve template IDs, manifest schema versions, and provenance history;
6. run both Empathy-side and standalone validation during the transition.

## Non-goals during incubation

- coupling template manifests to Empathy-specific paths;
- requiring Renderflow to validate or instantiate templates;
- encoding publication-specific research content in the Beacon runtime;
- making GitHub repository creation mandatory for project initialization.
