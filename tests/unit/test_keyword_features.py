"""Unit tests for keyword feature engineering helpers."""

from __future__ import annotations

import pytest
from src.analysis.keyword_features import (
    KeywordFeatureError,
    build_keyword_feature_set,
    build_lexical_features,
    extract_tokens,
    normalize_keyword,
    vectorize_keywords,
)


def test_normalize_keyword_and_extract_tokens_are_deterministic() -> None:
    normalized = normalize_keyword("  Logo   Design 2026  ")
    assert normalized == "logo design 2026"
    assert extract_tokens(normalized) == ("logo", "design", "2026")


def test_build_lexical_features_includes_expected_shape() -> None:
    features = build_lexical_features("SEO audit 24/7")
    assert features["normalized"] == "seo audit 24/7"
    assert features["token_count"] == 4
    assert features["has_digits"] is True


def test_build_lexical_features_rejects_empty_or_non_alphanumeric_keyword() -> None:
    with pytest.raises(KeywordFeatureError, match="empty"):
        build_lexical_features("   ")
    with pytest.raises(KeywordFeatureError, match="alphanumeric"):
        build_lexical_features("!!!")


def test_build_keyword_feature_set_collects_warnings_for_bad_keywords() -> None:
    features, warnings = build_keyword_feature_set(["logo design", "!!!"], source_id="unit-test")
    assert len(features) == 1
    assert len(warnings) == 1
    assert warnings[0].code == "keyword_feature_warning"
    assert warnings[0].missing_data_fields == ["keywords[1]"]


def test_vectorize_keywords_returns_vectors_vocab_and_warnings() -> None:
    vectors, vocabulary, warnings = vectorize_keywords(["logo design", "logo mockup"], source_id="source")
    assert vocabulary == ["design", "logo", "mockup"]
    assert len(vectors) == 2
    assert warnings == []
    assert vectors[0] == [0.5, 0.5, 0.0]


def test_vectorize_keywords_handles_all_invalid_keywords() -> None:
    vectors, vocabulary, warnings = vectorize_keywords(["!!!"], source_id="source")
    assert vectors == []
    assert vocabulary == []
    assert len(warnings) == 1
