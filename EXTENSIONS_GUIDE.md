# HIL Extensions Guide

**Applies to:** HIL Core v1.0  
**Status:** Normative  
**Audience:** Contributors, researchers, downstream users

---

## Purpose

This document defines **how to extend HIL without violating the Core Invariants**.

HIL is intentionally narrow at its core.  
Power comes from **extensions**, not from expanding the core.

This guide exists to ensure that:
- extensions are expressive,
- invariants remain intact,
- and epistemic discipline is preserved.

---

## Fundamental Rule

> **Nothing outside `hil/core` may weaken, reinterpret, or bypass the Core Invariants.**

If an idea requires changing a core invariant, it is **not an extension**.  
It is a **core revision** and must follow the process defined in `CORE_INVARIANTS.md`.

---

## Directory Structure Convention

All extensions **must** live outside `hil/core`.

Recommended layout:

```
hil/
├── core/                  # frozen
├── extensions/
│   ├── diachronic/
│   ├── institutional/
│   ├── adversarial/
│   ├── comparative/
│   └── experimental/
└── tests/
```

Extensions may depend on core, but **core must never depend on extensions**.

---

## What Extensions Are Allowed to Do

Extensions may:

- Interpret geometry
- Label regimes
- Compare across corpora
- Aggregate diagnostics
- Detect transitions or anomalies
- Attach semantics or narratives
- Introduce learning or optimization
- Produce decisions or recommendations
- Interface with humans or downstream systems

All of the above are **explicitly excluded from core** and are therefore valid extensions.

---

## What Extensions Must Never Do

Extensions must **not**:

- Modify `hil/core/**`
- Reinterpret core diagnostics as truth claims
- Treat coordinate-dependent rates as invariants
- Override noise floors
- Silence instability or dispersion
- Introduce hidden state into core operators
- Smuggle decisions into “diagnostics”

If an extension needs to do these things, it must do so **explicitly and locally**, never by altering the core.

---

## Extension Categories (Canonical)

### 1. Diachronic Extensions

**Purpose:**  
Interpret change over time using covariant Hilbert paths.

Examples:
- Regime shift detection (via curvature spikes)
- Structural acceleration / deceleration
- Phase segmentation
- Narrative arc extraction

Allowed tools:
- Curvature thresholds
- Path segmentation
- Event labeling
- Windowed summaries

Must respect:
- Covariant geometry
- Noise-aware thresholds
- No privileged clock

---

### 2. Institutional / Multi-Corpus Extensions

**Purpose:**  
Compare multiple Hilbert processes.

Examples:
- Institutional drift
- Policy evolution analysis
- Cross-corpus structural alignment
- Comparative trajectories

Allowed tools:
- Overlay alignment
- Relative geometry
- Path-to-path distance
- Reference/null fields

Must respect:
- No semantic alignment inside core
- Explicit alignment assumptions
- Geometry-first comparison

---

### 3. Adversarial / Stress-Test Extensions

**Purpose:**  
Probe robustness and sensitivity.

Examples:
- Adversarial perturbations
- Moduli stress testing
- Probe amplification
- Noise injection analysis

Allowed tools:
- Synthetic probes
- Worst-case analysis
- Sensitivity envelopes

Must respect:
- Core noise floor definitions
- No silent stabilization
- Explicit reporting of fragility

---

### 4. Decision or Policy Extensions (Downstream)

**Purpose:**  
Use HIL diagnostics to support decisions.

Examples:
- Risk flags
- Trust thresholds
- Alerts
- Policy recommendations

Allowed tools:
- Thresholding
- Classification
- Optimization
- Learning systems

**Hard rule:**  
These outputs are **not HIL outputs**.  
They are *applications built on HIL*.

They must:
- cite which diagnostics they use,
- expose thresholds,
- acknowledge non-invariance.

---

### 5. Experimental / Research Extensions

**Purpose:**  
Explore ideas without stabilizing them.

Examples:
- Alternative metrics
- New consolidation operators
- Hypothetical invariants
- Speculative geometry

Rules:
- Must live under `hil/extensions/experimental`
- Must not be imported by production code
- Must not modify core tests

---

## Testing Requirements for Extensions

Extensions **must add their own tests**.

They must **not**:
- weaken or bypass core tests
- reinterpret failing core tests as “expected”

Recommended extension test types:
- invariance sensitivity tests
- perturbation robustness tests
- cross-parameter consistency tests

---

## Documentation Requirements

Every extension must include:

1. **What invariant(s) it relies on**
2. **What new assumptions it introduces**
3. **Which outputs are invariant vs coordinate-dependent**
4. **What failure modes exist**

Silence about assumptions is a violation of discipline.

---

## Canonical Anti-Patterns (Do Not Do This)

- “Just one more flag in core”
- “We can default this threshold”
- “Users probably won’t notice instability”
- “It works well enough in practice”
- “Let’s add semantics here for convenience”

These are exactly how instruments decay.

---

## One-Sentence Extension Rule

> **Extensions may interpret, decide, or act—but only by standing on core invariants, never by weakening them.**

---

## Final Declaration

HIL Core is **finished**.  
Extensions are **where creativity belongs**.

If an idea feels powerful but dangerous:
- that is a sign it belongs in an extension.

If an idea feels “obviously necessary”:
- that is a sign it must be justified against the invariants.

There is no shortcut around this discipline.

---
