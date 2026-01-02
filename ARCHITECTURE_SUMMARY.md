# Architecture Summary (Durable Reference)

## Status

This document freezes a set of **durable architectural summaries** for the
Hilbert Information Laboratory (HIL) work-in-progress repository.

It is intentionally:
- descriptive, not prescriptive,
- stable across refactors,
- independent of implementation details,
- valid throughout the pre-submission (v0.1) phase.

This file should be updated only when **core architectural commitments change**,
not when code is reorganised.

---

## 1. What This Repository Is

This repository is a **full-stack epistemic laboratory**.

It is not:
- a single model,
- a classifier,
- a decision system,
- a production platform.

It **is**:
- a computational framework for constructing and inspecting
  epistemic structure,
- a diagnostic system for observing informational stability and instability,
- a laboratory for running controlled experiments over informational fields.

The system is explicitly **diagnostic**, not prescriptive.

---

## 2. Canonical Epistemic Primitives (Core)

The following objects define *what exists* in the system.
They are canonical and must not be duplicated with competing semantics.

### Structural Primitives
- **Element**  
  Minimal embedded informational unit (vector + identity).

- **Field**  
  Geometric configuration of elements in Hilbert space.

- **Graph**  
  Structural relations over elements (edges + weights only).

- **Molecule**  
  Structural aggregates of elements (e.g. connected components),
  without narrative or semantic interpretation.

These are **structural containers**, not interpretations.

---

## 3. Canonical Diagnostics (Core Metrics)

The following quantities define *what is measured*.
They are deterministic, numeric, and diagnostic-only.

- **Entropy**  
  Dispersion of structural mass in the graph.

- **Coherence**  
  Geometric alignment and coupling in embedding space.

- **Stability**  
  Relationship between entropy and coherence.

- **Potential**  
  Scalar field over configuration geometry (dispersion energy).

Core metrics:
- do not classify,
- do not threshold,
- do not decide,
- do not feed back into control.

All higher layers must **consume these metrics**, not redefine them.

---

## 4. State vs Process Invariant

A central architectural invariant:

> **State is measured in the core.  
> Process is observed outside the core.**

Implications:
- Core describes *what a configuration is*.
- Pipelines describe *how a configuration is produced*.
- Orchestration records *when and in what order* things occur.
- Visualization displays *results*, not logic.

No layer should reinterpret metrics as actions or decisions.

---

## 5. Orchestration and Provenance

The orchestrator exists to:
- sequence pipeline stages,
- record provenance (inputs, configs, timing, hashes),
- manage run directories and artifacts.

The orchestrator must not:
- compute epistemic metrics,
- enforce thresholds,
- select “best” outcomes.

Runs are treated as **inspectable experiments**, not optimizations.

---

## 6. Artifact Spine (Critical)

Each run should emit a **small, stable artifact spine**.
This spine is the interface between computation, CI, visualization, and analysis.

Minimum expected artifacts per run:
- `RUN_METADATA`
- `INPUT_MANIFEST`
- `CONFIG_SNAPSHOT`
- `FIELD_SUMMARY`
- `GRAPH_SUMMARY`
- `METRICS`
- `ARTIFACT_INDEX`

Optional downstream artifacts (non-authoritative):
- persistence diagrams,
- signature plots,
- sampled graph visualizations,
- ECED traces.

CI, diffs, and the frontend should rely primarily on this spine.

---

## 7. Visualization Contract

The frontend:
- reads artifacts,
- visualizes structure and diagnostics,
- never recomputes core metrics.

Visualization is **interpretive**, not epistemic authority.

---

## 8. ECED (Entropy-Constrained Effort Dynamics)

ECED is a **meta-diagnostic layer**.

It:
- observes how algorithms behave under constrained effort,
- produces traces and falsifications,
- exposes failure modes.

ECED:
- consumes core metrics and artifacts,
- runs downstream of normal pipeline execution,
- never gates, optimizes, or controls the system.

Invariant:

> **ECED may observe, perturb, and record.  
> It may not select, enforce, or decide.**

---

## 9. Database Layer

Any database (e.g. local sqlite) is a **functional convenience**, not an authority.

The filesystem artifact spine is sufficient to:
- reproduce results,
- inspect runs,
- support visualization.

Databases may be replaced or removed without changing epistemic meaning.

---

## 10. Native / Accelerated Code

Native code:
- exists solely for performance,
- must exactly match core semantics,
- must remain optional.

Native acceleration never introduces new meaning.

---

## 11. What Is Intentionally Incomplete

The following are expected to be incomplete at v0.1:
- export consolidation logic,
- long-term storage backends,
- labeling and semantic enrichment,
- full ECED integration,
- submission-time freezing and citation.

These are deferred by design.

---

## 12. One-Sentence Summary

> This repository is a living epistemic laboratory whose core measures
> informational structure, whose pipelines construct it, whose orchestrator
> records it, whose artifacts expose it, and whose meta-diagnostics test it —
> without ever deciding what should be believed or done.

---

*End of Architecture Summary*
