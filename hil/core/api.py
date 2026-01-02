# hil/core/api.py
"""
hil.core.api

Canonical public interface to the HIL epistemic core.

This module is the ONLY sanctioned entrypoint into the epistemic engine.
Everything outside `hil/core` (orchestrator, graphs, reports, hosting, DB)
must call *only* these functions.

Epistemic invariants enforced by design:
- Diagnostic, not prescriptive (no labels, no thresholds, no decisions)
- Theory-first (code witnesses defined constructs; does not define them)
- Stateless and deterministic (no persistence, no run registry, no IO)
- No orchestration (pipelines/stages belong outside core)
- No external authority (no LLM calls, no network, no hidden randomness)

This file should remain small. If it grows, the boundary is leaking.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

import numpy as np

from hil.core.structure.graph import Graph


# --- Core guardrails ---------------------------------------------------------

def _core_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core invariant] {message}")


# --- Minimal core data carriers ---------------------------------------------

@dataclass(frozen=True)
class CoreEmbedding:
    vectors: np.ndarray
    vocabulary: Dict[str, int]


@dataclass(frozen=True)
class CoreField:
    vectors: np.ndarray
    metadata: Optional[Dict[str, Any]] = None


# --- API functions -----------------------------------------------------------

def build_embedding(
    documents: Iterable[str],
    *,
    n_components: int = 300,
    vocabulary: Optional[Dict[str, int]] = None,
) -> CoreEmbedding:
    """
    Build an embedding space for a given set of documents.

    Stub: implementation will call `hil.core.embeddings.vocabulary` and `lsa`.
    Invariants:
    - No IO (documents are provided as strings)
    - Deterministic output given same inputs
    """
    _core_invariant(n_components > 0, "n_components must be > 0")

    docs = list(documents)
    _core_invariant(len(docs) > 0, "documents must be non-empty")

    # Placeholder embedding: deterministic, shape-correct
    vecs = np.zeros((len(docs), n_components), dtype=np.float64)
    vocab = vocabulary or {}

    return CoreEmbedding(vectors=vecs, vocabulary=vocab)


def build_field(
    embedding: CoreEmbedding,
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> CoreField:
    """
    Construct a field object from embedding vectors.

    Invariants:
    - Field is a mathematical object (vectors + optional metadata)
    - No persistence, no IDs, no run state
    """
    _core_invariant(
        isinstance(embedding.vectors, np.ndarray),
        "embedding.vectors must be np.ndarray",
    )
    _core_invariant(
        embedding.vectors.ndim == 2,
        "embedding.vectors must be 2D (n, d)",
    )

    return CoreField(vectors=embedding.vectors, metadata=metadata)


def build_structure(
    field: CoreField,
) -> Graph:
    """
    Construct a structural graph from a field.

    This is a *temporary scaffold* for the sanity run:
    - empty edge set
    - correct node count
    - deterministic
    - explicitly non-heuristic

    Invariants:
    - Structure is derived deterministically
    - No semantic interpretation or labels
    """
    _core_invariant(field.vectors.ndim == 2, "field.vectors must be 2D")
    n = int(field.vectors.shape[0])
    _core_invariant(n >= 1, "field must have at least one vector")

    # Empty structural scaffold (valid graph)
    src = np.zeros((0,), dtype=np.uint32)
    dst = np.zeros((0,), dtype=np.uint32)
    w = np.zeros((0,), dtype=np.float64)

    return Graph(
        src=src,
        dst=dst,
        weight=w,
        num_nodes=n,
    )


def compute_diagnostics(
    field: CoreField,
    graph: Graph,
) -> Dict[str, Any]:
    """
    Compute diagnostic quantities (entropy, coherence, stability).

    Invariants:
    - Return raw numeric diagnostics only
    - No regime assignment
    - No thresholds
    - No action recommendations
    """
    _core_invariant(field.vectors.ndim == 2, "field.vectors must be 2D")
    _core_invariant(
        graph.num_nodes == field.vectors.shape[0],
        "graph.num_nodes must match field size",
    )

    # Lazy imports to preserve boundary discipline
    from hil.core.metrics.entropy import structural_entropy  # noqa: WPS433
    from hil.core.metrics.coherence import field_coherence  # noqa: WPS433

    entropy = structural_entropy(graph)
    coherence = field_coherence(field.vectors)

    return {
        "entropy": float(entropy),
        "coherence": float(coherence),
        "stability": None,  # intentionally deferred
    }


__all__ = [
    "CoreEmbedding",
    "CoreField",
    "build_embedding",
    "build_field",
    "build_structure",
    "compute_diagnostics",
]
