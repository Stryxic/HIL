# hil/core/metrics/coherence.py
"""
hil.core.metrics.coherence

Field coherence computations.

This module mirrors the native C implementation of field coherence
exactly (hil_field_coherence in hilbert_native.c), for correctness and
cross-language parity.

Definition (matches C):

- Let x_r be row vectors (elements) in the field coordinates matrix (n x d)
- Let c = (1/n) * sum_r x_r  (centroid)
- Let ||c|| = norm(c), clamped to eps
- For each row x_r:
    cos_r = dot(x_r, c) / (||x_r|| * ||c||), with each norm clamped to eps
- Coherence = (1/n) * sum_r cos_r

Invariants:
- Geometric, not semantic
- Diagnostic only (returns numbers; never classifies or labels)
- Deterministic (no randomness, no hidden global state)
- No IO, no persistence
"""

from __future__ import annotations

import numpy as np


# Match the C epsilon exactly
_HIL_EPS = 1e-12


def _metric_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.metrics.coherence invariant] {message}")


def _clamp_min(x: float, m: float) -> float:
    return m if x < m else x


def field_coherence(vectors: np.ndarray) -> float:
    """
    Compute field coherence for an embedding matrix.

    Parameters
    ----------
    vectors : np.ndarray
        Dense matrix of shape (n, d), where each row is an element vector.

    Returns
    -------
    float
        Mean cosine similarity to centroid (coherence proxy), matching C semantics.
    """
    X = np.asarray(vectors, dtype=np.float64)

    _metric_invariant(X.ndim == 2, "vectors must be 2D (n, d)")
    n, d = X.shape
    _metric_invariant(n >= 1, "vectors must have at least one row")
    _metric_invariant(d >= 1, "vectors must have at least one column")

    # Centroid (matches C: sum then scale by 1/n)
    centroid = X.sum(axis=0) / float(n)

    # Norm clamps (matches C hil_clamp_min)
    c_norm = _clamp_min(float(np.linalg.norm(centroid)), _HIL_EPS)

    # Mean cosine similarity to centroid
    sum_cos = 0.0
    for r in range(n):
        row = X[r]
        r_norm = _clamp_min(float(np.linalg.norm(row)), _HIL_EPS)
        dot = float(np.dot(row, centroid))
        sum_cos += dot / (r_norm * c_norm)

    return float(sum_cos / float(n))
