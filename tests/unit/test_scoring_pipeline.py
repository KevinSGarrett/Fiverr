"""Unit tests for async scoring pipeline integration helpers."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from src.scoring.pipeline import (
    DEPTH_SCORE_AVAILABILITY,
    SCORING_PROFILES,
    assign_tag,
    calculate_final_score,
    calculate_weighted_composite,
    detect_red_flags_from_scores,
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
    ) -> dict[str, Any]:
        del profile_name, db, llm_client, cache
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


def test_write_keyword_score_rolls_back_on_session_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.models import Base, Keyword, Niche

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
