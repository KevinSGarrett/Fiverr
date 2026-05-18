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
from src.recommendations.tasks import generate_gig_titles


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
