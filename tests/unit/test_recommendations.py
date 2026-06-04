"""Unit tests for recommendation context, gates, and first task executors."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

from src.models import (
    AnalysisResult,
    CompetitorSnapshot,
    ExternalSignal,
    FinalScore,
    Gig,
    GigVisualAnalysis,
    Keyword,
    Niche,
    PriceAnalysis,
    Recommendation,
    Review,
    ScoreComponent,
    SearchResult,
    Seller,
)
from src.recommendations.context import RecommendationContext, build_recommendation_context
from src.recommendations.eligibility import (
    _coerce_datetime,
    _tags_at_or_above,
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.run import run_recommendations_stage
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
    generate_pricing_strategy,
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

    def outerjoin(self, *args: Any, **kwargs: Any) -> FakeQuery:
        return self

    def limit(self, _value: int) -> FakeQuery:
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

    def query(self, *models: Any) -> FakeQuery:
        if len(models) == 1:
            key: Any = models[0]
        else:
            key = tuple(models)
        return FakeQuery(self._rows_by_model.get(key, []))


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


def test_context_pricing_fields_default_none() -> None:
    context = RecommendationContext(keyword_id=1, keyword_text="k", niche_id=1)
    assert context.price_distribution is None
    assert context.price_review_correlation is None
    assert context.market_type is None
    assert context.calculated_entry_prices is None
    assert context.calculated_price_ladder is None
    assert context.new_seller_discount_pct is None
    assert context.competitor_price_positions is None


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


def test_coerce_datetime_passthrough_datetime() -> None:
    now = datetime.now(UTC)
    assert _coerce_datetime(now) == now


def test_coerce_datetime_invalid_string_returns_none() -> None:
    assert _coerce_datetime("not-a-datetime") is None


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


def test_get_eligible_keywords_skips_disabled_niche_recommendations() -> None:
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


def test_context_price_distribution_populated(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(
            keyword_id=101,
            analyzed_at=now,
            basic_median=100.0,
            basic_mean=120.0,
            basic_min=70.0,
            basic_max=180.0,
            basic_cv=0.22,
            basic_gaps=[{"gap_midpoint": 90}],
            standard_median=180.0,
            standard_mean=210.0,
            standard_min=120.0,
            standard_max=300.0,
            premium_median=350.0,
            premium_mean=390.0,
            premium_min=250.0,
            premium_max=550.0,
            moat_strength="MEDIUM",
            review_premium=45.0,
            market_type="MODERATE_SPREAD",
            basic_n=20,
            basic_skewness=0.1,
        )
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.price_distribution is not None
    assert context.price_distribution["basic"]["median"] == 100.0
    assert context.price_distribution["basic"]["gaps"] == [{"gap_midpoint": 90}]


def test_context_market_type_populated(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(
            keyword_id=101,
            analyzed_at=now,
            basic_median=100.0,
            standard_median=180.0,
            premium_median=350.0,
            market_type="COMMODITY",
            moat_strength=None,
        )
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.market_type == "COMMODITY"


def test_context_calculated_prices_populated(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(
            keyword_id=101,
            analyzed_at=now,
            basic_median=100.0,
            standard_median=180.0,
            premium_median=350.0,
            basic_n=15,
            basic_skewness=0.0,
            basic_gaps=[],
            market_type="MODERATE_SPREAD",
            moat_strength="LOW",
        )
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.calculated_entry_prices is not None
    assert set(context.calculated_entry_prices.keys()) == {"basic", "standard", "premium"}


def test_context_price_ladder_populated(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(
            keyword_id=101,
            analyzed_at=now,
            basic_median=100.0,
            standard_median=180.0,
            premium_median=350.0,
            basic_n=15,
            basic_skewness=0.0,
            basic_gaps=[],
            market_type="MODERATE_SPREAD",
            moat_strength="LOW",
        )
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.calculated_price_ladder is not None
    assert len(context.calculated_price_ladder) >= 4
    assert "milestone_reviews" in context.calculated_price_ladder[0]


def test_context_no_price_analysis_safe(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    db = _context_db()
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.price_distribution is None
    assert context.price_review_correlation is None
    assert context.market_type is None
    assert context.calculated_entry_prices is None
    assert context.calculated_price_ladder is None
    assert context.new_seller_discount_pct is None
    assert context.competitor_price_positions is None


def test_context_competitor_positions_populated(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(
            keyword_id=101,
            analyzed_at=now,
            basic_median=100.0,
            standard_median=180.0,
            premium_median=350.0,
            basic_n=15,
            basic_skewness=0.0,
            basic_gaps=[],
            market_type="MODERATE_SPREAD",
            moat_strength=None,
        )
    ]
    db._rows_by_model[(SearchResult, Gig, Seller)] = [
        (
            SimpleNamespace(rank=1),
            SimpleNamespace(starting_price=95.0, review_count=210),
            SimpleNamespace(seller_handle="seller_a", level="LEVEL_TWO"),
        ),
        (
            SimpleNamespace(rank=2),
            SimpleNamespace(starting_price=110.0, review_count=140),
            SimpleNamespace(seller_handle="seller_b", level="TOP_RATED"),
        ),
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.competitor_price_positions is not None
    assert len(context.competitor_price_positions) == 2
    assert context.competitor_price_positions[0]["seller"] == "seller_a"


def test_context_score_components_falls_back_to_final_raw() -> None:
    db = _context_db()
    db._rows_by_model[ScoreComponent] = []
    db._rows_by_model[FinalScore] = [
        SimpleNamespace(
            keyword_id=101,
            final_score=82.0,
            created_at=datetime.now(UTC),
            raw_json={"tag": "STRONG_GO", "score_components": {"profitability_score": {"score_value": 77.0}}},
        )
    ]
    context = build_recommendation_context(101, db, _context_config())
    assert context.score_components["profitability_score"]["score_value"] == 77.0


def test_context_bad_float_values_coerce_to_none() -> None:
    db = _context_db()
    db._rows_by_model[FinalScore] = [
        SimpleNamespace(
            keyword_id=101,
            final_score=82.0,
            created_at=datetime.now(UTC),
            raw_json={"tag": "STRONG_GO", "demand_score": object()},
        )
    ]
    context = build_recommendation_context(101, db, _context_config())
    assert context.demand_score is None


def test_context_price_analysis_query_exception_is_safe(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    class BrokenPriceAnalysisDB(FakeDB):
        def query(self, *models: Any) -> FakeQuery:
            if len(models) == 1 and models[0] is PriceAnalysis:
                raise RuntimeError("boom")
            return super().query(*models)

    db = BrokenPriceAnalysisDB(_context_db()._rows_by_model)
    monkeypatch.setattr(context_module, "Session", BrokenPriceAnalysisDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.price_distribution is None
    assert context.market_type is None


def test_context_pricing_calculation_exception_is_safe(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(keyword_id=101, analyzed_at=now, market_type="MODERATE_SPREAD", moat_strength=None)
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    monkeypatch.setattr(
        "src.pricing.new_seller_pricing.calculate_new_seller_pricing",
        lambda *args: (_ for _ in ()).throw(RuntimeError("calc failed")),
    )
    context = build_recommendation_context(101, db, _context_config())
    assert context.calculated_entry_prices is None
    assert context.calculated_price_ladder is None


def test_context_competitor_rows_skip_none_gig(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(keyword_id=101, analyzed_at=now, market_type="MODERATE_SPREAD", moat_strength=None)
    ]
    db._rows_by_model[(SearchResult, Gig, Seller)] = [
        (SimpleNamespace(rank=1), None, SimpleNamespace(seller_handle="seller_a", level="LEVEL_TWO")),
        (SimpleNamespace(rank=2), SimpleNamespace(starting_price=110.0, review_count=140), None),
    ]
    monkeypatch.setattr(context_module, "Session", FakeDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.competitor_price_positions is not None
    assert len(context.competitor_price_positions) == 1
    assert context.competitor_price_positions[0]["seller"] == "UNKNOWN"


def test_context_competitor_query_exception_sets_none(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    class BrokenCompetitorDB(FakeDB):
        def query(self, *models: Any) -> FakeQuery:
            if len(models) == 3:
                raise RuntimeError("competitor query failed")
            return super().query(*models)

    now = datetime.now(UTC)
    db = BrokenCompetitorDB(_context_db()._rows_by_model)
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(keyword_id=101, analyzed_at=now, market_type="MODERATE_SPREAD", moat_strength=None)
    ]
    monkeypatch.setattr(context_module, "Session", BrokenCompetitorDB)
    context = build_recommendation_context(101, db, _context_config())
    assert context.competitor_price_positions is None


def test_context_non_dict_price_ladder_entries_are_ignored(monkeypatch: Any) -> None:
    from src.recommendations import context as context_module

    now = datetime.now(UTC)
    db = _context_db()
    db._rows_by_model[PriceAnalysis] = [
        SimpleNamespace(keyword_id=101, analyzed_at=now, market_type="MODERATE_SPREAD", moat_strength=None)
    ]

    class PricingRec:
        entry_basic = 60
        entry_standard = 120
        entry_premium = 220
        price_ladder = ["bad-step", None]

    monkeypatch.setattr(context_module, "Session", FakeDB)
    monkeypatch.setattr("src.pricing.new_seller_pricing.calculate_new_seller_pricing", lambda *args: PricingRec())
    context = build_recommendation_context(101, db, _context_config())
    assert context.calculated_entry_prices is not None
    assert context.calculated_price_ladder is None


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
    monkeypatch.setattr("src.recommendations.tasks.pricing_llm_task", AsyncMock(return_value={"entry_prices": {}}))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert result["generation_complete"] is True
    assert result["gig_titles"] == ["t1"]
    assert result["niche_viability_assessment"] == {"verdict": "good"}
    assert result["pricing_strategy"] == {"entry_prices": {}}


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
    monkeypatch.setattr("src.recommendations.tasks.pricing_llm_task", AsyncMock(return_value={"entry_prices": {}}))
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
    monkeypatch.setattr("src.recommendations.tasks.pricing_llm_task", AsyncMock(return_value={"entry_prices": {}}))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert abs(result["llm_cost_usd"] - 0.22) < 1e-9


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
    monkeypatch.setattr("src.recommendations.tasks.pricing_llm_task", AsyncMock(return_value={"entry_prices": {}}))
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


def test_12_task_names_match_field_names() -> None:
    assert len(RECOMMENDATION_FIELD_NAMES) == 12
    assert len(set(RECOMMENDATION_FIELD_NAMES)) == 12


def test_generate_pricing_strategy_no_price_distribution_recommendations() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    result = asyncio.run(generate_pricing_strategy(context, llm_client=Mock(), cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_generate_pricing_strategy_with_price_distribution() -> None:
    context = RecommendationContext(
        keyword_text="python automation",
        niche_id=12,
        price_distribution={
            "basic": {"median": 100, "mean": 110, "min": 70, "max": 180, "q1": 80, "q3": 140, "clusters": [], "gaps": []},
            "standard": {"median": 180, "min": 130, "max": 290},
            "premium": {"median": 350, "min": 240, "max": 520},
        },
        competitor_price_positions=[],
    )
    llm_client = Mock()
    payload = {
        "pricing_strategy": {
            "entry_prices": {
                "basic": 65,
                "standard": 135,
                "premium": 260,
                "lead_tier": "basic",
                "lead_tier_reasoning": "Lead with Basic to reduce buyer risk and accelerate first conversions.",
            },
            "acquisition_prices": {
                "basic": 55,
                "standard": 120,
                "premium": 235,
                "acquisition_period": "first 5 orders",
            },
            "price_ladder": [
                {"milestone_reviews": 5, "basic": 70, "standard": 145, "premium": 275, "adjustment_rationale": "Initial baseline."},
                {"milestone_reviews": 10, "basic": 75, "standard": 155, "premium": 290, "adjustment_rationale": "Early proof gained."},
                {
                    "milestone_reviews": 25,
                    "basic": 82,
                    "standard": 170,
                    "premium": 315,
                    "adjustment_rationale": "Demand improves and delivery confidence rises.",
                },
                {
                    "milestone_reviews": 50,
                    "basic": 90,
                    "standard": 185,
                    "premium": 340,
                    "adjustment_rationale": "Positioning strengthens with social proof.",
                },
            ],
            "strategy_narrative": (
                "Set entry pricing in the lower-middle cluster to win first conversions while avoiding a pure bargain signal. "
                "Use a measured ladder tied to review milestones so each increase is justified by proven execution and buyer trust. "
                "Preserve perceived value by widening package separation and emphasizing faster turnaround plus optional extras."
            ),
            "pricing_risks": [
                {
                    "risk": "Undercutting too hard can attract low-quality buyers.",
                    "severity": "MEDIUM",
                    "mitigation": "Keep scope tight and enforce revisions limits.",
                }
            ],
            "recommended_extras": [
                {"name": "24-hour delivery", "price": 25, "rationale": "Captures urgent buyers and improves average order value."},
                {"name": "Source file handoff", "price": 20, "rationale": "Adds perceived professionalism and monetizes final assets."},
            ],
            "projected_aov": {"at_entry": 96.5, "at_50_reviews": 142.0, "aov_growth_pct": 47.2},
        }
    }
    llm_client.complete.return_value = SimpleNamespace(
        text=json.dumps(payload),
        metadata={"estimated_cost_usd": 0.01},
    )
    result = asyncio.run(generate_pricing_strategy(context, llm_client=llm_client, cache=None))
    assert result["output"] is not None
    assert result["output"]["entry_prices"]["basic"] == 65


def test_generate_pricing_strategy_handles_none_correlation_fields() -> None:
    context = RecommendationContext(
        keyword_text="python automation",
        niche_id=12,
        price_distribution={
            "basic": {"median": 100, "mean": 110, "min": 70, "max": 180, "q1": 80, "q3": 140, "clusters": [], "gaps": []},
            "standard": {"median": 180, "min": 130, "max": 290},
            "premium": {"median": 350, "min": 240, "max": 520},
        },
        price_review_correlation={
            "moat_strength": "HIGH",
            "pearson": None,
            "review_premium_usd": 35.0,
            "new_seller_avg_price": None,
            "new_seller_discount_pct": None,
        },
        competitor_price_positions=[],
    )
    llm_client = Mock()
    pricing_payload = {
        "entry_prices": {
            "basic": 50,
            "standard": 100,
            "premium": 180,
            "lead_tier": "basic",
            "lead_tier_reasoning": "Lead with basic to maximize early conversion and collect first reviews quickly.",
        },
        "acquisition_prices": {
            "basic": 40,
            "standard": 80,
            "premium": 150,
            "acquisition_period": "first 5 orders",
        },
        "price_ladder": [
            {"milestone_reviews": 5, "basic": 50, "standard": 100, "premium": 180, "adjustment_rationale": "Initial baseline."},
            {"milestone_reviews": 10, "basic": 60, "standard": 120, "premium": 210, "adjustment_rationale": "Early proof gained."},
            {
                "milestone_reviews": 25,
                "basic": 75,
                "standard": 145,
                "premium": 250,
                "adjustment_rationale": "Demand improves and delivery confidence rises.",
            },
            {
                "milestone_reviews": 50,
                "basic": 90,
                "standard": 170,
                "premium": 290,
                "adjustment_rationale": "Positioning strengthens with social proof.",
            },
        ],
        "strategy_narrative": (
            "Set entry pricing in the lower-middle cluster to win first conversions while avoiding a pure bargain signal. "
            "Use a measured ladder tied to review milestones so each increase is justified by proven execution and buyer trust. "
            "Preserve perceived value by widening package separation and emphasizing faster turnaround plus optional extras."
        ),
        "pricing_risks": [
            {
                "risk": "Undercutting too hard can attract low-quality buyers.",
                "severity": "MEDIUM",
                "mitigation": "Keep scope tight and enforce revisions limits.",
            }
        ],
        "recommended_extras": [
            {"name": "24-hour delivery", "price": 25, "rationale": "Captures urgent buyers and improves average order value."},
            {"name": "Source file handoff", "price": 20, "rationale": "Adds perceived professionalism and monetizes final assets."},
        ],
        "projected_aov": {"at_entry": 72.0, "at_50_reviews": 118.0, "aov_growth_pct": 63.9},
    }
    llm_client.complete.return_value = SimpleNamespace(
        text=json.dumps({"pricing_strategy": pricing_payload}),
        metadata={"estimated_cost_usd": 0.01},
    )
    result = asyncio.run(generate_pricing_strategy(context, llm_client=llm_client, cache=None))
    assert result["output"] is not None
    assert result["output"]["entry_prices"]["basic"] == 50


def test_generate_pricing_strategy_missing_pricing_strategy_key_returns_none() -> None:
    context = RecommendationContext(
        keyword_text="python automation",
        niche_id=12,
        price_distribution={
            "basic": {"median": 100, "mean": 110, "min": 70, "max": 180, "q1": 80, "q3": 140, "clusters": [], "gaps": []},
            "standard": {"median": 180, "min": 130, "max": 290},
            "premium": {"median": 350, "min": 240, "max": 520},
        },
    )
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text=json.dumps({"not_pricing_strategy": {}}),
        metadata={"estimated_cost_usd": 0.01},
    )
    result = asyncio.run(generate_pricing_strategy(context, llm_client=llm_client, cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_generate_recommendation_no_crash_no_llm() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    result = asyncio.run(generate_recommendation(101, context, llm_client=None, cache=None, db=Mock()))
    assert result["generation_complete"] is False
    assert result["llm_cost_usd"] == 0.0


def test_run_recommendations_stage_dry_run_summary_keys(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 101, "final_score": 80.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (True, "ok"))
    monkeypatch.setattr("src.recommendations.run.should_regenerate_recommendation", lambda keyword_id, score, db: True)
    monkeypatch.setattr(
        "src.recommendations.run.build_recommendation_context",
        lambda keyword_id, db, config: RecommendationContext(keyword_id=keyword_id, keyword_text="k", niche_id=1),
    )
    writes: list[int] = []
    monkeypatch.setattr(
        "src.recommendations.run.write_recommendation",
        lambda keyword_id, run_id, context, result, db: writes.append(keyword_id) or True,
    )
    summary = asyncio.run(run_recommendations_stage("run-1", db=Mock(), config={}, llm_client=None, cache=None))
    assert set(summary.keys()) == {"eligible_count", "generated", "skipped", "failed", "total_cost_usd"}
    assert summary["eligible_count"] == 1
    assert summary["generated"] == 1
    assert writes == [101]


def test_run_recommendations_stage_skips_when_gate_fails(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 201, "final_score": 70.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (False, "blocked"))
    summary = asyncio.run(run_recommendations_stage("run-2", db=Mock(), config={}, llm_client=None, cache=None))
    assert summary["generated"] == 0
    assert summary["skipped"] == 1
    assert summary["failed"] == 0


def test_run_recommendations_stage_skips_when_no_regen(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 202, "final_score": 70.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (True, "ok"))
    monkeypatch.setattr("src.recommendations.run.should_regenerate_recommendation", lambda keyword_id, score, db: False)
    summary = asyncio.run(run_recommendations_stage("run-3", db=Mock(), config={}, llm_client=None, cache=None))
    assert summary["generated"] == 0
    assert summary["skipped"] == 1


def test_run_recommendations_stage_records_failures(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 303, "final_score": 75.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (True, "ok"))
    monkeypatch.setattr("src.recommendations.run.should_regenerate_recommendation", lambda keyword_id, score, db: True)

    def _boom(keyword_id: int, db: Any, config: Any) -> RecommendationContext:
        del keyword_id, db, config
        raise RuntimeError("context failed")

    monkeypatch.setattr("src.recommendations.run.build_recommendation_context", _boom)
    summary = asyncio.run(run_recommendations_stage("run-4", db=Mock(), config={}, llm_client=None, cache=None))
    assert summary["failed"] == 1
    assert summary["generated"] == 0


def test_run_recommendations_stage_accumulates_llm_cost(monkeypatch: Any) -> None:
    async def _fake_generate(keyword_id: int, context: Any, llm_client: Any, cache: Any, db: Any) -> dict[str, Any]:
        del keyword_id, context, llm_client, cache, db
        return {"generation_complete": True, "llm_cost_usd": 0.45}

    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 401, "final_score": 81.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (True, "ok"))
    monkeypatch.setattr("src.recommendations.run.should_regenerate_recommendation", lambda keyword_id, score, db: True)
    monkeypatch.setattr(
        "src.recommendations.run.build_recommendation_context",
        lambda keyword_id, db, config: RecommendationContext(keyword_id=keyword_id, keyword_text="k", niche_id=1),
    )
    monkeypatch.setattr("src.recommendations.run.generate_recommendation", _fake_generate)
    summary = asyncio.run(
        run_recommendations_stage("run-5", db=Mock(), config={}, llm_client=Mock(), cache=Mock(), dry_run=False)
    )
    assert summary["generated"] == 1
    assert summary["total_cost_usd"] == 0.45


def test_write_recommendation_creates_missing_output_directory(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "data" / "recommendation_results"
    assert not output_dir.exists()
    context = RecommendationContext(keyword_id=9, keyword_text="k", niche_id=1, niche_name="N", tag="MONITOR")
    recommendation_data = {"generation_complete": False, "llm_cost_usd": 0.0}
    ok = write_recommendation(9, "run-dir", context, recommendation_data, db=None)
    assert ok is True
    assert output_dir.exists()
    assert (output_dir / "9_run-dir.json").exists()


def test_get_eligible_keywords_returns_empty_when_no_go_tags() -> None:
    db = FakeDB(
        {
            FinalScore: [
                SimpleNamespace(keyword_id=101, final_score=35.0, raw_json={"tag": "MONITOR"}),
                SimpleNamespace(keyword_id=102, final_score=15.0, raw_json={"tag": "PASS"}),
            ],
            Keyword: [
                SimpleNamespace(id=101, keyword="k1", niche_id=12, metadata_json={}),
                SimpleNamespace(id=102, keyword="k2", niche_id=12, metadata_json={}),
            ],
        }
    )
    rows = get_eligible_keywords("1", db, _context_config())
    assert rows == []


def test_get_eligible_keywords_non_numeric_run_id_uses_latest_final_scores() -> None:
    db = FakeDB(
        {
            FinalScore: [
                SimpleNamespace(keyword_id=101, final_score=80.0, created_at=datetime(2026, 1, 2, tzinfo=UTC), raw_json={"tag": "STRONG_GO"}),
                SimpleNamespace(keyword_id=101, final_score=75.0, created_at=datetime(2026, 1, 1, tzinfo=UTC), raw_json={"tag": "CONDITIONAL_GO"}),
                SimpleNamespace(keyword_id=102, final_score=30.0, created_at=datetime(2026, 1, 3, tzinfo=UTC), raw_json={"tag": "PASS"}),
            ],
            Keyword: [
                SimpleNamespace(id=101, keyword="k1", niche_id=12, metadata_json={}),
                SimpleNamespace(id=102, keyword="k2", niche_id=12, metadata_json={}),
            ],
        }
    )
    rows = get_eligible_keywords("run-abc", db, _context_config())
    assert len(rows) == 1
    assert rows[0]["keyword_id"] == 101
    assert rows[0]["final_score"] == 80.0


def test_build_context_missing_keyword_returns_safe_default_object() -> None:
    context = build_recommendation_context(12345, FakeDB({}), _context_config())
    assert context is not None
    assert context.keyword_id == 12345
    assert context.niche_name == "Unknown"


def test_run_recommendations_stage_counts_invalid_keyword_as_failed(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 0, "final_score": 50.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (True, "ok"))
    summary = asyncio.run(run_recommendations_stage("run-6", db=Mock(), config={}, llm_client=None, cache=None))
    assert summary["failed"] == 1
    assert summary["generated"] == 0


def test_run_recommendations_stage_write_failure_counts_failed(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        "src.recommendations.run.get_eligible_keywords",
        lambda run_id, db, config: [{"keyword_id": 808, "final_score": 70.0}],
    )
    monkeypatch.setattr("src.recommendations.run.passes_recommendation_gates", lambda kw, db: (True, "ok"))
    monkeypatch.setattr("src.recommendations.run.should_regenerate_recommendation", lambda keyword_id, score, db: True)
    monkeypatch.setattr(
        "src.recommendations.run.build_recommendation_context",
        lambda keyword_id, db, config: RecommendationContext(keyword_id=keyword_id, keyword_text="k", niche_id=1),
    )
    monkeypatch.setattr("src.recommendations.run.write_recommendation", lambda *args, **kwargs: False)
    summary = asyncio.run(run_recommendations_stage("run-7", db=Mock(), config={}, llm_client=None, cache=None))
    assert summary["generated"] == 0
    assert summary["failed"] == 1


def test_passes_gates_invalid_keyword_id() -> None:
    ok, reason = passes_recommendation_gates({"keyword_id": 0}, _context_db())
    assert ok is False
    assert "Invalid keyword id" in reason


def test_extract_tag_and_confidence_defaults_when_raw_not_dict() -> None:
    from src.recommendations import eligibility

    row = SimpleNamespace(raw_json="not-a-dict")
    assert eligibility._extract_tag_from_raw(row) == "MONITOR"
    assert eligibility._extract_confidence_modifier(row) == 1.0


def test_resolve_demand_score_uses_keyword_score_model(monkeypatch: Any) -> None:
    from src.recommendations import eligibility

    class _KeywordScore:
        keyword_id = object()

    db = FakeDB({_KeywordScore: [SimpleNamespace(demand_score=47.0)]})
    monkeypatch.setattr(eligibility, "_model_by_name", lambda name: _KeywordScore if name == "KeywordScore" else None)
    assert eligibility._resolve_demand_score(101, {}, db) == 47.0


def test_has_gig_analysis_uses_registered_model(monkeypatch: Any) -> None:
    from src.recommendations import eligibility

    class _GigQuality:
        keyword_id = object()

        class analysis_complete:
            @staticmethod
            def is_(_value: object) -> object:
                return object()

    db = FakeDB({_GigQuality: [SimpleNamespace(keyword_id=101)]})
    monkeypatch.setattr(eligibility, "_model_by_name", lambda name: _GigQuality if name == "GigQualityScore" else None)
    assert eligibility._has_gig_analysis(101, db) is True


def test_write_recommendation_uses_sidecar_when_model_missing(monkeypatch: Any, tmp_path: Path) -> None:
    from src.recommendations import storage

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(storage, "_model_by_name", lambda _name: None)
    context = RecommendationContext(keyword_id=5, keyword_text="k", niche_id=1, niche_name="N", tag="MONITOR")
    assert write_recommendation(5, "run-no-model", context, {"generation_complete": True, "llm_cost_usd": 0.0}, db=Mock()) is True


def test_write_recommendation_persists_pricing_strategy_field(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    context = RecommendationContext(keyword_id=7, keyword_text="k", niche_id=1, niche_name="N", tag="MONITOR")
    payload = {
        "generation_complete": True,
        "llm_cost_usd": 0.0,
        "pricing_strategy": {"entry_prices": {"basic": 50}},
    }
    assert write_recommendation(7, "run-pricing", context, payload, db=None) is True
    persisted = json.loads((tmp_path / "data" / "recommendation_results" / "7_run-pricing.json").read_text())
    assert persisted["pricing_strategy"] == {"entry_prices": {"basic": 50}}


def test_write_recommendation_sidecar_write_failure_returns_false(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    context = RecommendationContext(keyword_id=6, keyword_text="k", niche_id=1, niche_name="N", tag="MONITOR")

    def _raise(*args: Any, **kwargs: Any) -> int:
        del args, kwargs
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", _raise)
    assert write_recommendation(6, "run-fail", context, {"generation_complete": True, "llm_cost_usd": 0.0}, db=None) is False


def test_storage_private_helpers_cover_fallback_branches() -> None:
    from src.recommendations import storage

    assert storage._model_by_name("DefinitelyMissingModel") is None
    assert storage._to_float("bad-value", 3.5) == 3.5


def test_tasks_private_parsers_fallback_paths() -> None:
    from src.recommendations import tasks

    assert tasks._parse_titles('{"titles":"bad"}') == []
    assert tasks._parse_tag_sets('{"tag_sets":"bad"}') == []
    assert tasks._parse_differentiation_angle('{"not_statement":"x"}') == ""
    assert tasks._parse_red_flags('{"risks":"bad"}') == []
    assert tasks._parse_faq_entries('{"faq_entries":"bad"}') == []
    assert tasks._parse_thumbnail_direction('{"nope":"x"}') == ""
    assert tasks._parse_upsell_structure("[]") == []
    assert tasks._parse_upsell_structure('{"something_else": 1}') == []


def test_tasks_private_runtime_fallback_paths() -> None:
    from src.recommendations import tasks

    class _Client:
        @staticmethod
        def complete(*, prompt: str, model: str, cache: Any | None = None) -> str:
            del prompt, model
            if cache is not None:
                raise TypeError("no cache support")
            return "ok"

    assert tasks._extract_cost_usd(SimpleNamespace(metadata={"estimated_cost_usd": "bad"})) == 0.0
    assert tasks._extract_cost_usd(SimpleNamespace(metadata={})) == 0.0
    assert tasks._extract_cost_usd(SimpleNamespace(metadata=None)) == 0.0
    assert tasks._to_float("bad", default=2.0) == 2.0
    assert tasks._complete_with_optional_cache(_Client(), "p", "m", cache=object()) == "ok"
    assert tasks._extract_llm_text("direct") == "direct"
    assert tasks._extract_llm_text(SimpleNamespace(text=None)) == "namespace(text=None)"
