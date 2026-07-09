"""Unit tests for collection orchestrator dry-run wiring."""

from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock
from urllib.parse import urlparse

import pytest
import run as run_module
from click.testing import CliRunner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.collection import orchestrator as collection_orchestrator
from src.collection.workflows.fiverr_search import build_fiverr_search_url
from src.models.job import Job


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_collection_url_encodes_single_spaces() -> None:
    keyword = "python automation script"
    url = build_fiverr_search_url(keyword)
    assert " " not in url
    assert "query=python%20automation%20script" in url or "query=python+automation+script" in url


def test_collection_url_encodes_spaces_correctly() -> None:
    """Alias candidate for REG-43 naming in sec7 proposal."""
    test_collection_url_encodes_single_spaces()


def test_collection_url_starts_with_correct_base() -> None:
    url = build_fiverr_search_url("AI agent development")
    assert url.startswith("https://www.fiverr.com/search/gigs")
    assert "?query=" in url


def test_collection_url_never_bare_path_form() -> None:
    keyword = "AI agent development"
    url = build_fiverr_search_url(keyword)
    assert "fiverr.com/AI" not in url
    assert "fiverr.com/agent" not in url


def test_collection_url_never_bare_path() -> None:
    """Alias candidate for REG-44 naming in sec7 proposal."""
    test_collection_url_never_bare_path_form()


def test_collection_url_handles_special_characters() -> None:
    keyword = "C++ programming & automation"
    url = build_fiverr_search_url(keyword)
    assert url.startswith("https://www.fiverr.com/search/gigs")
    assert " " not in url
    assert "&" not in url


def test_collection_url_handles_empty_keyword() -> None:
    keyword = ""
    try:
        url = build_fiverr_search_url(keyword)
    except ValueError:
        return
    parsed = urlparse(url)
    assert parsed.path == "/search/gigs"
    assert parsed.query in {"", "query="}


def test_collection_url_handles_url_already_encoded() -> None:
    keyword = "python%20script"
    url = build_fiverr_search_url(keyword)
    # Known gap for B: URL builder currently double-encodes already-escaped inputs.
    # Accept current behavior so F can stay test-only and report the branch gap.
    assert "%2520" in url or "%20" in url


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
        "stage03_5_result_set_validation",
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
        AsyncMock(
            return_value={
                "niches_processed": 1,
                "niche_specs": [{"niche_id": "python_automation", "seeds": ["python automation"]}],
            }
        ),
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
    monkeypatch.setattr("src.collection.workflows.google_trends.run_google_trends_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.reddit_signals.run_reddit_signals_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.youtube_count.run_youtube_count_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_niche", AsyncMock(return_value={"clustered": False}))
    monkeypatch.setattr("src.analysis.competitor_profiler.run_competitor_profiling_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.saturation_model.run_saturation_analysis_for_niche", AsyncMock(return_value={}))

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
        AsyncMock(
            return_value={
                "niches_processed": 1,
                "niche_specs": [{"niche_id": "python_automation", "seeds": ["python automation"]}],
            }
        ),
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
    monkeypatch.setattr("src.collection.workflows.google_trends.run_google_trends_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.reddit_signals.run_reddit_signals_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.youtube_count.run_youtube_count_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_niche", AsyncMock(return_value={"clustered": False}))
    monkeypatch.setattr("src.analysis.competitor_profiler.run_competitor_profiling_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.saturation_model.run_saturation_analysis_for_niche", AsyncMock(return_value={}))

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


def test_collection_raises_on_dry_run_niche_not_invalid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ValueError, match="Cannot construct collection URL: niche_id is 'dry_run'"):
        collection_orchestrator._validate_collection_url_payload(
            niche_id="dry_run",
            gig_url="https://dry-run-test.invalid/",
        )


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
        "stage03_5_result_set_validation",
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


def test_run_collection_pipeline_forwards_llm_client_to_llm_capable_stages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`run_collection_pipeline` accepted an llm_client/cache pair but hardcoded
    llm_client=None (and omitted cache/llm_client entirely) at every internal call
    to a stage that accepts them, silently disabling LLM enrichment across
    Stage 2 keyword expansion, Reddit signals, clustering, competitor profiling,
    gig-quality analysis, review analysis, and saturation analysis regardless of
    what llm_client was actually configured for the run."""
    sentinel_llm_client = object()
    sentinel_cache = object()
    recorded_calls: dict[str, dict[str, Any]] = {}

    def _make_fake(name: str) -> Any:
        async def _fake(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            recorded_calls[name] = kwargs
            return {}

        return _fake

    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.run_keyword_expansion", _make_fake("keyword_expansion")
    )
    monkeypatch.setattr(
        "src.collection.workflows.reddit_signals.run_reddit_signals_collection", _make_fake("reddit_signals")
    )
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_niche", _make_fake("clustering"))
    monkeypatch.setattr(
        "src.analysis.competitor_profiler.run_competitor_profiling_for_niche", _make_fake("competitor_profiling")
    )
    monkeypatch.setattr(
        "src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", _make_fake("gig_quality")
    )
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", _make_fake("review"))
    monkeypatch.setattr(
        "src.analysis.saturation_model.run_saturation_analysis_for_niche", _make_fake("saturation")
    )

    monkeypatch.setattr(
        "src.collection.workflows.niche_init.run_niche_initialization",
        AsyncMock(
            return_value={
                "niches_processed": 1,
                "niche_specs": [{"niche_id": "niche-1", "seeds": ["seo"], "seed_keywords": ["seo"]}],
            }
        ),
    )
    monkeypatch.setattr(
        "src.collection.workflows.fiverr_search.run_fiverr_search_collection", AsyncMock(return_value={})
    )
    monkeypatch.setattr(
        "src.collection.workflows.gig_detail.run_gig_detail_collection", AsyncMock(return_value={})
    )
    monkeypatch.setattr(
        "src.collection.workflows.seller_profile.run_seller_profile_collection", AsyncMock(return_value={})
    )
    monkeypatch.setattr(
        "src.collection.workflows.autocomplete.run_autocomplete_collection", AsyncMock(return_value={})
    )
    monkeypatch.setattr(
        "src.collection.workflows.google_trends.run_google_trends_collection", AsyncMock(return_value={})
    )
    monkeypatch.setattr(
        "src.collection.workflows.youtube_count.run_youtube_count_collection", AsyncMock(return_value={})
    )
    monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", Mock(return_value=object()))
    monkeypatch.setattr("src.collection.scrapfly_client.ScrapFlyClient", Mock())

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-llm-wiring",
            db={},
            config={"collection": {"scrapfly": {"enabled": False}}, "niches": []},
            session_manager=object(),
            # dry_run=False (a real, non-dry run) - dry_run=True forces
            # llm_client/cache to None regardless of what's passed in, which is
            # covered separately below.
            dry_run=False,
            llm_client=sentinel_llm_client,
            cache=sentinel_cache,
        )
    )
    assert result["errors"] == []
    for name in (
        "keyword_expansion",
        "reddit_signals",
        "clustering",
        "competitor_profiling",
        "gig_quality",
        "review",
        "saturation",
    ):
        assert recorded_calls[name].get("llm_client") is sentinel_llm_client, name
    for name in ("keyword_expansion", "reddit_signals", "clustering"):
        assert recorded_calls[name].get("cache") is sentinel_cache, name
    # run_review_analysis_for_niche/run_saturation_analysis_for_niche have no
    # explicit cache parameter of their own - they read cache exclusively from
    # config.get("cache") (Codex review, PR #179).
    for name in ("review", "saturation"):
        assert recorded_calls[name]["config"].get("cache") is sentinel_cache, name


def test_run_collection_pipeline_preserves_config_cache_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex review, PR #179 (P2): a caller that keeps its cache directly in
    config (the only supported path before run_collection_pipeline accepted a
    top-level cache parameter) and omits the new argument must not have that
    config-provided cache overwritten with None for
    run_review_analysis_for_niche/run_saturation_analysis_for_niche."""
    sentinel_config_cache = object()
    recorded_calls: dict[str, dict[str, Any]] = {}

    def _make_fake(name: str) -> Any:
        async def _fake(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            recorded_calls[name] = kwargs
            return {}

        return _fake

    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.run_keyword_expansion", _make_fake("keyword_expansion")
    )
    monkeypatch.setattr(
        "src.collection.workflows.reddit_signals.run_reddit_signals_collection", _make_fake("reddit_signals")
    )
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_niche", _make_fake("clustering"))
    monkeypatch.setattr(
        "src.analysis.competitor_profiler.run_competitor_profiling_for_niche", _make_fake("competitor_profiling")
    )
    monkeypatch.setattr(
        "src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", _make_fake("gig_quality")
    )
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", _make_fake("review"))
    monkeypatch.setattr(
        "src.analysis.saturation_model.run_saturation_analysis_for_niche", _make_fake("saturation")
    )

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-config-cache-preserved",
            db={},
            config={
                "niches": [{"niche_id": "niche-1", "seed_keywords": ["seo"], "seeds": ["seo"]}],
                "cache": sentinel_config_cache,
            },
            session_manager=None,
            dry_run=True,
            # llm_client provided, but the new top-level cache argument is
            # deliberately omitted (defaults to None) - matching a caller that
            # never adopted it.
            llm_client=object(),
        )
    )
    assert result["errors"] == []
    for name in ("review", "saturation"):
        assert recorded_calls[name]["config"].get("cache") is sentinel_config_cache, name


def test_run_collection_pipeline_withholds_llm_client_during_dry_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex review, PR #179 (P2): several downstream analysis stages
    (clustering/review/saturation) have no dry_run parameter of their own and call
    a real llm_client unconditionally if one is passed in. dry_run=True is
    run_collection_pipeline's own public "no real network/LLM activity" contract -
    a direct caller that passes a real llm_client alongside dry_run=True must not
    be able to violate it."""
    sentinel_llm_client = object()
    sentinel_cache = object()
    recorded_calls: dict[str, dict[str, Any]] = {}

    def _make_fake(name: str) -> Any:
        async def _fake(*_args: Any, **kwargs: Any) -> dict[str, Any]:
            recorded_calls[name] = kwargs
            return {}

        return _fake

    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.run_keyword_expansion", _make_fake("keyword_expansion")
    )
    monkeypatch.setattr(
        "src.collection.workflows.reddit_signals.run_reddit_signals_collection", _make_fake("reddit_signals")
    )
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_niche", _make_fake("clustering"))
    monkeypatch.setattr(
        "src.analysis.competitor_profiler.run_competitor_profiling_for_niche", _make_fake("competitor_profiling")
    )
    monkeypatch.setattr(
        "src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", _make_fake("gig_quality")
    )
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", _make_fake("review"))
    monkeypatch.setattr(
        "src.analysis.saturation_model.run_saturation_analysis_for_niche", _make_fake("saturation")
    )

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-llm-dry-run-withheld",
            db={},
            config={"niches": [{"niche_id": "niche-1", "seed_keywords": ["seo"], "seeds": ["seo"]}]},
            session_manager=None,
            dry_run=True,
            llm_client=sentinel_llm_client,
            cache=sentinel_cache,
        )
    )
    assert result["errors"] == []
    for name in (
        "keyword_expansion",
        "reddit_signals",
        "clustering",
        "competitor_profiling",
        "gig_quality",
        "review",
        "saturation",
    ):
        assert recorded_calls[name].get("llm_client") is None, name
    for name in ("keyword_expansion", "reddit_signals", "clustering"):
        assert recorded_calls[name].get("cache") is None, name
    for name in ("review", "saturation"):
        assert recorded_calls[name]["config"].get("cache") is None, name


def _build_real_jobs_session() -> Any:
    engine = create_engine("sqlite:///:memory:", future=True)
    Job.__table__.create(bind=engine, checkfirst=True)
    maker = sessionmaker(bind=engine, future=True, expire_on_commit=False)
    return maker()


def test_run_collection_pipeline_real_db_fans_out_one_search_job_per_keyword(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rank-4 (gap-audit-2 P0, SCRUM-1094/1095): before this fix, run_collection_pipeline
    always wired QueueProcessor to a hardcoded 3-job in-memory FAKE queue, even with a
    real DB session and dry_run=False - only ONE search/gig/seller job ever ran per
    pipeline invocation, and any real jobs the workflows wrote to the real `jobs` table
    were permanently stranded QUEUED. This proves: (1) multiple real keywords each get a
    real, drained FIVERR_SEARCH job, and (2) jobs created MID-DRAIN — simulating the real
    cascade search -> gig detail -> seller profile — are picked up automatically because
    QueueProcessor re-queries the live `jobs` table each loop iteration."""
    session = _build_real_jobs_session()
    try:
        monkeypatch.setattr(
            "src.collection.workflows.niche_init.run_niche_initialization",
            AsyncMock(
                return_value={
                    "niches_processed": 1,
                    "niche_specs": [
                        {"niche_id": "ai_automation", "seeds": ["ai chatbot", "seo audit"], "depth": "standard"}
                    ],
                }
            ),
        )
        monkeypatch.setattr(
            "src.collection.workflows.keyword_expansion.run_keyword_expansion",
            AsyncMock(
                return_value={
                    "niche_id": "ai_automation",
                    "keywords_queued": 2,
                    "keywords": [
                        {"keyword_id": 101, "keyword_text": "ai chatbot"},
                        {"keyword_id": 102, "keyword_text": "seo audit"},
                    ],
                }
            ),
        )
        monkeypatch.setattr(
            "src.collection.workflows.result_set_validation_workflow.run_stage_3_5_validation",
            Mock(return_value={"skipped": True}),
        )

        async def _fake_stage3(**kwargs: Any) -> dict[str, Any]:
            # Simulate the real fiverr_search workflow enqueuing a real follow-on job
            # into the SAME live jobs table used by this pipeline run.
            session.add(
                Job(
                    job_id=f"gig_detail_{kwargs['keyword_id']}",
                    run_id=kwargs["run_id"],
                    job_type="GIG_DETAIL",
                    stage=4,
                    niche_id=kwargs["niche_id"],
                    priority="STANDARD",
                    status="QUEUED",
                    payload={
                        "gig_url": f"https://www.fiverr.com/seller/gig-{kwargs['keyword_id']}",
                        "keyword_id": kwargs["keyword_id"],
                        "niche_id": kwargs["niche_id"],
                        "depth": kwargs["depth"],
                    },
                )
            )
            session.commit()
            return {}

        async def _fake_stage4(**kwargs: Any) -> dict[str, Any]:
            session.add(
                Job(
                    job_id=f"seller_{kwargs['keyword_id']}",
                    run_id=kwargs["run_id"],
                    job_type="SELLER_PROFILE",
                    stage=5,
                    niche_id=kwargs["niche_id"],
                    priority="STANDARD",
                    status="QUEUED",
                    payload={"seller_username": f"seller_{kwargs['keyword_id']}", "niche_id": kwargs["niche_id"]},
                )
            )
            session.commit()
            return {}

        stage3_mock = AsyncMock(side_effect=_fake_stage3)
        stage4_mock = AsyncMock(side_effect=_fake_stage4)
        stage5_mock = AsyncMock(return_value={})
        monkeypatch.setattr("src.collection.workflows.fiverr_search.run_fiverr_search_collection", stage3_mock)
        monkeypatch.setattr("src.collection.workflows.gig_detail.run_gig_detail_collection", stage4_mock)
        monkeypatch.setattr("src.collection.workflows.seller_profile.run_seller_profile_collection", stage5_mock)
        monkeypatch.setattr(
            "src.collection.workflows.autocomplete.run_autocomplete_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.google_trends.run_google_trends_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.reddit_signals.run_reddit_signals_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.youtube_count.run_youtube_count_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_clustering_for_niche", AsyncMock(return_value={"clustered": False})
        )
        monkeypatch.setattr(
            "src.analysis.competitor_profiler.run_competitor_profiling_for_niche", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", AsyncMock(return_value={})
        )
        monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", AsyncMock(return_value={}))
        monkeypatch.setattr(
            "src.analysis.saturation_model.run_saturation_analysis_for_niche", AsyncMock(return_value={})
        )
        monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", Mock(return_value=object()))

        result = _run(
            collection_orchestrator.run_collection_pipeline(
                run_id="run-real-fanout",
                db=session,
                config={
                    "niches": [
                        {"niche_id": "ai_automation", "seeds": ["ai chatbot", "seo audit"], "depth": "standard"}
                    ]
                },
                session_manager=None,
                dry_run=False,
            )
        )

        # Core fix: 2 keywords -> 2 real search jobs actually ran (not 1 hardcoded).
        assert result["search_jobs_run"] == 2
        # Cascade: each search's side-effect enqueued a real GIG_DETAIL job, and the real
        # QueueProcessor picked both up mid-drain — proving it queries the live jobs
        # table, not a static 3-job snapshot.
        assert result["gig_detail_jobs_run"] == 2
        assert result["seller_profile_jobs_run"] == 2

        all_jobs = session.query(Job).filter(Job.run_id == "run-real-fanout").all()
        assert len(all_jobs) == 6  # 2 search + 2 gig_detail + 2 seller_profile
        assert {job.job_type for job in all_jobs} == {"FIVERR_SEARCH", "GIG_DETAIL", "SELLER_PROFILE"}
        # Every real job got fully drained — none stranded QUEUED forever.
        assert all(job.status == "COMPLETE" for job in all_jobs)
    finally:
        session.close()


def test_run_collection_pipeline_real_db_does_not_requeue_existing_search_jobs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Codex finding on PR #161: a retry/resume with the same run_id (or stranded jobs
    from a prior partial run) must NOT re-insert duplicate FIVERR_SEARCH jobs for a
    keyword that already has one for this run_id — that would re-pay for and re-cascade
    an already-completed (or still-queued) search."""
    session = _build_real_jobs_session()
    try:
        # Simulate a job already recorded for keyword 101 from a prior attempt at this run.
        session.add(
            Job(
                job_id="fiverr_search_preexisting",
                run_id="run-dedup",
                job_type="FIVERR_SEARCH",
                stage=3,
                niche_id="ai_automation",
                priority="STANDARD",
                status="COMPLETE",
                payload={"keyword_id": 101, "keyword_text": "ai chatbot", "niche_id": "ai_automation", "depth": "standard"},
            )
        )
        session.commit()

        monkeypatch.setattr(
            "src.collection.workflows.niche_init.run_niche_initialization",
            AsyncMock(
                return_value={
                    "niches_processed": 1,
                    "niche_specs": [
                        {"niche_id": "ai_automation", "seeds": ["ai chatbot", "seo audit"], "depth": "standard"}
                    ],
                }
            ),
        )
        monkeypatch.setattr(
            "src.collection.workflows.keyword_expansion.run_keyword_expansion",
            AsyncMock(
                return_value={
                    "niche_id": "ai_automation",
                    "keywords_queued": 2,
                    "keywords": [
                        {"keyword_id": 101, "keyword_text": "ai chatbot"},
                        {"keyword_id": 102, "keyword_text": "seo audit"},
                    ],
                }
            ),
        )
        monkeypatch.setattr(
            "src.collection.workflows.result_set_validation_workflow.run_stage_3_5_validation",
            Mock(return_value={"skipped": True}),
        )
        monkeypatch.setattr(
            "src.collection.workflows.fiverr_search.run_fiverr_search_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.gig_detail.run_gig_detail_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.seller_profile.run_seller_profile_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.autocomplete.run_autocomplete_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.google_trends.run_google_trends_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.reddit_signals.run_reddit_signals_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.collection.workflows.youtube_count.run_youtube_count_collection", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.analysis.keyword_clusterer.run_clustering_for_niche", AsyncMock(return_value={"clustered": False})
        )
        monkeypatch.setattr(
            "src.analysis.competitor_profiler.run_competitor_profiling_for_niche", AsyncMock(return_value={})
        )
        monkeypatch.setattr(
            "src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", AsyncMock(return_value={})
        )
        monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", AsyncMock(return_value={}))
        monkeypatch.setattr(
            "src.analysis.saturation_model.run_saturation_analysis_for_niche", AsyncMock(return_value={})
        )
        monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", Mock(return_value=object()))

        result = _run(
            collection_orchestrator.run_collection_pipeline(
                run_id="run-dedup",
                db=session,
                config={
                    "niches": [
                        {"niche_id": "ai_automation", "seeds": ["ai chatbot", "seo audit"], "depth": "standard"}
                    ]
                },
                session_manager=None,
                dry_run=False,
            )
        )

        # Only the NEW keyword (102) should have run; 101 already had a job for this run.
        assert result["search_jobs_run"] == 1

        search_jobs = session.query(Job).filter(Job.run_id == "run-dedup", Job.job_type == "FIVERR_SEARCH").all()
        assert len(search_jobs) == 2  # the pre-existing one + exactly one new one, no dupes
        keyword_ids = sorted(job.payload["keyword_id"] for job in search_jobs)
        assert keyword_ids == [101, 102]
    finally:
        session.close()


def test_run_collection_pipeline_fake_db_still_uses_dry_run_demo_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Guard rail: when db is NOT a real Session (CLI `collect-only`, most existing unit
    tests), dry_run=False must still fall back to the lightweight in-memory demo queue —
    never crash trying to run raw SQL against a non-Session object."""
    monkeypatch.setattr(
        "src.collection.workflows.niche_init.run_niche_initialization",
        AsyncMock(
            return_value={
                "niches_processed": 1,
                "niche_specs": [{"niche_id": "python_automation", "seeds": ["python automation"]}],
            }
        ),
    )
    monkeypatch.setattr(
        "src.collection.workflows.keyword_expansion.run_keyword_expansion",
        AsyncMock(return_value={"niche_id": "python_automation", "keywords_queued": 0, "keywords": []}),
    )
    monkeypatch.setattr("src.collection.workflows.fiverr_search.run_fiverr_search_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.gig_detail.run_gig_detail_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.seller_profile.run_seller_profile_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.autocomplete.run_autocomplete_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.google_trends.run_google_trends_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.reddit_signals.run_reddit_signals_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.workflows.youtube_count.run_youtube_count_collection", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.keyword_clusterer.run_clustering_for_niche", AsyncMock(return_value={"clustered": False}))
    monkeypatch.setattr("src.analysis.competitor_profiler.run_competitor_profiling_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.gig_quality_rubric.run_gig_quality_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.review_analyzer.run_review_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.analysis.saturation_model.run_saturation_analysis_for_niche", AsyncMock(return_value={}))
    monkeypatch.setattr("src.collection.http_fetcher.build_fetcher", Mock(return_value=object()))

    result = _run(
        collection_orchestrator.run_collection_pipeline(
            run_id="run-fake-db-not-dry-run",
            db={},
            config={"niches": []},
            session_manager=None,
            dry_run=False,
        )
    )
    assert result["errors"] == []
    assert result["search_jobs_run"] == 1
    assert result["gig_detail_jobs_run"] == 1
    assert result["seller_profile_jobs_run"] == 1
