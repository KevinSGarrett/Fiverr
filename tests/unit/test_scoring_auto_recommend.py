"""Unit tests for score-triggered auto recommendation wiring."""

from __future__ import annotations

import asyncio
from typing import Any

from src.scoring.pipeline import score_keyword


class FakePipelineDB:
    """In-memory signal source for scoring pipeline tests."""

    def __init__(self, depth: str = "standard") -> None:
        self._depth = depth
        self._base = {
            "total_result_count": 1000,
            "autocomplete_position": 2,
            "trends_12mo_score": 60,
            "reddit_demand_intent_score": 7.0,
            "avg_review_count_top10": 300,
            "avg_seller_level_top10": "Level 2",
            "proportion_with_100_plus_reviews": 0.5,
            "pro_verified_presence_ratio": 0.4,
            "avg_starting_price_top10": 45.0,
            "llm_competitor_strength_rating": 6.0,
            "level1_or_new_ratio_top10": 0.5,
            "lowest_ranked_review_count_page1": 10,
            "price_diversity_top10": 0.6,
            "llm_gig_quality_weakness_avg_top10": 6.5,
            "llm_entry_gap_assessment": 6.0,
            "avg_premium_package_price_top10": 200.0,
            "keyword_universe_starting_price_min": 20.0,
            "keyword_universe_starting_price_max": 200.0,
            "keyword_universe_premium_price_min": 60.0,
            "keyword_universe_premium_price_max": 400.0,
            "typical_delivery_days": 3,
            "extras_presence_ratio": 0.7,
            "avg_extras_price": 30.0,
            "llm_upsell_potential_assessment": 7.0,
            "keyword": "python automation script",
            "llm_buyer_intent_classification": "HIGH_INTENT",
            "total_gig_count": 3000,
            "title_duplication_rate": 0.4,
            "price_compression_signal": 0.3,
            "seller_portfolio_overlap_ratio": 0.4,
            "llm_saturation_assessment": 6.0,
            "video_absence_rate": 0.2,
            "portfolio_absence_rate": 0.3,
            "llm_description_quality_score": 6.0,
            "llm_weakness_count_per_gig": 3.0,
            "llm_thumbnail_quality_score": 7.0,
            "llm_faq_completeness_score": 7.0,
            "llm_package_differentiation_score": 6.0,
            "llm_niche_specificity_score": 6.5,
            "google_trends_slope": 8.0,
            "trends_3mo_avg": 65.0,
            "trends_12mo_avg": 55.0,
            "reddit_recent_post_volume": 25.0,
            "reddit_historical_post_volume": 20.0,
            "llm_trend_classification": "RISING",
        }

    def get_keyword_depth(self, keyword_id: int) -> str:
        del keyword_id
        return self._depth

    def _get(self, keyword_id: int) -> dict[str, Any]:
        del keyword_id
        return dict(self._base)

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_feasibility_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_profitability_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_intent_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_saturation_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_weakness_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)

    def get_trend_inputs(self, keyword_id: int) -> dict[str, Any]:
        return self._get(keyword_id)


def _setup_auto_recommend_mocks(monkeypatch, tag: str) -> dict[str, Any]:
    from src.scoring import pipeline

    calls: dict[str, Any] = {"generate": 0, "write": 0}

    async def _fake_generate(*args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        calls["generate"] += 1
        return {"generation_complete": True, "llm_cost_usd": 0.0}

    def _fake_write(*args: Any, **kwargs: Any) -> bool:
        del args, kwargs
        calls["write"] += 1
        return True

    monkeypatch.setattr(pipeline, "assign_tag", lambda _score, _modifier: tag)
    monkeypatch.setattr(pipeline, "write_keyword_score", lambda **kwargs: True)
    monkeypatch.setattr("src.recommendations.tasks.generate_recommendation", _fake_generate)
    monkeypatch.setattr("src.recommendations.storage.write_recommendation", _fake_write)
    monkeypatch.setattr(
        "src.recommendations.eligibility.should_regenerate_recommendation",
        lambda keyword_id, current_final_score, db: True,
    )
    return calls


def test_score_keyword_strong_go_triggers_recommendation(monkeypatch) -> None:
    calls = _setup_auto_recommend_mocks(monkeypatch, "STRONG_GO")
    result = asyncio.run(
        score_keyword(
            keyword_id=101,
            profile_name="default",
            db=FakePipelineDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )
    assert result["tag"] == "STRONG_GO"
    assert calls["generate"] == 1
    assert calls["write"] == 1


def test_score_keyword_conditional_go_triggers_recommendation(monkeypatch) -> None:
    calls = _setup_auto_recommend_mocks(monkeypatch, "CONDITIONAL_GO")
    result = asyncio.run(
        score_keyword(
            keyword_id=102,
            profile_name="default",
            db=FakePipelineDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )
    assert result["tag"] == "CONDITIONAL_GO"
    assert calls["generate"] == 1
    assert calls["write"] == 1


def test_score_keyword_no_go_does_not_trigger(monkeypatch) -> None:
    calls = _setup_auto_recommend_mocks(monkeypatch, "PASS")
    result = asyncio.run(
        score_keyword(
            keyword_id=103,
            profile_name="default",
            db=FakePipelineDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )
    assert result["tag"] == "PASS"
    assert calls["generate"] == 0
    assert calls["write"] == 0


def test_score_keyword_auto_generate_disabled(monkeypatch) -> None:
    calls = _setup_auto_recommend_mocks(monkeypatch, "STRONG_GO")
    result = asyncio.run(
        score_keyword(
            keyword_id=104,
            profile_name="default",
            db=FakePipelineDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": False}},
        )
    )
    assert result["tag"] == "STRONG_GO"
    assert calls["generate"] == 0
    assert calls["write"] == 0


def test_score_keyword_recommendation_exception_does_not_crash_scoring(monkeypatch) -> None:
    from src.scoring import pipeline

    async def _boom(*args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        raise RuntimeError("recommendation failure")

    monkeypatch.setattr(pipeline, "assign_tag", lambda _score, _modifier: "STRONG_GO")
    monkeypatch.setattr(pipeline, "write_keyword_score", lambda **kwargs: True)
    monkeypatch.setattr("src.recommendations.tasks.generate_recommendation", _boom)
    monkeypatch.setattr(
        "src.recommendations.eligibility.should_regenerate_recommendation",
        lambda keyword_id, current_final_score, db: True,
    )

    result = asyncio.run(
        score_keyword(
            keyword_id=105,
            profile_name="default",
            db=FakePipelineDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )
    assert result["keyword_id"] == 105
    assert result["tag"] == "STRONG_GO"


def test_score_keyword_trigger_is_idempotent(monkeypatch) -> None:
    from src.scoring import pipeline

    class _RegenAwareDb(FakePipelineDB):
        def query(self, *args: Any, **kwargs: Any) -> list[Any]:
            del args, kwargs
            return []

    calls = {"generate": 0}
    regen_responses = iter([True, False])

    async def _fake_generate(*args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        calls["generate"] += 1
        return {"generation_complete": True, "llm_cost_usd": 0.0}

    monkeypatch.setattr(pipeline, "assign_tag", lambda _score, _modifier: "STRONG_GO")
    monkeypatch.setattr(pipeline, "write_keyword_score", lambda **kwargs: True)
    monkeypatch.setattr("src.recommendations.tasks.generate_recommendation", _fake_generate)
    monkeypatch.setattr("src.recommendations.storage.write_recommendation", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        "src.recommendations.eligibility.should_regenerate_recommendation",
        lambda keyword_id, current_final_score, db: next(regen_responses),
    )

    asyncio.run(
        score_keyword(
            keyword_id=106,
            profile_name="default",
            db=_RegenAwareDb(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )
    asyncio.run(
        score_keyword(
            keyword_id=106,
            profile_name="default",
            db=_RegenAwareDb(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )

    assert calls["generate"] == 1


# ---------------------------------------------------------------------------
# Rank-11 (gap-audit-2 P1, SCRUM-1112): the auto path must use the full
# DB-backed context (pricing, competitor, review signals) when a real queryable
# db is available - previously it always hand-built a minimal context, so the
# pricing-aware builder was reachable from no production path at all and
# generate_pricing_strategy silently skipped on every real auto run.
# ---------------------------------------------------------------------------


class _QueryableFakeDB(FakePipelineDB):
    """Signals-fake that also looks like an ORM session (query returns [])."""

    def query(self, *args: Any, **kwargs: Any) -> list[Any]:
        del args, kwargs
        return []


def test_auto_recommendation_uses_full_context_when_db_queryable(monkeypatch) -> None:
    from src.recommendations.context import RecommendationContext
    from src.scoring import pipeline

    captured: dict[str, Any] = {}

    async def _fake_generate(**kwargs: Any) -> dict[str, Any]:
        captured["context"] = kwargs["context"]
        return {"generation_complete": True, "llm_cost_usd": 0.0}

    full_context = RecommendationContext(
        keyword_id=201,
        keyword_text="stale keyword text",
        niche_id=7,
        niche_name="Real Niche Name",
        tag="MONITOR",  # stale persisted tag - must be overlaid by this run's tag
        final_score=1.0,  # stale - must be overlaid
        price_distribution={"basic": {"min": 70.0, "max": 180.0, "median": 100.0}},
        market_type="MODERATE_SPREAD",
        top_buyer_complaints=["slow delivery"],
    )
    monkeypatch.setattr(
        "src.recommendations.context.build_recommendation_context",
        lambda keyword_id, db, config: full_context,
    )
    monkeypatch.setattr(pipeline, "assign_tag", lambda _score, _modifier: "STRONG_GO")
    monkeypatch.setattr(pipeline, "write_keyword_score", lambda **kwargs: True)
    monkeypatch.setattr("src.recommendations.tasks.generate_recommendation", _fake_generate)
    monkeypatch.setattr("src.recommendations.storage.write_recommendation", lambda *a, **k: True)
    monkeypatch.setattr(
        "src.recommendations.eligibility.should_regenerate_recommendation",
        lambda keyword_id, current_final_score, db: True,
    )

    result = asyncio.run(
        score_keyword(
            keyword_id=201,
            profile_name="default",
            db=_QueryableFakeDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )

    context = captured["context"]
    # Full DB-backed context fields survive...
    assert context.price_distribution == {"basic": {"min": 70.0, "max": 180.0, "median": 100.0}}
    assert context.market_type == "MODERATE_SPREAD"
    assert context.top_buyer_complaints == ["slow delivery"]
    assert context.niche_name == "Real Niche Name"
    # ...while this run's fresh results overlay the stale persisted values.
    assert context.tag == "STRONG_GO"
    assert context.final_score == result["final_score"]
    assert context.final_score != 1.0


def test_auto_recommendation_falls_back_to_minimal_context_on_builder_failure(monkeypatch) -> None:
    from src.scoring import pipeline

    captured: dict[str, Any] = {}

    async def _fake_generate(**kwargs: Any) -> dict[str, Any]:
        captured["context"] = kwargs["context"]
        return {"generation_complete": True, "llm_cost_usd": 0.0}

    def _boom_builder(keyword_id: int, db: Any, config: Any) -> Any:
        raise RuntimeError("context build exploded")

    monkeypatch.setattr("src.recommendations.context.build_recommendation_context", _boom_builder)
    monkeypatch.setattr(pipeline, "assign_tag", lambda _score, _modifier: "STRONG_GO")
    monkeypatch.setattr(pipeline, "write_keyword_score", lambda **kwargs: True)
    monkeypatch.setattr("src.recommendations.tasks.generate_recommendation", _fake_generate)
    monkeypatch.setattr("src.recommendations.storage.write_recommendation", lambda *a, **k: True)
    monkeypatch.setattr(
        "src.recommendations.eligibility.should_regenerate_recommendation",
        lambda keyword_id, current_final_score, db: True,
    )

    result = asyncio.run(
        score_keyword(
            keyword_id=202,
            profile_name="default",
            db=_QueryableFakeDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )

    # A context-builder failure must never block the recommendation itself.
    context = captured["context"]
    assert context.tag == "STRONG_GO"
    assert context.final_score == result["final_score"]
    assert context.price_distribution is None  # minimal fallback has no pricing data


def test_auto_recommendation_rolls_back_session_after_builder_failure(monkeypatch) -> None:
    """Codex finding on PR #168: a failed context query leaves a real Session in
    pending-rollback state, which would poison the fallback path's own
    generate/write calls on the same session - the helper must roll back before
    continuing with the minimal context."""
    from src.scoring import pipeline

    calls: dict[str, Any] = {"rollback": 0, "generate": 0, "write": 0}

    class _RollbackTrackingDB(_QueryableFakeDB):
        def rollback(self) -> None:
            calls["rollback"] += 1

    async def _fake_generate(**kwargs: Any) -> dict[str, Any]:
        calls["generate"] += 1
        return {"generation_complete": True, "llm_cost_usd": 0.0}

    def _fake_write(*args: Any, **kwargs: Any) -> bool:
        calls["write"] += 1
        return True

    def _boom_builder(keyword_id: int, db: Any, config: Any) -> Any:
        raise RuntimeError("query failed mid-transaction")

    monkeypatch.setattr("src.recommendations.context.build_recommendation_context", _boom_builder)
    monkeypatch.setattr(pipeline, "assign_tag", lambda _score, _modifier: "STRONG_GO")
    monkeypatch.setattr(pipeline, "write_keyword_score", lambda **kwargs: True)
    monkeypatch.setattr("src.recommendations.tasks.generate_recommendation", _fake_generate)
    monkeypatch.setattr("src.recommendations.storage.write_recommendation", _fake_write)
    monkeypatch.setattr(
        "src.recommendations.eligibility.should_regenerate_recommendation",
        lambda keyword_id, current_final_score, db: True,
    )

    asyncio.run(
        score_keyword(
            keyword_id=203,
            profile_name="default",
            db=_RollbackTrackingDB(),
            llm_client=None,
            cache=None,
            config={"recommendations": {"auto_generate": True}},
        )
    )

    assert calls["rollback"] >= 1  # session healed before the fallback continued
    assert calls["generate"] == 1  # recommendation still generated
    assert calls["write"] == 1  # and persisted
