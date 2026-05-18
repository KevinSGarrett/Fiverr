"""Unit tests for Stage 1-5 collection orchestrator dry-run wiring."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
import run as run_module
from click.testing import CliRunner
from src.collection import orchestrator as collection_orchestrator


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_run_collection_dry_run_returns_summary() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-summary",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert isinstance(result, dict)
    assert result["run_id"] == "run-summary"


def test_run_collection_dry_run_stages_run() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stages",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert result["stages_run"] == [
        "stage01_niche_init",
        "stage02_keyword_expansion",
        "stage03_fiverr_search",
        "stage04_gig_detail",
        "stage05_seller_profile",
    ]


def test_run_collection_dry_run_no_errors() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-no-errors",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert result["errors"] == []


def test_run_collection_raises_without_dry_run() -> None:
    with pytest.raises(NotImplementedError):
        _run(
            collection_orchestrator.run_collection_pipeline(
                run_id="run-non-dry",
                db={},
                config={},
                session_manager=None,
                dry_run=False,
            )
        )


def test_collect_only_cli_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: 0)
    runner = CliRunner()
    result = runner.invoke(run_module.cli, ["collect-only", "--config-path", "config.yaml"])
    assert result.exit_code == 0


def test_run_collection_niches_processed() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-niches",
            db={},
            config={"niches": [{"niche_id": "logo", "seed_keywords": ["logo design"]}]},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "niches_initialized" in result
    assert result["niches_initialized"] == 1


def test_run_collection_stages_list() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage-list",
            db={},
            config={},
            session_manager=None,
            dry_run=True,
        )
    )
    assert isinstance(result["stages_run"], list)
    assert len(result["stages_run"]) >= 1


def test_orchestrator_checkpoint_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "run-checkpoint"
    _run(
        collection_orchestrator.run_collection_pipeline(
            run_id=run_id,
            db={},
            config={"niches": [{"niche_id": "seo", "seed_keywords": ["seo audit"]}]},
            session_manager=None,
            dry_run=True,
        )
    )
    checkpoint_path = tmp_path / "data" / "checkpoints" / run_id / "stage01_all_niches.json"
    assert checkpoint_path.exists()


def test_orchestrator_handles_stage1_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("stage1 broke")

    monkeypatch.setattr("src.collection.workflows.niche_init.run_niche_initialization", _boom)
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage1-error",
            db={},
            config={},
            session_manager=None,
            dry_run=True,
        )
    )
    assert any("Stage 1 error: stage1 broke" in error for error in result["errors"])
    assert "stage05_seller_profile" in result["stages_run"]


def test_orchestrator_session_manager_none() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-no-session",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert result["errors"] == []


def test_run_collection_keywords_queued_accumulates(monkeypatch: pytest.MonkeyPatch) -> None:
    async_mock = AsyncMock(
        return_value={
            "niche_id": "niche_001",
            "keywords_queued": 3,
            "sources": {},
            "dry_run": True,
        }
    )
    monkeypatch.setattr("src.collection.workflows.keyword_expansion.run_keyword_expansion", async_mock)
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-keywords",
            db={},
            config={
                "niches": [
                    {"niche_id": "niche_001", "seed_keywords": ["seo"]},
                    {"niche_id": "niche_002", "seed_keywords": ["logo"]},
                ]
            },
            session_manager=None,
            dry_run=True,
        )
    )
    assert result["keywords_queued"] == 6


def test_run_collection_counts_queue_stage_jobs() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-queue-jobs",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert result["search_jobs_run"] == 1
    assert result["gig_detail_jobs_run"] == 1
    assert result["seller_profile_jobs_run"] == 1
