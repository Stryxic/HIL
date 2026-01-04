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
from hil.core.embeddings.lsa import build_lsa_embedding


# ---------------------------------------------------------------------------
# Core guardrails
# ---------------------------------------------------------------------------

def _core_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core invariant] {message}")


# ---------------------------------------------------------------------------
# Core data carriers (pure, immutable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CoreEmbedding:
    vectors: np.ndarray
    vocabulary: Dict[str, int]


@dataclass(frozen=True)
class CoreField:
    vectors: np.ndarray
    metadata: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# API functions
# ---------------------------------------------------------------------------

def build_embedding(
    documents: Iterable[str],
    *,
    n_components: int = 300,
) -> CoreEmbedding:
    """
    Build an embedding space for a given set of documents.

    Implementation:
    - Deterministic Latent Semantic Analysis (LSA)
    - Purely structural (term co-occurrence geometry)
    - No semantic interpretation

    Invariants:
    - No IO (documents provided as strings)
    - Deterministic output for fixed inputs
    """
    _core_invariant(n_components > 0, "n_components must be > 0")

    docs = list(documents)
    _core_invariant(len(docs) > 0, "documents must be non-empty")

    vectors, vocabulary = build_lsa_embedding(
        docs,
        n_components=n_components,
    )

    _core_invariant(
        vectors.shape[0] == len(docs),
        "embedding row count must match number of documents",
    )
    _core_invariant(
        vectors.ndim == 2,
        "embedding vectors must be 2D",
    )

    return CoreEmbedding(
        vectors=vectors,
        vocabulary=vocabulary,
    )


def build_field(
    embedding: CoreEmbedding,
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> CoreField:
    """
    Construct a Hilbert Epistemic Field from embedding vectors.

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

    return CoreField(
        vectors=embedding.vectors,
        metadata=metadata,
    )


def build_structure(field: CoreField) -> Graph:
    """
    Construct structural graph from a field.

    Minimal calibration implementation:
    - Fully-connected undirected cosine graph (i < j)
    - Non-negative weights by shifting cosine similarity into [0, 1]
      w = (cos + 1) / 2

    Properties:
    - Structural (geometry only)
    - Deterministic
    - Label-free
    """
    _core_invariant(field.vectors.ndim == 2, "field.vectors must be 2D")

    X = field.vectors.astype(np.float64, copy=False)
    n = int(X.shape[0])
    _core_invariant(n >= 1, "field must have at least one vector")

    # Normalize rows deterministically
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    V = X / norms

    src_list: list[int] = []
    dst_list: list[int] = []
    w_list: list[float] = []

    for i in range(n):
        vi = V[i]
        for j in range(i + 1, n):
            cos = float(np.dot(vi, V[j]))
            w = (cos + 1.0) * 0.5  # shift to [0, 1]
            src_list.append(i)
            dst_list.append(j)
            w_list.append(w)

    src = np.asarray(src_list, dtype=np.int32)
    dst = np.asarray(dst_list, dtype=np.int32)
    w = np.asarray(w_list, dtype=np.float64)

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
