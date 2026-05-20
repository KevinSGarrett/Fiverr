"""Unit tests for collection orchestrator dry-run wiring."""

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
        "stage09_keyword_clustering",
        "stage03_fiverr_search",
        "stage04_gig_detail",
        "stage05_seller_profile",
        "stage08_autocomplete",
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


def test_stage9_registered_in_pipeline() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage9-registered",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "stage09_keyword_clustering" in result["stages_run"]


def test_stage9_skipped_at_feasibility_depth() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage9-feasibility",
            db={},
            config={"niches": [{"niche_id": "feasibility-niche", "seed_keywords": ["seed"], "depth": "feasibility"}]},
            session_manager=None,
            dry_run=True,
        )
    )
    assert any(
        entry.get("reason") == "feasibility_depth_skip"
        for entry in result["clustering_results"]
        if isinstance(entry, dict)
    )


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
    assert result["autocomplete_jobs_run"] == 1


def test_dry_run_job_state_transitions() -> None:
    job = collection_orchestrator._DryRunJob(id=1, run_id="run-1", job_type="FIVERR_SEARCH", stage=3)
    job.mark_running()
    job.mark_complete()
    assert job.status == "COMPLETE"
    assert job.started_at is not None
    assert job.completed_at is not None
    assert job.duration_seconds is not None


def test_dry_run_job_mark_failed_non_dead_letter_then_dead_letter() -> None:
    job = collection_orchestrator._DryRunJob(
        id=2,
        run_id="run-2",
        job_type="GIG_DETAIL",
        stage=4,
        max_retries=2,
    )
    job.mark_failed("first")
    assert job.status == "FAILED"
    assert job.should_dead_letter() is False
    job.mark_failed("second")
    assert job.status == "DEAD_LETTER"
    assert job.should_dead_letter() is True


def test_in_memory_queue_db_selects_next_job_and_query_first() -> None:
    queued = collection_orchestrator._DryRunJob(id=9, run_id="run-q", job_type="SELLER_PROFILE", stage=5)
    db = collection_orchestrator._InMemoryQueueDb([queued])
    row = db.execute(None, {"run_id": "run-q"}).mappings().first()
    assert row == {"id": 9}
    selected = db.query(object()).filter().first()
    assert selected is queued
    db.commit()


def test_in_memory_queue_db_returns_none_when_empty() -> None:
    db = collection_orchestrator._InMemoryQueueDb([])
    row = db.execute(None, {"run_id": "missing"}).mappings().first()
    assert row is None
    assert db.query(object()).first() is None


def test_run_collection_pipeline_stage2_error_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("stage2 broke")

    monkeypatch.setattr("src.collection.workflows.keyword_expansion.run_keyword_expansion", _boom)
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage2-error",
            db={},
            config={"niches": [{"niche_id": "niche-1", "seed_keywords": ["seo"]}]},
            session_manager=None,
            dry_run=True,
        )
    )
    assert any("Stage 2 error (niche-1): stage2 broke" in error for error in result["errors"])


def test_run_collection_pipeline_queue_error_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raise_queue_error(self: Any, run_id: str) -> tuple[int, int]:
        _ = (self, run_id)
        raise RuntimeError("queue failed")

    monkeypatch.setattr(
        "src.scheduler.queue_processor.QueueProcessor.run_until_empty",
        _raise_queue_error,
    )
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-queue-error",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert any("Queue processing error: queue failed" in error for error in result["errors"])
