# hil/core/embeddings/lsa.py
"""
hil.core.embeddings.lsa

Latent Semantic Analysis (LSA) embedding for HIL.

This module provides a minimal, deterministic LSA implementation suitable
for constructing structural embeddings from text.

Invariants:
- Structural, not semantic (co-occurrence geometry only)
- Deterministic given fixed inputs
- No labels, no topic naming
- No persistence, no global state
- No adaptive or online behavior
"""

from __future__ import annotations

from typing import Iterable, Dict, Tuple, Optional, List

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import TruncatedSVD


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _lsa_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.core.embeddings.lsa invariant] {message}")


# ---------------------------------------------------------------------------
# LSA
# ---------------------------------------------------------------------------

def build_lsa_embedding(
    documents: Iterable[str],
    *,
    n_components: int = 300,
    min_df: int = 1,
    max_df: float = 1.0,
    stop_words: Optional[str] = "english",
) -> Tuple[np.ndarray, Dict[str, int]]:
    """
    Build an LSA embedding from raw documents.

    Parameters
    ----------
    documents : iterable of str
        Raw document texts.
    n_components : int
        Target dimensionality of latent space.
    min_df : int
        Minimum document frequency for terms.
    max_df : float
        Maximum document frequency (fraction).
    stop_words : str or None
        Stop-word handling (passed through to sklearn).

    Returns
    -------
    vectors : np.ndarray
        Document vectors of shape (n_docs, k), where k <= n_components.
    vocabulary : dict
        Mapping from term to column index in the term-document matrix.
    """
    # ------------------------------------------------------------------
    # Input normalization and checks
    # ------------------------------------------------------------------
    docs: List[str] = [d for d in documents if isinstance(d, str)]
    _lsa_invariant(len(docs) > 0, "documents must be non-empty")
    _lsa_invariant(n_components > 0, "n_components must be > 0")

    # ------------------------------------------------------------------
    # Term-document matrix (counts only)
    # ------------------------------------------------------------------
    vectorizer = CountVectorizer(
        min_df=min_df,
        max_df=max_df,
        stop_words=stop_words,
    )

    term_doc = vectorizer.fit_transform(docs)
    _lsa_invariant(
        term_doc.shape[0] == len(docs),
        "term-document row count mismatch",
    )

    # Number of documents and terms
    n_docs, n_terms = term_doc.shape
    _lsa_invariant(n_terms > 0, "no terms survived vectorization")

    # ------------------------------------------------------------------
    # Determine effective rank
    # ------------------------------------------------------------------
    # TruncatedSVD requires: 1 <= k < min(n_docs, n_terms)
    max_rank = min(n_docs, n_terms) - 1
    _lsa_invariant(max_rank >= 1, "insufficient rank for LSA")

    k = min(n_components, max_rank)
    _lsa_invariant(k >= 1, "effective n_components must be >= 1")

    # ------------------------------------------------------------------
    # SVD (deterministic)
    # ------------------------------------------------------------------
    # NOTE:
    # - randomized SVD is acceptable here because:
    #   - random_state is fixed
    #   - we only require determinism, not exact algebraic equivalence
    svd = TruncatedSVD(
        n_components=k,
        algorithm="randomized",
        random_state=0,
    )

    vectors = svd.fit_transform(term_doc)

    # ------------------------------------------------------------------
    # Output normalization
    # ------------------------------------------------------------------
    _lsa_invariant(
        vectors.shape == (n_docs, k),
        "unexpected embedding shape",
    )
    _lsa_invariant(
        np.isfinite(vectors).all(),
        "embedding contains non-finite values",
    )

    vocabulary: Dict[str, int] = dict(vectorizer.vocabulary_)

    return vectors.astype(np.float64, copy=False), vocabulary


__all__ = [
    "build_lsa_embedding",
]
