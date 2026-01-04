# HIL Core Invariants

**Status:** Frozen  
**Applies to:** HIL Core v1.0  
**Scope:** `hil/core/**`, `hil/tests/**` (core tests only)

---

## Purpose of This Document

This document defines the **non-negotiable invariants** of the HIL (Hilbert Information Laboratory) core.

These invariants are not implementation details.
They are **epistemic constraints**.

Any change that violates an invariant below constitutes a **core break** and requires:
- an explicit version increment, and
- a written justification explaining which invariant is being relaxed and why.

---

## Definition: “Core”

The **HIL Core** consists of:

- Deterministic construction of geometric structure from text
- Diagnostic (non-decisional) measurement operators
- Timebase calibration and certification
- Stream discipline (time vs index separation)
- Covariant path geometry
- Overlay comparability across corpora
- CI-enforced invariance tests

Anything outside this is an **extension**, not core.

---

## Core Invariants

### I. Determinism

- All core operations are deterministic.
- Given identical inputs, outputs are identical across runs.
- No randomness unless explicitly injected as a probe and labeled as such.
- No hidden state, caches, or learning loops.

**Enforced by:**  
`test_calibration_vertical_slice.py`, `test_trust_vertical_slice.py`

---

### II. Geometry First, Semantics Excluded

- Core operates on **geometry**, not meaning.
- No labels, topics, scores, classifications, or thresholds.
- No claims of truth, trust, correctness, or intent.

Interpretation is **external** to the core.

---

### III. Diagnostic-Only Outputs

- Core outputs are continuous, non-decisional diagnostics.
- No binary decisions.
- No optimization objectives.
- No loss functions that imply improvement toward a goal.

Core answers *“what structure exists?”*, never *“what should be done?”*.

---

### IV. Theory–Code Discipline

- Theory precedes code.
- Code witnesses theory; it does not define it.
- Any new operator must have:
  - a mathematical definition,
  - a clear domain,
  - and an invariance justification.

---

### V. Stream Authority Over Time

- Time is an **external index**, not an intrinsic machine state.
- Streams define:
  - which time anchors are valid,
  - how durations map to slices.
- Instruments must never infer time validity implicitly.

**Invariant:**  
Duration ≠ index.

**Enforced by:**  
`StreamProtocol`, `test_timebase.py`

---

### VI. Certified Timebase

- HIL must not sample faster than it can distinguish structure from noise.
- A minimum viable tick (Δt) must be established via:
  - data sufficiency,
  - compute constraints,
  - noise floor estimation.
- Oversampling noise is a test failure, not a configuration choice.

**Enforced by:**  
Time–frequency tradeoff diagnostics and CI tests.

---

### VII. Noise-Aware Measurement

- Structural change below the instrument noise floor is not treated as resolved.
- Noise floors are derived from admissible moduli variation.
- Sensitivity and stability are properties of the instrument, not the data.

---

### VIII. Overlay Comparability Without Semantics

- Fields of different intrinsic dimensionality may be compared.
- Comparability is achieved via:
  - explicit alignment contracts,
  - shared linear subspaces,
  - deterministic projections.
- No semantic alignment, normalization, or topic matching is permitted.

**Enforced by:**  
`test_overlay_field.py`

---

### IX. Covariance Under Reparameterization

- No privileged clock.
- No privileged sampling density.
- Diagnostics must be invariant under monotone reparameterizations of time.

Time may change; **geometry must not**.

---

### X. Covariant Hilbert Paths

- Diachronic structure is represented as paths in diagnostic space.
- Paths may be irregular, sparse, or discontinuous in time.
- Core path metrics are geometric invariants:
  - arc length,
  - diameter,
  - total turning / curvature.
- Coordinate-dependent rates are allowed only if:
  - explicitly labeled,
  - never mixed with invariants.

**Enforced by:**  
`test_path_covariant_invariance.py`

---

### XI. Invariance Bands, Not Point Claims

- Core reports bands, dispersions, and sensitivity curves.
- Single numbers are allowed only when:
  - derived from invariant geometry,
  - accompanied by stability guarantees.
- Silence is preferred to unstable precision.

---

### XII. No Internal Causality

- Core does not model causes, mechanisms, or dynamics.
- No arrows of causation.
- No predictive claims.

HIL measures **structure**, not behavior.

---

## What the Core Explicitly Does *Not* Do

- ❌ Learning
- ❌ Optimization
- ❌ Forecasting
- ❌ Classification
- ❌ Ranking
- ❌ Scoring
- ❌ Policy evaluation
- ❌ Ground truth comparison
- ❌ Truth adjudication

If any of the above appear, the code is **not core**.

---

## Extension Rule

New work must fall into one of two categories:

1. **Core-preserving extension**
   - Lives outside `hil/core`
   - Depends on core, but does not modify it

2. **Core revision**
   - Requires:
     - updated invariants,
     - new tests,
     - explicit version bump,
     - written rationale

Silent erosion of invariants is not permitted.

---

## Canonical One-Sentence Definition

> **HIL Core is a deterministic, covariant, noise-aware measurement instrument that extracts geometric invariants from structured representations without semantics, decisions, or optimization.**

---

## Status Declaration

As of this document:

> **HIL Core v1.0 is complete and frozen.**

All future work is either:
- extension, or
- explicit revision.

There is no third category.

---
