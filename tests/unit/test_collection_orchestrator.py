"""Unit tests for collection orchestrator dry-run wiring."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

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
        "stage06a_google_trends",
        "stage06b_reddit_signals",
        "stage06c_youtube_count",
        "stage08_autocomplete",
        "stage09_keyword_clustering",
        "stage10_competitor_profiling",
        "stage11_gig_quality_analysis",
        "stage12_review_analysis",
        "stage13_saturation_analysis",
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


def test_orchestrator_scrapfly_disabled_uses_playwright_fetcher(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel_fetcher = object()
    session_manager = object()

    monkeypatch.setattr(
        "src.collection.workflows.niche_init.run_niche_initialization",
        AsyncMock(return_value={"niches_processed": 0, "niche_specs": []}),
    )
    stage3_mock = AsyncMock(return_value={})
    stage4_mock = AsyncMock(return_value={})
    stage5_mock = AsyncMock(return_value={})
    monkeypatch.setattr("src.collection.workflows.fiverr_search.run_fiverr_search_collection", stage3_mock)
    monkeypatch.setattr("src.collection.workflows.gig_detail.run_gig_detail_collection", stage4_mock)
    monkeypatch.setattr("src.collection.workflows.seller_profile.run_seller_profile_collection", stage5_mock)
    monkeypatch.setattr(
        "src.collection.workflows.autocomplete.run_autocomplete_collection",
        AsyncMock(return_value={}),
    )

    build_fetcher_mock = Mock(return_value=sentinel_fetcher)
    scrapfly_ctor = Mock()
    monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", build_fetcher_mock)
    monkeypatch.setattr("src.collection.scrapfly_client.ScrapFlyClient", scrapfly_ctor)

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-sf-disabled",
            db={},
            config={"collection": {"scrapfly": {"enabled": False}}, "niches": []},
            session_manager=session_manager,
            dry_run=False,
        )
    )

    assert result["errors"] == []
    scrapfly_ctor.assert_not_called()
    build_fetcher_mock.assert_called_once()
    assert build_fetcher_mock.call_args.kwargs["session_manager"] is session_manager
    assert build_fetcher_mock.call_args.kwargs["scrapfly_client"] is None
    assert build_fetcher_mock.call_args.kwargs["prefer_scrapfly"] is False
    stage3_call = stage3_mock.await_args
    stage4_call = stage4_mock.await_args
    stage5_call = stage5_mock.await_args
    assert stage3_call is not None
    assert stage4_call is not None
    assert stage5_call is not None
    assert stage3_call.kwargs["fetcher"] is sentinel_fetcher
    assert stage4_call.kwargs["fetcher"] is sentinel_fetcher
    assert stage5_call.kwargs["fetcher"] is sentinel_fetcher
    assert stage3_call.kwargs["dry_run"] is False
    assert stage4_call.kwargs["dry_run"] is False
    assert stage5_call.kwargs["dry_run"] is False
    assert stage4_call.kwargs["config"] == {"collection": {"scrapfly": {"enabled": False}}, "niches": []}


def test_orchestrator_scrapfly_enabled_uses_scrapfly_fetcher(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel_fetcher = object()
    session_manager = object()

    monkeypatch.setattr(
        "src.collection.workflows.niche_init.run_niche_initialization",
        AsyncMock(return_value={"niches_processed": 0, "niche_specs": []}),
    )
    stage3_mock = AsyncMock(return_value={})
    stage4_mock = AsyncMock(return_value={})
    stage5_mock = AsyncMock(return_value={})
    monkeypatch.setattr("src.collection.workflows.fiverr_search.run_fiverr_search_collection", stage3_mock)
    monkeypatch.setattr("src.collection.workflows.gig_detail.run_gig_detail_collection", stage4_mock)
    monkeypatch.setattr("src.collection.workflows.seller_profile.run_seller_profile_collection", stage5_mock)
    monkeypatch.setattr(
        "src.collection.workflows.autocomplete.run_autocomplete_collection",
        AsyncMock(return_value={}),
    )

    build_fetcher_mock = Mock(return_value=sentinel_fetcher)
    sf_client = Mock()
    sf_client.open = AsyncMock()
    sf_client.close = AsyncMock()
    sf_client.stats = SimpleNamespace(total_requests=3, total_credits_used=75)
    scrapfly_ctor = Mock(return_value=sf_client)
    monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", build_fetcher_mock)
    monkeypatch.setattr("src.collection.scrapfly_client.ScrapFlyClient", scrapfly_ctor)

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-sf-enabled",
            db={},
            config={"collection": {"scrapfly": {"enabled": True}}, "niches": []},
            session_manager=session_manager,
            dry_run=False,
        )
    )

    assert result["errors"] == []
    scrapfly_ctor.assert_called_once()
    sf_config = scrapfly_ctor.call_args.args[0]
    assert sf_config.api_key_env_var == "SCRAPFLY_API_KEY"
    sf_client.open.assert_awaited_once()
    sf_client.close.assert_awaited_once()
    build_fetcher_mock.assert_called_once()
    assert build_fetcher_mock.call_args.kwargs["scrapfly_client"] is sf_client
    assert build_fetcher_mock.call_args.kwargs["prefer_scrapfly"] is True
    stage3_call = stage3_mock.await_args
    stage4_call = stage4_mock.await_args
    stage5_call = stage5_mock.await_args
    assert stage3_call is not None
    assert stage4_call is not None
    assert stage5_call is not None
    assert stage3_call.kwargs["fetcher"] is sentinel_fetcher
    assert stage4_call.kwargs["fetcher"] is sentinel_fetcher
    assert stage5_call.kwargs["fetcher"] is sentinel_fetcher
    assert stage3_call.kwargs["dry_run"] is False
    assert stage4_call.kwargs["dry_run"] is False
    assert stage5_call.kwargs["dry_run"] is False
    assert stage4_call.kwargs["config"] == {"collection": {"scrapfly": {"enabled": True}}, "niches": []}


def test_orchestrator_dry_run_never_opens_scrapfly_client(monkeypatch: pytest.MonkeyPatch) -> None:
    build_fetcher_mock = Mock(return_value=object())
    sf_client = Mock()
    sf_client.open = AsyncMock()
    scrapfly_ctor = Mock(return_value=sf_client)
    monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", build_fetcher_mock)
    monkeypatch.setattr("src.collection.scrapfly_client.ScrapFlyClient", scrapfly_ctor)

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-sf-dry",
            db={},
            config={"collection": {"scrapfly": {"enabled": True}}, "niches": []},
            session_manager=object(),
            dry_run=True,
        )
    )

    assert result["errors"] == []
    scrapfly_ctor.assert_not_called()
    build_fetcher_mock.assert_not_called()


def test_collect_only_cli_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_module, "run_pipeline", lambda **_kwargs: 0)
    runner = CliRunner()
    result = runner.invoke(run_module.cli, ["collect-only", "--config-path", "config.yaml"])
    assert result.exit_code == 0


def test_collect_only_does_not_break_with_new_cli_modes(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_run_pipeline(**kwargs: Any) -> int:
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(run_module, "run_pipeline", _fake_run_pipeline)
    runner = CliRunner()
    result = runner.invoke(run_module.cli, ["collect-only", "--config-path", "config.yaml"])

    assert result.exit_code == 0
    assert captured["mode"] == "collect-only"


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


def test_all_stage6_signals_registered() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage6-registered",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "stage06a_google_trends" in result["stages_run"]
    assert "stage06b_reddit_signals" in result["stages_run"]
    assert "stage06c_youtube_count" in result["stages_run"]


def test_orchestrator_stage_sequence_correct() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage-sequence",
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
        "stage06a_google_trends",
        "stage06b_reddit_signals",
        "stage06c_youtube_count",
        "stage08_autocomplete",
        "stage09_keyword_clustering",
        "stage10_competitor_profiling",
        "stage11_gig_quality_analysis",
        "stage12_review_analysis",
        "stage13_saturation_analysis",
    ]


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


def test_stage10_registered_in_pipeline() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage10-registered",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "stage10_competitor_profiling" in result["stages_run"]


def test_stage10_after_stage5() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage10-order",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    stage_order = result["stages_run"]
    assert stage_order.index("stage10_competitor_profiling") > stage_order.index("stage05_seller_profile")


def test_stage11_registered() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage11-registered",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "stage11_gig_quality_analysis" in result["stages_run"]


def test_stage11_runs_after_stage5() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage11-order",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    stage_order = result["stages_run"]
    assert stage_order.index("stage11_gig_quality_analysis") > stage_order.index("stage05_seller_profile")


def test_stage12_registered() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage12-registered",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "stage12_review_analysis" in result["stages_run"]


def test_stage12_runs_after_stage4() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage12-order",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    stage_order = result["stages_run"]
    assert stage_order.index("stage12_review_analysis") > stage_order.index("stage04_gig_detail")


def test_stage13_registered() -> None:
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage13-registered",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=True,
        )
    )
    assert "stage13_saturation_analysis" in result["stages_run"]


def test_stage13_errors_are_captured_in_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom(**_kwargs: Any) -> dict[str, Any]:
        raise RuntimeError("stage13 boom")

    monkeypatch.setattr("src.analysis.saturation_model.run_saturation_analysis_for_niche", _boom)
    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-stage13-error",
            db={},
            config={"niches": [{"niche_id": "seo", "seed_keywords": ["seo audit"]}]},
            session_manager=None,
            dry_run=True,
        )
    )
    assert result["saturation_analysis_niches_run"] == 0
    assert any("Stage 13 error (seo): stage13 boom" in error for error in result["errors"])


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
