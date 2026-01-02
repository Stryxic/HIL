# hil/core/native/_shim.py
"""
hil.core.native._shim

Thin Python-to-native shim.

This module is the ONLY location in `hil/core` allowed to import the compiled
native extension (e.g. `hil.core.native._native`).

Invariants:
- No policy, no decisions, no thresholds
- No orchestration
- No persistence / run state
- Deterministic calls only
- Accept NumPy arrays; validate dtype/shape; forward to native

Development stages:
A) Stub functions (this file) so Python core can shape its needs.
B) Optional pure-Python fallbacks (still here, explicitly).
C) Native calls once `_native` exists and exports stable function names.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import os
import numpy as np


class NativeUnavailable(RuntimeError):
    pass


def _native_available() -> bool:
    try:
        from hil.core.native import _native  # type: ignore  # noqa: F401
        return True
    except Exception:
        return False


def _require_native() -> Any:
    """
    Import the native extension or raise a clear error.
    Autobuild is *explicitly opt-in* via HIL_NATIVE_AUTOBUILD=1.
    """
    try:
        from hil.core.native import _native  # type: ignore
        return _native
    except Exception as e:
        if os.environ.get("HIL_NATIVE_AUTOBUILD") == "1":
            # Optional: trigger editable install build; keep minimal and explicit.
            import subprocess, sys  # noqa: WPS433
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", repo_root])
            from hil.core.native import _native  # type: ignore
            return _native
        raise NativeUnavailable(
            "Native extension not available. Build with `pip install -e .` "
            "from repo root, or set HIL_NATIVE_AUTOBUILD=1 to allow opt-in autobuild."
        ) from e


def graph_entropy(
    src: np.ndarray,
    dst: np.ndarray,
    weight: np.ndarray,
    num_nodes: int,
) -> float:
    """
    Native structural entropy.

    Stub shape:
      - src, dst: uint32 arrays (1D)
      - weight: float64 array (1D)
      - num_nodes: int

    Returns: float entropy

    NOTE: This function will call `_native.graph_entropy` once bindings exist.
    """
    src = np.asarray(src, dtype=np.uint32)
    dst = np.asarray(dst, dtype=np.uint32)
    weight = np.asarray(weight, dtype=np.float64)

    if src.ndim != 1 or dst.ndim != 1 or weight.ndim != 1:
        raise ValueError("src, dst, weight must be 1D arrays")
    if src.shape != dst.shape or src.shape != weight.shape:
        raise ValueError("src, dst, weight must have identical shapes")
    if num_nodes < 1:
        raise ValueError("num_nodes must be >= 1")

    # Stage C: native
    native = _require_native()
    if not hasattr(native, "graph_entropy"):
        raise AttributeError("Native module missing graph_entropy export")
    return float(native.graph_entropy(src, dst, weight, int(num_nodes)))


def graph_metrics(
    src: np.ndarray,
    dst: np.ndarray,
    weight: np.ndarray,
    num_nodes: int,
) -> Dict[str, float]:
    """
    Optional convenience wrapper returning a dict of native graph metrics.

    Not required for core correctness, but useful as a single call boundary.

    Will call `_native.graph_metrics` if present; otherwise only entropy is returned.
    """
    native = _require_native()

    if hasattr(native, "graph_metrics"):
        out = native.graph_metrics(
            np.asarray(src, dtype=np.uint32),
            np.asarray(dst, dtype=np.uint32),
            np.asarray(weight, dtype=np.float64),
            int(num_nodes),
        )
        # Expect dict-like output from native; coerce to Python floats.
        return {str(k): float(v) for k, v in dict(out).items()}

    # Fallback: only entropy via the single-function export
    return {"entropy": graph_entropy(src, dst, weight, num_nodes)}
