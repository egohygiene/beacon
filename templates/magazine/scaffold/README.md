# Magazine Publication

This repository owns its structured edition, page sources, artwork provenance,
and complete local build kit. It was initialized from Beacon's `magazine`
profile version 0.1.0, but building and checking it does not require a Beacon
checkout.

Edit `beacon-project.toml`, `magazine/edition.json`, and the ordered page sources
under `magazine/pages/`. Then use either supported developer interface:

```bash
make check
task check
```

Both commands delegate to `scripts/tasks.py`; neither interface owns separate
publication behavior. Run `make clean` or `task clean` to remove generated
artifacts under `build/`.
