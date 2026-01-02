# hil/orchestrator/diff.py
"""
hil.orchestrator.diff

Artifact comparison utilities for the HIL orchestrator.

This module defines:
- how diagnostic artifacts from different runs are compared
- how numeric and structural differences are reported

This module does NOT:
- interpret differences
- apply thresholds
- label outcomes
- trigger actions
- participate in execution or planning

Diffs are descriptive, not evaluative.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _diff_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.orchestrator.diff invariant] {message}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> Dict[str, Any]:
    _diff_invariant(path.exists(), f"artifact not found: {path}")
    _diff_invariant(path.suffix == ".json", f"artifact must be JSON: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _numeric_delta(a: Any, b: Any) -> Any:
    """
    Compute a numeric delta if possible, otherwise return None.

    This function does not coerce types or invent semantics.
    """
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return b - a
    return None


# ---------------------------------------------------------------------------
# Metric diffs
# ---------------------------------------------------------------------------

def diff_metrics(
    run_a: Path,
    run_b: Path,
) -> Dict[str, Any]:
    """
    Diff METRICS.json between two runs.

    Returns raw numeric deltas keyed by metric name.
    """
    metrics_a = _load_json(run_a / "METRICS.json")
    metrics_b = _load_json(run_b / "METRICS.json")

    diff: Dict[str, Any] = {}

    keys = set(metrics_a.keys()) | set(metrics_b.keys())
    for k in keys:
        va = metrics_a.get(k)
        vb = metrics_b.get(k)

        delta = _numeric_delta(va, vb)

        diff[k] = {
            "run_a": va,
            "run_b": vb,
            "delta": delta,
        }

    return diff


# ---------------------------------------------------------------------------
# Field diffs
# ---------------------------------------------------------------------------

def diff_field_summary(
    run_a: Path,
    run_b: Path,
) -> Dict[str, Any]:
    """
    Diff FIELD_SUMMARY.json between two runs.
    """
    field_a = _load_json(run_a / "FIELD_SUMMARY.json")
    field_b = _load_json(run_b / "FIELD_SUMMARY.json")

    diff: Dict[str, Any] = {}

    keys = set(field_a.keys()) | set(field_b.keys())
    for k in keys:
        va = field_a.get(k)
        vb = field_b.get(k)

        diff[k] = {
            "run_a": va,
            "run_b": vb,
            "delta": _numeric_delta(va, vb),
        }

    return diff


# ---------------------------------------------------------------------------
# Graph diffs
# ---------------------------------------------------------------------------

def diff_graph_summary(
    run_a: Path,
    run_b: Path,
) -> Dict[str, Any]:
    """
    Diff GRAPH_SUMMARY.json between two runs.
    """
    graph_a = _load_json(run_a / "GRAPH_SUMMARY.json")
    graph_b = _load_json(run_b / "GRAPH_SUMMARY.json")

    diff: Dict[str, Any] = {}

    keys = set(graph_a.keys()) | set(graph_b.keys())
    for k in keys:
        va = graph_a.get(k)
        vb = graph_b.get(k)

        diff[k] = {
            "run_a": va,
            "run_b": vb,
            "delta": _numeric_delta(va, vb),
        }

    return diff


# ---------------------------------------------------------------------------
# Composite diff
# ---------------------------------------------------------------------------

def diff_runs(
    run_a: Path,
    run_b: Path,
) -> Dict[str, Any]:
    """
    Compute a composite diff between two runs.

    This function aggregates metric, field, and graph diffs
    without interpretation.
    """
    _diff_invariant(run_a.is_dir(), f"run_a is not a directory: {run_a}")
    _diff_invariant(run_b.is_dir(), f"run_b is not a directory: {run_b}")

    return {
        "run_a": run_a.name,
        "run_b": run_b.name,
        "metrics": diff_metrics(run_a, run_b),
        "field": diff_field_summary(run_a, run_b),
        "graph": diff_graph_summary(run_a, run_b),
    }


__all__ = [
    "diff_metrics",
    "diff_field_summary",
    "diff_graph_summary",
    "diff_runs",
]
