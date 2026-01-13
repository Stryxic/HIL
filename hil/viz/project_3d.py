# hil/viz/project_3d.py
"""
hil.viz.project_3d

Deterministic 3D projection for Hilbert Epistemic Fields.

This module renders a static 3D diagnostic visualization using:
- PC1 (x-axis)
- PC2 (y-axis)
- structural stability (z-axis)

Invariants:
- Diagnostic only (no interpretation, no labels)
- Deterministic (fixed linear algebra and plotting)
- Read-only projection
- No IO except writing the output image
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (required for 3D)


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _viz_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.viz.project_3d invariant] {message}")


# ---------------------------------------------------------------------------
# PCA (2D) — duplicated deliberately to avoid cross-module coupling
# ---------------------------------------------------------------------------

def _pca_2d(X: np.ndarray) -> np.ndarray:
    """
    Deterministic 2D PCA projection.

    Parameters
    ----------
    X : np.ndarray, shape (n, d)

    Returns
    -------
    Y : np.ndarray, shape (n, 2)
    """
    _viz_invariant(X.ndim == 2, "X must be 2D")
    _viz_invariant(X.shape[0] >= 2, "X must have at least 2 rows")

    Xc = X - X.mean(axis=0, keepdims=True)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    Y = Xc @ Vt[:2].T

    _viz_invariant(Y.shape[1] == 2, "PCA output must be 2D")
    _viz_invariant(np.isfinite(Y).all(), "PCA output must be finite")

    return Y


# ---------------------------------------------------------------------------
# 3D projection
# ---------------------------------------------------------------------------

def project_field_3d(
    *,
    field_vectors: np.ndarray,
    stability: Dict[int, float],
    output_path: Path,
    method: str = "pca",
) -> None:
    """
    Render a deterministic 3D diagnostic plot.

    Axes:
    - X: PC1
    - Y: PC2
    - Z: structural stability (leave-one-out)

    Parameters
    ----------
    field_vectors : np.ndarray, shape (n, d)
        Field vectors.
    stability : dict[int, float]
        Mapping from element index to stability value.
    output_path : Path
        Output PNG file path.
    method : str
        Projection method (currently only 'pca' is supported).
    """
    _viz_invariant(method == "pca", "only 'pca' projection is supported")
    _viz_invariant(field_vectors.ndim == 2, "field_vectors must be 2D")

    n = field_vectors.shape[0]
    _viz_invariant(len(stability) == n, "stability size must match number of elements")

    # ------------------------------------------------------------------
    # Compute PCA projection
    # ------------------------------------------------------------------
    Y = _pca_2d(field_vectors)

    x = Y[:, 0]
    y = Y[:, 1]

    # Stability ordered by index
    z = np.array(
        [stability[i] for i in range(n)],
        dtype=np.float64,
    )

    _viz_invariant(np.isfinite(z).all(), "stability values must be finite")
    _viz_invariant(np.all(z >= 0.0), "stability values must be >= 0")

    # ------------------------------------------------------------------
    # Plot (deterministic)
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    scatter = ax.scatter(
        x,
        y,
        z,
        c=z,
        cmap="viridis",
        depthshade=False,
        s=60,
    )

    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("Stability")

    # Fixed viewing angle for determinism
    ax.view_init(elev=20, azim=45)

    # Colorbar (diagnostic scale only)
    fig.colorbar(scatter, ax=ax, shrink=0.6, pad=0.1)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)


__all__ = [
    "project_field_3d",
]
