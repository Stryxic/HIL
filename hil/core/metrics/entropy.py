# hil/core/metrics/entropy.py
"""
hil.core.metrics.entropy

Structural entropy computations.

Invariants:
- Structural, not semantic (computed from graph structure / weights)
- Diagnostic only (returns numbers; never classifies or labels)
- Deterministic (no randomness, no hidden global state)
- No IO, no persistence
"""

from __future__ import annotations

from typing import Protocol

import numpy as np


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _metric_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.metrics.entropy invariant] {message}")


# ---------------------------------------------------------------------------
# Graph protocol
# ---------------------------------------------------------------------------

class _GraphLike(Protocol):
    src: np.ndarray
    dst: np.ndarray
    weight: np.ndarray
    num_nodes: int


# ---------------------------------------------------------------------------
# Core entropy primitive
# ---------------------------------------------------------------------------

def _entropy_from_out_strengths(out_strength: np.ndarray) -> float:
    """
    Entropy over node-level outgoing weight mass.

    p_i = out_strength[i] / sum(out_strength)
    H = -sum_i p_i * log(p_i)

    Notes:
    - Uses natural log (nats).
    - Returns 0.0 if total mass is 0.
    """
    total = float(out_strength.sum())
    if total <= 0.0:
        return 0.0

    p = out_strength / total
    # Drop zeros to avoid log(0); deterministic and lossless for entropy.
    p = p[p > 0.0]
    if p.size == 0:
        return 0.0

    return float(-(p * np.log(p)).sum())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def structural_entropy(graph: _GraphLike) -> float:
    """
    Compute a structural entropy quantity for a graph.

    Definition (current, thesis-aligned first pass):
    - Let out_strength[i] be the sum of outgoing edge weights from node i.
    - Define a distribution over nodes p_i = out_strength[i] / sum(out_strength).
    - Return Shannon entropy H(p) in natural units (nats).

    Properties:
    - Structural (depends only on weighted adjacency mass)
    - Diagnostic (numeric only)
    - Deterministic (pure function)

    Backend stages:
    - Stage A/B: NumPy implementation (default).
    - Stage C: Optional native backend if hil.core.native._shim.graph_entropy exists.
      Native is strictly an acceleration, not a semantic change.
    """

    # --- Structural sanity ---------------------------------------------------
    _metric_invariant(isinstance(graph.num_nodes, int), "graph.num_nodes must be an int")
    _metric_invariant(graph.num_nodes >= 1, "graph.num_nodes must be >= 1")

    _metric_invariant(isinstance(graph.src, np.ndarray), "graph.src must be np.ndarray")
    _metric_invariant(isinstance(graph.dst, np.ndarray), "graph.dst must be np.ndarray")
    _metric_invariant(isinstance(graph.weight, np.ndarray), "graph.weight must be np.ndarray")

    _metric_invariant(graph.src.shape == graph.dst.shape, "src and dst must have same shape")
    _metric_invariant(graph.weight.shape == graph.src.shape, "weight must match src/dst shape")

    _metric_invariant(graph.src.ndim == 1, "src must be 1D")
    _metric_invariant(graph.dst.ndim == 1, "dst must be 1D")
    _metric_invariant(graph.weight.ndim == 1, "weight must be 1D")

    m = int(graph.src.size)
    if m == 0:
        # No edges → no dispersion
        return 0.0

    # --- Numeric sanity ------------------------------------------------------
    _metric_invariant(np.all(np.isfinite(graph.weight)), "weights must be finite")
    _metric_invariant(np.all(graph.weight >= 0.0), "weights must be non-negative")

    _metric_invariant(
        np.issubdtype(graph.src.dtype, np.integer),
        "src must be integer dtype",
    )
    _metric_invariant(
        np.issubdtype(graph.dst.dtype, np.integer),
        "dst must be integer dtype",
    )

    _metric_invariant(
        int(graph.src.min()) >= 0 and int(graph.src.max()) < graph.num_nodes,
        "src indices out of range",
    )
    _metric_invariant(
        int(graph.dst.min()) >= 0 and int(graph.dst.max()) < graph.num_nodes,
        "dst indices out of range",
    )

    # --- Stage C: optional native backend -----------------------------------
    try:
        # Import locally to preserve core boundary.
        from hil.core.native._shim import graph_entropy as _native_graph_entropy  # type: ignore
    except Exception:
        _native_graph_entropy = None  # type: ignore

    if _native_graph_entropy is not None:
        try:
            # Expected signature:
            # (src: ndarray, dst: ndarray, weight: ndarray, num_nodes: int) -> float
            h = float(
                _native_graph_entropy(
                    graph.src,
                    graph.dst,
                    graph.weight,
                    graph.num_nodes,
                )
            )
            _metric_invariant(np.isfinite(h), "native entropy must be finite")
            _metric_invariant(h >= 0.0, "entropy must be >= 0")
            return h
        except Exception:
            # Fall back to NumPy path on any native failure.
            pass

    # --- Stage A/B: NumPy implementation ------------------------------------
    # Out-strength per node: sum of outgoing weights grouped by src.
    out_strength = np.bincount(
        graph.src.astype(np.int64, copy=False),
        weights=graph.weight.astype(np.float64, copy=False),
        minlength=graph.num_nodes,
    ).astype(np.float64, copy=False)

    h = _entropy_from_out_strengths(out_strength)

    _metric_invariant(np.isfinite(h), "entropy must be finite")
    _metric_invariant(h >= 0.0, "entropy must be >= 0")

    return h


__all__ = [
    "structural_entropy",
]
