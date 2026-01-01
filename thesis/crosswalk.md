# Thesis–Repository Crosswalk  
## Mapping Claims, Theory, Code, and Evidence

---

## Purpose of This Document

This document provides a **systematic cross-reference** between:

- the doctoral thesis  
  *“Detecting Disinformation Campaigns in Social Media”*, and
- the materials contained in this repository.

Its purpose is to enable examiners and readers to:
- locate the formal and computational instantiation of specific claims,
- inspect supporting evidence without re-executing the full system,
- and verify coherence between theory, implementation, and empirical results.

This crosswalk is part of the scholarly record and should be read alongside the thesis manuscript.

---

## How to Read This Crosswalk

Each section below corresponds to a **chapter or appendix of the thesis** and lists:

- the primary conceptual claim,
- the relevant repository location(s),
- and the evidential artefacts supporting that claim.

The mapping is **many-to-many**: a single concept may appear in multiple forms (theory, code, trace), and a single artefact may support multiple claims.

---

## Chapter 1 — Introduction and Research Framing

**Thesis focus**
- Reframing disinformation as a structural epistemic phenomenon
- Motivation for label-free, theory-driven detection

**Repository artefacts**
- `README.md` — project orientation and scope
- `CHARTER.md` — epistemic boundaries and non-goals
- `theory/kit-principles.md` — foundational epistemic commitments

**Evidential role**
- Establishes intent, scope, and interpretive constraints
- No empirical artefacts required at this stage

---

## Chapter 2 — Knowledge–Information Theory (K–IT)

**Thesis focus**
- Distinction between data, information, and knowledge
- Stability, coherence, and constraint as epistemic primitives

**Repository artefacts**
- `theory/kit-principles.md`
- `theory/regimes.md`

**Supporting code (illustrative)**
- `code/hil/metrics/entropy.py`
- `code/hil/metrics/coherence.py`

**Evidential role**
- Formal definitions
- Conceptual grounding for later field construction

---

## Chapter 3 — Hilbert Epistemic Field (HEF) Formalism

**Thesis focus**
- Spectral–semantic embedding space
- Field representation of informational elements
- Entropy, coherence, potential, and stability operators

**Repository artefacts**
- `theory/hef-formalism.md`
- `thesis/appendices/appendix-a-math.pdf`

**Supporting code**
- `code/hil/embedding/lsa.py`
- `code/hil/field/field.py`
- `code/hil/field/potential.py`

**Evidential role**
- Demonstrates computability of theoretical constructs
- Connects mathematical formalism to executable structures

---

## Chapter 4 — Informational Elements, Molecules, and Structure

**Thesis focus**
- Element construction and centroid representations
- Molecule and compound structures
- Structural interpretation of narrative formation

**Repository artefacts**
- `theory/regimes.md`
- `diagrams/field/element_molecule_diagram.svg`

**Supporting code**
- `code/hil/elements/element.py`
- `code/hil/graph/molecule.py`

**Evidential role**
- Shows how higher-order informational structure emerges from embeddings

---

## Chapter 5 — Stability, Regimes, and Epistemic Behaviour

**Thesis focus**
- Stability as a diagnostic quantity
- Informational, misinformational, and disinformational regimes
- Structural, not semantic, detection

**Repository artefacts**
- `theory/regimes.md`
- `diagrams/field/regime_landscape.svg`

**Empirical traces**
- `traces/equilibrium/`
- `traces/resonance/`
- `traces/collapse/`

Each trace directory contains:
- frozen configuration,
- run manifest,
- stability and entropy outputs,
- regime visualisations.

---

## Chapter 6 — Empirical Evaluation and Case Studies

**Thesis focus**
- Behaviour of the system across contrasting corpora
- Detection of instability signatures
- Absence of supervised labels

**Repository artefacts**
- `code/notebooks/`
- `traces/*/README.md`

**Supporting notebooks**
- `code/notebooks/stability_analysis.ipynb`
- `code/notebooks/persistence_analysis.ipynb`

**Evidential role**
- Provides inspectable empirical support for claims
- Demonstrates reproducibility via frozen artefacts

---

## Appendix A — Mathematical Details

**Thesis focus**
- Extended derivations
- Operator definitions
- Complexity considerations

**Repository artefacts**
- `theory/hef-formalism.md`
- `thesis/appendices/`

**Supporting code**
- Inline comments and docstrings in:
  - `code/hil/field/*.py`
  - `code/hil/metrics/*.py`

---

## Appendix B — Extended Figures and Tables

**Thesis focus**
- Supplementary diagnostics and visualisations

**Repository artefacts**
- `diagrams/`
- `traces/*/outputs/`

**Evidential role**
- Mirrors and extends figures in the thesis
- Provides raw outputs where space constraints prevented inclusion

---

## Governance, Scale, and Federation (Conceptual)

**Thesis focus**
- Orthogonality to markets and politics
- Non-acquirable, custodial governance
- Federation as replication, not centralisation

**Repository artefacts**
- `CHARTER.md`
- `ROADMAP.md`
- `federation/protocol.md`
- `diagrams/governance/`

**Evidential role**
- Conceptual and normative grounding
- No operational claims are made in the thesis

---

## Reproducibility and Provenance

**Repository artefacts**
- `reproducibility/`
- `code/manifests/`
- `config.yaml` files within trace directories

**Evidential role**
- Establishes provenance of results
- Enables inspection without rerunning full pipelines

---

## Final Note to Readers and Examiners

This crosswalk is intended to make explicit that:

- theoretical claims are grounded in formal definitions,
- formal definitions are operationalised in code,
- and empirical claims are supported by frozen, inspectable artefacts.

The repository should be read as a **coherent whole**, not as a standalone software project.

---

*End of Crosswalk*
