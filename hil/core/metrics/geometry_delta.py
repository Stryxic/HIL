# hil/core/metrics/geometry_delta.py
"""
hil.core.metrics.geometry_delta

Geometric delta metrics for Hilbert Epistemic Fields.

This module provides a deterministic, structural measure of how the
geometry of a field changes under controlled perturbation.

Current implementation:
- Orthogonal Procrustes distance between 2D PCA projections
  (baseline vs leave-one-out)

Invariants:
- Structural, not semantic
- Deterministic (no randomness, fixed linear algebra)
- Invariant to translation, rotation, reflection, and global scale
- No IO, no persistence
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _geom_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.metrics.geometry_delta invariant] {message}")


# ---------------------------------------------------------------------------
# PCA (2D)
# ---------------------------------------------------------------------------

def _pca_2d(X: np.ndarray) -> np.ndarray:
    """
    Compute a deterministic 2D PCA projection of X.

    Parameters
    ----------
    X : np.ndarray, shape (n, d)
        Input vectors.

    Returns
    -------
    Y : np.ndarray, shape (n, 2)
        2D PCA projection.
    """
    _geom_invariant(isinstance(X, np.ndarray), "X must be np.ndarray")
    _geom_invariant(X.ndim == 2, "X must be 2D")
    _geom_invariant(X.shape[0] >= 2, "X must have at least 2 rows")

    # Center
    Xc = X - X.mean(axis=0, keepdims=True)

    # SVD (deterministic)
    # Xc = U S V^T  -> PCA directions = V
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)

    # Project onto first two components
    Y = Xc @ Vt[:2].T

    _geom_invariant(Y.shape[1] == 2, "PCA projection must be 2D")
    _geom_invariant(np.isfinite(Y).all(), "PCA projection must be finite")

    return Y


# ---------------------------------------------------------------------------
# Procrustes alignment
# ---------------------------------------------------------------------------

def _procrustes_distance(A: np.ndarray, B: np.ndarray) -> float:
    """
    Compute orthogonal Procrustes distance between two point sets.

    A and B must be:
    - same shape (n, 2)
    - centered and scale-normalized beforehand

    Returns
    -------
    dist : float
        Frobenius norm of residual after optimal orthogonal alignment.
    """
    _geom_invariant(A.shape == B.shape, "A and B must have same shape")
    _geom_invariant(A.shape[1] == 2, "A and B must be 2D")

    # Optimal orthogonal alignment via SVD
    M = A.T @ B
    U, _, Vt = np.linalg.svd(M)
    R = U @ Vt

    residual = A - B @ R
    dist = float(np.linalg.norm(residual, ord="fro"))

    _geom_invariant(np.isfinite(dist), "distance must be finite")
    _geom_invariant(dist >= 0.0, "distance must be >= 0")

    return dist


# ---------------------------------------------------------------------------
# Geometry delta (leave-one-out)
# ---------------------------------------------------------------------------

def geometry_delta_procrustes_2d(
    X_full: np.ndarray,
    X_loo: np.ndarray,
    removed_index: int,
) -> float:
    """
    Compute geometry delta for a leave-one-out perturbation using
    2D PCA + orthogonal Procrustes distance.

    Parameters
    ----------
    X_full : np.ndarray, shape (n, d)
        Original field vectors.
    X_loo : np.ndarray, shape (n-1, d)
        Field vectors with one element removed.
    removed_index : int
        Index of the removed element in X_full.

    Returns
    -------
    delta : float
        Scalar geometry delta.
    """
    _geom_invariant(X_full.ndim == 2, "X_full must be 2D")
    _geom_invariant(X_loo.ndim == 2, "X_loo must be 2D")
    _geom_invariant(X_full.shape[0] == X_loo.shape[0] + 1, "row mismatch")
    _geom_invariant(0 <= removed_index < X_full.shape[0], "removed_index out of range")

    # PCA projections
    Y_full = _pca_2d(X_full)
    Y_loo = _pca_2d(X_loo)

    # Remove corresponding point from full projection
    Y_full_reduced = np.delete(Y_full, removed_index, axis=0)

    # Center
    Yf = Y_full_reduced - Y_full_reduced.mean(axis=0, keepdims=True)
    Yl = Y_loo - Y_loo.mean(axis=0, keepdims=True)

    # Normalize scale (Frobenius norm)
    nf = np.linalg.norm(Yf, ord="fro")
    nl = np.linalg.norm(Yl, ord="fro")

    if nf == 0.0 or nl == 0.0:
        # Degenerate but deterministic: no geometry to compare
        return 0.0

    Yf /= nf
    Yl /= nl

    return _procrustes_distance(Yf, Yl)


__all__ = [
    "geometry_delta_procrustes_2d",
]
