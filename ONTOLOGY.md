---
schema: aether.architecture-document/v1
id: beacon-ontology
title: Beacon Ontology
kind: architecture-document
version: 0.1.0
status: provisional
owners:
  - egohygiene
created: 2026-08-19
updated: 2026-08-19
governed_by:
  - architecture-ontology
depends_on:
  - beacon-purpose
  - beacon-vision
  - beacon-principles
  - beacon-epistemology
related:
  - beacon-pillars
  - beacon-manifesto
  - beacon-ai-constitution
  - beacon-personal-model
supersedes: []
---

# Beacon Ontology

## Domain scope

Beacon models the concepts needed for make publication projects easy to initialize, govern, validate, render, and release from reusable templates. The ontology names conceptual entities and relationships; it is not a source-code class model, API schema, or database design.

## Canonical concepts

| Concept | Meaning |
| --- | --- |
| Publication project | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Template | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Manuscript | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Metadata | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Asset | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Render target | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Validation | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Release package | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Citation | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |
| Archive | A canonical concept in the Beacon domain whose exact fields belong to specifications or schemas, not this ontology. |

## Core relationships

- A repository or person provides source context to one or more domain artifacts.
- A specification constrains how an artifact is interpreted or produced.
- A plan separates proposed action from execution.
- Evidence supports a claim; a decision authorizes a durable direction.
- Provenance connects derived artifacts to their inputs and processing context.
- A consumer integrates through an explicit interface rather than internal structure.

## Boundaries

- Conceptual identity is distinct from filesystem path, database identifier, or display label.
- Observed state is distinct from desired state.
- Proposed relationships are not accepted facts.
- Neighboring repositories retain ownership of their domain concepts.

## Evidence and uncertainty

- **Observed:** The repository README establishes the intended boundary as a publishing platform for assembling, validating, packaging, and distributing polished documents and research artifacts; significant implementation remains incomplete.
- **Decided for this draft:** The repository owns the bounded concern described here and participates through versioned contracts.
- **Proposed:** Target systems and later roadmap phases remain proposals until accepted and implemented.
- **Open question:** Which parts of this draft should become active in the first independently versioned release?
