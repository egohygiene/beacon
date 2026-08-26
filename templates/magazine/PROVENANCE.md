# Provenance

The active package is an original Beacon implementation released under MIT. No
Reflector artwork, prompt, manuscript prose, LaTeX file, font, logo, or staged
third-party template is copied into this package.

Each artifact bundle records both the revision declared by the project and the
revision observed from Git when available. Project-scoped uncommitted changes
remain explicit, and publication-ready validation refuses a dirty or mismatched
revision. Canonical source files and declared assets carry SHA-256 evidence in
the publication manifest; rendered artifacts carry SHA-256 evidence in the
provenance record.

## Reflector reference evidence

The design and compatibility audit reviewed Reflector commit
`d04549a3df171d3cd0008ab74a46fb0549deebeb`:

- `magazine/` tree `e69616dd6326aab9ddee321a7ac93623f78ca51d`;
- `magazine/tex/` tree `b0e31c710e448433d8089f33ad68cbfb503f08bb`;
- magazine consistency specification blob
  `96a6520261b5498972143d4e027638ae3b208fdb`;
- future-knowledge style specification blob
  `d3eac0c043d270bb95bc6f796dd1a559040ed333`.

Those sources prove page ordering, paired digital/print outputs, prompt
provenance, visual-companion intent, and manuscript consistency. Beacon
generalizes the contracts while keeping Reflector's content and identity in
Reflector.

## Retained staging references

No `.staging` path is removed in this migration. The remaining nearby sources
represent distinct formats and are retained until dedicated profiles assess
them:

- professional newsletter tree `0e06035417fdbbf022d0fe48806e27e5ce8bbbf5`;
- short three-column newsletter tree `c6377666be4430862c3fa18b0046179710226df5`;
- conference booklet tree `707b6a9dfd20c8bad1304443ca354fc944bbc20a`;
- books intake tree `f5b0a3d8a621d0847777470bf1636f932b849041`.

Magazine, newsletter, event booklet, and book semantics overlap visually but
are not interchangeable. Retaining these sources prevents premature deletion
and keeps each later disposition recoverable and explicit.
