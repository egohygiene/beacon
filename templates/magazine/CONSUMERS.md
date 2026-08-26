# Consumer contract

## Reflector compatibility canary

[`egohygiene/reflector`](https://github.com/egohygiene/reflector) remains the
owner of its completed 14-page visual companion. Its current image-first model
maps to Beacon pages using `layout = "full-bleed-artwork"`; adoption must not
move or rewrite its canonical artwork merely for conformity.

The compatibility seam preserves:

- explicit page order;
- one prompt provenance record per generated page where available;
- separate trim/digital and print artifacts;
- a manuscript-to-magazine consistency mapping;
- stable product-owned release identity.

## Ego Hygiene magazine

The first new consumer is the Ego Hygiene magazine tracked by private product
issues
[`egohygiene/egohygiene#308`](https://github.com/egohygiene/egohygiene/issues/308)
and
[`egohygiene/egohygiene#309`](https://github.com/egohygiene/egohygiene/issues/309).
Its existing `*.page.json`, artwork, prompt, and optional animation structure
can migrate into this contract incrementally. Its product repository retains
all authored content and should eventually expose a stable `/magazine` route.

## Future browser authoring

Dreamscape may later edit the same edition JSON, page JSON, Markdown, and asset
references in the browser, then write changes to a branch and open a pull
request. Beacon owns schemas, validation, and deterministic compilation;
Dreamscape owns editing interaction and Git synchronization.

The comic-book content model is intentionally excluded. Comics may reuse the
publication core later, but series, volumes, panels, balloons, and reading
order require a sibling profile rather than magazine-specific exceptions. No
canonical comics repository is selected by this package.
