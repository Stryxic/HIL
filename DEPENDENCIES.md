# DEPENDENCIES.md  
## Conceptual and Technical Dependencies

---

## Purpose of This Document

This document enumerates the **conceptual, mathematical, and software dependencies**
of the Hilbert Information Lab (HIL) reference implementation contained in this
repository.

Its purpose is **not** to provide an installation guide or exhaustive requirements
file, but to clarify:

- which external ideas and tools the work relies on,
- which components are interchangeable,
- and which dependencies are incidental rather than foundational.

This supports accurate scholarly interpretation and prevents novelty from being
misattributed to underlying libraries.

---

## Conceptual Dependencies

The primary intellectual dependencies of this work are **theoretical**, not
software-based.

### Information Theory
- Shannon, C. (1948). *A Mathematical Theory of Communication*
- Weaver, W. (1949). *Recent Contributions to the Mathematical Theory of Communication*

Used for:
- entropy as a measure of dispersion,
- probabilistic interpretation of neighbourhood structure.

These ideas are foundational and not specific to any implementation.

---

### Spectral Semantics
- Latent Semantic Analysis (LSA)
- Singular Value Decomposition (SVD)

Used for:
- constructing a Hilbert embedding space,
- identifying low-rank semantic structure.

The novelty of this work lies in **how** spectral semantics are used as an epistemic
substrate, not in the decomposition method itself.

---

### Formal Epistemology
- Coherence theories of knowledge
- Stability and constraint-based epistemology
- Regime-based interpretations of epistemic behaviour

Used for:
- distinguishing informational, misinformational, and disinformational regimes
without truth arbitration.

---

### Dynamical Systems and Field Theory
- Gradient flow
- Potential functions
- Stability analysis

Used for:
- modelling epistemic dynamics over semantic space,
- interpreting instability as a structural phenomenon.

---

### Topological Data Analysis
- Persistent homology
- Vietoris–Rips filtrations

Used for:
- detecting global structural features,
- distinguishing stable from collapsing informational regimes.

---

## Software Dependencies (Reference Implementation)

The reference implementation relies on a small number of widely used scientific
Python libraries.

These dependencies were chosen for **clarity and accessibility**, not novelty.

### Core Numerical Libraries
- **NumPy**  
  Linear algebra, array operations.

- **SciPy**  
  Sparse matrices, SVD routines, numerical utilities.

These are interchangeable with equivalent numerical backends.

---

### Text and Semantic Processing
- **scikit-learn**  
  TF–IDF vectorisation, truncated SVD.

Alternative implementations (e.g. custom SVD, GPU backends) would not alter the
epistemic claims of the thesis.

---

### Graph and Network Analysis
- **NetworkX**  
  Graph construction, connectivity, molecule identification.

Chosen for readability; large-scale or optimised graph frameworks could replace it
without conceptual change.

---

### Topological Analysis
- **Gudhi** or equivalent TDA libraries  
  Persistent homology computation.

This dependency supports inspection of topological structure but is not essential
to all analyses presented.

---

### Visualisation
- **Matplotlib**
- **Seaborn** (optional)

Used only for explanatory figures and diagnostics.

---

## Optional and Incidental Dependencies

Some tools appear in notebooks or scripts for convenience:

- Jupyter
- Pandas
- tqdm

These are **incidental** and not required to understand the core framework.

---

## What This Work Does *Not* Depend On

Explicitly excluded dependencies include:

- deep learning frameworks (e.g. TensorFlow, PyTorch),
- pretrained language models,
- external annotation datasets,
- behavioural or user-level data,
- proprietary APIs or services.

The absence of these dependencies is intentional and supports interpretability
and epistemic restraint.

---

## Interchangeability and Robustness

With the exception of basic linear algebra routines, **no dependency is
conceptually irreplaceable**.

Substituting alternative libraries would affect:
- performance,
- scale,
- or convenience,

but not:
- the formal theory,
- the epistemic interpretation,
- or the central claims of the thesis.

---

## Final Statement

The Hilbert Information Lab is **library-light by design**.

Its contributions arise from:
- the composition of established methods,
- the introduction of stability-based epistemic operators,
- and the interpretation of informational behaviour as a field phenomenon.

This document exists to ensure that credit for novelty is assigned appropriately
and that the work is read as a contribution to epistemic science rather than
software engineering.

---

*End of DEPENDENCIES.md*
