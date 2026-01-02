# hil/core/metrics/stability.py
"""
hil.core.metrics.stability

Structural stability computations.

Stability is treated here as a *diagnostic geometric quantity* derived from
other structural metrics. It does NOT classify regimes, enforce thresholds,
or imply desirability.

Invariants:
- Structural, not semantic
- Diagnostic only (returns numbers; never labels or decides)
- Deterministic (no randomness, no hidden global state)
- No IO, no persistence
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _metric_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.metrics.stability invariant] {message}")


# ---------------------------------------------------------------------------
# Stability
# ---------------------------------------------------------------------------

def structural_stability(
    *,
    entropy: float,
    coherence: float,
) -> float:
    """
    Compute a structural stability proxy from entropy and coherence.

    First-pass definition (intentionally simple and inspectable):

    - Stability increases with coherence
    - Stability decreases with entropy
    - Both quantities are treated as continuous, real-valued diagnostics

    Current form:
        stability = coherence / (1.0 + entropy)

    Properties:
    - stability >= 0
    - monotonic in coherence
    - monotonic decreasing in entropy
    - no thresholds, no regimes

    Notes:
    - This is a *proxy*, not a final or exclusive definition.
    - The form is chosen for numerical stability and interpretability.
    """
    _metric_invariant(np.isfinite(entropy), "entropy must be finite")
    _metric_invariant(entropy >= 0.0, "entropy must be >= 0")

    _metric_invariant(np.isfinite(coherence), "coherence must be finite")
    _metric_invariant(coherence >= 0.0, "coherence must be >= 0")

    stability = float(coherence / (1.0 + entropy))

    _metric_invariant(np.isfinite(stability), "stability must be finite")
    _metric_invariant(stability >= 0.0, "stability must be >= 0")

    return stability


__all__ = [
    "structural_stability",
]
