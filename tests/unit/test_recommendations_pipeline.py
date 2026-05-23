"""Unit tests for Stage 14 recommendations pipeline orchestration."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

import src.orchestrator as orchestrator
import src.recommendations.pipeline as recommendations_pipeline
from src.recommendations.contracts import RecommendationContext
from src.recommendations.schemas import RecommendationOutput


def _keyword_row(
    keyword_id: int,
    *,
    final_score: float = 80.0,
    confidence_modifier: float = 0.8,
    niche_id: str = "1",
) -> dict[str, Any]:
    return {
        "keyword_id": keyword_id,
        "keyword_text": f"keyword-{keyword_id}",
        "niche_id": niche_id,
        "tag": "STRONG GO",
        "final_score": final_score,
        "confidence_modifier": confidence_modifier,
    }


def _context(keyword_id: int) -> RecommendationContext:
    return RecommendationContext(
        keyword_id=keyword_id,
        keyword_text=f"keyword-{keyword_id}",
        niche_id="1",
        niche_name="Automation",
        run_id="run-pipeline-1",
        tag="STRONG GO",
        final_score=82.0,
        confidence_modifier=0.82,
        top_competitor_weaknesses=[],
    )


def _output(cost: float = 0.11) -> RecommendationOutput:
    return RecommendationOutput(generation_complete=False, failed_tasks=["dry_run"], total_llm_cost_usd=cost)


def test_pipeline_skips_keywords_that_fail_gates(monkeypatch: Any) -> None:
    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(101)])
    monkeypatch.setattr(
        recommendations_pipeline,
        "passes_recommendation_gates",
        lambda *_args, **_kwargs: (False, "confidence too low"),
    )

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-gate-fail",
            db=object(),
            config={},
            llm_client=None,
            cache=None,
            dry_run=False,
        )
    )

    assert summary["eligible"] == 1
    assert summary["gates_passed"] == 0
    assert summary["generated"] == 0
    assert summary["skipped"] == 1
    assert summary["failed"] == 0


def test_pipeline_with_zero_eligible_keywords_returns_empty_result(monkeypatch: Any) -> None:
    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [])

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-zero-eligible",
            db=object(),
            config={},
            llm_client=None,
            cache=None,
            dry_run=False,
        )
    )

    assert summary["eligible"] == 0
    assert summary["gates_passed"] == 0
    assert summary["generated"] == 0
    assert summary["skipped"] == 0
    assert summary["failed"] == 0


def test_pipeline_where_all_keywords_fail_gates(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        recommendations_pipeline,
        "get_eligible_keywords",
        lambda *_args, **_kwargs: [_keyword_row(711), _keyword_row(712), _keyword_row(713)],
    )
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (False, "gate fail"))

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-all-gates-fail",
            db=object(),
            config={},
            llm_client=None,
            cache=None,
            dry_run=False,
        )
    )

    assert summary["eligible"] == 3
    assert summary["gates_passed"] == 0
    assert summary["generated"] == 0
    assert summary["skipped"] == 3


def test_pipeline_skips_unchanged_scores(monkeypatch: Any) -> None:
    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(201)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: False)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-no-regen",
            db=object(),
            config={},
            llm_client=None,
            cache=None,
            dry_run=False,
        )
    )

    assert summary["eligible"] == 1
    assert summary["gates_passed"] == 1
    assert summary["generated"] == 0
    assert summary["skipped"] == 1
    assert summary["failed"] == 0


def test_pipeline_skips_all_keywords_when_regeneration_not_needed(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        recommendations_pipeline,
        "get_eligible_keywords",
        lambda *_args, **_kwargs: [_keyword_row(721), _keyword_row(722)],
    )
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: False)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-all-skip-regeneration",
            db=object(),
            config={},
            llm_client=None,
            cache=None,
            dry_run=False,
        )
    )

    assert summary["eligible"] == 2
    assert summary["gates_passed"] == 2
    assert summary["generated"] == 0
    assert summary["skipped"] == 2
    assert summary["failed"] == 0


def test_pipeline_generates_for_eligible_keywords(monkeypatch: Any) -> None:
    generated_context = _context(301)
    generate_mock = AsyncMock(return_value=_output(0.19))
    save_mock = Mock(return_value="rec-301")

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(301)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **_kwargs: generated_context)
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-generate",
            db=object(),
            config={},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    generate_mock.assert_awaited_once()
    save_mock.assert_called_once()
    assert summary["generated"] == 1
    assert summary["failed"] == 0
    assert summary["total_cost_usd"] == 0.19


def test_pipeline_includes_markdown_when_auto_export_enabled(monkeypatch: Any, tmp_path: Any) -> None:
    generated_context = _context(701)
    generate_mock = AsyncMock(return_value=_output(0.21))
    save_mock = Mock(return_value="rec-701")
    export_mock = AsyncMock(return_value=("# Recommendation: keyword-701", None))

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(701)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **_kwargs: generated_context)
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)
    monkeypatch.setattr(recommendations_pipeline, "export_recommendation_by_keyword", export_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-export-on",
            db=object(),
            config={"recommendations": {"auto_export_markdown": True, "export_dir": str(tmp_path)}},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    export_mock.assert_awaited_once()
    assert summary["markdown_exports"] == {"keyword-701": "# Recommendation: keyword-701"}
    assert len(summary["export_paths"]) == 1
    assert "keyword_701.md" in summary["export_paths"][0]


def test_pipeline_skips_markdown_when_auto_export_disabled(monkeypatch: Any) -> None:
    generated_context = _context(702)
    generate_mock = AsyncMock(return_value=_output(0.22))
    save_mock = Mock(return_value="rec-702")
    export_mock = AsyncMock(return_value=("# Recommendation: keyword-702", None))

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(702)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **_kwargs: generated_context)
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)
    monkeypatch.setattr(recommendations_pipeline, "export_recommendation_by_keyword", export_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-export-off",
            db=object(),
            config={"recommendations": {"auto_export_markdown": False}},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert summary["markdown_exports"] == {}
    assert summary["export_paths"] == []
    assert export_mock.await_count == 0


def test_pipeline_result_includes_export_paths(monkeypatch: Any, tmp_path: Any) -> None:
    generated_context = _context(703)
    generate_mock = AsyncMock(return_value=_output(0.23))
    save_mock = Mock(return_value="rec-703")
    export_mock = AsyncMock(return_value=("# Recommendation: keyword-703", None))

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(703)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **_kwargs: generated_context)
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)
    monkeypatch.setattr(recommendations_pipeline, "export_recommendation_by_keyword", export_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-export-path",
            db=object(),
            config={"recommendations": {"auto_export_markdown": True, "export_dir": str(tmp_path)}},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert len(summary["export_paths"]) == 1
    assert summary["export_paths"][0].endswith("keyword_703.md")


def test_pipeline_result_empty_export_paths_when_disabled(monkeypatch: Any) -> None:
    generated_context = _context(704)
    generate_mock = AsyncMock(return_value=_output(0.24))
    save_mock = Mock(return_value="rec-704")
    export_mock = AsyncMock(return_value=("# Recommendation: keyword-704", None))

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(704)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **_kwargs: generated_context)
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)
    monkeypatch.setattr(recommendations_pipeline, "export_recommendation_by_keyword", export_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-export-path-disabled",
            db=object(),
            config={"recommendations": {"auto_export_markdown": False}},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert summary["export_paths"] == []


def test_pipeline_returns_summary_counts(monkeypatch: Any) -> None:
    keywords = [_keyword_row(1), _keyword_row(2), _keyword_row(3), _keyword_row(4)]
    generated_context = _context(4)
    generate_mock = AsyncMock(return_value=_output(0.12))
    save_mock = Mock(return_value="rec-4")

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: keywords)

    def _passes(keyword_data: dict[str, Any], _db: Any) -> tuple[bool, str]:
        if keyword_data["keyword_id"] == 1:
            return False, "gate fail"
        return True, "ok"

    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", _passes)
    monkeypatch.setattr(
        recommendations_pipeline,
        "should_regenerate_recommendation",
        lambda keyword_id, *_args, **_kwargs: keyword_id != 2,
    )
    monkeypatch.setattr(
        recommendations_pipeline,
        "build_recommendation_context",
        lambda keyword_id, **_kwargs: None if keyword_id == 3 else generated_context,
    )
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-summary",
            db=object(),
            config={},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert summary == {
        "run_id": "run-summary",
        "eligible": 4,
        "gates_passed": 3,
        "generated": 1,
        "skipped": 2,
        "failed": 1,
        "total_cost_usd": 0.12,
        "markdown_exports": {},
        "export_paths": [],
    }


def test_pipeline_marks_failed_when_keyword_id_is_invalid(monkeypatch: Any) -> None:
    keyword_row = _keyword_row(501)
    keyword_row["keyword_id"] = "invalid-id"

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [keyword_row])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-invalid-keyword-id",
            db=object(),
            config={},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert summary["eligible"] == 1
    assert summary["gates_passed"] == 1
    assert summary["generated"] == 0
    assert summary["failed"] == 1


def test_pipeline_marks_failed_when_generation_raises(monkeypatch: Any) -> None:
    generate_mock = AsyncMock(side_effect=RuntimeError("llm unavailable"))
    save_mock = Mock()

    monkeypatch.setattr(recommendations_pipeline, "get_eligible_keywords", lambda *_args, **_kwargs: [_keyword_row(601)])
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **kwargs: _context(kwargs["keyword_id"]))
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-generation-fail",
            db=object(),
            config={},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    generate_mock.assert_awaited_once()
    save_mock.assert_not_called()
    assert summary["generated"] == 0
    assert summary["failed"] == 1


def test_pipeline_coercion_helpers_handle_invalid_values() -> None:
    assert recommendations_pipeline._to_positive_int("not-int") is None
    assert recommendations_pipeline._to_positive_int(0) is None
    assert recommendations_pipeline._to_positive_int(7) == 7
    assert recommendations_pipeline._to_float("bad-float", default=0.75) == 0.75


def test_recommendations_only_dry_run(monkeypatch: Any) -> None:
    generate_mock = AsyncMock(side_effect=AssertionError("LLM should not be called in dry-run mode"))
    save_mock = Mock(side_effect=AssertionError("DB writes should not happen in dry-run mode"))

    monkeypatch.setattr(
        recommendations_pipeline,
        "get_eligible_keywords",
        lambda *_args, **_kwargs: [_keyword_row(401), _keyword_row(402)],
    )
    monkeypatch.setattr(recommendations_pipeline, "passes_recommendation_gates", lambda *_args, **_kwargs: (True, "ok"))
    monkeypatch.setattr(recommendations_pipeline, "should_regenerate_recommendation", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(recommendations_pipeline, "build_recommendation_context", lambda **kwargs: _context(kwargs["keyword_id"]))
    monkeypatch.setattr(recommendations_pipeline, "generate_recommendation_async", generate_mock)
    monkeypatch.setattr(recommendations_pipeline, "save_recommendation", save_mock)

    summary = asyncio.run(
        recommendations_pipeline.run_recommendations_pipeline(
            run_id="run-dry",
            db=object(),
            config={},
            llm_client=object(),
            cache=object(),
            dry_run=True,
        )
    )

    assert summary["generated"] == 2
    assert summary["failed"] == 0
    assert summary["total_cost_usd"] == 0.0
    assert generate_mock.await_count == 0
    assert save_mock.call_count == 0


def test_recommendations_only_calls_pipeline(monkeypatch: Any) -> None:
    called_with: dict[str, Any] = {}

    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"recommendations": {"min_tag": "CONDITIONAL GO"}})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_pipeline(**kwargs: Any) -> dict[str, Any]:
        called_with.update(kwargs)
        return {
            "run_id": kwargs["run_id"],
            "eligible": 1,
            "gates_passed": 1,
            "generated": 1,
            "skipped": 0,
            "failed": 0,
            "total_cost_usd": 0.0,
        }

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr("src.recommendations.pipeline.run_recommendations_pipeline", _fake_pipeline)

    exit_code = orchestrator.run_pipeline("recommendations-only", config_path="config.yaml", database_url=None)

    assert exit_code == 0
    assert called_with["dry_run"] is True
    assert called_with["llm_client"] is None


def test_recommendations_only_mode_runs_without_collection_stages(monkeypatch: Any) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return SimpleNamespace(model_dump=lambda: {"recommendations": {"min_tag": "CONDITIONAL GO"}})

    class _FakeSessionContext:
        def __enter__(self) -> object:
            return object()

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            del exc_type, exc, tb
            return None

    async def _fake_pipeline(**kwargs: Any) -> dict[str, Any]:
        del kwargs
        return {
            "run_id": "run-1",
            "eligible": 0,
            "gates_passed": 0,
            "generated": 0,
            "skipped": 0,
            "failed": 0,
            "total_cost_usd": 0.0,
        }

    async def _fail_collection_stage(**_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("collection stages should not run for recommendations-only mode")

    monkeypatch.setattr(orchestrator, "configure_logging", lambda: None)
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)
    monkeypatch.setattr(orchestrator, "normalize_database_url", lambda db: "sqlite:///tmp.db")
    monkeypatch.setattr(orchestrator, "initialize_database", lambda database_url: object())
    monkeypatch.setattr(orchestrator, "create_session_factory", lambda _engine: object())
    monkeypatch.setattr(orchestrator, "get_session", lambda _factory: _FakeSessionContext())
    monkeypatch.setattr("src.recommendations.pipeline.run_recommendations_pipeline", _fake_pipeline)
    monkeypatch.setattr("src.collection.orchestrator.run_collection_pipeline", _fail_collection_stage)

    assert orchestrator.run_pipeline("recommendations-only", config_path="config.yaml", database_url=None) == 0


def test_executor_and_pipeline_exported() -> None:
    import src.recommendations as recommendations

    assert hasattr(recommendations, "generate_recommendation")
    assert hasattr(recommendations, "run_recommendations_pipeline")
