# hil/core/structure/molecule.py
"""
hil.core.structure.molecule

Canonical molecular aggregate representation for the HIL epistemic core.

A Molecule is a structural grouping of Elements. It represents aggregation,
not interpretation.

This module defines what a molecule *is*, not how molecules are formed.

Invariants:
- Structural, not semantic
- Deterministic, stateless
- No IO, no persistence
- No clustering or discovery logic
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple

import numpy as np

from hil.core.structure.element import Element, elements_to_matrix


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _molecule_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.structure.molecule invariant] {message}")


# ---------------------------------------------------------------------------
# Molecule
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Molecule:
    """
    Structural aggregate of Elements.

    Fields:
    - molecule_id: stable identifier within a run
    - elements: ordered tuple of Elements
    - metadata: optional, non-authoritative annotations

    Notes:
    - Ordering of elements is preserved and meaningful only for determinism.
    - Membership implies no semantic unity.
    """

    molecule_id: str
    elements: Tuple[Element, ...]
    metadata: Dict[str, Any]

    def __post_init__(self) -> None:
        _molecule_invariant(
            isinstance(self.molecule_id, str) and self.molecule_id.strip() != "",
            "molecule_id must be a non-empty string",
        )
        _molecule_invariant(
            isinstance(self.elements, tuple) and len(self.elements) > 0,
            "elements must be a non-empty tuple",
        )
        _molecule_invariant(
            all(isinstance(e, Element) for e in self.elements),
            "all members must be Element instances",
        )
        _molecule_invariant(
            isinstance(self.metadata, dict),
            "metadata must be a dictionary",
        )

        # Dimensional consistency
        dims = {e.dim for e in self.elements}
        _molecule_invariant(
            len(dims) == 1,
            "all elements in a molecule must have the same embedding dimension",
        )

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        """Number of elements in the molecule."""
        return len(self.elements)

    @property
    def dim(self) -> int:
        """Embedding dimension of the molecule."""
        return self.elements[0].dim

    @property
    def matrix(self) -> np.ndarray:
        """
        Stack element vectors into a matrix of shape (n_elements, dim).

        This is a pure view used for diagnostics.
        """
        return elements_to_matrix(list(self.elements))

    @property
    def centroid(self) -> np.ndarray:
        """
        Compute the centroid of the molecule in embedding space.

        This is a geometric quantity, not a semantic one.
        """
        mat = self.matrix
        return mat.mean(axis=0)

    def summary(self) -> Dict[str, Any]:
        """
        Minimal, JSON-safe summary for artifacts.
        """
        centroid = self.centroid
        return {
            "molecule_id": self.molecule_id,
            "num_elements": self.size,
            "dim": self.dim,
            "centroid_norm": float(np.linalg.norm(centroid)),
        }


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def molecules_to_matrix(molecules: Iterable[Molecule]) -> np.ndarray:
    """
    Stack molecule centroids into a matrix of shape (n_molecules, dim).

    Invariants:
    - All molecules must share the same dimension.
    """
    mols = list(molecules)
    _molecule_invariant(len(mols) > 0, "molecules must be non-empty")

    d0 = mols[0].dim
    for m in mols:
        _molecule_invariant(m.dim == d0, "all molecules must have the same dimension")

    mat = np.vstack([m.centroid for m in mols]).astype(np.float64, copy=False)
    _molecule_invariant(
        mat.shape == (len(mols), d0),
        "stacked centroid matrix has unexpected shape",
    )
    return mat


__all__ = [
    "Molecule",
    "molecules_to_matrix",
]
