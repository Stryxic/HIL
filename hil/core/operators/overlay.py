# hil/core/operators/overlay.py
"""
hil.core.operators.overlay

Overlay operators for comparing multiple HIL fields
in a shared projection space.

This operator explicitly projects fields into their
maximum common linear subspace before comparison.

Invariants:
- Diagnostic only
- Deterministic
- No semantic alignment
- No metric recomputation
- No mutation of input fields
"""

from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from sklearn.decomposition import PCA


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _op_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.operators.overlay invariant] {message}")


# ---------------------------------------------------------------------------
# Overlay / Alignment
# ---------------------------------------------------------------------------

def compute_shared_pca(
    fields: Dict[str, np.ndarray],
    *,
    n_components: int = 3,
) -> Tuple[PCA, Dict[str, np.ndarray]]:
    """
    Fit a single PCA model over multiple fields after
    truncating each to their maximum common dimensionality.

    This enforces the **Field Alignment Contract**:

    - Fields need NOT have equal original dimensionality
    - Fields MUST share a common linear subspace
    - Alignment is achieved by deterministic truncation
    - Projection is shared, not per-field

    Preserves:
    - Linear structure
    - Determinism
    - Diagnostic comparability

    Does NOT:
    - Fuse corpora
    - Reinterpret axes
    - Modify original embeddings
    - Recompute metrics
    """

    # -----------------------------
    # Basic sanity
    # -----------------------------
    _op_invariant(len(fields) >= 2, "need at least two fields to overlay")
    _op_invariant(n_components in (2, 3), "n_components must be 2 or 3")

    for name, arr in fields.items():
        _op_invariant(
            isinstance(arr, np.ndarray),
            f"field '{name}' must be a numpy array",
        )
        _op_invariant(
            arr.ndim == 2,
            f"field '{name}' must be 2D (n, d)",
        )
        _op_invariant(
            arr.shape[0] >= 1,
            f"field '{name}' must have at least one element",
        )
        _op_invariant(
            np.isfinite(arr).all(),
            f"field '{name}' contains non-finite values",
        )

    # -----------------------------
    # Determine common subspace
    # -----------------------------
    dims = [arr.shape[1] for arr in fields.values()]
    common_dim = min(dims)

    _op_invariant(
        common_dim >= n_components,
        "common dimensionality too small for requested projection",
    )

    # -----------------------------
    # Truncate deterministically
    # -----------------------------
    truncated: Dict[str, np.ndarray] = {
        name: arr[:, :common_dim]
        for name, arr in fields.items()
    }

    # -----------------------------
    # Shared PCA fit
    # -----------------------------
    X_all = np.vstack(list(truncated.values()))

    pca = PCA(
        n_components=n_components,
        random_state=0,  # determinism
    )

    X_all_proj = pca.fit_transform(X_all)

    # -----------------------------
    # Split projections back out
    # -----------------------------
    projections: Dict[str, np.ndarray] = {}
    idx = 0

    for name, arr in truncated.items():
        n = arr.shape[0]
        projections[name] = X_all_proj[idx : idx + n]
        idx += n

    _op_invariant(
        idx == X_all.shape[0],
        "projection split mismatch",
    )

    return pca, projections


__all__ = [
    "compute_shared_pca",
]
