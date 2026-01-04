# Field Alignment Contract

## Status
Normative contract for HIL operators and tests.
Applies to all comparative, overlay, or multi-field operations.

## Purpose

This contract governs when and how multiple epistemic fields may be
compared, overlaid, or jointly visualized within the Hilbert Information Lab (HIL).

Its purpose is to prevent invalid comparisons between fields that do not
share a common representational basis, while permitting explicitly defined
alignment operations that preserve epistemic integrity.

---

## Definitions

**Field**  
A field is a finite set of vectors embedded in a Hilbert space, produced by
a deterministic embedding operator acting on a corpus.

**Embedding Basis**  
The latent coordinate system produced by an embedding operator
(e.g. LSA, spectral embedding).

**Field Alignment**  
An explicit operation that maps two or more fields into a shared embedding
basis under declared constraints.

---

## Core Principle

> Two fields may only be compared, overlaid, or jointly visualized if they
> are represented in the same embedding basis.

“Same basis” does not mean “same dimensionality by coincidence”.
It means **shared generative origin** or **explicit alignment operator**.

---

## Prohibited Operations (Hard Violations)

The following are explicitly forbidden:

1. Overlaying fields embedded independently into different latent spaces.
2. Truncating, padding, or reshaping vectors to force dimensional equality
   without an explicit alignment operator.
3. Re-running dimensionality reduction separately per field and overlaying
   the results.
4. Interpreting geometric proximity across unaligned fields.
5. Treating dimensional coincidence as epistemic equivalence.

Any of the above constitutes an *epistemic category error*.

---

## Permitted Alignment Operations

The following alignment strategies are permitted **only if explicit**:

### A. Shared Embedding Alignment (Preferred)

- Multiple corpora are embedded together using a single embedding operator.
- Resulting vectors are then partitioned back into fields.
- This preserves a common basis by construction.

### B. Declared Projection Alignment (Restricted)

- Fields are projected into a declared common linear subspace.
- Projection method must be:
  - deterministic,
  - linear,
  - explicitly documented.
- Projection loss must be acknowledged as a diagnostic artifact.

---

## Overlay Semantics

An overlay does NOT imply:

- semantic equivalence,
- explanatory dominance,
- normative evaluation,
- regime classification.

An overlay ONLY indicates:

- co-location under a shared geometric instrument,
- relative structural dispersion,
- diagnostic contrast.

---

## Stability Axis Constraint

If stability (or any derived scalar) is used as an additional axis:

- Stability MUST be computed independently per field.
- Stability MUST NOT be recomputed after alignment.
- Stability MUST NOT be normalized across fields.

Stability is diagnostic, not comparative.

---

## Determinism Requirement

All alignment operations MUST be deterministic with respect to:

- corpus content,
- operator parameters,
- ordering of inputs.

Alignment that introduces stochasticity violates this contract.

---

## Summary Invariant

> No shared geometry without shared origin or explicit alignment.

This contract exists to ensure that HIL comparisons remain
structurally meaningful, epistemically honest, and scientifically inspectable.

