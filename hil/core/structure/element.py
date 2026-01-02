# hil/core/structure/element.py
"""
hil.core.structure.element

Canonical informational element representation for the HIL epistemic core.

An Element is the minimal unit of structure that can be embedded in a field and
participate in diagnostics. It is intentionally small: an ID, a vector, and
optional non-authoritative metadata.

Invariants:
- Structural, not semantic (no truth claims, no labels, no regimes)
- Deterministic, stateless (no IO, no persistence, no hidden randomness)
- Pure data container (no orchestration logic)
- Minimal surface area (core should not become a schema dumping ground)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _element_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.structure.element invariant] {message}")


# ---------------------------------------------------------------------------
# Core element type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Element:
    """
    Minimal informational element.

    Fields:
    - element_id: stable identifier within a run/corpus scope
    - vector: embedding vector (1D float array)
    - metadata: optional, non-authoritative annotations (diagnostic context only)

    Notes:
    - `metadata` must never be treated as semantic truth.
    - `metadata` exists to preserve inspectability/provenance downstream.
    """

    element_id: str
    vector: np.ndarray
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        _element_invariant(
            isinstance(self.element_id, str) and self.element_id.strip() != "",
            "element_id must be a non-empty string",
        )
        _element_invariant(isinstance(self.vector, np.ndarray), "vector must be a numpy array")
        _element_invariant(self.vector.ndim == 1, "vector must be 1D")
        _element_invariant(self.vector.size > 0, "vector must be non-empty")
        _element_invariant(
            np.issubdtype(self.vector.dtype, np.floating),
            "vector dtype must be floating",
        )
        _element_invariant(np.all(np.isfinite(self.vector)), "vector values must be finite")

        if self.metadata is not None:
            _element_invariant(isinstance(self.metadata, dict), "metadata must be a dict or None")

    @property
    def dim(self) -> int:
        """Embedding dimension."""
        return int(self.vector.size)

    def summary(self) -> Dict[str, Any]:
        """
        Minimal, JSON-safe summary for artifacts.

        This intentionally excludes raw vectors.
        """
        v = self.vector
        return {
            "element_id": self.element_id,
            "dim": int(v.size),
            "norm": float(np.linalg.norm(v)),
        }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def elements_to_matrix(elements: list[Element]) -> np.ndarray:
    """
    Stack element vectors into a matrix of shape (n, d).

    Invariants:
    - All elements must share the same dimension.
    - Returns float64 for numerical stability in downstream computations.
    """
    _element_invariant(len(elements) > 0, "elements must be non-empty")

    d0 = elements[0].dim
    _element_invariant(d0 > 0, "element dimension must be > 0")
    for e in elements:
        _element_invariant(e.dim == d0, "all elements must have the same dimension")

    mat = np.vstack([e.vector for e in elements]).astype(np.float64, copy=False)
    _element_invariant(mat.shape == (len(elements), d0), "stacked matrix has unexpected shape")
    return mat


__all__ = [
    "Element",
    "elements_to_matrix",
]
