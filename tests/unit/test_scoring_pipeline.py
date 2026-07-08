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
        detail_collected_at=datetime.now(UTC),
    )
    session.add(gig)
    session.flush()
    session.add(SearchResult(keyword_id=keyword.id, rank=1, gig_id=gig.id, title=gig.title))
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
    assert context["data_freshness_score"] == 0.0


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
    assert context["data_freshness_score"] == pytest.approx(1.0 - (480.0 / 720.0), abs=0.03)
    assert context["data_freshness_score"] > 0.0


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
    assert context["data_freshness_score"] == 0.0
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
    assert context["data_freshness_score"] == 0.0


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
    assert context["data_freshness_score"] == 0.0


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
    assert degraded["llm_analysis_completion_ratio"] == pytest.approx(1.0 - (2 / 5))


def test_confidence_context_llm_completion_ratio_ignores_weakness_stub_warnings() -> None:
    """Codex review, PR #176 (P1): src/scoring/weakness.py emits its own
    llm_not_implemented warnings (llm_weakness_count_per_gig,
    llm_faq_completeness_score, llm_package_differentiation_score,
    llm_niche_specificity_score) whose text does not contain "quality" or
    "competitor" at all. An exclude-by-substring filter would miscount these as
    one of the 5 intended "other" signals and collapse llm_analysis_completion_ratio
    to 0.0 in the common no-LLM-key case even though buyer intent/upsell/
    saturation/trend/entry-gap are all present. feasibility.py's "missing LLM gig
    weakness assessment" warning has the same shape and must also be ignored."""
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
            "llm_not_implemented: missing LLM gig weakness assessment.",
        ],
        db={},
    )
    assert context["llm_analysis_completion_ratio"] == pytest.approx(1.0)


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
