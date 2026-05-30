"""Extended matrix tests for Devvit bridge normalization and PII safety."""

from __future__ import annotations

from typing import Any

import pytest
from src.collection.workflows.reddit_devvit_bridge import (
    normalize_devvit_payload,
    strip_pii_fields,
    validate_devvit_payload,
)


def _base_payload() -> dict[str, Any]:
    return {
        "schema_version": "reddit_devvit_signal_v1",
        "niche_id": "support_kb_readiness",
        "keywords": ["AI chatbot handoff"],
        "subreddits_searched": ["OpenAI"],
        "posts_collected": 1,
        "post_count_90d": 1,
        "reddit_top_snippets": [{"post_id": "t3_1", "title": "example", "upvotes": 1}],
        "reddit_post_count_90d": 1,
    }


@pytest.mark.parametrize(
    "field_name",
    [
        "username",
        "user",
        "author",
        "author_id",
        "profile_url",
        "private_email",
        "account_id",
        "private_message",
        "saved_posts",
        "vote_history",
    ],
)
def test_strip_pii_removes_all_root_level_fields(field_name: str) -> None:
    payload = _base_payload()
    payload[field_name] = "sensitive"
    stripped = strip_pii_fields(payload)
    assert field_name not in stripped


@pytest.mark.parametrize(
    "field_name",
    [
        "username",
        "user",
        "author",
        "author_id",
        "profile_url",
        "private_email",
        "account_id",
        "private_message",
        "saved_posts",
        "vote_history",
    ],
)
def test_strip_pii_removes_all_snippet_level_fields(field_name: str) -> None:
    payload = _base_payload()
    payload["reddit_top_snippets"][0][field_name] = "sensitive"
    stripped = strip_pii_fields(payload)
    assert field_name not in stripped["reddit_top_snippets"][0]


@pytest.mark.parametrize(
    "raw_value,expected",
    [
        (None, 0),
        ("0", 0),
        ("1", 1),
        ("8", 8),
        ("999", 999),
        (0, 0),
        (4, 4),
        (12, 12),
        (12.9, 12),
        ("12.9", 0),
        ("bad", 0),
        (object(), 0),
    ],
)
def test_normalize_reddit_post_count_matrix(raw_value: Any, expected: int) -> None:
    payload = _base_payload()
    payload["reddit_post_count_90d"] = raw_value
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_post_count_90d"] == expected


@pytest.mark.parametrize(
    "raw_value,expected",
    [
        (None, None),
        (0, 0.0),
        (1, 1.0),
        (5.5, 5.5),
        ("7.25", 7.25),
        ("0", 0.0),
        ("bad", None),
        ({}, None),
        ([], None),
        (object(), None),
    ],
)
def test_normalize_reddit_demand_intent_score_matrix(raw_value: Any, expected: float | None) -> None:
    payload = _base_payload()
    payload["reddit_demand_intent_score"] = raw_value
    normalized = normalize_devvit_payload(payload)
    assert normalized["reddit_demand_intent_score"] == expected


@pytest.mark.parametrize("snippet_value", [None, {}, "bad", 123, ["ok"], [{"post_id": "t3_valid"}]])
def test_normalize_snippet_shape_matrix(snippet_value: Any) -> None:
    payload = _base_payload()
    payload["reddit_top_snippets"] = snippet_value
    normalized = normalize_devvit_payload(payload)
    if isinstance(snippet_value, list):
        assert normalized["reddit_top_snippets"] == snippet_value
    else:
        assert normalized["reddit_top_snippets"] == []


@pytest.mark.parametrize(
    "missing_key",
    [
        "niche_id",
        "keywords",
        "subreddits_searched",
        "posts_collected",
        "post_count_90d",
        "reddit_top_snippets",
    ],
)
def test_validate_payload_missing_required_key_matrix(missing_key: str) -> None:
    payload = _base_payload()
    payload.pop(missing_key, None)
    valid, errors = validate_devvit_payload(payload)
    assert valid is False
    assert any(missing_key in error for error in errors)


@pytest.mark.parametrize("schema_version", ["reddit_devvit_signal_v1", "v2", "", None])
def test_validate_schema_version_matrix(schema_version: Any) -> None:
    payload = _base_payload()
    payload["schema_version"] = schema_version
    valid, _ = validate_devvit_payload(payload)
    assert valid is (schema_version == "reddit_devvit_signal_v1")


def test_strip_pii_never_mutates_original_payload() -> None:
    payload = _base_payload()
    payload["reddit_top_snippets"][0]["author"] = "secret"
    stripped = strip_pii_fields(payload)
    assert "author" in payload["reddit_top_snippets"][0]
    assert "author" not in stripped["reddit_top_snippets"][0]
