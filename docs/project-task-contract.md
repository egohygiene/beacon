# Standalone project task contract

Every project initialized by an active Beacon profile owns the files required
to build and check its publication artifacts. Beacon is an optional initializer,
upgrade coordinator, validator, and packager; it is not a runtime dependency of
the initialized product.

## Separation of concerns

An initialized repository contains three local interfaces over one
implementation:

| Layer | Responsibility | Requires Beacon? |
| --- | --- | --- |
| `scripts/tasks.py` | Canonical project build, check, cleanup, and reproducibility orchestration | No |
| `Makefile` | GNU Make developer entrypoint | No |
| `Taskfile.yml` | Task developer entrypoint | No |
| Beacon CLI | Profile initialization, pin validation, planning, transactional execution, and packaging | Only when using Beacon commands |

Make and Task do not call one another. Both delegate to the same project-owned
Python task adapter, and Beacon invokes that adapter directly. Document-specific
renderers and checkers remain local to the project as well.

This boundary lets another orchestrator, including future Renderflow or
Dreamscape integrations, invoke the same stable project contract without moving
authored content or reconstructing Beacon internals.

## Command parity

Run commands from an initialized project root:

| Outcome | Make | Task |
| --- | --- | --- |
| Build governed outputs | `make build` or `make` | `task build` |
| Build and validate | `make check` | `task check` |
| Remove selected generated output | `make clean` | `task clean` |
| Verify deterministic output when supported | `make reproducibility` | `task reproducibility` |
| Check live links when supported | `make check-links` | `task check-links` |

The default `task` command lists available tasks. The default `make` command
builds the profile's governed outputs.

## Profile surface

| Profile | Build | Check | Clean | Reproducibility | Live links | Profile bootstrap test |
| --- | --- | --- | --- | --- | --- | --- |
| `research-paper` | Yes | Yes | Yes | Yes | Yes | Yes |
| `technical-whitepaper` | Yes | Yes | Yes | Yes | Yes | — |
| `magazine` | Yes | Yes | Yes | Yes | — | Yes |
| `nih-nimh-rpg` | Yes | Yes | Yes | — | — | — |

Bootstrap tests exercise Beacon's initializer and therefore run only in the
Beacon profile checkout. The parity command remains discoverable in initialized
projects but reports a successful skip because products do not clone themselves.

## Overrides

Make accepts variables after the target:

```bash
make check THEME="egohygiene" BUILD_DIR="build/review"
```

Task accepts the same uppercase variables:

```bash
task check THEME="egohygiene" BUILD_DIR="build/review"
```

Common variables are:

| Variable | Profiles | Purpose |
| --- | --- | --- |
| `PYTHON` | All | Python 3 executable used for the shared adapter and checks |
| `BUILD_DIR` | All | Generated output directory below the project root |
| `THEME` | Research paper, whitepaper, magazine | Selected governed theme |
| `PROJECT` | Research paper, magazine profile checkout | Explicit project source; initialized projects autodetect themselves |
| `PANDOC` | Technical whitepaper | Pandoc executable |
| `PDF_ENGINE` | Technical whitepaper | Pandoc PDF engine |
| `SOURCE_DATE_EPOCH` | Technical whitepaper | Optional override for the project-pinned reproducibility epoch |

Cleanup refuses the project root, filesystem root, and paths outside the
project-owned build-kit root.

## Prerequisites

Direct developer use requires Python 3.11 or newer plus the renderers and
inspection tools declared by the selected profile. GNU Make and Task 3 are
optional alternative frontends: install either one, or invoke
`python3 scripts/tasks.py --help` directly.

Beacon itself does not require Make or Task to build an initialized project. Its
execution manifest calls the same project-local Python adapter used by both
developer frontends.
