"""Unit tests for recommendation context, gates, and first task executors."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

from src.models import (
    AnalysisResult,
    CompetitorSnapshot,
    ExternalSignal,
    FinalScore,
    GigVisualAnalysis,
    Keyword,
    Niche,
    Recommendation,
    Review,
    ScoreComponent,
    SearchResult,
)
from src.recommendations.context import RecommendationContext, build_recommendation_context
from src.recommendations.eligibility import (
    _tags_at_or_above,
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.storage import write_recommendation
from src.recommendations.tasks import (
    RECOMMENDATION_FIELD_NAMES,
    generate_buyer_persona,
    generate_description_outline,
    generate_differentiation_angle,
    generate_faq_entries,
    generate_gig_titles,
    generate_niche_viability,
    generate_package_structure,
    generate_recommendation,
    generate_red_flags,
    generate_tag_sets,
    generate_thumbnail_direction,
    generate_upsell_structure,
)


class FakeQuery:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def filter(self, *args: Any, **kwargs: Any) -> FakeQuery:
        return self

    def order_by(self, *args: Any, **kwargs: Any) -> FakeQuery:
        return self

    def join(self, *args: Any, **kwargs: Any) -> FakeQuery:
        return self

    def all(self) -> list[Any]:
        return list(self._rows)

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def count(self) -> int:
        return len(self._rows)


class FakeDB:
    def __init__(self, rows_by_model: dict[Any, list[Any]]) -> None:
        self._rows_by_model = rows_by_model

    def query(self, model: Any) -> FakeQuery:
        return FakeQuery(self._rows_by_model.get(model, []))


def _context_config() -> dict[str, Any]:
    return {
        "recommendations": {
            "min_tag": "CONDITIONAL_GO",
            "niches": {
                "12": {
                    "starter_price_basic": 50,
                    "starter_price_standard": 100,
                    "starter_price_premium": 200,
                    "hard_exclusions": ["adult"],
                    "recommendation_generation": True,
                }
            },
        }
    }


def _context_db() -> FakeDB:
    now = datetime.now(UTC)
    return FakeDB(
        {
            Keyword: [SimpleNamespace(id=101, keyword="python automation", niche_id=12, metadata_json={})],
            Niche: [SimpleNamespace(id=12, name="Automation", metadata_json={})],
            FinalScore: [
                SimpleNamespace(
                    keyword_id=101,
                    final_score=82.0,
                    created_at=now,
                    raw_json={
                        "tag": "STRONG_GO",
                        "demand_score": 70.0,
                        "competition_score": 50.0,
                        "opportunity_score": 76.0,
                        "feasibility_score": 65.0,
                        "profitability_score": 72.0,
                    },
                )
            ],
            ScoreComponent: [
                SimpleNamespace(score_name="demand_score", score_value=70.0, weight=0.2, explanation="x")
            ],
            CompetitorSnapshot: [
                SimpleNamespace(
                    keyword_id=101,
                    created_at=now,
                    snapshot_json={
                        "synthesis_narrative": "Market is active.",
                        "entry_feasibility_rating": 62.0,
                        "dominant_sellers": [{"name": "A"}],
                        "positioning_gaps": [{"gap": "fast delivery"}],
                        "weaknesses": [{"weakness": "slow comms"}],
                        "gig_title": "I will automate workflows",
                    },
                )
            ],
            Review: [
                SimpleNamespace(review_text="Great communication and fast delivery"),
                SimpleNamespace(review_text="Late delivery and poor quality"),
            ],
            SearchResult: [SimpleNamespace(keyword_id=101), SimpleNamespace(keyword_id=101)],
            ExternalSignal: [
                SimpleNamespace(signal_type="google_trends", raw_value_json={"google_trends_slope": "1.2"}),
                SimpleNamespace(signal_type="reddit_demand", raw_value_json={"reddit_demand_intent_score": 7.2}),
            ],
            AnalysisResult: [SimpleNamespace(raw_json={"cluster_label": "A", "opportunity_narrative": "High"})],
            GigVisualAnalysis: [SimpleNamespace(gig_id=1)],
            Recommendation: [],
        }
    )


def test_recommendation_context_valid_construction() -> None:
    context = RecommendationContext(
        keyword_id=1,
        keyword_text="k",
        niche_id=1,
        niche_name="N",
        tag="STRONG_GO",
        final_score=80.0,
    )
    assert context.keyword_text == "k"


def test_recommendation_context_optional_fields_none() -> None:
    context = RecommendationContext(
        keyword_id=1,
        keyword_text="k",
        niche_id=1,
        niche_name="N",
        tag="MONITOR",
        final_score=0.0,
        demand_score=None,
        competition_score=None,
    )
    assert context.demand_score is None


def test_build_context_with_mock_db() -> None:
    context = build_recommendation_context(101, _context_db(), _context_config())
    assert context.keyword_id == 101
    assert context.niche_name == "Automation"


def test_get_eligible_keywords_filters_tags() -> None:
    db = FakeDB(
        {
            FinalScore: [
                SimpleNamespace(keyword_id=101, final_score=80.0, raw_json={"tag": "STRONG_GO", "confidence_modifier": 0.8}),
                SimpleNamespace(keyword_id=102, final_score=30.0, raw_json={"tag": "PASS", "confidence_modifier": 0.9}),
            ],
            Keyword: [
                SimpleNamespace(id=101, keyword="python automation", niche_id=12, metadata_json={}),
                SimpleNamespace(id=102, keyword="other", niche_id=12, metadata_json={}),
            ],
        }
    )
    rows = get_eligible_keywords("1", db, _context_config())
    assert len(rows) == 1
    assert rows[0]["keyword_id"] == 101


def test_tags_at_or_above_conditional() -> None:
    assert _tags_at_or_above("CONDITIONAL_GO") == ["STRONG_GO", "CONDITIONAL_GO"]


def test_passes_gates_confidence_too_low() -> None:
    ok, reason = passes_recommendation_gates({"keyword_id": 101, "confidence_modifier": 0.2}, _context_db())
    assert ok is False
    assert "below 0.40" in reason


def test_passes_gates_demand_too_low() -> None:
    ok, reason = passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.9, "demand_score": 5.0},
        _context_db(),
    )
    assert ok is False
    assert "Demand score" in reason


def test_passes_gates_no_gig_analysis() -> None:
    db = _context_db()
    db._rows_by_model[GigVisualAnalysis] = []
    ok, reason = passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.9, "demand_score": 50.0},
        db,
    )
    assert ok is False
    assert "No gig quality analysis" in reason


def test_passes_gates_all_pass() -> None:
    ok, reason = passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.9, "demand_score": 50.0},
        _context_db(),
    )
    assert ok is True
    assert reason == "All gates passed"


def test_should_regenerate_no_existing() -> None:
    db = _context_db()
    db._rows_by_model[Recommendation] = []
    assert should_regenerate_recommendation(101, 80.0, db) is True


def test_should_regenerate_score_delta() -> None:
    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[Recommendation] = [
        SimpleNamespace(created_at=now, raw_json={"generation_complete": True, "final_score": 50.0})
    ]
    assert should_regenerate_recommendation(101, 60.5, db) is True


def test_should_regenerate_stable() -> None:
    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[Recommendation] = [
        SimpleNamespace(created_at=now, raw_json={"generation_complete": True, "final_score": 80.0})
    ]
    db._rows_by_model[CompetitorSnapshot] = [SimpleNamespace(created_at=now - timedelta(minutes=10))]
    assert should_regenerate_recommendation(101, 82.0, db) is False


def test_gig_titles_task_mock_llm() -> None:
    context = RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id=12,
        niche_name="Automation",
        tag="STRONG_GO",
        final_score=80.0,
    )
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"titles":[{"title":"I will automate your workflows","rationale":"high intent"}]}',
        metadata={"estimated_cost_usd": 0.01},
    )
    result = asyncio.run(generate_gig_titles(context, llm_client, cache=None))
    assert isinstance(result["output"], list)
    assert result["output"][0] == "I will automate your workflows"


def test_recommendation_context_legacy_keyword_alias() -> None:
    context = RecommendationContext(keyword="legacy keyword", niche_id="n1")
    assert context.keyword_text == "legacy keyword"


def test_build_context_missing_keyword_returns_default() -> None:
    db = FakeDB({})
    context = build_recommendation_context(999, db, _context_config())
    assert context.keyword_id == 999
    assert context.final_score == 0.0


def test_get_eligible_keywords_skips_disabled_niche() -> None:
    db = FakeDB(
        {
            FinalScore: [SimpleNamespace(keyword_id=101, final_score=80.0, raw_json={"tag": "STRONG_GO"})],
            Keyword: [SimpleNamespace(id=101, keyword="python automation", niche_id=12, metadata_json={})],
        }
    )
    config = _context_config()
    config["recommendations"]["niches"]["12"]["recommendation_generation"] = False
    rows = get_eligible_keywords("1", db, config)
    assert rows == []


def test_get_eligible_keywords_includes_force_flag() -> None:
    db = FakeDB(
        {
            FinalScore: [SimpleNamespace(keyword_id=101, final_score=80.0, raw_json={"tag": "STRONG_GO"})],
            Keyword: [
                SimpleNamespace(
                    id=101,
                    keyword="python automation",
                    niche_id=12,
                    metadata_json={"force_recommended": True},
                )
            ],
        }
    )
    rows = get_eligible_keywords("1", db, _context_config())
    assert rows[0]["force_recommended"] is True


def test_tags_at_or_above_invalid_defaults_to_conditional() -> None:
    assert _tags_at_or_above("UNKNOWN") == ["STRONG_GO", "CONDITIONAL_GO"]


def test_passes_gates_force_recommended_override() -> None:
    ok, reason = passes_recommendation_gates(
        {"keyword_id": 101, "confidence_modifier": 0.0, "force_recommended": True},
        _context_db(),
    )
    assert ok is True
    assert "forced recommendation" in reason


def test_should_regenerate_on_newer_competitor_data() -> None:
    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[Recommendation] = [
        SimpleNamespace(created_at=now, raw_json={"generation_complete": True, "final_score": 80.0})
    ]
    db._rows_by_model[CompetitorSnapshot] = [SimpleNamespace(created_at=now + timedelta(minutes=1))]
    assert should_regenerate_recommendation(101, 82.0, db) is True


def test_should_regenerate_when_generation_incomplete() -> None:
    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[Recommendation] = [
        SimpleNamespace(created_at=now, raw_json={"generation_complete": False, "final_score": 80.0})
    ]
    assert should_regenerate_recommendation(101, 80.0, db) is True


def test_tag_sets_task_mock_llm() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"tag_sets":[{"tags":["python automation","workflow automation","api automation","task scripts","python dev"]}]}',
        metadata={"estimated_cost_usd": 0.002},
    )
    result = asyncio.run(generate_tag_sets(context, llm_client, cache=None))
    assert isinstance(result["output"], list)
    assert len(result["output"][0]) == 5


def test_differentiation_angle_task_mock_llm() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"positioning_statement":"Automation with fast turnaround","differentiators":["speed","clarity","maintainability"]}',
        metadata={"estimated_cost_usd": 0.01},
    )
    result = asyncio.run(generate_differentiation_angle(context, llm_client, cache=None))
    assert result["output"] == "Automation with fast turnaround"


def test_red_flags_task_mock_llm() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"risk_level":"HIGH","risks":["race to bottom pricing","unclear scope"]}',
        metadata={"estimated_cost_usd": 0.008},
    )
    result = asyncio.run(generate_red_flags(context, llm_client, cache=None))
    assert result["output"] == ["race to bottom pricing", "unclear scope"]


def test_task_returns_none_on_llm_failure() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.side_effect = RuntimeError("boom")
    result = asyncio.run(generate_gig_titles(context, llm_client, cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_task_returns_none_on_invalid_json() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="not-json", metadata={"estimated_cost_usd": 0.01})
    result = asyncio.run(generate_tag_sets(context, llm_client, cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_task_returns_none_with_no_client() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    result = asyncio.run(generate_red_flags(context, llm_client=None, cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_build_context_includes_score_components_from_rows() -> None:
    context = build_recommendation_context(101, _context_db(), _context_config())
    assert "demand_score" in context.score_components


def test_build_context_uses_niche_pricing_defaults() -> None:
    context = build_recommendation_context(101, _context_db(), _context_config())
    assert context.starter_price_basic == 50
    assert context.starter_price_standard == 100
    assert context.starter_price_premium == 200


def test_generate_package_structure_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"basic":{"price":50},"standard":{"price":100},"premium":{"price":200}}',
        metadata={"estimated_cost_usd": 0.02},
    )
    result = asyncio.run(generate_package_structure(context, llm_client, cache=None))
    assert isinstance(result["output"], dict)
    assert "basic" in result["output"]


def test_generate_description_outline_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"overview":"A","experience":"B","process":"C","why_us":"D"}',
        metadata={"estimated_cost_usd": 0.02},
    )
    result = asyncio.run(generate_description_outline(context, llm_client, cache=None))
    assert isinstance(result["output"], dict)
    assert "overview" in result["output"]


def test_generate_faq_entries_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"faq_entries":[{"question":"Q1","answer":"A1"},{"question":"Q2","answer":"A2"}]}',
        metadata={"estimated_cost_usd": 0.003},
    )
    result = asyncio.run(generate_faq_entries(context, llm_client, cache=None))
    assert isinstance(result["output"], list)
    assert len(result["output"]) == 2


def test_generate_buyer_persona_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"persona_name":"Ops Manager","goals":["save time"]}',
        metadata={"estimated_cost_usd": 0.003},
    )
    result = asyncio.run(generate_buyer_persona(context, llm_client, cache=None))
    assert isinstance(result["output"], dict)
    assert result["output"]["persona_name"] == "Ops Manager"


def test_generate_thumbnail_direction_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"thumbnail_direction":"Use high-contrast before/after visual metaphor"}',
        metadata={"estimated_cost_usd": 0.003},
    )
    result = asyncio.run(generate_thumbnail_direction(context, llm_client, cache=None))
    assert isinstance(result["output"], str)
    assert "before/after" in result["output"]


def test_generate_upsell_structure_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"upsells":[{"name":"24h delivery"},{"name":"monitoring setup"}]}',
        metadata={"estimated_cost_usd": 0.003},
    )
    result = asyncio.run(generate_upsell_structure(context, llm_client, cache=None))
    assert isinstance(result["output"], list)
    assert len(result["output"]) == 2


def test_generate_niche_viability_mock() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text='{"verdict":"viable","confidence":"medium"}',
        metadata={"estimated_cost_usd": 0.01},
    )
    result = asyncio.run(generate_niche_viability(context, llm_client, cache=None))
    assert isinstance(result["output"], dict)
    assert result["output"]["verdict"] == "viable"


def _success_task(output: Any, cost: float = 0.01) -> Any:
    async def _inner(context: RecommendationContext, llm_client: Any, cache: Any) -> dict[str, Any]:
        del context, llm_client, cache
        return {"output": output, "cost_usd": cost}

    return _inner


def test_generate_recommendation_all_succeed(monkeypatch: Any) -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _success_task(["t1"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _success_task([["a", "b"]]))
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _success_task({"basic": {}}))
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _success_task({"overview": "x"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _success_task([{"question": "q", "answer": "a"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _success_task("angle"))
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _success_task({"persona": "ops"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _success_task("direction"))
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _success_task([{"name": "u1"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _success_task(["risk"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _success_task({"verdict": "good"}))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert result["generation_complete"] is True
    assert result["gig_titles"] == ["t1"]
    assert result["niche_viability_assessment"] == {"verdict": "good"}


def test_generate_recommendation_partial_failure(monkeypatch: Any) -> None:
    async def _raise(context: RecommendationContext, llm_client: Any, cache: Any) -> dict[str, Any]:
        del context, llm_client, cache
        raise RuntimeError("boom")

    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _success_task(["t1"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _success_task([["a", "b"]]))
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _raise)
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _success_task({"overview": "x"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _success_task([{"question": "q", "answer": "a"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _success_task("angle"))
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _success_task({"persona": "ops"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _success_task("direction"))
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _raise)
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _success_task(["risk"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _success_task({"verdict": "good"}))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert result["generation_complete"] is False
    assert result["package_structure"] is None
    assert result["upsell_structure"] is None


def test_generate_recommendation_cost_accumulated(monkeypatch: Any) -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _success_task(["t1"], cost=0.02))
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _success_task([["a", "b"]], cost=0.01))
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _success_task({"basic": {}}, cost=0.03))
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _success_task({"overview": "x"}, cost=0.03))
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _success_task([{"question": "q", "answer": "a"}], cost=0.01))
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _success_task("angle", cost=0.02))
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _success_task({"persona": "ops"}, cost=0.01))
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _success_task("direction", cost=0.01))
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _success_task([{"name": "u1"}], cost=0.01))
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _success_task(["risk"], cost=0.02))
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _success_task({"verdict": "good"}, cost=0.04))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert abs(result["llm_cost_usd"] - 0.21) < 1e-9


def test_generate_recommendation_exception_handling(monkeypatch: Any) -> None:
    async def _raise(context: RecommendationContext, llm_client: Any, cache: Any) -> dict[str, Any]:
        del context, llm_client, cache
        raise ValueError("bad llm")

    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _raise)
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _success_task([["a", "b"]]))
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _success_task({"basic": {}}))
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _success_task({"overview": "x"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _success_task([{"question": "q", "answer": "a"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _success_task("angle"))
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _success_task({"persona": "ops"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _success_task("direction"))
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _success_task([{"name": "u1"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _success_task(["risk"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _success_task({"verdict": "good"}))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert result["gig_titles"] is None
    assert result["generation_complete"] is False


def test_write_recommendation_returns_true(monkeypatch: Any, tmp_path: Any) -> None:
    monkeypatch.chdir(tmp_path)
    context = RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id=12,
        niche_name="Automation",
        tag="STRONG_GO",
        final_score=82.0,
    )
    recommendation_data = {name: {"sample": name} for name in RECOMMENDATION_FIELD_NAMES}
    recommendation_data["generation_complete"] = True
    recommendation_data["llm_cost_usd"] = 0.11
    ok = write_recommendation(101, "run-1", context, recommendation_data, db=None)
    assert ok is True
    assert (tmp_path / "data" / "recommendation_results" / "101_run-1.json").exists()


def test_11_task_names_match_field_names() -> None:
    assert len(RECOMMENDATION_FIELD_NAMES) == 11
    assert len(set(RECOMMENDATION_FIELD_NAMES)) == 11


def test_generate_recommendation_no_crash_no_llm() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    result = asyncio.run(generate_recommendation(101, context, llm_client=None, cache=None, db=Mock()))
    assert result["generation_complete"] is False
    assert result["llm_cost_usd"] == 0.0
