"""Tests for read-only collection safety guardrails."""

from __future__ import annotations

import pytest
from src.collection.safety import validate_collection_action


def test_validate_collection_action_allows_read_only_action() -> None:
    assert validate_collection_action("manual_snapshot") is True


def test_validate_collection_action_rejects_forbidden_action() -> None:
    with pytest.raises(ValueError, match="Forbidden collection action"):
        validate_collection_action("purchase")


def test_validate_collection_action_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        validate_collection_action("   ")
