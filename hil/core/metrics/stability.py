# hil/core/metrics/stability.py
"""
hil.core.metrics.stability

Structural stability diagnostics for Hilbert Epistemic Fields.

Stability is defined here as the inverse sensitivity of the field under
controlled, deterministic perturbation (leave-one-out), combining:

- geometric change (primary signal),
- entropy change (dispersion sensitivity),
- coherence change (structural coupling sensitivity).

Stability is:
- diagnostic, not prescriptive,
- structural, not semantic,
- deterministic,
- comparative (defined only relative to a perturbation).

No thresholds, no regimes, no desirability claims are made.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from hil.core.metrics.geometry_delta import geometry_delta_procrustes_2d
from hil.core.metrics.entropy import structural_entropy
from hil.core.metrics.coherence import field_coherence
from hil.core.structure.graph import Graph


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _metric_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.metrics.stability invariant] {message}")


# ---------------------------------------------------------------------------
# Stability (leave-one-out)
# ---------------------------------------------------------------------------

def structural_stability_leave_one_out(
    *,
    field_vectors: np.ndarray,
    graph: Graph,
    epsilon: float = 1e-9,
) -> Dict[int, float]:
    """
    Compute elementwise structural stability via leave-one-out perturbation.

    For each element i:
        - remove i from the field,
        - recompute geometry, entropy, and coherence,
        - measure deltas relative to the full field,
        - define stability as the inverse total delta.

    Stability_i =
        1 / (Δ_geometry_i + Δ_entropy_i + Δ_coherence_i + epsilon)

    Parameters
    ----------
    field_vectors : np.ndarray, shape (n, d)
        Field vectors.
    graph : Graph
        Structural graph derived from the full field.
    epsilon : float
        Small constant to ensure numerical safety.

    Returns
    -------
    stability : dict[int, float]
        Mapping from element index to stability value.
    """
    _metric_invariant(field_vectors.ndim == 2, "field_vectors must be 2D")

    n = field_vectors.shape[0]
    _metric_invariant(n >= 2, "stability requires at least 2 elements")

    # --- Baseline diagnostics ------------------------------------------
    base_entropy = structural_entropy(graph)
    base_coherence = field_coherence(field_vectors)

    _metric_invariant(np.isfinite(base_entropy), "base entropy must be finite")
    _metric_invariant(np.isfinite(base_coherence), "base coherence must be finite")

    stability: Dict[int, float] = {}

    # --- Leave-one-out loop --------------------------------------------
    for i in range(n):
        # Remove element i
        X_loo = np.delete(field_vectors, i, axis=0)

        # Geometry delta (primary signal)
        delta_geom = geometry_delta_procrustes_2d(
            field_vectors,
            X_loo,
            removed_index=i,
        )

        # Rebuild graph deterministically for LOO field
        # (reuse the same construction rule as in core.api)
        from hil.core.api import build_structure, CoreField  # local import by design

        loo_field = CoreField(vectors=X_loo)
        loo_graph = build_structure(loo_field)

        # Secondary deltas
        entropy_loo = structural_entropy(loo_graph)
        coherence_loo = field_coherence(X_loo)

        delta_entropy = abs(base_entropy - entropy_loo)
        delta_coherence = abs(base_coherence - coherence_loo)

        _metric_invariant(delta_geom >= 0.0, "geometry delta must be >= 0")
        _metric_invariant(delta_entropy >= 0.0, "entropy delta must be >= 0")
        _metric_invariant(delta_coherence >= 0.0, "coherence delta must be >= 0")

        total_delta = delta_geom + delta_entropy + delta_coherence

        s_i = 1.0 / (total_delta + epsilon)

        _metric_invariant(np.isfinite(s_i), "stability must be finite")
        _metric_invariant(s_i >= 0.0, "stability must be >= 0")

        stability[i] = float(s_i)

    return stability


__all__ = [
    "structural_stability_leave_one_out",
]
