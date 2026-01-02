# hil/core/structure/field.py
"""
hil.core.structure.field

Hilbert Epistemic Field (HEF) core structure.

A Field is a geometric container over embedded elements. It represents
a configuration of informational mass in a Hilbert space and exposes
only structural, diagnostic properties.

This module defines what a field *is*, not how it is built, analysed,
or interpreted.

Invariants:
- Structural, not semantic
- Deterministic, stateless
- No IO, no persistence
- No orchestration logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import numpy as np

from hil.core.structure.element import Element, elements_to_matrix


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _field_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.structure.field invariant] {message}")


# ---------------------------------------------------------------------------
# Field
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Field:
    """
    Hilbert Epistemic Field.

    Fields:
    - elements: ordered tuple of Elements defining the field
    - metadata: optional, non-authoritative annotations

    Notes:
    - Ordering is preserved for determinism only.
    - Metadata must never be used for epistemic decisions.
    """

    elements: tuple[Element, ...]
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        _field_invariant(
            isinstance(self.elements, tuple) and len(self.elements) > 0,
            "elements must be a non-empty tuple",
        )
        _field_invariant(
            all(isinstance(e, Element) for e in self.elements),
            "all members must be Element instances",
        )

        if self.metadata is not None:
            _field_invariant(
                isinstance(self.metadata, dict),
                "metadata must be a dict or None",
            )

        # Dimensional consistency
        dims = {e.dim for e in self.elements}
        _field_invariant(
            len(dims) == 1,
            "all elements must share the same embedding dimension",
        )

    # ------------------------------------------------------------------
    # Core geometric views
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of elements in the field."""
        return len(self.elements)

    @property
    def dim(self) -> int:
        """Embedding dimension of the field."""
        return self.elements[0].dim

    @property
    def matrix(self) -> np.ndarray:
        """
        Stack element vectors into a matrix of shape (n_elements, dim).

        This is a pure, deterministic view.
        """
        return elements_to_matrix(list(self.elements))

    @property
    def centroid(self) -> np.ndarray:
        """
        Centroid of the field in embedding space.

        Geometric quantity only.
        """
        mat = self.matrix
        return mat.mean(axis=0)

    @property
    def centroid_norm(self) -> float:
        """Euclidean norm of the field centroid."""
        return float(np.linalg.norm(self.centroid))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """
        Minimal, JSON-safe summary of the field.

        Intended for build artifacts and inspection.
        """
        return {
            "num_elements": self.size,
            "dim": self.dim,
            "centroid_norm": self.centroid_norm,
        }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def build_field_from_elements(
    elements: Iterable[Element],
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> Field:
    """
    Construct a Field from an iterable of Elements.

    This helper exists to make construction explicit and invariant-checked.
    """
    elems = tuple(elements)
    _field_invariant(len(elems) > 0, "elements iterable must be non-empty")
    return Field(elements=elems, metadata=metadata)


__all__ = [
    "Field",
    "build_field_from_elements",
]
