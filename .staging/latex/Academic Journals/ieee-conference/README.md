# IEEE conference starter

An original neutral Beacon example using the separately installed `IEEEtran`
class. This reference is outside Beacon's active template registry.
The starter source is covered by Beacon's MIT license; the dependency retains
its own LPPL terms.

Install IEEEtran through your TeX distribution or obtain the complete package
from <https://ctan.org/pkg/ieeetran>. Follow your target venue's current
instructions: <https://conferences.ieeeauthorcenter.ieee.org/write-your-paper/authoring-tools-and-templates/>.

From this directory:

```sh
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape main.tex
pdflatex --interaction=nonstopmode --halt-on-error --no-shell-escape main.tex
```

The historical 2019 provider example bundle was preserved privately rather
than partially republished or silently relicensed. No provider source files
are vendored here. Validation uses the retained IEEEtran 1.8b dependency in an
isolated build directory; see `../../MIGRATION-2026-10-25.md`.

[Rendered example](preview.pdf) — generated during the October 25 validation.
