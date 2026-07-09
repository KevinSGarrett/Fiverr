"""Unit tests for async scoring pipeline integration helpers."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, ExternalSignal, Gig, Keyword, Niche, SearchResult, Seller
from src.scoring.contracts import FeasibilityScoreResult, WeaknessScoreResult
from src.scoring.pipeline import (
    DEPTH_SCORE_AVAILABILITY,
    SCORING_PROFILES,
    assign_tag,
    calculate_final_score,
    calculate_weighted_composite,
    detect_red_flags_from_scores,
    generate_score_explanation,
    score_keyword,
    score_keyword_batch,
    validate_scoring_profile,
    write_keyword_score,
)


class FakePipelineDB:
    """In-memory signal source for pipeline tests."""

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


def test_assign_tag_strong_go() -> None:
    assert assign_tag(85.0, 0.9) == "STRONG_GO"


def test_assign_tag_pass() -> None:
    assert assign_tag(10.0, 1.0) == "PASS"


def test_assign_tag_confidence_demotion() -> None:
    assert assign_tag(75.0, 0.4) == "MONITOR"


def test_assign_tag_no_demotion_above_threshold() -> None:
    assert assign_tag(75.0, 0.6) == "CONDITIONAL_GO"


def test_depth_keyword_only_limits_scores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    result = asyncio.run(score_keyword(101, "default", FakePipelineDB("keyword_only"), None, None))
    assert result["score_depth"] == "scores_1_to_3"
    assert result["scores"]["feasibility_score"] is None
    assert result["scores"]["trend_score"] is None


def test_depth_standard_allows_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    result = asyncio.run(score_keyword(101, "default", FakePipelineDB("standard"), None, None))
    assert result["scores"]["feasibility_score"] is not None
    assert result["scores"]["trend_score"] is not None


def test_score_keyword_passes_llm_client_to_llm_capable_calculators(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Codex review, PR #176 (P1): score_keyword accepted llm_client/cache
    parameters but never forwarded them to intent/saturation/weakness/trend's own
    calculate() calls, so those calculators always fell back to their no-real-LLM
    warning paths (llm_not_implemented) even when a real llm_client was provided -
    which llm_analysis_completion_ratio then turns into a confidence penalty for
    runs where an LLM was actually available."""
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    sentinel_llm_client = object()
    sentinel_cache = object()
    recorded_calls: dict[str, dict[str, Any]] = {}

    def _make_fake_calculator(name: str) -> type:
        class _FakeCalculator:
            def calculate(self, *args: Any, **kwargs: Any) -> None:
                recorded_calls[name] = kwargs
                return None

        return _FakeCalculator

    monkeypatch.setattr(pipeline, "ConversionIntentScoreCalculator", _make_fake_calculator("intent"))
    monkeypatch.setattr(pipeline, "SaturationScoreCalculator", _make_fake_calculator("saturation"))
    monkeypatch.setattr(pipeline, "GigQualityWeaknessScoreCalculator", _make_fake_calculator("weakness"))
    monkeypatch.setattr(pipeline, "TrendScoreCalculator", _make_fake_calculator("trend"))

    asyncio.run(
        score_keyword(
            101,
            "default",
            FakePipelineDB("standard"),
            llm_client=sentinel_llm_client,
            cache=sentinel_cache,
        )
    )

    for name in ("intent", "saturation", "weakness", "trend"):
        assert recorded_calls[name].get("llm_client") is sentinel_llm_client, name
        assert recorded_calls[name].get("cache") is sentinel_cache, name


def test_score4_higher_when_low_weakness_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)

    def _fixed_feasibility(
        self: Any,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> FeasibilityScoreResult:
        del self, db, config
        return FeasibilityScoreResult(keyword_id=keyword_id, score_value=60.0)

    def _low_weakness(
        self: Any,
        keyword_id: int,
        db: Any,
        llm_client: Any | None = None,
        cache: Any | None = None,
    ) -> WeaknessScoreResult:
        del self, db, llm_client, cache
        return WeaknessScoreResult(keyword_id=keyword_id, score_value=20.0)

    def _high_weakness(
        self: Any,
        keyword_id: int,
        db: Any,
        llm_client: Any | None = None,
        cache: Any | None = None,
    ) -> WeaknessScoreResult:
        del self, db, llm_client, cache
        return WeaknessScoreResult(keyword_id=keyword_id, score_value=80.0)

    monkeypatch.setattr(pipeline.NewSellerFeasibilityCalculator, "calculate", _fixed_feasibility)
    monkeypatch.setattr(pipeline.GigQualityWeaknessScoreCalculator, "calculate", _low_weakness)
    low_payload = asyncio.run(score_keyword(901, "default", FakePipelineDB("standard"), None, None))

    monkeypatch.setattr(pipeline.GigQualityWeaknessScoreCalculator, "calculate", _high_weakness)
    high_payload = asyncio.run(score_keyword(901, "default", FakePipelineDB("standard"), None, None))

    assert low_payload["scores"]["feasibility_score"] is not None
    assert high_payload["scores"]["feasibility_score"] is not None
    assert low_payload["scores"]["feasibility_score"] > high_payload["scores"]["feasibility_score"]


def test_score4_lower_when_high_weakness_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)

    def _fixed_feasibility(
        self: Any,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> FeasibilityScoreResult:
        del self, keyword_id, db, config
        return FeasibilityScoreResult(score_value=60.0)

    def _high_weakness(
        self: Any,
        keyword_id: int,
        db: Any,
        llm_client: Any | None = None,
        cache: Any | None = None,
    ) -> WeaknessScoreResult:
        del self, keyword_id, db, llm_client, cache
        return WeaknessScoreResult(score_value=90.0)

    monkeypatch.setattr(pipeline.NewSellerFeasibilityCalculator, "calculate", _fixed_feasibility)
    monkeypatch.setattr(pipeline.GigQualityWeaknessScoreCalculator, "calculate", _high_weakness)
    payload = asyncio.run(score_keyword(902, "default", FakePipelineDB("standard"), None, None))

    assert payload["scores"]["feasibility_score"] is not None
    assert payload["scores"]["feasibility_score"] < 60.0


def test_calculate_weighted_composite_all_present() -> None:
    scores = {
        "demand_score": 80.0,
        "competition_score": 40.0,
        "opportunity_score": 70.0,
        "feasibility_score": 60.0,
        "profitability_score": 50.0,
        "intent_score": 60.0,
        "saturation_score": 30.0,
        "weakness_score": 65.0,
        "trend_score": 55.0,
    }
    composite, _ = calculate_weighted_composite(scores, SCORING_PROFILES["default"])
    assert composite > 0.0


def test_calculate_weighted_composite_missing_component() -> None:
    scores = {
        "demand_score": 80.0,
        "competition_score": 40.0,
        "opportunity_score": 70.0,
        "feasibility_score": None,
        "profitability_score": None,
        "intent_score": None,
        "saturation_score": None,
        "weakness_score": None,
        "trend_score": None,
    }
    composite, _ = calculate_weighted_composite(scores, SCORING_PROFILES["default"])
    assert composite > 0.0


def test_calculate_weighted_composite_competition_inverted() -> None:
    scores_low_comp = {
        "demand_score": 70.0,
        "competition_score": 10.0,
        "opportunity_score": 70.0,
        "feasibility_score": 70.0,
        "profitability_score": 70.0,
        "intent_score": 70.0,
        "saturation_score": 70.0,
        "weakness_score": 70.0,
        "trend_score": 70.0,
    }
    scores_high_comp = dict(scores_low_comp)
    scores_high_comp["competition_score"] = 90.0
    low_comp_value, _ = calculate_weighted_composite(scores_low_comp, SCORING_PROFILES["default"])
    high_comp_value, _ = calculate_weighted_composite(scores_high_comp, SCORING_PROFILES["default"])
    assert low_comp_value > high_comp_value


def test_calculate_final_score_confidence_floor() -> None:
    assert calculate_final_score(50.0, 0.0) == 10.0


def test_validate_scoring_profile_valid() -> None:
    validate_scoring_profile("default", SCORING_PROFILES["default"])


def test_validate_scoring_profile_invalid() -> None:
    with pytest.raises(ValueError):
        validate_scoring_profile("invalid", {"demand": 0.2, "competition_inv": 0.2})


def test_detect_red_flags_high_competition() -> None:
    flags = detect_red_flags_from_scores(
        {"competition_score": 90.0, "demand_score": 50.0, "trend_score": 50.0},
        {"confidence_modifier": 0.8},
        1,
        None,
    )
    assert any(flag["source"] == "competition_score" for flag in flags)


def test_detect_red_flags_low_confidence() -> None:
    flags = detect_red_flags_from_scores(
        {"competition_score": 30.0, "demand_score": 50.0, "trend_score": 50.0},
        {"confidence_modifier": 0.3},
        1,
        None,
    )
    assert any(flag["source"] == "confidence_modifier" for flag in flags)


def test_write_keyword_score_returns_true(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    ok = write_keyword_score(
        keyword_id=100,
        scores={"demand_score": 70.0, "competition_score": 30.0},
        weighted_composite=75.0,
        confidence_modifier=0.9,
        final_score=67.5,
        tag="CONDITIONAL_GO",
        score_components={},
        confidence_breakdown={},
        explanation_text="test",
        red_flags=[],
        scoring_profile="default",
        score_depth="all_11",
        db=None,
    )
    assert ok is True
    assert (tmp_path / "100.json").exists()


def test_red_flags_empty_for_good_scores() -> None:
    flags = detect_red_flags_from_scores(
        {"competition_score": 20.0, "demand_score": 80.0, "trend_score": 70.0},
        {"confidence_modifier": 0.9},
        1,
        None,
    )
    assert flags == []


def test_score_keyword_batch_handles_empty() -> None:
    result = asyncio.run(score_keyword_batch([], "default", FakePipelineDB(), None, None))
    assert result == []


def test_write_keyword_score_creates_json_sidecar(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    write_keyword_score(
        keyword_id=200,
        scores={"demand_score": 88.0, "competition_score": 22.0},
        weighted_composite=80.0,
        confidence_modifier=0.95,
        final_score=76.0,
        tag="CONDITIONAL_GO",
        score_components={"demand_score": {"weight": 0.2}},
        confidence_breakdown={"remaining_modifier": 0.95},
        explanation_text="pipeline write",
        red_flags=[],
        scoring_profile="default",
        score_depth="all_11",
        db=None,
    )
    payload = json.loads((tmp_path / "200.json").read_text(encoding="utf-8"))
    assert payload["keyword_id"] == 200
    assert payload["tag"] == "CONDITIONAL_GO"


def test_score_keyword_handles_sparse_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    class SparseDB(FakePipelineDB):
        def __init__(self) -> None:
            super().__init__(depth="keyword_only")
            self._base = {}

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    result = asyncio.run(score_keyword(404, "default", SparseDB(), llm_client=None, cache=None))
    assert result["keyword_id"] == 404
    assert result["scores"]["demand_score"] is None
    assert result["scores"]["feasibility_score"] is None


def test_score_keyword_batch_mixed_success_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    async def _fake_score_keyword(
        keyword_id: int,
        profile_name: str,
        db: Any,
        llm_client: Any,
        cache: Any,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del profile_name, db, llm_client, cache, config
        if keyword_id == 2:
            raise RuntimeError("boom")
        return {"keyword_id": keyword_id, "final_score": 50.0, "tag": "MONITOR", "persisted": True}

    monkeypatch.setattr(pipeline, "score_keyword", _fake_score_keyword)
    payload = asyncio.run(score_keyword_batch([1, 2, 3], "default", FakePipelineDB(), None, None))
    assert len(payload) == 3
    assert payload[1]["keyword_id"] == 2
    assert payload[1]["persisted"] is False
    assert payload[1]["tag"] == "PASS"
    assert "boom" in payload[1]["error"]


def test_write_keyword_score_creates_missing_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    target_dir = tmp_path / "nested" / "scoring_results"
    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", target_dir)
    ok = write_keyword_score(
        keyword_id=777,
        scores={"demand_score": 42.0},
        weighted_composite=42.0,
        confidence_modifier=1.0,
        final_score=42.0,
        tag="MONITOR",
        score_components={},
        confidence_breakdown={},
        explanation_text="ok",
        red_flags=[],
        scoring_profile="default",
        score_depth="scores_1_to_5",
        db=None,
    )
    assert ok is True
    assert target_dir.exists()
    assert (target_dir / "777.json").exists()


def test_detect_red_flags_declining_trend_has_medium_severity() -> None:
    flags = detect_red_flags_from_scores(
        {"competition_score": 30.0, "demand_score": 50.0, "trend_score": 24.0},
        {"confidence_modifier": 0.8},
        1,
        None,
    )
    assert any(flag["source"] == "trend_score" and flag["severity"] == "MEDIUM" for flag in flags)


def test_depth_availability_feasibility_excludes_scores_6_to_9() -> None:
    feasibility = DEPTH_SCORE_AVAILABILITY["feasibility"]
    for score_idx in (6, 7, 8, 9):
        assert score_idx not in feasibility


def test_validate_scoring_profile_accepts_999_total() -> None:
    validate_scoring_profile("tolerant", {"a": 0.333, "b": 0.333, "c": 0.333})


def test_calculate_final_score_applies_confidence_floor_for_zero_modifier() -> None:
    assert calculate_final_score(100.0, 0.0) == 20.0


def test_generate_score_explanation_no_llm() -> None:
    text = asyncio.run(
        generate_score_explanation(
            keyword_id=1,
            keyword_text="ai assistant",
            scores={"confidence_modifier": 0.88, "scoring_profile": "default"},
            components={"demand_score": {"contribution": 12.5}},
            final_score=72.3,
            tag="CONDITIONAL_GO",
            llm_client=None,
            cache=None,
        )
    )
    assert text.startswith("Final score:")


def test_generate_score_explanation_template_contains_score() -> None:
    text = asyncio.run(
        generate_score_explanation(
            keyword_id=2,
            keyword_text="automation",
            scores={"confidence_modifier": 0.5, "scoring_profile": "default"},
            components={"demand_score": {"contribution": 11.0}},
            final_score=55.7,
            tag="MONITOR",
            llm_client=None,
            cache=None,
        )
    )
    assert "55.7" in text


def test_generate_score_explanation_template_contains_tag() -> None:
    text = asyncio.run(
        generate_score_explanation(
            keyword_id=3,
            keyword_text="automation",
            scores={"confidence_modifier": 0.5, "scoring_profile": "default"},
            components={"demand_score": {"contribution": 11.0}},
            final_score=45.7,
            tag="MONITOR",
            llm_client=None,
            cache=None,
        )
    )
    assert "(MONITOR)" in text


def test_generate_score_explanation_llm_mock() -> None:
    class _MockLLM:
        @staticmethod
        async def complete(**kwargs: Any) -> Any:
            del kwargs
            return type("Resp", (), {"text": "LLM explanation"})()

    text = asyncio.run(
        generate_score_explanation(
            keyword_id=4,
            keyword_text="automation",
            scores={"confidence_modifier": 0.7, "scoring_profile": "default"},
            components={"demand_score": {"contribution": 9.0}},
            final_score=60.0,
            tag="CONDITIONAL_GO",
            llm_client=_MockLLM(),
            cache=None,
        )
    )
    assert text == "LLM explanation"


def test_generate_score_explanation_llm_failure() -> None:
    class _MockLLM:
        @staticmethod
        def complete(**kwargs: Any) -> Any:
            del kwargs
            raise RuntimeError("llm failed")

    text = asyncio.run(
        generate_score_explanation(
            keyword_id=5,
            keyword_text="automation",
            scores={"confidence_modifier": 0.7, "scoring_profile": "default"},
            components={"demand_score": {"contribution": 9.0}},
            final_score=60.0,
            tag="CONDITIONAL_GO",
            llm_client=_MockLLM(),
            cache=None,
        )
    )
    assert text.startswith("Final score:")


def test_generate_score_explanation_empty_components() -> None:
    text = asyncio.run(
        generate_score_explanation(
            keyword_id=6,
            keyword_text="automation",
            scores={"confidence_modifier": 0.7, "scoring_profile": "default"},
            components={},
            final_score=60.0,
            tag="CONDITIONAL_GO",
            llm_client=None,
            cache=None,
        )
    )
    assert "Top drivers:" in text


def test_score_keyword_explanation_populated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    result = asyncio.run(score_keyword(808, "default", FakePipelineDB("standard"), llm_client=None, cache=None))
    assert isinstance(result["explanation_text"], str)
    assert result["explanation_text"]


def test_confidence_context_uses_reddit_signal_presence_from_db() -> None:
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx2", name="Context2", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="context keyword", normalized_keyword="context keyword")
    session.add(keyword)
    session.flush()
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_demand",
            signal_value=1.0,
            signal_json={"reddit_demand_intent_score": 1.0},
            collected_at=datetime.now(UTC),
            run_id="ctx-run",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=["reddit_not_implemented"],
        db=session,
    )
    assert context["reddit_signals_available"] is True


def test_confidence_context_handles_naive_external_signal_timestamp() -> None:
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx3", name="Context3", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="naive timestamp keyword", normalized_keyword="naive timestamp keyword")
    session.add(keyword)
    session.flush()
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_demand",
            signal_value=1.0,
            signal_json={"reddit_demand_intent_score": 1.0},
            collected_at=datetime.now(),
            run_id="ctx-run-naive",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=["reddit_not_implemented"],
        db=session,
    )
    assert context["signal_age_days"] >= 0
    assert context["external_signal_context_present"] is True


def test_confidence_context_detects_real_gig_detail_and_seller_profile_collection() -> None:
    """SCRUM-1153: gig_detail_collected/seller_profiles_collected must reflect real
    Gig.detail_collected_at/Seller.profile_collected state, not a hardcoded True."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-detail", name="ContextDetail", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="detailed keyword", normalized_keyword="detailed keyword")
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="detailed_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do detailed work",
        normalized_title="detailed work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=50.0,
            signal_json={"trends_12mo_score": 60.0},
            collected_at=datetime.now(UTC),
            run_id="ctx-detail-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["gig_detail_collected"] is True
    assert context["seller_profiles_collected"] is True
    assert context["source_diversity_score"] == pytest.approx(1.0)
    assert context["data_freshness_score"] == pytest.approx(1.0, abs=0.01)


def test_confidence_context_diversity_requires_real_google_trends_signal() -> None:
    """Codex review, PR #176 (P2): TrendScoreCalculator can produce a non-null
    trend_score from Reddit plus LLM classification alone with Google Trends
    absent. A non-null trend_score must not be treated as proof Google Trends
    contributed to source_diversity_score."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-trend-no-google", name="ContextTrendNoGoogle", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="trend no google keyword", normalized_keyword="trend no google keyword"
    )
    session.add(keyword)
    session.flush()
    # Only a Reddit signal exists - no google_trends row - yet trend_score is non-null
    # (TrendScoreCalculator can score from Reddit + LLM classification alone).
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_demand",
            signal_value=1.0,
            signal_json={},
            collected_at=datetime.now(UTC),
            run_id="ctx-trend-no-google-run",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is False


def test_confidence_context_requires_usable_google_trends_payload() -> None:
    """Codex review, PR #176 (P2): DemandScoreCalculator/TrendScoreCalculator both
    treat a google_trends row with no trends_12mo_score/slope/series data as
    missing (their own missing_google_trends deductions fire). A mere row of that
    signal_type with an empty payload must not be treated as proof Google Trends
    contributed to source_diversity_score."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-google-trends-empty", name="ContextGoogleTrendsEmpty", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="google trends empty keyword", normalized_keyword="google trends empty keyword"
    )
    session.add(keyword)
    session.flush()
    # A google_trends row exists, but its payload has none of the fields
    # DemandScoreCalculator/TrendScoreCalculator actually read.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=None,
            signal_json={},
            collected_at=datetime.now(UTC),
            run_id="ctx-google-trends-empty-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is False


def test_confidence_context_counts_legacy_signal_value_google_trends_as_available() -> None:
    """Codex review, PR #176 (P2): DemandScoreCalculator._signal_float falls back to
    the row's own signal_value/normalized_value when trends_12mo_score is absent
    from the JSON payload (a legacy/back-compat shape). That fallback still feeds
    demand scoring, so it must count as usable Google Trends data even with an
    empty JSON payload."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-google-trends-legacy", name="ContextGoogleTrendsLegacy", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="google trends legacy keyword", normalized_keyword="google trends legacy keyword"
    )
    session.add(keyword)
    session.flush()
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=72.0,
            signal_json={},
            collected_at=datetime.now(UTC),
            run_id="ctx-google-trends-legacy-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is True


def test_confidence_context_ignores_unread_trends_3mo_score_field() -> None:
    """Codex review, PR #176 (P2): trends_3mo_score is extracted into
    TrendScoreCalculator's signals dict (_load_signals_from_db) but never read by
    any of its _resolve_* methods - a google_trends row containing only that field
    must not count as proof Google Trends contributed to source_diversity_score."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-google-trends-unread-field", name="ContextGoogleTrendsUnreadField", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="google trends unread field keyword",
        normalized_keyword="google trends unread field keyword",
    )
    session.add(keyword)
    session.flush()
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=None,
            signal_json={"trends_3mo_score": 42.0},
            collected_at=datetime.now(UTC),
            run_id="ctx-google-trends-unread-field-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is False


def test_confidence_context_requires_both_sides_of_trend_acceleration_average() -> None:
    """Codex review, PR #176 (P2): TrendScoreCalculator._resolve_acceleration_score
    returns None unless BOTH a 3mo and a 12mo average (explicit or series-derived)
    are present - one side alone must not count as usable Google Trends data."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-google-trends-one-sided", name="ContextGoogleTrendsOneSided", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="google trends one sided keyword",
        normalized_keyword="google trends one sided keyword",
    )
    session.add(keyword)
    session.flush()
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=None,
            signal_json={"trends_12mo_avg": 55.0},
            collected_at=datetime.now(UTC),
            run_id="ctx-google-trends-one-sided-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is False


def test_confidence_context_counts_trend_acceleration_average_as_usable() -> None:
    """Codex review, PR #176 (P2): with both a 3mo and a 12mo average present,
    TrendScoreCalculator._resolve_acceleration_score can produce a real score -
    that must count as usable Google Trends data."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-google-trends-acceleration", name="ContextGoogleTrendsAcceleration", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="google trends acceleration keyword",
        normalized_keyword="google trends acceleration keyword",
    )
    session.add(keyword)
    session.flush()
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=None,
            signal_json={"trends_3mo_avg": 65.0, "trends_12mo_avg": 55.0},
            collected_at=datetime.now(UTC),
            run_id="ctx-google-trends-acceleration-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is True


def test_confidence_context_resolves_gigs_from_gig_cards() -> None:
    """Codex review, PR #176 (P2): a page-level SearchResult row can carry multiple
    gig cards in gig_cards beyond the single gig_id it links to.
    ProfitabilityScoreCalculator/GigQualityWeaknessScoreCalculator resolve those card
    URLs to real top-N gigs too - a fresh linked gig must not hide a stale,
    zombie card gig referenced only via gig_cards."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-gig-cards", name="ContextGigCards", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="gig cards keyword", normalized_keyword="gig cards keyword")
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="gig_cards_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    # The linked gig is fresh and not a zombie.
    linked_gig = Gig(
        seller_id=seller.id,
        title="I will do fresh linked work",
        normalized_title="fresh linked work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
    )
    session.add(linked_gig)
    # A second gig on the same page, referenced only via gig_cards (no SearchResult
    # row links to it directly), and it is a zombie. run_id="legacy" matches
    # write_search_result's implicit default for a SearchResult that doesn't specify
    # one below, so the active-run-scoped exact card-URL match can find it.
    card_only_gig = Gig(
        seller_id=seller.id,
        run_id="legacy",
        gig_url="https://www.fiverr.com/card_only_gig",
        title="I will do zombie card work",
        normalized_title="zombie card work",
        is_zombie=True,
    )
    session.add(card_only_gig)
    session.commit()
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            rank=1,
            gig_id=linked_gig.id,
            title=linked_gig.title,
            gig_cards=[{"gig_url": linked_gig.gig_url, "position": 1}, {"gig_url": card_only_gig.gig_url, "position": 2}],
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["zombie_fraction"] == pytest.approx(0.5)


def test_confidence_context_limits_card_gigs_to_scoring_window() -> None:
    """Codex review, PR #176 (P2): write_search_result stamps a whole page's
    SearchResult row with its first card's rank, so a single page row can carry
    gig_cards positions well outside top_n_for_scoring. Card URLs must be sorted by
    position and sliced to the same scoring window the loaders use before being
    resolved to gigs, or a bad card far down the page can wrongly demote
    confidence."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-card-window", name="ContextCardWindow", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="card window keyword", normalized_keyword="card window keyword")
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="card_window_seller", profile_collected=True)
    session.add(seller)
    session.flush()

    gig_cards = []
    for position in range(1, 13):
        # Positions 1-10 fall inside the default top_n_for_scoring window and are
        # healthy; positions 11-12 fall outside it and are zombies that must be
        # ignored.
        is_zombie = position > 10
        # run_id="legacy" matches write_search_result's implicit default for the
        # SearchResult below, so the active-run-scoped exact card-URL match can find
        # these gigs.
        gig = Gig(
            seller_id=seller.id,
            run_id="legacy",
            gig_url=f"https://www.fiverr.com/card_window_gig_{position}",
            title=f"I will do card window work {position}",
            normalized_title=f"card window work {position}",
            detail_collected=True,
            detail_collected_at=datetime.now(UTC),
            is_zombie=is_zombie,
        )
        session.add(gig)
        gig_cards.append({"gig_url": gig.gig_url, "position": position})
    session.commit()

    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_cards=gig_cards))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    # Only positions 1-10 (the top_n_for_scoring window) should resolve to real
    # gigs - the zombie cards at positions 11-12 must not count.
    assert context["zombie_fraction"] == pytest.approx(0.0)


def test_confidence_context_reaches_organic_gigs_past_sponsored_top_positions() -> None:
    """Codex review, PR #176 (P2): when sponsored slots occupy some of the first
    top_n_for_scoring card positions, the real top-N organic gigs that fed the score
    sit further down the page. ProfitabilityScoreCalculator/the feasibility loader
    gather a wider candidate_window, skip sponsored, and slice to the top N organic
    gigs - confidence must reach those same organic gigs instead of cutting off at
    a naive top_n_for_scoring position cutoff."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-sponsored-window", name="ContextSponsoredWindow", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="sponsored window keyword", normalized_keyword="sponsored window keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="sponsored_window_seller", profile_collected=True)
    session.add(seller)
    session.flush()

    gig_cards = []
    for position in range(1, 14):
        # Positions 1-3 are sponsored - the top_n_for_scoring=10 organic gigs that
        # actually fed the real score are positions 4-13, reaching past position 10.
        is_sponsored = position <= 3
        # The last organic gig (position 13) - unreachable under the old
        # top_n_for_scoring-sized card_gig_urls limit - is a zombie.
        is_zombie = position == 13
        gig = Gig(
            seller_id=seller.id,
            run_id="legacy",
            gig_url=f"https://www.fiverr.com/sponsored_window_gig_{position}",
            title=f"I will do sponsored window work {position}",
            normalized_title=f"sponsored window work {position}",
            detail_collected=True,
            detail_collected_at=datetime.now(UTC),
            is_sponsored=is_sponsored,
            is_zombie=is_zombie,
        )
        session.add(gig)
        gig_cards.append({"gig_url": gig.gig_url, "position": position})
    session.commit()

    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_cards=gig_cards))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    # The top 10 organic gigs are positions 4-13 (one of them, position 13, a
    # zombie) - the sponsored slots at 1-3 must not crowd them out of the window.
    assert context["zombie_fraction"] == pytest.approx(0.1)


def test_confidence_context_reaches_organic_gigs_past_sponsored_ranked_rows() -> None:
    """Codex review, PR #176 (P2): ProfitabilityScoreCalculator/the feasibility
    loader load rank <= candidate_window (not top_n_for_scoring) for per-gig-rank-
    linked SearchResult rows too, so sponsored gigs occupying the first ranks don't
    crowd the organic gigs that fed the score out of confidence's window."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-ranked-sponsored-window", name="ContextRankedSponsoredWindow", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="ranked sponsored window keyword",
        normalized_keyword="ranked sponsored window keyword",
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="ranked_sponsored_window_seller", profile_collected=True)
    session.add(seller)
    session.flush()

    for rank in range(1, 14):
        # Ranks 1-3 are sponsored - the top_n_for_scoring=10 organic gigs that
        # actually fed the real score are ranks 4-13.
        is_sponsored = rank <= 3
        # The last organic gig (rank 13) - unreachable under the old
        # top_n_for_scoring-sized SearchResult rank filter - is a zombie.
        is_zombie = rank == 13
        gig = Gig(
            seller_id=seller.id,
            title=f"I will do ranked sponsored window work {rank}",
            normalized_title=f"ranked sponsored window work {rank}",
            detail_collected=True,
            detail_collected_at=datetime.now(UTC),
            is_sponsored=is_sponsored,
            is_zombie=is_zombie,
        )
        session.add(gig)
        session.flush()
        session.add(SearchResult(keyword_id=keyword.id, rank=rank, gig_id=gig.id, title=gig.title))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["zombie_fraction"] == pytest.approx(0.1)


def test_confidence_context_ignores_freshness_of_unused_candidate_window_rows() -> None:
    """Codex review, PR #176 (P2): a later SearchResult row from deeper in the
    widened candidate_window that was never admitted to the scored top-N window
    (because the organic quota was already met) never contributed to the score and
    must not affect data_freshness_score."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(
        slug="ctx-unused-candidate-freshness", name="ContextUnusedCandidateFreshness", category_path="a/b"
    )
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="unused candidate freshness keyword",
        normalized_keyword="unused candidate freshness keyword",
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="unused_candidate_freshness_seller", profile_collected=True)
    session.add(seller)
    session.flush()

    ancient_at = datetime.now(UTC) - timedelta(hours=3000)
    fresh_at = datetime.now(UTC)
    for rank in range(1, 14):
        # Ranks 1-10 fill the top_n_for_scoring=10 organic quota and are fresh.
        # Ranks 11-13 fall past the quota (never admitted) and are ancient.
        within_quota = rank <= 10
        gig = Gig(
            seller_id=seller.id,
            title=f"I will do unused candidate freshness work {rank}",
            normalized_title=f"unused candidate freshness work {rank}",
            detail_collected=True,
            detail_collected_at=fresh_at if within_quota else ancient_at,
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                rank=rank,
                gig_id=gig.id,
                title=gig.title,
                collected_at=fresh_at if within_quota else ancient_at,
            )
        )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_freshness_score"] == pytest.approx(1.0)


def test_confidence_context_resolves_card_gigs_via_normalized_url_identity() -> None:
    """Codex review, PR #176 (P2): ProfitabilityScoreCalculator/WeaknessCalculator
    normalize card URLs by path identity and fall back through the keyword's own
    gigs when an exact string match misses (tracking query strings, fragments,
    URL-encoded paths, trailing slashes). Confidence must resolve the same gig via
    the same identity match instead of silently dropping it."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-card-url-identity", name="ContextCardUrlIdentity", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="card url identity keyword", normalized_keyword="card url identity keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="card_url_identity_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    # The persisted Gig's URL differs from the card's URL only by a tracking query
    # string - an exact Gig.gig_url.in_(...) match must not miss it. run_id="legacy"
    # matches the SearchResult's implicit default below, so this is reachable via
    # the keyword+run-scoped identity fallback specifically (not the unscoped
    # total_organic==0 recovery tier, which would mask this test's intent).
    zombie_gig = Gig(
        seller_id=seller.id,
        keyword_id=keyword.id,
        run_id="legacy",
        gig_url="https://www.fiverr.com/card_identity_gig",
        title="I will do zombie identity work",
        normalized_title="zombie identity work",
        is_zombie=True,
    )
    session.add(zombie_gig)
    session.commit()

    session.add(
        SearchResult(
            keyword_id=keyword.id,
            rank=1,
            gig_cards=[{"gig_url": "https://www.fiverr.com/card_identity_gig?ref=track_123", "position": 1}],
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["zombie_fraction"] == pytest.approx(1.0)


def test_confidence_context_scopes_exact_card_gig_match_to_active_run() -> None:
    """Codex review, PR #176 (P2): Gig.gig_url is only unique for the row's current
    collection state, not scoped to a particular run - a Gig row last updated by a
    different/older run must not be pulled in as the active run's card gig just
    because its URL matches a card on the active run's page, mirroring
    ProfitabilityScoreCalculator's active-run filter on its own exact card-URL
    lookup."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-card-run-scope", name="ContextCardRunScope", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="card run scope keyword", normalized_keyword="card run scope keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="card_run_scope_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    # Directly linked to the active run's SearchResult row, fresh and not a zombie -
    # total_organic > 0 so the total_organic==0 fallback tier never engages, keeping
    # this test isolated to the exact card-URL match path.
    linked_gig = Gig(
        seller_id=seller.id,
        title="I will do fresh linked run work",
        normalized_title="fresh linked run work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
    )
    session.add(linked_gig)
    # This Gig row's URL is referenced by the active run's gig_cards, but the row
    # itself was last updated by a DIFFERENT, older run - and it is a zombie.
    stale_gig = Gig(
        seller_id=seller.id,
        keyword_id=keyword.id,
        run_id="ctx-card-run-scope-old-run",
        gig_url="https://www.fiverr.com/card_run_scope_gig",
        title="I will do stale run gig work",
        normalized_title="stale run gig work",
        is_zombie=True,
    )
    session.add(stale_gig)
    session.commit()

    session.add(
        SearchResult(
            keyword_id=keyword.id,
            rank=1,
            gig_id=linked_gig.id,
            run_id="ctx-card-run-scope-new-run",
            title=linked_gig.title,
            gig_cards=[{"gig_url": stale_gig.gig_url, "position": 2}],
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    # The other run's zombie gig must not be counted just because its URL matches.
    assert context["zombie_fraction"] == pytest.approx(0.0)


def test_confidence_context_honors_disabled_sponsored_exclusion_config() -> None:
    """Codex review, PR #176 (P2): ProfitabilityScoreCalculator/FeasibilityCalculator
    /CompetitionScoreCalculator all gate their own sponsored-gig skip on
    relevance.enable_sponsored_exclusion (default True). When a deployment disables
    it, sponsored gigs stay in the real scored top-N set - confidence must resolve
    their detail/freshness state too instead of unconditionally dropping them."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-sponsored-included", name="ContextSponsoredIncluded", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="sponsored included keyword", normalized_keyword="sponsored included keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="sponsored_included_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    # The only gig is sponsored, but it does have real, fresh detail data.
    gig = Gig(
        seller_id=seller.id,
        title="I will do sponsored included work",
        normalized_title="sponsored included work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
        is_sponsored=True,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
        config={"relevance": {"enable_sponsored_exclusion": False}},
    )
    assert context["gig_detail_collected"] is True


def test_confidence_context_reports_missing_gig_detail_and_seller_profile() -> None:
    """SCRUM-1153: a gig/seller with no detail/profile collected must NOT be
    silently reported as collected."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-missing", name="ContextMissing", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="undetailed keyword", normalized_keyword="undetailed keyword")
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="undetailed_seller")
    session.add(seller)
    session.flush()
    gig = Gig(seller_id=seller.id, title="I will do undetailed work", normalized_title="undetailed work")
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["gig_detail_collected"] is False
    assert context["seller_profiles_collected"] is False
    assert context["source_diversity_score"] == pytest.approx(0.0)


def test_confidence_context_keyword_only_depth_preserves_lenient_detail_flags() -> None:
    """Codex review, PR #176 (P2): _queue_gig_detail_jobs
    (src/collection/workflows/fiverr_search.py) returns 0 unconditionally for
    depth="keyword_only" - no gig/seller in that run will ever have
    detail_collected/profile_collected=True. confidence.py already applies a
    separate partial_depth_mode deduction for keyword_only - missing_gig_detail/
    missing_seller_profiles must not stack on top of it for data that was never in
    scope to collect."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-keyword-only-lenient", name="ContextKeywordOnlyLenient", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="keyword only lenient keyword", normalized_keyword="keyword only lenient keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="keyword_only_lenient_seller")
    session.add(seller)
    session.flush()
    # No detail_collected/profile_collected - exactly what a keyword_only run's gigs
    # actually look like, since detail collection is structurally never queued.
    gig = Gig(seller_id=seller.id, title="I will do keyword-only work", normalized_title="keyword-only work")
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="keyword_only",
        warnings=[],
        db=session,
    )
    assert context["gig_detail_collected"] is True
    assert context["seller_profiles_collected"] is True


def test_confidence_context_requires_detail_collected_flag_not_just_timestamp() -> None:
    """Codex review, PR #176 (P2): Gig.is_stale() requires BOTH detail_collected
    (bool) and detail_collected_at. write_gig_card() resets detail_collected=False
    on every re-seen search card WITHOUT clearing the old detail_collected_at, so a
    stale leftover timestamp alone must not be treated as proof detail collection
    succeeded for the current run."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-invalidated-detail", name="ContextInvalidatedDetail", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="invalidated detail keyword", normalized_keyword="invalidated detail keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="invalidated_detail_seller")
    session.add(seller)
    session.flush()
    # A gig re-seen by card collection: detail_collected reset to False, but the old
    # detail_collected_at timestamp from a prior successful scrape was left intact.
    gig = Gig(
        seller_id=seller.id,
        title="I will do work with invalidated detail",
        normalized_title="invalidated detail work",
        detail_collected=False,
        detail_collected_at=datetime.now(UTC),
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["gig_detail_collected"] is False


def test_confidence_context_reddit_demand_freshness_independent_of_reddit_activity() -> None:
    """Codex review, PR #176 (P2): demand/intent scoring reads reddit_demand
    specifically, regardless of reddit_activity's freshness. A stale reddit_demand
    row that is still the one actually used by scoring must not be hidden behind a
    fresher reddit_activity row that only feeds trend scoring."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-reddit-demand-stale", name="ContextRedditDemandStale", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="reddit demand stale keyword", normalized_keyword="reddit demand stale keyword"
    )
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=2000)
    fresh_at = datetime.now(UTC)
    # Stale reddit_demand row - still the one demand/intent scoring actually reads.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_demand",
            signal_value=1.0,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-reddit-demand-stale-run",
            collection_method="reddit_devvit_bridge",
        )
    )
    # Fresh reddit_activity row - only feeds trend scoring's combined pool.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_activity",
            signal_value=1.0,
            signal_json={},
            collected_at=fresh_at,
            run_id="ctx-reddit-demand-stale-run",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    # The stale reddit_demand row must still be able to drive staleness even though a
    # fresher reddit_activity row exists for the same keyword.
    assert context["data_age_hours"] >= 168.0


def test_confidence_context_ignores_disabled_youtube_signal_freshness() -> None:
    """Codex review, PR #176 (P2): youtube_count is only ever consumed by
    ConfidenceScoreModifier's own youtube-confidence-gate when
    external_signals_enabled is true. A stale leftover youtube_count row must not
    depress freshness while that feature is disabled, since nothing reads it."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-youtube-disabled", name="ContextYoutubeDisabled", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="youtube disabled keyword", normalized_keyword="youtube disabled keyword"
    )
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=2000)
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_YOUTUBE_COUNT,
            signal_value=1.0,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-youtube-disabled-run",
            collection_method="youtube_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
        config={"analysis": {"external_signals_enabled": False}},
    )
    assert context["data_freshness_score"] == pytest.approx(1.0)


def test_confidence_context_ignores_disabled_autocomplete_signal_freshness() -> None:
    """Codex review, PR #176 (P2): DemandScoreCalculator reads its
    "autocomplete_position" signal from Keyword.metadata_json, not this
    ExternalSignal row - the row's own JSON payload is only consulted by
    _classify_autocomplete_absence, itself only called when
    external_signals_enabled is true. A stale leftover row must not depress
    freshness while that feature is disabled, since nothing reads it."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-autocomplete-disabled", name="ContextAutocompleteDisabled", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="autocomplete disabled keyword",
        normalized_keyword="autocomplete disabled keyword",
    )
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=2000)
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_AUTOCOMPLETE_POSITION,
            signal_value=1.0,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-autocomplete-disabled-run",
            collection_method="fiverr_autocomplete",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
        config={"analysis": {"external_signals_enabled": False}},
    )
    assert context["data_freshness_score"] == pytest.approx(1.0)


def test_confidence_context_ignores_unusable_google_trends_row_in_freshness() -> None:
    """Codex review, PR #176 (P2): an empty/failed google_trends row (no field
    either DemandScoreCalculator or TrendScoreCalculator reads) is already reported
    as missing via google_trends_available - it must not also depress
    data_freshness_score, since nothing consumes it either way."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(
        slug="ctx-google-trends-unusable-freshness",
        name="ContextGoogleTrendsUnusableFreshness",
        category_path="a/b",
    )
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="google trends unusable freshness keyword",
        normalized_keyword="google trends unusable freshness keyword",
    )
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=3000)
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
            signal_value=None,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-google-trends-unusable-freshness-run",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["google_trends_available"] is False
    assert context["data_freshness_score"] == pytest.approx(1.0)


def test_confidence_context_freshness_reflects_stale_records() -> None:
    """SCRUM-1153: data_freshness_score/data_age_hours must reflect real record
    age, not a hardcoded 0.0-age/1.0-freshness pair."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-stale", name="ContextStale", category_path="a/b")
    session.add(niche)
    session.flush()
    stale_at = datetime.now(UTC) - timedelta(hours=400)
    keyword = Keyword(
        niche_id=niche.id,
        keyword="stale keyword",
        normalized_keyword="stale keyword",
        updated_at=stale_at,
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="stale_seller", profile_collected=True, updated_at=stale_at)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do stale work",
        normalized_title="stale work",
        detail_collected=True,
        detail_collected_at=stale_at,
        updated_at=stale_at,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, updated_at=stale_at))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] >= 168.0
    assert context["data_ttl_hours"] == pytest.approx(168.0)
    # data_freshness_score averages every contributing record's individual freshness
    # (FRESHNESS_MODEL.md) - most records here share the 400h-stale timestamp at a
    # 168h TTL (fully stale, 0.0 each), while the seller's 720h TTL keeps it partially
    # fresh, so the mean lands well below 0.5 without being exactly 0.0.
    assert context["data_freshness_score"] < 0.5


def test_confidence_context_freshness_picks_highest_staleness_ratio_not_oldest_timestamp() -> None:
    """Codex review, PR #176 (P2): with mixed TTLs, the absolute-oldest timestamp is
    not necessarily the most stale record relative to its own TTL. A 500h-old seller
    (720h TTL, ratio 0.69) is older in wall-clock terms than a 400h-old gig (168h TTL,
    ratio 2.38), but the gig is far more over its own TTL and must win."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-ratio", name="ContextRatio", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="ratio keyword", normalized_keyword="ratio keyword")
    session.add(keyword)
    session.flush()
    seller_stale_at = datetime.now(UTC) - timedelta(hours=500)
    gig_stale_at = datetime.now(UTC) - timedelta(hours=400)
    seller = Seller(seller_handle="ratio_seller", profile_collected=True, profile_collected_at=seller_stale_at)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do ratio work",
        normalized_title="ratio work",
        detail_collected=True,
        detail_collected_at=gig_stale_at,
        updated_at=gig_stale_at,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, updated_at=gig_stale_at))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    # The 168h-TTL gig (ratio ~2.38) must win over the 720h-TTL seller (ratio ~0.69),
    # even though the seller's timestamp is older in absolute wall-clock terms.
    assert context["data_ttl_hours"] == pytest.approx(168.0)
    assert context["data_age_hours"] == pytest.approx(400.0, abs=15.0)


def test_confidence_context_freshness_ignores_superseded_signal_rows() -> None:
    """Codex review, PR #176 (P1): the real scoring loaders (e.g.
    DemandScoreCalculator._load_signals_from_db) only read the newest ExternalSignal
    row per signal_type. An old row from a prior run must not drive staleness when a
    fresher same-type row is the one actually contributing to the score."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-superseded", name="ContextSuperseded", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="superseded keyword", normalized_keyword="superseded keyword")
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=2000)
    fresh_at = datetime.now(UTC)
    # Old row from a prior run - superseded, must be excluded from freshness.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="google_trends",
            signal_value=1.0,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-superseded-run-1",
            collection_method="google_trends_api",
        )
    )
    session.commit()
    # Fresh row from the current run, same signal_type - this is the one the real
    # scoring loaders actually read.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="google_trends",
            signal_value=1.0,
            signal_json={},
            collected_at=fresh_at,
            run_id="ctx-superseded-run-2",
            collection_method="google_trends_api",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] < 24.0
    assert context["data_freshness_score"] > 0.9


def test_confidence_context_freshness_groups_reddit_aliases_like_trend_loader() -> None:
    """Codex review, PR #176 (P2): TrendScoreCalculator._load_signals_from_db treats
    reddit_demand and reddit_activity as one combined pool
    (signal_type.in_([...]).order_by(created_at.desc()).first()), reading only the
    newest row across both. A stale reddit_activity row from an old run must not
    count once a fresher reddit_demand row exists for the same keyword."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-reddit-alias", name="ContextRedditAlias", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="reddit alias keyword", normalized_keyword="reddit alias keyword")
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=2000)
    fresh_at = datetime.now(UTC)
    # Stale reddit_activity row from an old run.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_activity",
            signal_value=1.0,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-reddit-alias-run-1",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()
    # Fresh reddit_demand row from the current run - a different literal signal_type,
    # but the same "reddit" source group as far as the real trend loader is concerned.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_demand",
            signal_value=1.0,
            signal_json={},
            collected_at=fresh_at,
            run_id="ctx-reddit-alias-run-2",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] < 24.0
    assert context["data_freshness_score"] > 0.9


def test_confidence_context_gates_reddit_activity_freshness_on_trend_scoring() -> None:
    """Codex review, PR #176 (P2): TrendScoreCalculator is the only reader of
    reddit_activity, and only when trend scoring (score 9) actually ran. In
    keyword_only/feasibility runs where score 9 is skipped and trend_score is None,
    an unused stale reddit_activity row must not demote freshness for a signal
    nothing in that run reads."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-reddit-activity-ungated", name="ContextRedditActivityUngated", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="reddit activity ungated keyword",
        normalized_keyword="reddit activity ungated keyword",
    )
    session.add(keyword)
    session.flush()
    ancient_at = datetime.now(UTC) - timedelta(hours=3000)
    # Only reddit_activity exists (no reddit_demand) - TrendScoreCalculator's only
    # reader of this signal - and this run never scored trend (score 9 skipped).
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_activity",
            signal_value=1.0,
            signal_json={},
            collected_at=ancient_at,
            run_id="ctx-reddit-activity-ungated-run",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="feasibility",
        warnings=[],
        db=session,
    )
    assert context["data_freshness_score"] == pytest.approx(1.0)
    assert context["data_age_hours"] == pytest.approx(0.0)


def test_confidence_context_freshness_includes_unranked_marketplace_snapshot() -> None:
    """Codex review, PR #176 (P2): DemandScoreCalculator._resolve_marketplace_snapshot
    reads the SearchResult row with the highest total_result_count regardless of rank
    (it can be unranked or outside the top-N), so demand can be driven by a row the
    rank-filtered top_results query never sees. A stale unranked snapshot row must
    still be able to trigger staleness."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-marketplace-snapshot", name="ContextMarketplaceSnapshot", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="marketplace snapshot keyword", normalized_keyword="marketplace snapshot keyword"
    )
    session.add(keyword)
    session.flush()
    stale_at = datetime.now(UTC) - timedelta(hours=400)
    fresh_at = datetime.now(UTC)
    seller = Seller(seller_handle="snapshot_seller", profile_collected=True, profile_collected_at=fresh_at)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do fresh ranked work",
        normalized_title="fresh ranked work",
        detail_collected=True,
        detail_collected_at=fresh_at,
        updated_at=fresh_at,
    )
    session.add(gig)
    session.flush()
    # A normal, fresh, ranked top-10 row.
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, collected_at=fresh_at))
    # A separate, unranked marketplace-snapshot row carrying total_result_count -
    # this is what DemandScoreCalculator._resolve_marketplace_snapshot actually reads,
    # and it is stale even though the ranked row above is fresh.
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id="snapshot-run",
            rank=None,
            total_result_count=5000,
            collected_at=stale_at,
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] >= 168.0
    assert context["data_ttl_hours"] == pytest.approx(168.0)


def test_confidence_context_resolves_gigs_via_keyword_id_fallback() -> None:
    """Codex review, PR #176 (P2): ProfitabilityScoreCalculator and
    GigQualityWeaknessScoreCalculator both fall back to Gig.keyword_id (bypassing
    SearchResult.gig_id entirely) when no gig can be resolved through search-result
    linkage. A keyword whose gigs are only reachable that way must not report
    gig_detail_collected=False just because no SearchResult row links to a gig."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-keyword-fallback", name="ContextKeywordFallback", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="keyword id fallback keyword", normalized_keyword="keyword id fallback keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="fallback_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    # This gig is linked to the keyword directly (Gig.keyword_id), not through any
    # SearchResult.gig_id - the fallback tier both calculators use when search-result
    # linkage is unavailable.
    gig = Gig(
        seller_id=seller.id,
        keyword_id=keyword.id,
        title="I will do keyword-linked work",
        normalized_title="keyword-linked work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
    )
    session.add(gig)
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["gig_detail_collected"] is True
    assert context["seller_profiles_collected"] is True


def test_confidence_context_keyword_fallback_retries_unscoped_after_run_scoped_miss() -> None:
    """Codex review, PR #176 (P2): profitability.py/weakness.py retry an UNSCOPED
    Gig.keyword_id query when the run-scoped fallback comes up empty (a stale
    active_run_id can point to unlinked SearchResult rows with no matching
    Gig.run_id at all). Mirror that final recovery tier."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-unscoped-fallback", name="ContextUnscopedFallback", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="unscoped fallback keyword", normalized_keyword="unscoped fallback keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="unscoped_fallback_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    # This gig has a DIFFERENT run_id than the active run determined from the
    # SearchResult row below, and is only reachable via the unscoped retry tier.
    gig = Gig(
        seller_id=seller.id,
        keyword_id=keyword.id,
        title="I will do unscoped-run work",
        normalized_title="unscoped-run work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
        run_id="run-legacy",
    )
    session.add(gig)
    session.flush()
    # An unlinked SearchResult row (no gig_id) determines the active run, but no Gig
    # row actually carries that run_id.
    session.add(
        SearchResult(keyword_id=keyword.id, rank=1, gig_id=None, title="unlinked row", run_id="run-current")
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["gig_detail_collected"] is True
    assert context["seller_profiles_collected"] is True


def test_confidence_context_fallback_gigs_count_toward_zombie_concentration() -> None:
    """Codex review, PR #176 (P2): the search-result-linked path counts
    total_organic/zombie_count before processing gigs, but the Gig.keyword_id
    fallback path left both at 0 - a keyword scored entirely from fallback gigs
    must still be able to trigger zombie_concentration_high/moderate when those
    gigs are zombies."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-fallback-zombie", name="ContextFallbackZombie", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id, keyword="fallback zombie keyword", normalized_keyword="fallback zombie keyword"
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="fallback_zombie_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    for i in range(4):
        session.add(
            Gig(
                seller_id=seller.id,
                keyword_id=keyword.id,
                title=f"I will do zombie work {i}",
                normalized_title=f"zombie work {i}",
                detail_collected=True,
                detail_collected_at=datetime.now(UTC),
                is_zombie=True,
            )
        )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["zombie_fraction"] == pytest.approx(1.0)


def test_confidence_context_keyword_fallback_reaches_organic_gigs_past_sponsored() -> None:
    """Codex review, PR #176 (P2): when the keyword has no SearchResult-linked gigs
    at all, the Gig.keyword_id fallback tier must gather the same candidate_window
    ProfitabilityScoreCalculator/the feasibility loader use before skipping
    sponsored gigs, not a naive top_n_for_scoring position cutoff - otherwise
    sponsored gigs occupying the first positions crowd out the real organic gigs
    that fed the score."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-fallback-sponsored-window", name="ContextFallbackSponsoredWindow", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="fallback sponsored window keyword",
        normalized_keyword="fallback sponsored window keyword",
    )
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="fallback_sponsored_window_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    for position in range(1, 14):
        # Positions 1-3 are sponsored - the top_n_for_scoring=10 organic gigs that
        # actually fed the real score are positions 4-13.
        is_sponsored = position <= 3
        # The last organic gig (position 13) - unreachable under the old
        # top_n_for_scoring-sized fallback limit - is a zombie.
        is_zombie = position == 13
        session.add(
            Gig(
                seller_id=seller.id,
                keyword_id=keyword.id,
                position=position,
                title=f"I will do fallback sponsored window work {position}",
                normalized_title=f"fallback sponsored window work {position}",
                detail_collected=True,
                detail_collected_at=datetime.now(UTC),
                is_sponsored=is_sponsored,
                is_zombie=is_zombie,
            )
        )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["zombie_fraction"] == pytest.approx(0.1)


def test_confidence_context_scopes_search_results_to_active_run() -> None:
    """Codex review, PR #176 (P2): ProfitabilityScoreCalculator/
    GigQualityWeaknessScoreCalculator resolve an active_run_id (the run_id of the
    lowest-rank SearchResult row) and scope their inputs to it. A stale row left
    over from an older run must not feed freshness/detail checks once a fresher
    run's rows exist for the same keyword."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-active-run", name="ContextActiveRun", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="active run keyword", normalized_keyword="active run keyword")
    session.add(keyword)
    session.flush()
    stale_at = datetime.now(UTC) - timedelta(hours=400)
    fresh_at = datetime.now(UTC)
    seller = Seller(seller_handle="active_run_seller", profile_collected=True, profile_collected_at=fresh_at)
    session.add(seller)
    session.flush()
    fresh_gig = Gig(
        seller_id=seller.id,
        title="I will do fresh active-run work",
        normalized_title="fresh active-run work",
        detail_collected=True,
        detail_collected_at=fresh_at,
        updated_at=fresh_at,
        run_id="run-new",
    )
    session.add(fresh_gig)
    stale_gig = Gig(
        seller_id=seller.id,
        title="I will do stale old-run work",
        normalized_title="stale old-run work",
        detail_collected=True,
        detail_collected_at=stale_at,
        updated_at=stale_at,
        run_id="run-old",
    )
    session.add(stale_gig)
    session.flush()
    # Old run's rank 4 row is stale and must be excluded once a fresher run exists.
    session.add(
        SearchResult(
            keyword_id=keyword.id, rank=4, gig_id=stale_gig.id, title=stale_gig.title, run_id="run-old",
            collected_at=stale_at,
        )
    )
    # New run's rank 1 row is fresh and determines the active run.
    session.add(
        SearchResult(
            keyword_id=keyword.id, rank=1, gig_id=fresh_gig.id, title=fresh_gig.title, run_id="run-new",
            collected_at=fresh_at,
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_freshness_score"] > 0.9


def test_confidence_context_llm_quality_incomplete_counted_even_when_detail_collected() -> None:
    """Codex review, PR #176 (P2): whether gig detail was scraped and whether LLM
    quality analysis ran on it are unrelated. A gig with a fully-collected detail
    payload but no LLM quality score must still count toward
    llm_gig_quality_incomplete_count, not be silently excluded because detail
    collection succeeded."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-quality-gap", name="ContextQualityGap", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="quality gap keyword", normalized_keyword="quality gap keyword")
    session.add(keyword)
    session.flush()
    seller = Seller(seller_handle="quality_gap_seller", profile_collected=True)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do fully detailed work",
        normalized_title="fully detailed work",
        detail_collected=True,
        detail_collected_at=datetime.now(UTC),
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=["llm_not_implemented: missing LLM gig quality weakness."],
        db=session,
    )
    assert context["gig_detail_collected"] is True
    assert context["llm_gig_quality_incomplete_count"] == 1


def test_confidence_context_freshness_uses_record_own_ttl_not_global_default() -> None:
    """Codex review, PR #176 (P2): Seller defaults to a 720h TTL
    (src/models/seller.py), longer than the old flat 168h assumption. A seller
    profile collected 480h ago is still within its own TTL and must not be
    reported as fully stale (freshness=0.0) just because 480h > 168h."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-seller-ttl", name="ContextSellerTtl", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="seller ttl keyword", normalized_keyword="seller ttl keyword")
    session.add(keyword)
    session.flush()
    seller_stale_at = datetime.now(UTC) - timedelta(hours=480)
    fresh_at = datetime.now(UTC)
    # Seller's own 720h default TTL means 480h old is still within TTL, unlike a
    # 168h-TTL source (Gig/SearchResult) at the same age.
    seller = Seller(seller_handle="ttl_seller", profile_collected=True, profile_collected_at=seller_stale_at)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do fresh gig work",
        normalized_title="fresh gig work",
        detail_collected=True,
        detail_collected_at=fresh_at,
        updated_at=fresh_at,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, updated_at=fresh_at))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_ttl_hours"] == pytest.approx(720.0)
    # Generous tolerance: naive-vs-aware SQLite round-tripping can introduce a
    # local-UTC-offset-sized skew (see the pre-existing "SQLite often round-trips
    # timestamps as naive" handling elsewhere in this function).
    assert context["data_age_hours"] == pytest.approx(480.0, abs=15.0)
    # data_freshness_score averages every record (mostly fresh here); it must not be
    # collapsed to near-zero just because the seller is old in absolute terms while
    # still within its own 720h TTL.
    assert context["data_freshness_score"] > 0.7


def test_confidence_context_freshness_aggregates_all_external_signals() -> None:
    """Codex review, PR #176 (P2): a stale Google Trends signal must still be able
    to trigger staleness even when a fresher Reddit/YouTube signal exists for the
    same keyword - aggregating only the single newest signal would hide this."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-multi-signal", name="ContextMultiSignal", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="multi signal keyword", normalized_keyword="multi signal keyword")
    session.add(keyword)
    session.flush()
    stale_at = datetime.now(UTC) - timedelta(hours=400)
    fresh_at = datetime.now(UTC)
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="google_trends",
            signal_value=1.0,
            signal_json={},
            collected_at=stale_at,
            run_id="ctx-multi-run",
            collection_method="google_trends_api",
        )
    )
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="reddit_demand",
            signal_value=1.0,
            signal_json={},
            collected_at=fresh_at,
            run_id="ctx-multi-run",
            collection_method="reddit_devvit_bridge",
        )
    )
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] >= 168.0
    assert context["data_ttl_hours"] == pytest.approx(168.0)
    # data_freshness_score averages the stale Trends signal alongside the fresh Reddit
    # signal and keyword row, so it must not sit at 1.0 (proving the stale signal was
    # NOT dropped) even though it isn't fully collapsed to 0.0 either.
    assert context["data_freshness_score"] < 1.0
    # The newest-signal-derived fields must still reflect the freshest signal.
    assert context["signal_age_days"] == 0
    assert context["external_signal_context_present"] is True


def test_confidence_context_freshness_uses_oldest_not_newest_contributing_record() -> None:
    """SCRUM-1153/Codex review: DATA_FLOW.md's Stage 11 defines freshness as the age
    of the OLDEST contributing record vs. TTL. A single recently-touched record (e.g.
    a fresh external signal) must not mask a stale gig/seller elsewhere in the same
    keyword's data."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-mixed", name="ContextMixed", category_path="a/b")
    session.add(niche)
    session.flush()
    stale_at = datetime.now(UTC) - timedelta(hours=400)
    fresh_at = datetime.now(UTC)
    keyword = Keyword(niche_id=niche.id, keyword="mixed freshness keyword", normalized_keyword="mixed freshness keyword")
    session.add(keyword)
    session.flush()
    # A fresh external signal exists alongside a stale gig - overall freshness must
    # still reflect the stale gig, not the fresh signal.
    session.add(
        ExternalSignal(
            keyword_id=int(keyword.id),
            signal_type="google_trends",
            signal_value=1.0,
            signal_json={},
            collected_at=fresh_at,
            run_id="ctx-mixed-run",
            collection_method="google_trends_api",
        )
    )
    seller = Seller(seller_handle="mixed_seller", profile_collected=True, updated_at=fresh_at)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do stale work with a fresh signal",
        normalized_title="mixed freshness work",
        detail_collected=True,
        detail_collected_at=stale_at,
        updated_at=stale_at,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, updated_at=stale_at))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] >= 168.0
    assert context["data_ttl_hours"] == pytest.approx(168.0)
    # data_freshness_score averages in the fresh signal too, so it must not sit at 1.0
    # (proving the stale gig/search-result was not masked by the fresh signal alone).
    assert context["data_freshness_score"] < 1.0


def test_confidence_context_freshness_uses_collected_at_not_metadata_touch() -> None:
    """SCRUM-1153/Codex review: a gig/seller's updated_at can be refreshed by an
    unrelated metadata write (relevance/zombie flag, price) long after its detail
    payload or profile was actually scraped. Freshness must key off
    detail_collected_at/profile_collected_at, not updated_at, or a stale gig detail
    payload could hide behind a recent unrelated write."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-metadata-touch", name="ContextMetadataTouch", category_path="a/b")
    session.add(niche)
    session.flush()
    stale_at = datetime.now(UTC) - timedelta(hours=400)
    fresh_at = datetime.now(UTC)
    keyword = Keyword(niche_id=niche.id, keyword="metadata touch keyword", normalized_keyword="metadata touch keyword")
    session.add(keyword)
    session.flush()
    # Seller profile collected long ago, but a later unrelated write bumped updated_at.
    seller = Seller(seller_handle="metadata_touch_seller", profile_collected=True, profile_collected_at=stale_at, updated_at=fresh_at)
    session.add(seller)
    session.flush()
    # Gig detail collected long ago, but a later relevance/zombie reprocessing pass
    # bumped updated_at without re-scraping the detail payload.
    gig = Gig(
        seller_id=seller.id,
        title="I will do work with stale detail but a fresh metadata touch",
        normalized_title="metadata touch work",
        detail_collected=True,
        detail_collected_at=stale_at,
        updated_at=fresh_at,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, updated_at=fresh_at))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={},
        depth="standard",
        warnings=[],
        db=session,
    )
    assert context["data_age_hours"] >= 168.0
    assert context["data_ttl_hours"] == pytest.approx(168.0)
    # data_freshness_score averages in the fresh search-result/keyword rows too, so it
    # must not sit at 1.0 (proving the stale gig detail was not masked by the fresh
    # metadata-only write to updated_at).
    assert context["data_freshness_score"] < 1.0


def test_confidence_context_freshness_score_is_mean_not_worst_record() -> None:
    """Codex review, PR #176 (P2): FRESHNESS_MODEL.md's calculate_data_freshness_score
    and CONFIDENCE_SCORE.md both define data_freshness_score as the MEAN of each
    contributing record's individual freshness, not just the single worst record - one
    expired signal must not collapse confidence to 0 when the rest of the data is
    fresh."""
    from src.scoring import pipeline

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx-mean-freshness", name="ContextMeanFreshness", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="mean freshness keyword", normalized_keyword="mean freshness keyword")
    session.add(keyword)
    session.flush()
    # One fully-stale (ratio 2.0, individual freshness 0.0) record alongside three
    # fully-fresh (ratio 0.0, individual freshness 1.0) records -> mean should be 0.75,
    # not 0.0.
    very_stale_at = datetime.now(UTC) - timedelta(hours=336)  # 2x the 168h default TTL
    fresh_at = datetime.now(UTC)
    seller = Seller(seller_handle="mean_seller", profile_collected=True, profile_collected_at=fresh_at)
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title="I will do mostly fresh work",
        normalized_title="mostly fresh work",
        detail_collected=True,
        detail_collected_at=very_stale_at,
        updated_at=very_stale_at,
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title, updated_at=fresh_at))
    session.commit()

    context = pipeline._build_confidence_context(
        keyword_id=int(keyword.id),
        scores={"trend_score": 50.0},
        depth="standard",
        warnings=[],
        db=session,
    )
    # data_age_hours/data_ttl_hours still reflect the single worst record (the stale
    # gig), for the discrete data_stale_over_2x_ttl deduction gate.
    assert context["data_ttl_hours"] == pytest.approx(168.0)
    assert context["data_age_hours"] >= 320.0
    # But data_freshness_score itself must be a mean, not collapsed by that one record.
    assert context["data_freshness_score"] > 0.5


def test_confidence_context_non_session_db_preserves_lenient_collection_defaults() -> None:
    """SCRUM-1153/Codex review: when no Session is available to check real collection
    state (e.g. a dict-based db payload), gig_detail_collected/seller_profiles_collected
    must stay at their pre-fix lenient default rather than being penalized for an
    unknown state we have no way to verify."""
    from src.scoring import pipeline

    context = pipeline._build_confidence_context(
        keyword_id=1,
        scores={},
        depth="standard",
        warnings=[],
        db={"some": "dict-based-payload"},
    )
    assert context["gig_detail_collected"] is True
    assert context["seller_profiles_collected"] is True


def test_confidence_context_llm_completion_ratio_ignores_quality_and_competitor_warnings() -> None:
    """SCRUM-1153: llm_analysis_completion_ratio must react to real LLM fallback
    warnings while avoiding double-counting the quality/competitor deductions
    that already have their own dedicated confidence penalties."""
    from src.scoring import pipeline

    full = pipeline._build_confidence_context(
        keyword_id=1,
        scores={},
        depth="standard",
        warnings=[],
        db={},
    )
    assert full["llm_analysis_completion_ratio"] == pytest.approx(1.0)

    degraded = pipeline._build_confidence_context(
        keyword_id=1,
        scores={},
        depth="standard",
        warnings=[
            "llm_not_implemented: missing LLM buyer intent classification; defaulted to CONSIDERATION (40).",
            "llm_not_implemented: no llm_trend_classification signal available.",
            "llm_not_implemented: missing LLM gig quality weakness.",
            "llm_not_implemented: missing competitor synthesis.",
        ],
        db={},
    )
    # 6 intended "other" signals total (buyer intent, upsell, saturation, trend,
    # entry-gap, gig-weakness-assessment); only buyer intent + trend are present here.
    assert degraded["llm_analysis_completion_ratio"] == pytest.approx(1.0 - (2 / 6))


def test_confidence_context_llm_completion_ratio_ignores_weakness_stub_warnings() -> None:
    """Codex review, PR #176 (P1): src/scoring/weakness.py emits its own
    llm_not_implemented warnings (llm_weakness_count_per_gig,
    llm_faq_completeness_score, llm_package_differentiation_score,
    llm_niche_specificity_score) whose text does not contain "quality" or
    "competitor" at all. An exclude-by-substring filter would miscount these as
    one of the intended "other" signals and collapse llm_analysis_completion_ratio
    to 0.0 in the common no-LLM-key case even though buyer intent/upsell/
    saturation/trend/entry-gap/gig-weakness are all present."""
    from src.scoring import pipeline

    context = pipeline._build_confidence_context(
        keyword_id=1,
        scores={},
        depth="standard",
        warnings=[
            "llm_not_implemented: missing llm_weakness_count_per_gig.",
            "llm_not_implemented: missing llm_faq_completeness_score.",
            "llm_not_implemented: missing llm_package_differentiation_score.",
            "llm_not_implemented: missing llm_niche_specificity_score.",
        ],
        db={},
    )
    assert context["llm_analysis_completion_ratio"] == pytest.approx(1.0)


def test_confidence_context_llm_completion_ratio_counts_gig_weakness_assessment() -> None:
    """Codex review, PR #176 (P2): feasibility.py's "missing LLM gig weakness
    assessment" is a real keyword-level LLM signal distinct from weakness.py's
    per-gig quality fields, and must count as one of the 6 intended "other" signals
    tracked by llm_analysis_completion_ratio, not be silently dropped."""
    from src.scoring import pipeline

    context = pipeline._build_confidence_context(
        keyword_id=1,
        scores={},
        depth="standard",
        warnings=["llm_not_implemented: missing LLM gig weakness assessment."],
        db={},
    )
    assert context["llm_analysis_completion_ratio"] == pytest.approx(1.0 - (1 / 6))


def test_mode_full_smoke() -> None:
    import src.orchestrator as orchestrator

    assert orchestrator.run_phase2_smoke(config_path="config.yaml") == 0


def test_resolve_depth_from_dict_payload() -> None:
    from src.scoring import pipeline

    assert pipeline._resolve_depth(1, {1: {"score_depth": "keyword_only"}}) == "keyword_only"


def test_resolve_keyword_context_from_session() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="ctx", name="Context", category_path="a/b")
    session.add(niche)
    session.flush()
    keyword = Keyword(niche_id=niche.id, keyword="context keyword", normalized_keyword="context keyword")
    session.add(keyword)
    session.commit()

    from src.scoring import pipeline

    keyword_text, niche_id = pipeline._resolve_keyword_context(int(keyword.id), session)
    assert keyword_text == "context keyword"
    assert niche_id == niche.id


def test_write_keyword_score_sidecar_oserror_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    class _FailingPath:
        def mkdir(self, *args: Any, **kwargs: Any) -> None:
            del args, kwargs
            return None

        def __truediv__(self, _other: str) -> _FailingPath:
            return self

        def write_text(self, *_args: Any, **_kwargs: Any) -> int:
            raise OSError("disk full")

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", _FailingPath())
    ok = write_keyword_score(
        keyword_id=1,
        scores={"demand_score": 1.0},
        weighted_composite=1.0,
        confidence_modifier=1.0,
        final_score=1.0,
        tag="PASS",
        score_components={},
        confidence_breakdown={},
        explanation_text="x",
        red_flags=[],
        scoring_profile="default",
        score_depth="standard",
        db=None,
    )
    assert ok is False


def test_write_keyword_score_rolls_back_on_session_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="rollback", name="Rollback", category_path="x/y")
    session.add(niche)
    session.flush()
    session.add(Keyword(niche_id=niche.id, keyword="rollback", normalized_keyword="rollback"))
    session.commit()

    rolled_back = {"value": False}
    original_rollback = session.rollback
    monkeypatch.setattr(session, "merge", lambda _row: (_ for _ in ()).throw(RuntimeError("merge failure")))

    def _tracked_rollback() -> None:
        rolled_back["value"] = True
        original_rollback()

    monkeypatch.setattr(session, "rollback", _tracked_rollback)
    ok = write_keyword_score(
        keyword_id=1,
        scores={"demand_score": 10.0},
        weighted_composite=10.0,
        confidence_modifier=1.0,
        final_score=10.0,
        tag="PASS",
        score_components={},
        confidence_breakdown={},
        explanation_text="x",
        red_flags=[],
        scoring_profile="default",
        score_depth="standard",
        db=session,
    )
    assert ok is True
    assert rolled_back["value"] is True


def test_normalized_profile_with_zero_total_returns_original() -> None:
    from src.scoring import pipeline

    profile = {"a": 0.0, "b": 0.0}
    assert pipeline._normalized_profile(profile) == profile


def test_calculate_weighted_composite_skips_zero_weight_entries() -> None:
    scores = {
        "demand_score": 80.0,
        "competition_score": 40.0,
        "opportunity_score": 70.0,
        "feasibility_score": 60.0,
        "profitability_score": 50.0,
        "intent_score": 60.0,
        "saturation_score": 30.0,
        "weakness_score": 65.0,
        "trend_score": 55.0,
    }
    profile = dict(SCORING_PROFILES["default"])
    profile["demand"] = 0.0
    _, components = calculate_weighted_composite(scores, profile)
    assert "demand_score" not in components


def test_detect_red_flags_low_demand() -> None:
    flags = detect_red_flags_from_scores(
        {"competition_score": 30.0, "demand_score": 10.0, "trend_score": 40.0},
        {"confidence_modifier": 0.8},
        1,
        None,
    )
    assert any(flag["source"] == "demand_score" for flag in flags)


def test_score_keyword_raises_for_unknown_profile() -> None:
    with pytest.raises(ValueError, match="Unknown scoring profile"):
        asyncio.run(score_keyword(1, "missing-profile", FakePipelineDB(), None, None))


def test_resolve_depth_defaults_to_standard_for_unknown_value() -> None:
    from src.scoring import pipeline

    assert pipeline._resolve_depth(1, {1: {"score_depth": "not-a-depth"}}) == "standard"


_ASSIGN_TAG_SCORE_GRID = [
    -100.0,
    -1.0,
    -0.01,
    0.0,
    0.01,
    1.0,
    10.0,
    19.98,
    19.99,
    20.0,
    20.01,
    21.0,
    30.0,
    39.98,
    39.99,
    40.0,
    40.01,
    41.0,
    50.0,
    59.98,
    59.99,
    60.0,
    60.01,
    61.0,
    70.0,
    79.98,
    79.99,
    80.0,
    80.01,
    81.0,
    90.0,
    99.99,
    100.0,
    250.0,
]

_ASSIGN_TAG_DEMOTION_MAP = {
    "STRONG_GO": "CONDITIONAL_GO",
    "CONDITIONAL_GO": "MONITOR",
    "MONITOR": "CAUTION",
    "CAUTION": "PASS",
    "PASS": "PASS",
}


def _expected_base_tag(final_score: float) -> str:
    if final_score >= 80.0:
        return "STRONG_GO"
    if final_score >= 60.0:
        return "CONDITIONAL_GO"
    if final_score >= 40.0:
        return "MONITOR"
    if final_score >= 20.0:
        return "CAUTION"
    return "PASS"


@pytest.mark.parametrize("final_score", _ASSIGN_TAG_SCORE_GRID)
@pytest.mark.parametrize("confidence_modifier", [0.5, 0.9])
def test_assign_tag_threshold_grid_without_demotion(
    final_score: float,
    confidence_modifier: float,
) -> None:
    expected = _expected_base_tag(final_score)
    assert assign_tag(final_score, confidence_modifier) == expected


@pytest.mark.parametrize("final_score", _ASSIGN_TAG_SCORE_GRID)
@pytest.mark.parametrize("confidence_modifier", [0.49, 0.0])
def test_assign_tag_threshold_grid_with_demotion(
    final_score: float,
    confidence_modifier: float,
) -> None:
    base = _expected_base_tag(final_score)
    expected = _ASSIGN_TAG_DEMOTION_MAP[base]
    assert assign_tag(final_score, confidence_modifier) == expected
