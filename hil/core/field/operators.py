# hil/core/operators.py
"""
hil.core.operators

Linear and spectral operators for the Hilbert Epistemic Field (HEF).

This module defines low-level linear-algebraic operations used by
field, structure, and metrics layers. These operators are purely
mathematical and do not encode interpretation, thresholds, or decisions.

Invariants:
- Linear / spectral only (no semantics, no regimes)
- Deterministic
- No IO, no persistence
- No orchestration or control flow
"""

from __future__ import annotations

from typing import Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _op_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.operators invariant] {message}")


# ---------------------------------------------------------------------------
# Vector operators
# ---------------------------------------------------------------------------

def l2_norm(v: np.ndarray) -> float:
    """
    Compute the L2 (Euclidean) norm of a vector.
    """
    _op_invariant(isinstance(v, np.ndarray), "v must be np.ndarray")
    _op_invariant(v.ndim == 1, "v must be 1D")
    return float(np.linalg.norm(v))


def normalize(v: np.ndarray) -> np.ndarray:
    """
    L2-normalize a vector.

    Returns a new array; does not mutate input.
    """
    _op_invariant(isinstance(v, np.ndarray), "v must be np.ndarray")
    _op_invariant(v.ndim == 1, "v must be 1D")

    n = np.linalg.norm(v)
    _op_invariant(n > 0.0, "cannot normalize zero vector")

    return v / n


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    """
    _op_invariant(isinstance(a, np.ndarray) and isinstance(b, np.ndarray), "inputs must be arrays")
    _op_invariant(a.ndim == 1 and b.ndim == 1, "inputs must be 1D")
    _op_invariant(a.shape == b.shape, "vectors must have same shape")

    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    _op_invariant(na > 0.0 and nb > 0.0, "vectors must have non-zero norm")

    return float(np.dot(a, b) / (na * nb))


# ---------------------------------------------------------------------------
# Matrix operators
# ---------------------------------------------------------------------------

def gram_matrix(mat: np.ndarray) -> np.ndarray:
    """
    Compute the Gram matrix G = X X^T for a matrix X.

    Used as a structural representation of pairwise inner products.
    """
    _op_invariant(isinstance(mat, np.ndarray), "mat must be np.ndarray")
    _op_invariant(mat.ndim == 2, "mat must be 2D")

    return mat @ mat.T


def covariance_matrix(mat: np.ndarray) -> np.ndarray:
    """
    Compute the empirical covariance matrix of rows in mat.

    Rows are treated as observations.
    """
    _op_invariant(isinstance(mat, np.ndarray), "mat must be np.ndarray")
    _op_invariant(mat.ndim == 2, "mat must be 2D")

    mean = mat.mean(axis=0, keepdims=True)
    centered = mat - mean
    return (centered.T @ centered) / float(mat.shape[0])


# ---------------------------------------------------------------------------
# Spectral operators
# ---------------------------------------------------------------------------

def spectrum(mat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute eigenvalues and eigenvectors of a symmetric matrix.

    Returns (eigenvalues, eigenvectors) sorted by descending eigenvalue.
    """
    _op_invariant(isinstance(mat, np.ndarray), "mat must be np.ndarray")
    _op_invariant(mat.ndim == 2, "mat must be 2D")
    _op_invariant(mat.shape[0] == mat.shape[1], "mat must be square")

    vals, vecs = np.linalg.eigh(mat)

    idx = np.argsort(vals)[::-1]
    return vals[idx], vecs[:, idx]


def spectral_energy(eigenvalues: np.ndarray) -> float:
    """
    Compute total spectral energy (sum of absolute eigenvalues).

    Diagnostic quantity only.
    """
    _op_invariant(isinstance(eigenvalues, np.ndarray), "eigenvalues must be np.ndarray")
    _op_invariant(eigenvalues.ndim == 1, "eigenvalues must be 1D")

    return float(np.sum(np.abs(eigenvalues)))


__all__ = [
    "l2_norm",
    "normalize",
    "cosine_similarity",
    "gram_matrix",
    "covariance_matrix",
    "spectrum",
    "spectral_energy",
]
