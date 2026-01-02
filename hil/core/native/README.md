# Native Epistemic Kernel (HIL)

## Purpose and Scope

This directory contains the **native C implementation of the numerical core** of the Hilbert Information Lab (HIL).

The native layer serves as the **numerical ground truth** for the project. It implements mathematically defined operators, metrics, and structural dynamics that are either:

- computationally intensive,
- numerically sensitive,
- or precision-critical

when implemented purely in Python.

This layer is **theory-witnessing**, not theory-defining. It exists to faithfully realise the formal constructs described in the thesis *“Hilbert Epistemic Fields and Informational Stability”* at the level of numerical computation.

---

## What This Layer Is (and Is Not)

### This layer **is**:

- A collection of **deterministic numerical primitives**
- A **reference implementation** for epistemic metrics
- The authoritative source of **numeric truth** for stability, entropy, and structural diagnostics
- A performance- and precision-oriented substrate for the Python epistemic core

### This layer **is not**:

- An orchestration engine
- A pipeline or workflow system
- A persistence or storage layer
- A semantic or interpretive component
- An agent, optimiser, or controller
- A system that makes decisions, assignments, or judgements

If a function in this directory appears to *decide*, *label*, *optimise*, or *interpret*, it does not belong here.

---

## Epistemic Constraints (Hard Rules)

The following constraints are **intentional and non-negotiable**:

1. **No Semantics**  
   Native code must not encode meaning, intent, truth, falsity, or belief.  
   It operates purely on numerical and structural representations.

2. **No Orchestration**  
   The native layer never controls execution order, iteration, or termination.  
   It does not “run” HIL; it computes values when called.

3. **No Persistence or Identity**  
   Native code does not manage files, paths, registries, IDs, or provenance.  
   All inputs are in-memory numeric structures.

4. **No External Authority**  
   Native code must not call external services, models, or APIs.  
   All randomness must be explicitly seeded.

5. **Determinism**  
   Given the same inputs, the same outputs must be produced across runs and machines (within numerical tolerance).

These constraints exist to preserve the **diagnostic, non-coercive** nature of the overall system.

---

## Responsibilities of the Native Layer

The native layer is responsible for **four classes of computation only**.

### 1. Linear and Spectral Operations

- Vector norms and distances
- Inner products and projections
- Normalisation and rescaling
- Stable accumulation and reduction
- Precision-safe arithmetic helpers

These operations define the **geometric substrate** of the Hilbert Epistemic Field.

---

### 2. Graph-Theoretic Metrics

- Degree distributions
- Density and sparsity
- Connected components
- Structural entropy
- Clustering and cohesion measures
- Graph-level stability diagnostics

Graphs are treated as **mathematical objects**, not social or semantic networks.

---

### 3. Structural Dynamics and Stability

- Field evolution under defined operators
- Controlled perturbation and relaxation
- Temporal decay functions
- Convergence and sensitivity analysis

“Simulation” here refers strictly to **counterfactual structural evolution**, not agent behaviour or optimisation.

---

### 4. Numerical Reference Implementations

- Canonical implementations of metrics also exposed in Python
- Sanity checks and validation harnesses
- Known-input → known-output tests
- Optional debug exports (clearly marked as diagnostic only)

Python code may wrap these functions, but must not silently replace them.

---

## File Overview

Typical contents of this directory include:

- `hilbert_native.h`  
  Declares the numerical epistemic primitives and ABI boundary.

- `hilbert_native.c`  
  Implements core graph and field diagnostics.

- `hilbert_math.c`  
  Low-level numeric helpers (decay, normalisation, precision handling).

- `hilbert_simulation.h` / `hilbert_simulation.c`  
  Structural dynamics and field evolution under formal operators.

- `pybind/`  
  Thin Python bindings exposing native functions to the Python core.

- `hilbert_test.c` (optional)  
  Numerical sanity checks and reference tests.

---

## Relationship to the Python Core

The relationship between layers is strictly **one-way**:

```
Python epistemic core  ──calls──▶  Native numerical kernel
```

The native layer never calls back into Python, never inspects Python objects beyond bound numeric buffers, and never participates in orchestration or control flow.

Python is responsible for:
- naming structures,
- assembling epistemic objects,
- exposing APIs to orchestration layers.

The native layer is responsible for:
- computing numbers correctly,
- efficiently,
- and reproducibly.

---

## Design Philosophy

This directory should feel:

- **boring** to read,
- **predictable** to use,
- **difficult to misuse**.

Its purpose is not to be clever, but to be **trustworthy**.

If future extensions require new numerical primitives, they should be added only if they can be:

- defined independently of any application context,
- justified directly by the formal theory,
- and implemented without introducing control or semantics.

---

## Final Note to Future Maintainers

This native layer is a **foundation**, not a growth surface.

Preserve its restraint.

If you are unsure whether a function belongs here, it probably does not.

---

*End of Native README*
