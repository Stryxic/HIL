# hil/core/potential.py
"""
hil.core.potential

Potential and derived scalar fields for the Hilbert Epistemic Field (HEF).

This module defines geometric scalar quantities derived from a Field.
Potential is treated as a diagnostic function over configuration space,
not as an objective, loss, or control signal.

Invariants:
- Structural, not semantic
- Diagnostic only (no optimisation, no thresholds, no actions)
- Deterministic
- No IO, no persistence
"""

from __future__ import annotations

from typing import Dict, Any

import numpy as np

from hil.core.structure.field import Field
from hil.core.operators import l2_norm


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _potential_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.potential invariant] {message}")


# ---------------------------------------------------------------------------
# Potential
# ---------------------------------------------------------------------------

def field_potential(field: Field) -> float:
    """
    Compute a scalar potential for a field configuration.

    First-pass definition (minimal, thesis-aligned):

    - Let c be the centroid of the field.
    - Potential is the mean squared distance of elements from c.

        V = (1/N) * sum_i ||x_i - c||^2

    Properties:
    - V >= 0
    - V = 0 iff all elements coincide
    - Increases with geometric dispersion
    - No semantics, no desirability implied
    """
    _potential_invariant(isinstance(field, Field), "field must be a Field")
    _potential_invariant(field.size >= 1, "field must contain at least one element")

    mat = field.matrix
    centroid = field.centroid

    diffs = mat - centroid
    sq_norms = np.einsum("ij,ij->i", diffs, diffs)

    V = float(sq_norms.mean())

    _potential_invariant(np.isfinite(V), "potential must be finite")
    _potential_invariant(V >= 0.0, "potential must be >= 0")

    return V


# ---------------------------------------------------------------------------
# Derived scalar fields
# ---------------------------------------------------------------------------

def element_potential(field: Field) -> np.ndarray:
    """
    Compute per-element potential contributions.

    Returns an array p_i = ||x_i - c||^2 for each element.

    This is a diagnostic field, not a ranking or importance score.
    """
    _potential_invariant(isinstance(field, Field), "field must be a Field")

    mat = field.matrix
    centroid = field.centroid

    diffs = mat - centroid
    p = np.einsum("ij,ij->i", diffs, diffs)

    _potential_invariant(np.all(np.isfinite(p)), "element potentials must be finite")
    _potential_invariant(np.all(p >= 0.0), "element potentials must be >= 0")

    return p.astype(np.float64, copy=False)


def potential_summary(field: Field) -> Dict[str, Any]:
    """
    Minimal, JSON-safe summary of field potential diagnostics.
    """
    p = element_potential(field)
    return {
        "field_potential": float(p.mean()),
        "max_element_potential": float(p.max()),
        "min_element_potential": float(p.min()),
    }


__all__ = [
    "field_potential",
    "element_potential",
    "potential_summary",
]
