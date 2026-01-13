"""
hil.viz.overlay_project_3d

3D overlay projection for multiple HIL fields.

Invariants:
- Diagnostic only
- Deterministic
- No semantic alignment
- No recomputation of metrics
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import matplotlib.pyplot as plt

from hil.core.operators.overlay import compute_shared_pca


def _viz_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.viz.overlay_project_3d invariant] {message}")


def _align_stability(
    coords: np.ndarray,
    stability: Dict[str, float] | None,
) -> np.ndarray:
    """
    Align a stability mapping to projected coordinates.

    Rule:
    - If stability is None, return zeros
    - Otherwise:
        * sort keys deterministically
        * take values in that order
        * truncate or pad with last value to match coords
    """
    n = coords.shape[0]

    if stability is None:
        return np.zeros(n, dtype=np.float64)

    # Deterministic ordering (JSON-safe)
    items = sorted(stability.items(), key=lambda kv: kv[0])
    values = np.array([v for _, v in items], dtype=np.float64)

    if values.size == 0:
        return np.zeros(n, dtype=np.float64)

    if values.size >= n:
        return values[:n]

    # Pad deterministically with last value
    pad = np.full(n - values.size, values[-1], dtype=np.float64)
    return np.concatenate([values, pad])


def overlay_fields_3d(
    *,
    fields: Dict[str, np.ndarray],
    stability: Dict[str, Dict[str, float]] | None,
    output_path: Path,
) -> None:
    """
    Overlay multiple fields in a shared 3D projection.

    Parameters
    ----------
    fields : dict[str, np.ndarray]
        Field vectors per corpus.
    stability : dict[str, dict] or None
        Per-field stability mappings.
    output_path : Path
        PNG output path.
    """
    _viz_invariant(len(fields) >= 2, "need at least two fields to overlay")

    # ------------------------------------------------------------------
    # Shared projection
    # ------------------------------------------------------------------
    _, projections = compute_shared_pca(fields, n_components=3)

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")

    for name, coords in projections.items():
        _viz_invariant(coords.shape[1] == 3, "projection must be 3D")

        stab_map = stability.get(name) if stability else None
        z = _align_stability(coords, stab_map)

        ax.scatter(
            coords[:, 0],
            coords[:, 1],
            z,
            label=name,
            alpha=0.7,
            s=40,
        )

    ax.set_title("Overlay Field Projection (3D)")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_zlabel("Stability")

    ax.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
