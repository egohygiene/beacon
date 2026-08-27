# Publication Hub

This project owns its catalog, site copy, artwork, style overrides, and build
kit. Beacon can initialize and package it, but the site remains buildable with
only Python 3 and either Make or Task:

```bash
make check
task check
```

Edit `publication-hub.json`. Draft and planned slots render honest landing
pages without download links. Change a slot to `available` only after adding a
real, non-empty artifact with an explicit media type and route.

The public tree is staged under `build/site`. The ownership marker remains in
`build`, outside the public tree.
