"""Deterministic keyword normalization and local feature generation."""

from __future__ import annotations

import re
from typing import Any

from src.analysis.contracts import AnalysisWarning

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - dependency is available in project.
    np = None  # type: ignore[assignment]

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class KeywordFeatureError(ValueError):
    """Raised when a keyword cannot be transformed into features."""


def normalize_keyword(text: str) -> str:
    """Normalize text for deterministic local keyword analysis."""
    compact = " ".join(text.strip().lower().split())
    normalized = re.sub(r"\s+", " ", compact)
    return normalized


def extract_tokens(keyword_text: str) -> tuple[str, ...]:
    """Extract alphanumeric tokens from normalized keyword text."""
    return tuple(_TOKEN_PATTERN.findall(keyword_text))


def build_lexical_features(keyword: str) -> dict[str, Any]:
    """Build lexical features for a single keyword."""
    normalized = normalize_keyword(keyword)
    if not normalized:
        raise KeywordFeatureError("Keyword is empty after normalization.")

    tokens = extract_tokens(normalized)
    if not tokens:
        raise KeywordFeatureError("Keyword does not contain alphanumeric tokens.")

    token_lengths = [len(token) for token in tokens]
    avg_token_length = sum(token_lengths) / len(token_lengths)

    return {
        "original": keyword,
        "normalized": normalized,
        "tokens": list(tokens),
        "token_count": len(tokens),
        "character_count": len(normalized),
        "average_token_length": round(avg_token_length, 4),
        "has_digits": any(char.isdigit() for char in normalized),
    }


def build_keyword_feature_set(
    keywords: list[str], *, source_id: str
) -> tuple[list[dict[str, Any]], list[AnalysisWarning]]:
    """Create feature records and warnings for a keyword list."""
    features: list[dict[str, Any]] = []
    warnings: list[AnalysisWarning] = []

    for index, keyword in enumerate(keywords):
        try:
            features.append(build_lexical_features(keyword))
        except KeywordFeatureError as exc:
            warnings.append(
                AnalysisWarning(
                    code="keyword_feature_warning",
                    message=str(exc),
                    source_id=source_id,
                    missing_data_fields=[f"keywords[{index}]"],
                    metadata={"keyword": keyword},
                )
            )
    return features, warnings


def vectorize_keywords(
    keywords: list[str], *, source_id: str
) -> tuple[list[list[float]], list[str], list[AnalysisWarning]]:
    """
    Build deterministic bag-of-words vectors.

    Returns tuple(vectors, vocabulary, warnings).
    """
    feature_records, warnings = build_keyword_feature_set(keywords, source_id=source_id)
    token_sets = [record["tokens"] for record in feature_records]
    vocabulary = sorted({token for tokens in token_sets for token in tokens})

    if not token_sets:
        return [], vocabulary, warnings

    vector_rows: list[list[float]] = []
    for tokens in token_sets:
        token_count = len(tokens)
        counts = {token: 0 for token in vocabulary}
        for token in tokens:
            counts[token] += 1
        vector_rows.append([counts[token] / token_count for token in vocabulary])

    if np is not None:
        matrix = np.array(vector_rows, dtype=float)
        return matrix.tolist(), vocabulary, warnings

    return vector_rows, vocabulary, warnings
