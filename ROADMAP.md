---
schema: aether.architecture-document/v1
id: beacon-roadmap
title: Beacon Roadmap
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-24
governed_by:
  - architecture-roadmap
depends_on:
  - beacon-vision
  - beacon-pillars
  - beacon-architecture
  - beacon-decisions
related:
  - beacon-purpose
  - beacon-principles
  - beacon-manifesto
  - beacon-epistemology
supersedes: []
---

# Beacon Roadmap

<!-- BEGIN ROADMAP EXECUTION SNAPSHOT -->
<!-- roadmap-manifest
schema: hygiene.roadmap/v1alpha1
repository: egohygiene/beacon
visibility: public
publication: central
route: /roadmap/beacon/
updated: 2026-08-24
-->
## 2026-08-24 execution snapshot

> This evidence-reconciled snapshot is the issue-generation and visual-roadmap handoff. The longer-horizon strategy below remains canonical context; generated HTML, JSON, progress, issue plans, and commit lists are projections.

**Lifecycle:** seed, extraction stage  
**Current gate:** Extract a runnable publication CLI and template package before expanding the whitepaper, dossier, magazine, and research formats.  
**North-star outcome:** A reproducible publication toolkit for evidence-linked whitepapers, research papers, dossiers, and magazines.

### Visual roadmap publication

**Mode:** `central`  
**Route:** `/roadmap/beacon/`  
**Current publication evidence:** Documentation only; target publication through Pages and versioned release artifacts is not implemented.

Publish the public-safe projection through egohygiene.io at /roadmap/beacon/. This repository owns intent and acceptance evidence; it does not add a second site deployment.

### Quest line

<!-- roadmap-step
id: BEA-Q01
status: complete
depends_on: []
issues: [1, 2, 3, 5]
-->
#### BEA-Q01 — Define the publication architecture

**State:** `complete`  
**Depends on:** None

**Outcome:** Architecture and format ambitions are documented in a standalone repository.

**Exit criteria:**

- [x] Repository responsibilities and intended formats are documented.
- [x] Initial format work is represented in issues.

**Current evidence:**

- Architecture PR #4 merged at c5aa9603d5641822f55c2df679eb67059ca4cd8c on 2026-08-19.
- Issues #1, #2, #3, and #5 describe publication formats.

<!-- roadmap-step
id: BEA-Q02
status: active
depends_on: [BEA-Q01]
issues: []
-->
#### BEA-Q02 — Extract the CLI and template package

**State:** `active`  
**Depends on:** `BEA-Q01`

**Outcome:** Beacon owns runnable publication tooling and a versioned template contract.

**Exit criteria:**

- [ ] A CLI renders a minimal fixture.
- [ ] Templates are packaged independently from Reflector manuscripts.

**Current evidence:**

- No CLI, templates, schemas, tests, or workflows were observed.

<!-- roadmap-step
id: BEA-Q03
status: planned
depends_on: [BEA-Q02]
issues: []
-->
#### BEA-Q03 — Publish versioned template artifacts

**State:** `planned`  
**Depends on:** `BEA-Q02`

**Outcome:** Consumers can pin templates and verify the source used for an output.

**Exit criteria:**

- [ ] A tagged package includes templates, schema, and checksums.
- [ ] A clean consumer renders the reference fixture.

**Current evidence:**

- No release was observed.

<!-- roadmap-step
id: BEA-Q04
status: planned
depends_on: [BEA-Q03]
issues: [1, 5]
-->
#### BEA-Q04 — Prove whitepaper and research-paper flows

**State:** `planned`  
**Depends on:** `BEA-Q03`

**Outcome:** Issues #1 and #5 produce accessible, reproducible long-form publications.

**Exit criteria:**

- [ ] Source, citations, figures, and metadata render deterministically.
- [ ] Outputs pass Renderflow and accessibility validation.

**Current evidence:**

- Issue #1 covers the whitepaper and issue #5 the research-paper format.

<!-- roadmap-step
id: BEA-Q05
status: planned
depends_on: [BEA-Q04]
issues: [2, 3]
-->
#### BEA-Q05 — Add dossier and magazine publication

**State:** `planned`  
**Depends on:** `BEA-Q04`

**Outcome:** Issues #2 and #3 extend the proven pipeline to dossier/PDF-A and magazine outputs.

**Exit criteria:**

- [ ] PDF/A, dossier, and magazine fixtures meet declared archival and layout checks.
- [ ] Pages or release publication exposes versioned examples.

**Current evidence:**

- Issues #2 and #3 track dossier/PDF-A and magazine formats.
- No Pages or release publication was observed.

### Roadmap-to-issue handoff

- A step is complete only when its exit criteria and required evidence are satisfied; commit count never determines progress.
- Ready steps without an issue are candidates for the private, duplicate-aware roadmap.issue-plan.json dry run. Planned steps remain preview-only unless a reviewer explicitly opts them in with issue_policy: propose.
- Issue creation or reconciliation requires human approval or an explicitly authorized Pace operation and returns issue references through a reviewable roadmap pull request.
- Pull requests and commits should include Roadmap-Step: <ID>; historical evidence may be linked through existing issue and pull-request relationships.
- Public rendering uses only allowlisted build-time evidence and never places a GitHub token or private issue plan in the browser artifact.

<!-- END ROADMAP EXECUTION SNAPSHOT -->

## Strategic context

This roadmap describes capability evolution, not promised dates or an issue queue. Sequence follows architecture dependencies and may change when evidence or risk changes.

## Phase 1: Extract the incubated Beacon CLI

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 2: Stabilize template packages

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 3: Add the canonical white-paper template

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 4: Integrate rendering and validation

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Phase 5: Publish archival and distribution adapters

**Outcome:** A bounded capability advances from documented intent to validated, independently usable behavior.

**Exit signals:**

- The owning contract and acceptance criteria are versioned.
- Implementation and documentation agree.
- Relevant tests and safety checks pass.
- Downstream consumers and migration impact are understood.
- Remaining uncertainty is visible.

## Cross-cutting tracks

- Security, privacy, accessibility, licensing, and provenance.
- Documentation, architecture portals, examples, and onboarding.
- Packaging, release, compatibility, and self-hosting.
- Organization integration through explicit contracts.
- Observatory evidence and Pace conformance when those systems exist.

## Deferred direction

Optional managed services, enterprise controls, marketplaces, and the conversational organization compiler remain later architecture work. Current choices should preserve portability and avoid foreclosing them.

## Evidence and uncertainty

- **Observed:** The repository README establishes the intended boundary as a publishing platform for assembling, validating, packaging, and distributing polished documents and research artifacts; significant implementation remains incomplete.
- **Decided for this draft:** The repository owns the bounded concern described here and participates through versioned contracts.
- **Proposed:** Target systems and later roadmap phases remain proposals until accepted and implemented.
- **Open question:** Which parts of this draft should become active in the first independently versioned release?
