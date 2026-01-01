# Thesis–Repository Crosswalk  
## Mapping Claims, Theory, Code, and Evidence

---

## Purpose of This Document

This document provides a **systematic cross-reference** between:

- the doctoral thesis  
  *“Detecting Disinformation Campaigns in Social Media”*, and
- the materials contained in this repository.

Its purpose is to enable examiners, readers, and future custodians to:
- locate the formal and computational instantiation of specific thesis claims,
- inspect supporting evidence without re-executing the full system,
- and verify coherence between theory, implementation, and empirical traces.

This crosswalk is part of the **doctoral scholarly record**. It does not introduce new claims and does not extend the thesis.

---

## Canonical Status

- The **thesis manuscript** is the authoritative source for all theoretical and interpretive claims.
- This crosswalk documents how those claims are witnessed in the repository at the time of doctoral submission.
- No post-submission additions or downstream work should be read back into this mapping.

If discrepancies arise, the thesis takes precedence.

---

## How to Read This Crosswalk

Each section below corresponds to a **chapter or appendix of the thesis** and lists:

- the primary conceptual focus of that chapter,
- the relevant repository artefacts,
- and the evidential role those artefacts play.

The mapping is intentionally **many-to-many**:
- a single concept may appear across theory, code, diagrams, and traces,
- a single artefact may support multiple claims.

Presence in the repository indicates **supporting evidence or illustration**, not independent authority.

---

## Chapter 1 — Introduction and Epistemic Framing

**Thesis focus**
- Motivation for structural, non-prescriptive epistemic diagnostics
- Separation of informational structure from truth, belief, and intent
- Rationale for theory-first, label-free analysis

**Repository artefacts**
- `README.md` — orientation, scope, and intent
- `CHARTER.md` — epistemic and governance boundaries
- `NON_CLAIMS.md` — explicit limits of what is not asserted
- `theory/kit-principles.md` — foundational epistemic commitments

**Evidential role**
- Establishes scope, framing, and interpretive constraints  
- No empirical artefacts are required at this stage

---

## Chapter 2 — Knowledge–Information Theory (K–IT)

**Thesis focus**
- Distinction between data, information, and knowledge
- Stability, coherence, and constraint as epistemic primitives
- Diagnostic rather than normative epistemology

**Repository artefacts**
- `theory/kit-principles.md`
- `theory/regimes.md`

**Supporting code (illustrative)**
- `code/hil/metrics/entropy.py`
- `code/hil/metrics/coherence.py`

**Evidential role**
- Provides formal definitions and conceptual grounding  
- Establishes primitives used throughout later chapters

---

## Chapter 3 — Hilbert Epistemic Field (HEF) Formalism

**Thesis focus**
- Hilbert-space representation as a formal modelling choice
- Field-based representation of informational relations
- Operators for entropy, coherence, potential, and stability

**Repository artefacts**
- `theory/hef-formalism.md`
- `thesis/appendices/appendix-a-math.pdf`

**Supporting code**
- `code/hil/embedding/lsa.py`
- `code/hil/field/field.py`
- `code/hil/field/potential.py`

**Evidential role**
- Demonstrates computability and internal coherence  
- Connects mathematical formalism to executable structures  
- Does not assert ontological or cognitive claims

---

## Chapter 4 — Informational Elements, Molecules, and Structure

**Thesis focus**
- Construction of informational elements
- Molecules and higher-order informational structure
- Structural interpretation of narrative formation

**Repository artefacts**
- `theory/regimes.md`
- `diagrams/field/element_molecule_diagram.svg`

**Supporting code**
- `code/hil/elements/element.py`
- `code/hil/graph/molecule.py`

**Evidential role**
- Illustrates how complex informational structure emerges  
- Supports structural, non-agentic interpretation

---

## Chapter 5 — Stability, Regimes, and Informational Behaviour

**Thesis focus**
- Stability as a structural diagnostic quantity
- Informational, misinformational, and disinformational regimes
- Absence of semantic labels or supervised classification

**Repository artefacts**
- `theory/regimes.md`
- `diagrams/field/regime_landscape.svg`

**Empirical traces**
- `traces/equilibrium/`
- `traces/resonance/`
- `traces/collapse/`

Each trace directory contains:
- frozen configuration and manifests,
- stability, entropy, and coherence outputs,
- regime visualisations.

**Evidential role**
- Supports claims about structural behaviour and regimes  
- Serves as inspectable evidence, not benchmarks

---

## Chapter 6 — Empirical Studies and Diagnostics

**Thesis focus**
- Behaviour across contrasting corpora
- Detection of instability signatures
- Reproducibility without re-execution

**Repository artefacts**
- `code/notebooks/`
- `traces/*/README.md`

**Supporting notebooks**
- `code/notebooks/stability_analysis.ipynb`
- `code/notebooks/persistence_analysis.ipynb`

**Evidential role**
- Enables inspection of empirical reasoning  
- Demonstrates alignment between theory and observed structure

---

## Appendix A — Mathematical Details

**Thesis focus**
- Extended derivations and operator definitions
- Formal properties and constraints

**Repository artefacts**
- `theory/hef-formalism.md`
- `thesis/appendices/`

**Supporting code**
- Inline comments and docstrings in:
  - `code/hil/field/*.py`
  - `code/hil/metrics/*.py`

**Evidential role**
- Clarifies mathematical assumptions and implementation choices

---

## Appendix B — Extended Figures and Tables

**Thesis focus**
- Supplementary diagnostics and visualisations

**Repository artefacts**
- `diagrams/`
- `traces/*/outputs/`

**Evidential role**
- Mirrors and supplements figures in the thesis  
- Provides raw outputs where space constraints applied

---

## Governance, Scale, and Federation (Conceptual Only)

**Thesis focus**
- Orthogonality to markets and politics
- Non-acquirable epistemic authority
- Federation as replication, not centralisation

**Repository artefacts**
- `CHARTER.md`
- `ROADMAP.md`
- `federation/protocol.md`
- `diagrams/governance/`

**Evidential role**
- Conceptual and boundary-setting only  
- No operational, enforcement, or governance mechanisms are claimed

---

## Reproducibility and Provenance

**Repository artefacts**
- `reproducibility/`
- `code/manifests/`
- `config.yaml` files within trace directories

**Evidential role**
- Establishes lineage and provenance of results  
- Enables inspection without rerunning full pipelines

---

## Final Note to Readers and Examiners

This crosswalk exists to make explicit that:

- theoretical claims are grounded in formal definitions,
- formal definitions are witnessed by code,
- and empirical claims are supported by frozen, inspectable artefacts.

The repository should be read as a **coherent scholarly archive**, not as a standalone software project or evolving system.

---

*End of Crosswalk*
