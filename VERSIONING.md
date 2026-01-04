# HIL Versioning Policy

**Applies to:** HIL Core v1.0 and all extensions  
**Status:** Normative

---

## Purpose

This document defines the **versioning rules** for HIL.

The goal of versioning in HIL is **not feature tracking**.  
It is **epistemic stability**.

Version numbers communicate:
- which invariants are guaranteed,
- what may have changed,
- and what downstream users must re‑validate.

---

## Fundamental Principle

> **Version numbers track invariant boundaries, not implementation detail.**

If an invariant changes, the version must change.  
If no invariant changes, the version must not change.

---

## Versioning Domains

HIL has **three distinct version domains**:

1. **Core Version**
2. **Extension Version**
3. **Artifact Version**

These domains are related but independent.

---

## 1. Core Versioning

### Definition

The **Core Version** applies to:

```
hil/core/**
hil/tests/**   (core tests only)
CORE_INVARIANTS.md
```

The Core Version defines the **epistemic contract** of HIL.

---

### Core Version Format

```
MAJOR.MINOR
```

Example:
```
1.0
```

There is **no PATCH number** for core.

---

### Core Version Semantics

#### MAJOR increment (breaking)

Increment MAJOR when **any Core Invariant changes**, including:

- determinism guarantees
- timebase certification rules
- noise floor definitions
- covariance requirements
- stream authority rules
- geometry-first constraints

A MAJOR bump means:

> **All prior conclusions must be reconsidered.**

Example:
```
1.0 → 2.0
```

---

#### MINOR increment (theoretical extension)

Increment MINOR when:

- a *new invariant* is added,
- an invariant is strictly strengthened,
- new mandatory tests are introduced,
- expressive power increases **without relaxing existing constraints**.

A MINOR bump means:

> **All previous guarantees still hold, plus more.**

Example:
```
1.0 → 1.1
```

---

### What Does *Not* Change Core Version

- Performance optimizations
- Refactoring without semantic change
- Additional comments or documentation
- Internal code reorganization
- New extension modules

If core tests still pass unchanged, the core version must not change.

---

## 2. Extension Versioning

### Definition

Extensions live under:

```
hil/extensions/**
```

Extensions are **explicitly allowed** to:

- interpret diagnostics,
- introduce semantics,
- learn or optimize,
- make decisions.

They must therefore version independently.

---

### Extension Version Format

```
CORE.MAJOR.MINOR.PATCH
```

Example:
```
1.0.2.3
```

Meaning:
- compatible with Core v1.0
- extension major version 2
- minor version 3

---

### Extension Version Semantics

- **CORE**  
  The core version the extension was built against.

- **MAJOR**  
  Breaking change in extension logic or assumptions.

- **MINOR**  
  New features or diagnostics.

- **PATCH**  
  Bug fixes or internal refactors.

---

### Extension Compatibility Rules

- Extensions **must declare** the core version they target.
- Extensions may support multiple core versions explicitly.
- Extensions must fail loudly if run against an incompatible core.

Silent degradation is forbidden.

---

## 3. Artifact Versioning

### Definition

Artifacts are serialized outputs such as:

- `timebase_report`
- covariant path reports
- calibration artifacts
- extension-generated summaries

Artifacts are **historical records**, not live code.

---

### Artifact Version Format

```
vN
```

Example:
```
v1
v2
```

---

### Artifact Version Semantics

Increment artifact version when:

- schema changes,
- field meanings change,
- invariants attached to fields change,
- interpretation rules change.

Artifact versions must be **monotone and explicit**.

---

## Compatibility Matrix

| Change Type | Core Version | Extension Version | Artifact Version |
|-----------|-------------|-------------------|------------------|
| Core invariant change | MAJOR | CORE component | new artifact |
| New core invariant | MINOR | CORE component | optional |
| Extension breaking change | — | MAJOR | new artifact |
| Extension feature | — | MINOR | optional |
| Bug fix | — | PATCH | no change |
| Schema change | — | — | increment |

---

## Testing and Version Discipline

- Core tests are **authoritative** for core version validity.
- Extensions must not alter or weaken core tests.
- Any test added to core implies a MINOR core version bump.

---

## Release Discipline

A valid HIL release must include:

- explicit Core Version
- frozen `CORE_INVARIANTS.md`
- passing core test suite
- declared extension compatibility (if any)

No “rolling releases.”  
No “best effort” compatibility.

---

## Canonical Examples

### Example 1 — Refactor

- Core logic unchanged
- Tests unchanged

→ **No version change**

---

### Example 2 — New invariant

- Add covariant curvature metric
- Add mandatory test

→ **Core version 1.1**

---

### Example 3 — Relax noise floor rule

- Allow undersampling

→ **Core version 2.0**

---

## One-Sentence Rule

> **If you cannot point to the invariant that changed, the version must not change.**

---

## Final Declaration

HIL version numbers encode **epistemic guarantees**, not marketing.

When the number changes, something fundamental has changed.  
When it does not, nothing fundamental has.

---
