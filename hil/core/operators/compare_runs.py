# hil/core/operators/compare_runs.py
"""
hil.core.operators.compare_runs

Diagnostic operators for comparing two HIL runs.

This module is intentionally downstream of hil.core.metrics:
- It does not interpret values.
- It does not classify regimes.
- It only computes structural deltas and summaries.

Invariants:
- Diagnostic only
- Deterministic
- No IO except explicit caller-provided paths (optional helpers)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np


def _op_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.operators.compare_runs invariant] {message}")


@dataclass(frozen=True)
class RunSummary:
    """
    Minimal in-memory representation of a run.

    This is designed to be constructed from artifacts/*/METRICS.json and STABILITY.json.
    """
    metrics: Dict[str, Any]
    stability: Dict[int, float]
    num_documents: int


def compare_runs(a: RunSummary, b: RunSummary) -> Dict[str, Any]:
    """
    Compare two runs a and b.

    Outputs only deltas and simple descriptive summaries:
    - metric deltas (b - a) for overlapping numeric keys
    - stability distribution deltas:
        mean, median, min, max
    """
    _op_invariant(a.num_documents > 0 and b.num_documents > 0, "num_documents must be > 0")
    _op_invariant(len(a.stability) > 0 and len(b.stability) > 0, "stability must be non-empty")

    out: Dict[str, Any] = {
        "a": {"num_documents": a.num_documents},
        "b": {"num_documents": b.num_documents},
        "metric_deltas": {},
        "stability_summary": {},
    }

    # --- Metric deltas (numeric overlap only) --------------------------
    keys = set(a.metrics.keys()) & set(b.metrics.keys())
    for k in sorted(keys):
        va = a.metrics[k]
        vb = b.metrics[k]
        if isinstance(va, float) and isinstance(vb, float) and np.isfinite(va) and np.isfinite(vb):
            out["metric_deltas"][k] = float(vb - va)

    # --- Stability summaries ------------------------------------------
    sa = np.array([a.stability[i] for i in sorted(a.stability.keys())], dtype=np.float64)
    sb = np.array([b.stability[i] for i in sorted(b.stability.keys())], dtype=np.float64)

    _op_invariant(np.isfinite(sa).all() and np.isfinite(sb).all(), "stability values must be finite")

    def _summ(x: np.ndarray) -> Dict[str, float]:
        return {
            "mean": float(x.mean()),
            "median": float(np.median(x)),
            "min": float(x.min()),
            "max": float(x.max()),
        }

    out["stability_summary"]["a"] = _summ(sa)
    out["stability_summary"]["b"] = _summ(sb)
    out["stability_summary"]["delta"] = {
        k: float(out["stability_summary"]["b"][k] - out["stability_summary"]["a"][k])
        for k in out["stability_summary"]["a"].keys()
    }

    return out


__all__ = [
    "RunSummary",
    "compare_runs",
]
