# hil/viz/overlay_project_2d.py
"""
Overlay multiple HIL fields in a shared 2D projection.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np

from hil.core.operators.overlay import compute_shared_pca


def overlay_fields_2d(
    *,
    fields: Dict[str, np.ndarray],
    output_path: Path,
) -> None:
    """
    Produce a 2D overlay plot of multiple fields.

    Each field is plotted in the same PCA space,
    with distinct markers.
    """
    _, proj = compute_shared_pca(fields, n_components=2)

    plt.figure(figsize=(8, 6))

    markers = ["o", "s", "^", "D"]
    for (name, coords), marker in zip(proj.items(), markers):
        plt.scatter(
            coords[:, 0],
            coords[:, 1],
            label=name,
            alpha=0.8,
            marker=marker,
        )

    plt.title("HIL Field Overlay (2D PCA)")
    plt.xlabel("PC1")
    plt.ylabel("PC2")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
