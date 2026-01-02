# hil/core/embeddings/lsa.py
"""
hil.core.embeddings.lsa

Latent Semantic Analysis (LSA) embedding for HIL.

This module provides a minimal, deterministic LSA implementation to replace
the current zero-vector scaffold in hil.core.api.build_embedding.

Invariants:
- Structural, not semantic
- Deterministic given fixed inputs
- No labels, no topic naming
- No persistence
- No adaptive behaviour
"""

from __future__ import annotations

from typing import Iterable, Dict, Tuple, Optional

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
        Dimensionality of latent space.
    min_df : int
        Minimum document frequency for terms.
    max_df : float
        Maximum document frequency (fraction).
    stop_words : str or None
        Stop-word handling (passed to sklearn).

    Returns
    -------
    vectors : np.ndarray
        Document vectors of shape (n_docs, n_components).
    vocabulary : dict
        Mapping from term to column index in the original term matrix.
    """
    docs = list(documents)
    _lsa_invariant(len(docs) > 0, "documents must be non-empty")
    _lsa_invariant(n_components > 0, "n_components must be > 0")

    # ------------------------------------------------------------------
    # Term-document matrix (counts only; no TF-IDF yet)
    # ------------------------------------------------------------------
    vectorizer = CountVectorizer(
        min_df=min_df,
        max_df=max_df,
        stop_words=stop_words,
    )

    term_doc = vectorizer.fit_transform(docs)
    _lsa_invariant(term_doc.shape[0] == len(docs), "row count mismatch")

    # ------------------------------------------------------------------
    # SVD
    # ------------------------------------------------------------------
    k = min(n_components, min(term_doc.shape) - 1)
    _lsa_invariant(k > 0, "effective n_components must be > 0")

    svd = TruncatedSVD(
        n_components=k,
        algorithm="randomized",
        random_state=0,  # determinism
    )

    vectors = svd.fit_transform(term_doc)

    # ------------------------------------------------------------------
    # Output
    # ------------------------------------------------------------------
    vocabulary = vectorizer.vocabulary_

    return vectors.astype(np.float64), vocabulary
