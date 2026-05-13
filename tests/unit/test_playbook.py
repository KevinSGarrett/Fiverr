"""Unit tests for playbook seed payload guidance."""

from __future__ import annotations

import pytest
from src.playbook import REQUIRED_SEED_FIELDS, validate_seed_payload_shape


def test_valid_seed_payload_shape_passes() -> None:
    payload = {
        "niche_id": "prd_ai_saas",
        "keywords": [
            "product requirements document",
            "AI SaaS PRD",
            "MVP roadmap",
            "startup PRD",
            "SaaS planning",
            "feature prioritization",
        ],
    }
    assert REQUIRED_SEED_FIELDS == ["niche_id", "keywords"]
    assert validate_seed_payload_shape(payload) is True


def test_missing_niche_id_fails_clearly() -> None:
    payload = {"keywords": ["one", "two", "three", "four", "five", "six"]}
    with pytest.raises(ValueError, match="niche_id"):
        validate_seed_payload_shape(payload)


def test_too_few_keywords_fails_clearly() -> None:
    payload = {"niche_id": "sample", "keywords": ["one", "two", "three", "four", "five"]}
    with pytest.raises(ValueError, match="6-8"):
        validate_seed_payload_shape(payload)

