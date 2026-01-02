"""
hil.core.embeddings.vocabulary

Vocabulary construction for the HIL epistemic core.

This module is responsible only for:
- normalising text
- extracting tokens
- constructing a stable token → index mapping

It does NOT:
- read files
- persist vocabularies
- apply semantic interpretation
- weight or rank tokens by importance

The vocabulary defines the coordinate basis of the embedding space.
"""

from __future__ import annotations

from typing import Dict, Iterable, List
import re
from collections import Counter


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")


def tokenize(text: str) -> List[str]:
    """
    Tokenize raw text into a list of normalised tokens.

    This tokenizer is intentionally simple and deterministic.
    More complex linguistic processing belongs outside the core.
    """
    return _TOKEN_PATTERN.findall(text.lower())


def build_vocabulary(
    documents: Iterable[str],
    *,
    min_count: int = 1,
    max_vocab_size: int | None = None,
) -> Dict[str, int]:
    """
    Build a token → index vocabulary from a corpus of documents.

    Parameters
    ----------
    documents
        Iterable of raw text documents.
    min_count
        Minimum frequency required for a token to be included.
    max_vocab_size
        Optional cap on vocabulary size (most frequent tokens retained).

    Returns
    -------
    Dict[str, int]
        Mapping from token to integer index.
    """

    counter: Counter[str] = Counter()

    for doc in documents:
        counter.update(tokenize(doc))

    # Filter by minimum count
    tokens = [
        token for token, count in counter.items()
        if count >= min_count
    ]

    # Sort deterministically:
    #   1. descending frequency
    #   2. lexicographically to break ties
    tokens.sort(key=lambda t: (-counter[t], t))

    if max_vocab_size is not None:
        tokens = tokens[:max_vocab_size]

    return {token: idx for idx, token in enumerate(tokens)}
