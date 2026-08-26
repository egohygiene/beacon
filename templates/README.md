# Beacon Template Registry

This directory contains Beacon's active, first-party template packages. Every
package is independently buildable, versioned, documented, and described by a
`beacon-template.toml` manifest.

## Active packages

| Package | Status | Purpose |
| --- | --- | --- |
| [`nih-nimh-rpg`](nih-nimh-rpg/) | experimental | NIH/NIMH research-project-grant concept and attachment authoring |
| [`technical-whitepaper`](technical-whitepaper/) | experimental | Evidence-led technical whitepapers with PDF and accessible web outputs |

Content under `.staging/` is reference intake, not part of this registry. A
staged template is removed after it has been deliberately re-authored,
validated, or rejected; staged files are never promoted by bulk copy.
