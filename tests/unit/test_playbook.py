"""Unit tests for playbook seed payload guidance."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from src.playbook import MIN_KEYWORDS, REQUIRED_SEED_FIELDS, validate_seed_payload_shape


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
    assert MIN_KEYWORDS == 6
    assert validate_seed_payload_shape(payload) is True


def test_missing_niche_id_fails_clearly() -> None:
    payload = {"keywords": ["one", "two", "three", "four", "five", "six"]}
    with pytest.raises(ValueError, match="niche_id"):
        validate_seed_payload_shape(payload)


def test_too_few_keywords_fails_clearly() -> None:
    payload = {"niche_id": "sample", "keywords": ["one", "two", "three", "four", "five"]}
    with pytest.raises(ValueError, match="at least 6"):
        validate_seed_payload_shape(payload)


def test_duplicate_keywords_fail_validation() -> None:
    payload = {
        "niche_id": "prd_ai_saas",
        "keywords": [
            "product requirements document",
            "Product Requirements Document",
            "startup prd writer",
            "mvp roadmap planning",
            "feature prioritization consultant",
            "product strategy documentation",
        ],
    }
    with pytest.raises(ValueError, match="Duplicate keywords"):
        validate_seed_payload_shape(payload)


def test_invalid_niche_id_characters_fail_validation() -> None:
    payload = {
        "niche_id": "PRD-AI-SAAS",
        "keywords": ["one", "two", "three", "four", "five", "six"],
    }
    with pytest.raises(ValueError, match="niche_id must match"):
        validate_seed_payload_shape(payload)


def test_seed_data_guide_yaml_examples_are_valid_if_pyyaml_available() -> None:
    doc_path = Path("docs/SEED_DATA_GUIDE.md")
    content = doc_path.read_text(encoding="utf-8")
    yaml_blocks = re.findall(r"```yaml\n(.*?)```", content, flags=re.DOTALL)
    assert len(yaml_blocks) >= 1

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        assert "Valid payload example" in content
        return

    loaded = [yaml.safe_load(block) for block in yaml_blocks]
    assert all(isinstance(item, dict) for item in loaded)

