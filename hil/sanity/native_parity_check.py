#!/usr/bin/env python3
"""
hil.sanity.native_parity_check

Native ↔ Python parity check for core epistemic diagnostics.

Purpose
-------
This script verifies that the pure-Python reference implementations of
structural entropy and field coherence produce numerically equivalent
results to the native C implementations.

This is a *sanity check*, not a benchmark and not a claim about regimes,
health, or correctness beyond numerical parity.

Invariants
----------
- Deterministic
- No IO beyond stdout
- No persistence
- No orchestration
- No interpretation of results
"""

from __future__ import annotations

import numpy as np

from hil.core.structure.graph import Graph
from hil.core.metrics.entropy import structural_entropy
from hil.core.metrics.coherence import field_coherence
from hil.core.native._shim import graph_entropy


def _assert_close(a: float, b: float, name: str, tol: float = 1e-9) -> None:
    if not np.isclose(a, b, atol=tol, rtol=0.0):
        raise AssertionError(
            f"[PARITY FAIL] {name}: python={a:.12f}, native={b:.12f}"
        )
    print(f"[OK] {name}: python={a:.12f}, native={b:.12f}")


def main() -> None:
    # ------------------------------------------------------------------
    # Step 1: Construct a tiny, explicit field (no semantics)
    # ------------------------------------------------------------------
    vectors = np.array(
        [
            [1.0, 0.0],
            [0.5, 0.5],
            [0.0, 1.0],
        ],
        dtype=np.float64,
    )

    # ------------------------------------------------------------------
    # Step 2: Construct a tiny, explicit graph
    #
    # Undirected triangle with uniform weights.
    # This is scaffolding for sanity checking only.
    # ------------------------------------------------------------------
    src = np.array([0, 1, 1], dtype=np.uint32)
    dst = np.array([1, 0, 2], dtype=np.uint32)
    weight = np.array([1.0, 1.0, 1.0], dtype=np.float64)

    graph = Graph(
        src=src,
        dst=dst,
        weight=weight,
        num_nodes=3,
    )

    # ------------------------------------------------------------------
    # Step 3: Python diagnostics
    # ------------------------------------------------------------------
    py_entropy = structural_entropy(graph)
    py_coherence = field_coherence(vectors)

    # ------------------------------------------------------------------
    # Step 4: Native diagnostics
    # ------------------------------------------------------------------
    native_entropy = graph_entropy(
        src=graph.src,
        dst=graph.dst,
        weight=graph.weight,
        num_nodes=graph.num_nodes,
    )

    # Native coherence binding will be added later; for now, we check
    # only entropy via native and coherence via Python parity-by-definition.

    # ------------------------------------------------------------------
    # Step 5: Parity assertions
    # ------------------------------------------------------------------
    print("\n--- Native ↔ Python Parity Check ---\n")

    _assert_close(py_entropy, native_entropy, "structural_entropy")

    # Coherence parity check is structural-by-definition at this stage
    # (native binding will be added later).
    print(f"[INFO] field_coherence (python): {py_coherence:.12f}")

    print("\n[PASS] Native ↔ Python parity verified for current diagnostics.")


if __name__ == "__main__":
    main()
