"""Hashing and similarity utilities — AC-1.6.4, AC-1.6.5."""

from __future__ import annotations

import hashlib


def sha256_hash(text: str) -> str:
    """Return a deterministic 64-character hex SHA-256 digest of *text*.

    Args:
        text: Input string to hash.

    Returns:
        64-character lowercase hex string.

    Examples:
        >>> len(sha256_hash("test"))
        64
        >>> sha256_hash("test") == sha256_hash("test")
        True
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two strings using word-level tokens.

    Tokenises each string on whitespace and punctuation, then computes::

        |intersection| / |union|

    Args:
        a: First string.
        b: Second string.

    Returns:
        Float in [0.0, 1.0] where 1.0 means identical token sets.

    Examples:
        >>> jaccard_similarity("ai saas prd", "ai saas prd")
        1.0
        >>> jaccard_similarity("hello world", "goodbye world")
        0.3333333333333333
        >>> jaccard_similarity("", "")
        1.0
    """
    import re

    def _tokenize(s: str) -> set[str]:
        return set(t.lower() for t in re.split(r"[\s\W]+", s) if t)

    tokens_a = _tokenize(a)
    tokens_b = _tokenize(b)
    if not tokens_a and not tokens_b:
        return 1.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union) if union else 0.0
