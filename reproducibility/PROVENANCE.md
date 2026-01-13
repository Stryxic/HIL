## Reproducibility, Determinism, and Result Lineage

---

## Purpose of This Document

This document defines what **provenance** and **reproducibility** mean for the
Hilbert Epistemic Field framework and the Hilbert Information Lab (HIL) reference
implementation contained in this repository.

Its purpose is to:
- clarify which aspects of the work are reproducible and in what sense,
- document how results were generated and preserved,
- prevent overclaiming of determinism in high-dimensional settings,
- and enable responsible reuse and inspection of empirical artefacts.

This document should be read alongside `STRUCTURE.md` and `NON_CLAIMS.md`.

---

## Definitions

### Provenance

*Provenance* refers to the documented lineage of an artefact, including:
- the code version used,
- configuration parameters,
- random seeds (where applicable),
- execution environment,
- and input data identifiers.

Provenance answers the question:  
**“Where did this result come from, and under what conditions?”**

---

### Reproducibility

In this work, reproducibility is understood in **epistemic**, not absolute,
terms.

Reproducibility answers the question:  
**“Do the same structural patterns recur under equivalent conditions?”**

It does *not* require bitwise-identical outputs in all cases.

---

## Levels of Reproducibility

Three levels of reproducibility are distinguished.

---

### 1. Deterministic Reproducibility

Certain components are deterministic given fixed inputs and parameters, including:

- TF–IDF vector construction,
- truncated SVD with fixed random state,
- graph construction from fixed embeddings,
- explicit stability and entropy calculations.

For these components, rerunning the pipeline with identical inputs and seeds
should yield identical numerical outputs up to floating-point tolerance.

---

### 2. Structural Reproducibility

Other components exhibit **structural stability** rather than strict numerical
identity, including:

- neighbourhood composition in high-dimensional spaces,
- persistence diagram structure,
- regime classification boundaries.

In these cases, small numerical differences may occur, but:
- qualitative regime behaviour,
- topological features,
- and stability patterns

are expected to recur.

This level of reproducibility is the primary target of the thesis.

---

### 3. Evidential Reproducibility

The repository provides **frozen traces** that allow inspection of results
*without rerunning the full pipeline*.

These traces constitute evidential reproducibility:
- results can be examined,
- figures can be verified,
- and claims can be inspected

even if the original computational environment is unavailable.

---

## Run Manifests

Each empirical trace directory contains a `run_manifest.json` file recording:

- repository commit hash,
- configuration hash,
- random seeds,
- library versions,
- execution timestamp,
- and system metadata.

These manifests define the authoritative provenance of each trace.

---

## Configuration Files

All non-default parameters used in analysis runs are recorded in explicit
configuration files.

Configuration files are versioned and preserved alongside outputs to prevent
implicit or undocumented parameter drift.

---

## Data Handling and Identification

To respect data governance constraints, raw corpora are not included in this
repository.

Instead:
- cryptographic hashes,
- corpus size metadata,
- and preprocessing summaries

are recorded where necessary to establish identity without redistributing data.

This allows verification of lineage without violating data ownership.

---

## Floating-Point and Platform Effects

Minor numerical variation may arise due to:
- floating-point arithmetic,
- library implementation differences,
- or hardware characteristics.

Such variation is not treated as a failure of reproducibility unless it alters
structural or regime-level conclusions.

---

## Limits of Reproducibility Claims

This work does **not** claim:

- bitwise reproducibility across all platforms,
- invariance under arbitrary parameter changes,
- reproducibility of results for all possible corpora.

Claims are limited to the conditions documented in manifests and traces.

---

## Relationship to Future Work

Future operational or federated implementations may adopt:
- stricter determinism,
- alternative numerical backends,
- or additional audit mechanisms.

Such developments would extend, not retroactively alter, the provenance claims
made here.

---

## Final Statement

Provenance in this repository is treated as an epistemic obligation rather than a
technical afterthought.

By explicitly documenting lineage, assumptions, and limits, this work aims to
make its claims inspectable, contestable, and responsibly reusable.

---

*End of PROVENANCE.md*
