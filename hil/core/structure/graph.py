# hil/core/structure/graph.py
"""
hil.core.structure.graph

Canonical structural graph representation for the HIL epistemic core.

This module defines what a graph *is* in HIL.
It does NOT define how graphs are constructed (builders live elsewhere).

Invariants:
- Structural only (no semantics, no labels)
- Deterministic
- No IO, no persistence
- No hidden state
- Numeric, inspectable, minimal
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _graph_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.structure.graph invariant] {message}")


# ---------------------------------------------------------------------------
# Core graph type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Graph:
    """
    Minimal directed weighted graph.

    Representation:
    - src[i] -> dst[i] with weight[i]
    - nodes are indexed [0, num_nodes)

    This is a *container*, not a policy object.
    """

    src: np.ndarray
    dst: np.ndarray
    weight: np.ndarray
    num_nodes: int

    def __post_init__(self) -> None:
        # --- basic type checks ---
        _graph_invariant(isinstance(self.src, np.ndarray), "src must be np.ndarray")
        _graph_invariant(isinstance(self.dst, np.ndarray), "dst must be np.ndarray")
        _graph_invariant(isinstance(self.weight, np.ndarray), "weight must be np.ndarray")

        # --- dimensionality ---
        _graph_invariant(self.src.ndim == 1, "src must be 1D")
        _graph_invariant(self.dst.ndim == 1, "dst must be 1D")
        _graph_invariant(self.weight.ndim == 1, "weight must be 1D")

        # --- shape agreement ---
        _graph_invariant(
            self.src.shape == self.dst.shape == self.weight.shape,
            "src, dst, and weight must have the same shape",
        )

        # --- node constraints ---
        _graph_invariant(
            isinstance(self.num_nodes, int) and self.num_nodes >= 0,
            "num_nodes must be a non-negative integer",
        )

        if self.src.size > 0:
            _graph_invariant(
                self.src.min() >= 0 and self.src.max() < self.num_nodes,
                "src indices out of range",
            )
            _graph_invariant(
                self.dst.min() >= 0 and self.dst.max() < self.num_nodes,
                "dst indices out of range",
            )

        # --- dtype discipline ---
        _graph_invariant(
            np.issubdtype(self.src.dtype, np.integer),
            "src must be integer dtype",
        )
        _graph_invariant(
            np.issubdtype(self.dst.dtype, np.integer),
            "dst must be integer dtype",
        )
        _graph_invariant(
            np.issubdtype(self.weight.dtype, np.floating),
            "weight must be floating dtype",
        )

        # --- numeric sanity ---
        if self.weight.size > 0:
            _graph_invariant(
                np.all(np.isfinite(self.weight)),
                "weights must be finite",
            )

    # ------------------------------------------------------------------
    # Derived properties (pure, no caching)
    # ------------------------------------------------------------------

    @property
    def num_edges(self) -> int:
        """Return the number of edges."""
        return int(self.src.size)

    @property
    def has_edges(self) -> bool:
        """True if the graph has at least one edge."""
        return self.num_edges > 0

    def summary(self) -> dict[str, Any]:
        """
        Return a minimal, JSON-safe summary of the graph.

        This is diagnostic only and intended for artifacts.
        """
        total_weight = float(self.weight.sum()) if self.weight.size > 0 else 0.0

        return {
            "num_nodes": int(self.num_nodes),
            "num_edges": int(self.num_edges),
            "total_weight": total_weight,
        }


__all__ = [
    "Graph",
]
