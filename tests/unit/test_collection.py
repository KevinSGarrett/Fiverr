"""Unit tests for collection package foundation scaffolding."""

import importlib
from datetime import UTC, datetime
from types import ModuleType

import pytest
from src.collection import CollectionStageResult
from src.collection.contracts import CollectionStageStatus
from src.collection.playwright_check import (
    INSTALL_COMMAND,
    check_playwright_chromium_available,
)
from src.collection.safety import validate_collection_action


def test_collection_package_and_exports_are_importable() -> None:
    module = importlib.import_module("src.collection")
    assert module is not None
    assert CollectionStageResult.__name__ == "CollectionStageResult"


def test_collection_stage_result_model_dump() -> None:
    result = CollectionStageResult(
        stage_name="seed_stage",
        status=CollectionStageStatus.SUCCESS,
        records_seen=12,
        records_written=10,
        warnings=["sample warning"],
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        metadata={"batch_id": "batch-001"},
    )

    payload = result.model_dump()
    assert payload["stage_name"] == "seed_stage"
    assert payload["records_seen"] == 12
    assert payload["metadata"]["batch_id"] == "batch-001"


def test_playwright_checker_import_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_import_error(name: str) -> ModuleType:
        raise ImportError(f"module not found: {name}")

    monkeypatch.setattr("src.collection.playwright_check.importlib.import_module", _raise_import_error)

    result = check_playwright_chromium_available()
    assert result["available"] is False
    assert result["needs_install"] is True
    assert result["command"] == INSTALL_COMMAND
    assert "not importable" in str(result["message"]).lower()


def test_playwright_checker_import_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def _import_ok(name: str) -> ModuleType:
        return ModuleType(name)

    monkeypatch.setattr("src.collection.playwright_check.importlib.import_module", _import_ok)

    result = check_playwright_chromium_available()
    assert result["available"] is True
    assert result["needs_install"] is False
    assert result["command"] == INSTALL_COMMAND
    assert "importable" in str(result["message"]).lower()


def test_validate_collection_action_allows_read_only_action() -> None:
    assert validate_collection_action("view_search_results") is True


def test_validate_collection_action_blocks_forbidden_mutation() -> None:
    with pytest.raises(ValueError, match="Forbidden collection action"):
        validate_collection_action("purchase")
