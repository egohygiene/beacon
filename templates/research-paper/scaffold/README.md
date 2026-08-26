# @@TITLE@@

This repository owns the canonical manuscript, bibliography, figures, notes,
source record, and complete local build kit for `@@PROJECT_ID@@`. It was
initialized from Beacon's `research-paper` profile version 0.1.0, but building
and checking it does not require a Beacon checkout.

Start in `beacon-project.toml`, then replace the visible TODO prompts under
`paper/sections/`. Do not add an ORCID identifier unless the author supplied or
authenticated it.

Use either supported developer interface:

```bash
make check
task check
```

Both commands delegate to `scripts/tasks.py`; neither interface owns separate
publication behavior. Run `make clean` or `task clean` to remove generated
artifacts under `build/`.
