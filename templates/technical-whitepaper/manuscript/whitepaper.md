# Executive summary

Technical whitepapers fail quietly when polished prose drifts away from the
evidence, diagrams, source revision, or release artifact it is meant to
describe. Beacon treats the paper as a small publication system: one semantic
manuscript, an explicit claims ledger, a source inventory, selectable Identity
metadata, and deterministic PDF and web renderers.

This package is intentionally practical. A writer can replace the reference
content and build locally today. Review and publication gates become stricter as
`whitepaper.toml` moves from `draft` to `publication-ready`.

# Problem and context

A layout file alone does not make a trustworthy whitepaper. The publication
also needs to answer five questions:

1. What exactly is being claimed?
2. Which source supports each claim?
3. Which source revision produced the artifacts?
4. What remains unknown, contested, or out of scope?
5. Can another reviewer rebuild and inspect the same outputs?

The package separates those concerns without forcing writers to maintain two
copies of the prose. Pandoc's reader, citation processor, templates, and writers
allow a single semantic manuscript to target multiple output formats
[@pandoc-manual].

# Evidence and claims

The normative claim records live in `evidence/claims.toml`. The visible IDs make
review comments precise and keep the prose connected to the ledger.

**CLM-001 - one semantic source.** The same Markdown manuscript renders to the
PDF and standalone HTML artifacts. Format-specific templates control
presentation, not the underlying argument [@pandoc-manual].

**CLM-002 - equivalent text for diagrams.** WCAG 2.2 requires a text alternative
for non-text content that serves the equivalent purpose [@wcag22]. Every Beacon
diagram therefore carries a concise visual label and a nearby narrative
equivalent.

**CLM-003 - stable build time.** SOURCE_DATE_EPOCH gives build tools a shared,
stable timestamp input [@source-date-epoch]. Beacon combines that input with
fixed document metadata and byte comparison across two clean builds.

# System model

The system has one authoring center and two output paths. The diagram is written
twice only at the presentation layer so each format gets native, accessible
markup; the following paragraph is the format-independent equivalent.

```{=latex}
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  node distance=8mm and 11mm,
  every node/.style={font=\sffamily\small,align=center},
  source/.style={draw=BeaconPrimary,fill=BeaconSurface,rounded corners=2pt,minimum width=32mm,minimum height=10mm},
  output/.style={draw=BeaconAccent,fill=white,rounded corners=2pt,minimum width=29mm,minimum height=10mm},
  arrow/.style={-Latex,thick,draw=BeaconAccent}
]
\node[source] (source) {Semantic source\\and evidence};
\node[output, right=of source, yshift=9mm] (pdf) {PDF template\\review artifact};
\node[output, right=of source, yshift=-9mm] (web) {HTML template\\accessible web};
\draw[arrow] (source.east) -- (pdf.west);
\draw[arrow] (source.east) -- (web.west);
\end{tikzpicture}
\caption{One evidence-led source is rendered through format-specific presentation templates.}
\label{fig:system-model}
\end{figure}
```

```{=html}
<figure class="system-model" role="group" aria-labelledby="system-model-caption">
  <div class="diagram-source">Semantic source<br><span>and evidence</span></div>
  <div class="diagram-arrows" aria-hidden="true"><span>→</span><span>→</span></div>
  <div class="diagram-outputs">
    <div>PDF template<br><span>review artifact</span></div>
    <div>HTML template<br><span>accessible web</span></div>
  </div>
  <figcaption id="system-model-caption">One evidence-led source is rendered through format-specific presentation templates.</figcaption>
</figure>
```

In words: authors maintain the manuscript, metadata, claims, evidence inventory,
and bibliography as the canonical source. Pandoc combines that source with one
selected Identity projection. The PDF renderer produces a paginated review
artifact; the HTML renderer produces a semantic web entrypoint. The validator
checks both before Relay is allowed to publish them from the same immutable
revision.

# Review and release gates

The document lifecycle is deliberately asymmetric. Draft mode surfaces warnings
while keeping the writing loop fast. Publication-ready mode requires an
immutable source revision, completed editorial, technical, evidence, and
accessibility reviews, successful live-link validation, enabled Relay
publication, and reproducible outputs.

The local workflow tests both checked-in theme projections. It does not pretend
to be the pending Identity compiler or Relay publisher; their issue references
and handoff paths are explicit in `whitepaper.toml` and `PUBLISHING.md`.

# Limitations

- The fallback theme JSON is a compatibility seam, not the final IDN-02 package.
- The local workflow validates artifacts but does not publish them through the
  pending REL-04 profile.
- Semantic HTML, contrast, landmarks, and alternatives establish a strong web
  baseline, but automated checks cannot replace assistive-technology review.
- The PDF check covers metadata, page geometry, embedded fonts, encryption, and
  JavaScript. Full tagged-PDF and PDF/UA conformance belongs to Beacon issue #2.
- Byte-for-byte repeatability covers the pinned local inputs; it does not prove
  that arbitrary future TeX or Pandoc versions will emit identical bytes.

# Reproducibility

Run `make check` from this directory. The build fixes SOURCE_DATE_EPOCH, uses
explicit metadata and template inputs, renders twice into isolated temporary
directories, and compares the resulting PDF and HTML bytes. The validator also
requires embedded PDF fonts and rejects encrypted or JavaScript-bearing files.

For a release candidate, pin the build environment, set `source_revision` to the
full commit SHA, complete every review field, run `make check-links`, and enable
the versioned Relay profile only after REL-04 publishes it.

# Version history

## 0.1.0 - 2026-08-26

Initial reference implementation with evidence records, selectable Identity
themes, native PDF and HTML diagrams, explicit limitations, deterministic build
checks, and a Relay publication boundary.
