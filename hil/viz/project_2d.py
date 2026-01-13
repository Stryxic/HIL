# hil/viz/project_2d.py
"""
hil.viz.project_2d

Deterministic 2D projection for a completed Hilbert State.

Contract (as used by hil/tests/test_calibration_vertical_slice.py):
- Exposes: project_field_2d(field_vectors, graph, output_path, method="pca") -> None
- Consumes ONLY existing state objects (field vectors + graph)
- Does NOT rebuild embeddings/fields/graphs/metrics
- Deterministic (no randomness)
- Writes exactly one file at output_path (PNG expected by tests)
- No semantic labels, no clustering, no regimes

This module is downstream of hil.core (visualization layer).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np


def _viz_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.viz.project_2d invariant] {message}")


@dataclass(frozen=True)
class _GraphLike:
    """
    Minimal structural contract for graph input.

    The core graph type (e.g., hil.core.api.CoreGraph) matches this shape.
    """
    src: np.ndarray
    dst: np.ndarray
    weight: np.ndarray
    num_nodes: int


def _pca_2d(x: np.ndarray) -> np.ndarray:
    """
    Deterministic PCA projection to 2D using SVD on mean-centered data.

    Notes:
    - No sklearn dependency.
    - Sign of singular vectors is deterministic up to a global sign; we fix sign
      by enforcing the largest-magnitude element in each component to be positive.
    """
    _viz_invariant(isinstance(x, np.ndarray), "field_vectors must be np.ndarray")
    _viz_invariant(x.ndim == 2, "field_vectors must be 2D")
    n, d = x.shape
    _viz_invariant(n >= 1 and d >= 1, "field_vectors must have shape (n>=1, d>=1)")

    # Mean center (float64 for numerical stability / determinism)
    xc = x.astype(np.float64, copy=False) - x.astype(np.float64, copy=False).mean(axis=0, keepdims=True)

    # If all vectors identical, projection is all zeros.
    if not np.isfinite(xc).all():
        raise ValueError("[hil.viz.project_2d invariant] field_vectors contains non-finite values")

    if np.allclose(xc, 0.0):
        return np.zeros((n, 2), dtype=np.float64)

    # SVD: xc = U S Vt ; principal axes = rows of Vt
    # full_matrices=False ensures deterministic shapes and avoids extra degrees of freedom.
    _, _, vt = np.linalg.svd(xc, full_matrices=False)

    # Take first two principal axes (or pad if d==1)
    if vt.shape[0] == 0:
        return np.zeros((n, 2), dtype=np.float64)

    comp = vt[:2, :]
    if comp.shape[0] == 1:
        comp = np.vstack([comp, np.zeros((1, d), dtype=np.float64)])

    # Fix sign deterministically for each component:
    # find index of largest magnitude element; ensure it is positive.
    comp_fixed = comp.copy()
    for i in range(2):
        row = comp_fixed[i]
        j = int(np.argmax(np.abs(row)))
        if row[j] < 0:
            comp_fixed[i] = -row

    # Project
    y = xc @ comp_fixed.T
    _viz_invariant(y.shape == (n, 2), "internal error: PCA projection has wrong shape")
    return y


def _compute_out_strength(graph: _GraphLike) -> np.ndarray:
    """
    Outgoing weight mass per node (out-strength).

    Returns float64 array of shape (num_nodes,).
    """
    m = int(graph.src.size)
    if m == 0:
        return np.zeros((graph.num_nodes,), dtype=np.float64)

    out_strength = np.bincount(
        graph.src.astype(np.int64, copy=False),
        weights=graph.weight.astype(np.float64, copy=False),
        minlength=int(graph.num_nodes),
    ).astype(np.float64, copy=False)

    if out_strength.shape[0] != int(graph.num_nodes):
        out_strength = np.resize(out_strength, (int(graph.num_nodes),)).astype(np.float64, copy=False)

    return out_strength


def project_field_2d(
    *,
    field_vectors: np.ndarray,
    graph: Any,
    output_path: Path,
    method: str = "pca",
) -> None:
    """
    Produce a deterministic 2D projection of a Hilbert State.

    Parameters
    ----------
    field_vectors:
        Array (n, d) for n elements in a d-dimensional field.
    graph:
        Graph-like object with attributes: src, dst, weight, num_nodes
        (e.g., hil.core.api.CoreGraph).
    output_path:
        Where to write the image (PNG expected by current tests).
    method:
        Currently only "pca" is supported.

    Output
    ------
    Writes exactly one file to output_path.
    """
    # --- Validate inputs -----------------------------------------------------
    _viz_invariant(isinstance(output_path, Path), "output_path must be a pathlib.Path")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _viz_invariant(isinstance(field_vectors, np.ndarray), "field_vectors must be np.ndarray")
    _viz_invariant(field_vectors.ndim == 2, "field_vectors must be 2D")
    _viz_invariant(np.isfinite(field_vectors).all(), "field_vectors must be finite")

    # Graph structural contract
    _viz_invariant(hasattr(graph, "src") and hasattr(graph, "dst") and hasattr(graph, "weight") and hasattr(graph, "num_nodes"),
                   "graph must provide src, dst, weight, num_nodes")

    g = _GraphLike(
        src=np.asarray(graph.src),
        dst=np.asarray(graph.dst),
        weight=np.asarray(graph.weight),
        num_nodes=int(graph.num_nodes),
    )

    n = int(field_vectors.shape[0])
    _viz_invariant(g.num_nodes == n, "graph.num_nodes must match field_vectors.shape[0]")
    _viz_invariant(g.src.shape == g.dst.shape == g.weight.shape, "graph arrays must have matching shapes")
    _viz_invariant(g.src.ndim == g.dst.ndim == g.weight.ndim == 1, "graph arrays must be 1D")
    _viz_invariant(np.isfinite(g.weight).all(), "graph weights must be finite")
    _viz_invariant(np.all(g.weight >= 0.0), "graph weights must be non-negative")

    if g.src.size > 0:
        _viz_invariant(np.issubdtype(g.src.dtype, np.integer), "graph.src must be integer dtype")
        _viz_invariant(np.issubdtype(g.dst.dtype, np.integer), "graph.dst must be integer dtype")
        _viz_invariant(int(g.src.min()) >= 0 and int(g.src.max()) < g.num_nodes, "graph.src out of range")
        _viz_invariant(int(g.dst.min()) >= 0 and int(g.dst.max()) < g.num_nodes, "graph.dst out of range")

    mth = (method or "").strip().lower()
    _viz_invariant(mth == "pca", f"Only method='pca' is supported (got '{method}')")

    # --- Compute projection --------------------------------------------------
    coords = _pca_2d(field_vectors)

    # --- Prepare structural overlay scalars ---------------------------------
    out_strength = _compute_out_strength(g)

    # --- Render (matplotlib) ------------------------------------------------
    # Keep matplotlib import local to avoid pulling it into environments that
    # might only run core logic.
    import matplotlib
    matplotlib.use("Agg")  # non-interactive, deterministic backend for CI-style usage
    import matplotlib.pyplot as plt

    # Figure parameters chosen for stable output across repeated calls on same machine.
    fig = plt.figure(figsize=(7.5, 5.0), dpi=150)
    ax = fig.add_subplot(111)

    ax.set_title("HIL Field Projection (2D) — PCA", fontsize=10)
    ax.set_xlabel("PC1", fontsize=9)
    ax.set_ylabel("PC2", fontsize=9)

    # Optional edge overlay (faint). Order is deterministic: iterate arrays in-order.
    if int(g.src.size) > 0:
        w = g.weight.astype(np.float64, copy=False)
        wmax = float(w.max()) if w.size else 0.0
        denom = wmax if wmax > 0.0 else 1.0

        for s, d, ww in zip(g.src.tolist(), g.dst.tolist(), w.tolist()):
            x0, y0 = coords[int(s), 0], coords[int(s), 1]
            x1, y1 = coords[int(d), 0], coords[int(d), 1]
            # Line width scaled by normalized weight (bounded)
            lw = 0.3 + 1.2 * float(ww) / denom
            ax.plot([x0, x1], [y0, y1], linewidth=lw, alpha=0.18)

    # Scatter nodes. Color by out-strength (structural only); if all zeros, use uniform color.
    if float(out_strength.sum()) > 0.0:
        sc = ax.scatter(
            coords[:, 0],
            coords[:, 1],
            c=out_strength,
            s=35,
            linewidths=0.0,
        )
        # Colorbar is diagnostic-only; no labels beyond the scalar name.
        cbar = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("out-strength", fontsize=8)
        cbar.ax.tick_params(labelsize=8)
    else:
        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            s=35,
            linewidths=0.0,
        )

    # Tight layout for stable spacing
    fig.tight_layout()

    # Write exactly one output file
    fig.savefig(output_path, format="png")
    plt.close(fig)


__all__ = ["project_field_2d"]
