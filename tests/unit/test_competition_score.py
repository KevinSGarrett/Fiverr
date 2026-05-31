"""Unit tests for CompetitorProfile integrations in Score 2/3/4."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.config import ConfigLoader
from src.models import Base, Gig, Keyword, Niche, ResultSetValidation, SearchResult, Seller, write_competitor_profile
from src.scoring.competition import (
    CompetitionScoreCalculator,
    _coerce_bool,
    _coerce_float,
    _normalize_gap_flags,
    compute_seller_level_competition_signal,
    get_competitor_profile_inputs,
)
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator, get_feasibility_gap_signal
from src.scoring.opportunity import OpportunityScoreCalculator

KEYWORD_ID = 7001


def _base_demand_inputs() -> dict[str, Any]:
    return {
        "total_result_count": 1200,
        "autocomplete_position": 2,
        "trends_12mo_score": 62,
        "reddit_demand_intent_score": 7.0,
    }


def _base_competition_inputs() -> dict[str, Any]:
    return {
        "total_result_count": 1200,
        "avg_review_count_top10": 25.0,
        "avg_seller_level_top10": "Level 1",
        "proportion_with_100_plus_reviews": 0.1,
        "pro_verified_presence_ratio": 0.0,
        "avg_starting_price_top10": 25.0,
        "llm_competitor_strength_rating": 3.0,
    }


def _base_feasibility_inputs() -> dict[str, Any]:
    return {
        "level1_or_new_ratio_top10": 0.45,
        "lowest_ranked_review_count_page1": 18.0,
        "price_diversity_top10": 0.6,
        "llm_gig_quality_weakness_avg_top10": 6.0,
        "llm_entry_gap_assessment": 5.5,
        "niche_name": "Python Automation",
    }


def _competition_config(*, use_competitor_profile: bool = True) -> dict[str, Any]:
    return {
        "scoring": {
            "competition": {
                "use_competitor_profile": use_competitor_profile,
            }
        }
    }


def _feasibility_config(
    *,
    gap_boost_per_flag: float = 10.0,
    max_gap_boost: float = 30.0,
) -> dict[str, Any]:
    return {
        "scoring": {
            "feasibility": {
                "gap_boost_per_flag": gap_boost_per_flag,
                "max_gap_boost": max_gap_boost,
            }
        }
    }


class FakeScoringDB:
    """Simple in-memory scoring signal provider."""

    def __init__(
        self,
        *,
        demand_inputs: dict[int, dict[str, Any]] | None = None,
        competition_inputs: dict[int, dict[str, Any]] | None = None,
        feasibility_inputs: dict[int, dict[str, Any]] | None = None,
    ) -> None:
        self._demand_inputs = demand_inputs or {}
        self._competition_inputs = competition_inputs or {}
        self._feasibility_inputs = feasibility_inputs or {}

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._demand_inputs.get(keyword_id, {}))

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._competition_inputs.get(keyword_id, {}))

    def get_feasibility_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._feasibility_inputs.get(keyword_id, {}))

    def get_keyword_depth(self, keyword_id: int) -> str:
        del keyword_id
        return "standard"


def _build_session() -> tuple[Session, Niche, Keyword]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    niche = Niche(slug="test_niche", name="Test Niche", category_path="programming-tech/testing")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation",
        normalized_keyword="python automation",
    )
    session.add(keyword)
    session.commit()
    session.refresh(niche)
    session.refresh(keyword)
    return session, niche, keyword


def _seed_competition_rows(session: Session, keyword_id: int, *, run_id: str) -> None:
    for rank in range(1, 4):
        seller = Seller(
            seller_handle=f"profile_seller_{rank}",
            level="Level 1" if rank == 1 else "Level 2",
            metadata_json={"is_pro": rank == 3},
        )
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            title=f"Competition gig {rank}",
            normalized_title=f"competition gig {rank}",
            starting_price=35.0 + (rank * 5),
            review_count=40 + (rank * 20),
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword_id,
                rank=rank,
                gig_id=gig.id,
                title=gig.title,
                run_id=run_id,
            )
        )
    session.commit()


def test_competitor_profile_inputs_returns_dict() -> None:
    session, _niche, _keyword = _build_session()
    try:
        write_competitor_profile(
            niche_id="test_niche",
            run_id="run-profile-01",
            db=session,
            top_gig_count=10,
            median_price=85.0,
            mean_reviews=320.0,
            seller_level_distribution={"TOP_RATED": 0.4, "LEVEL_2": 0.3, "LEVEL_1": 0.3},
            video_present_rate=0.3,
            portfolio_present_rate=0.4,
            new_seller_gap={"gap_flags": ["low_video_presence"], "opportunity_score": 35.0},
        )
        payload = get_competitor_profile_inputs("test_niche", "run-profile-01", session)
        assert payload["mean_reviews"] == 320.0
        assert payload["median_price"] == 85.0
        assert payload["seller_level_distribution"]["TOP_RATED"] == 0.4
        assert payload["video_present_rate"] == 0.3
        assert payload["portfolio_present_rate"] == 0.4
        assert payload["top_gig_count"] == 10
    finally:
        session.close()


def test_competitor_profile_inputs_empty_when_no_profile() -> None:
    session, _niche, _keyword = _build_session()
    try:
        assert get_competitor_profile_inputs("test_niche", "missing-run", session) == {}
    finally:
        session.close()


def test_competitor_profile_inputs_supports_mapping_source() -> None:
    payload = get_competitor_profile_inputs(
        "test_niche",
        "run-inline",
        {"competitor_profile": {"mean_reviews": 123.0, "median_price": 45.0}},
    )
    assert payload["mean_reviews"] == 123.0
    assert payload["median_price"] == 45.0


def test_competitor_profile_inputs_require_non_empty_ids() -> None:
    assert get_competitor_profile_inputs("", "run-inline", {}) == {}
    assert get_competitor_profile_inputs("test_niche", "", {}) == {}


def test_competition_score_uses_profile_mean_reviews() -> None:
    calculator = CompetitionScoreCalculator()
    base_inputs = _base_competition_inputs()
    profile = {
        "mean_reviews": 700.0,
        "median_price": 120.0,
        "seller_level_distribution": {"TOP_RATED": 0.8, "LEVEL_2": 0.2},
        "new_seller_gap": {"gap_flags": []},
    }
    with_profile = FakeScoringDB(
        competition_inputs={KEYWORD_ID: {**base_inputs, "competitor_profile": profile}},
    )
    without_profile = FakeScoringDB(competition_inputs={KEYWORD_ID: dict(base_inputs)})

    profile_result = calculator.calculate(
        KEYWORD_ID,
        with_profile,
        config=_competition_config(use_competitor_profile=True),
    )
    baseline_result = calculator.calculate(
        KEYWORD_ID,
        without_profile,
        config=_competition_config(use_competitor_profile=True),
    )

    assert profile_result.score_value is not None
    assert baseline_result.score_value is not None
    assert profile_result.score_value > baseline_result.score_value
    assert profile_result.score_components["avg_reviews"].raw == 700.0


def test_competition_score_fallback_when_no_profile() -> None:
    calculator = CompetitionScoreCalculator()
    db = FakeScoringDB(competition_inputs={KEYWORD_ID: _base_competition_inputs()})
    with_guard = calculator.calculate(
        KEYWORD_ID,
        db,
        config=_competition_config(use_competitor_profile=True),
    )
    without_guard = calculator.calculate(
        KEYWORD_ID,
        db,
        config=_competition_config(use_competitor_profile=False),
    )
    assert with_guard.score_value == without_guard.score_value


def test_competition_score_can_disable_inline_profile_usage() -> None:
    calculator = CompetitionScoreCalculator()
    loaded = calculator._load_signals(
        KEYWORD_ID,
        {
            KEYWORD_ID: {
                **_base_competition_inputs(),
                "competitor_profile": {"mean_reviews": 999.0},
            }
        },
        config=_competition_config(use_competitor_profile=False),
    )
    assert "competitor_profile" not in loaded


def test_competition_profile_derives_llm_rating_and_gap_adjustment_note() -> None:
    calculator = CompetitionScoreCalculator()
    profile = {
        "mean_reviews": 350.0,
        "median_price": 90.0,
        "seller_level_distribution": {"TRS": 0.6, "L1": 0.4},
        "new_seller_gap": {"gap_flags": ["LOW_VIDEO_PRESENCE"]},
    }
    result = calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(
            competition_inputs={
                KEYWORD_ID: {
                    **_base_competition_inputs(),
                    "llm_competitor_strength_rating": None,
                    "competitor_profile": profile,
                }
            }
        ),
        config=_competition_config(use_competitor_profile=True),
    )
    llm_component = result.score_components["llm_competitor_strength"]
    assert llm_component.note is not None
    assert "LOW_VIDEO_PRESENCE" in llm_component.note
    assert isinstance(llm_component.raw, float | int)


def test_competition_llm_rating_adjusts_from_top_level_gap_flags() -> None:
    calculator = CompetitionScoreCalculator()
    rating, note = calculator._derive_profile_llm_rating(
        profile_inputs={"gap_flags": ["low_video_presence"]},
        existing_rating=7.0,
    )
    assert rating == 6.0
    assert "LOW_VIDEO_PRESENCE" in note


def test_competition_score_uses_mean_price_when_median_missing() -> None:
    calculator = CompetitionScoreCalculator()
    profile = {
        "mean_reviews": 250.0,
        "mean_price": 155.0,
        "seller_level_distribution": {"TOP_RATED": 0.5, "LEVEL_2": 0.5},
    }
    result = calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(
            competition_inputs={
                KEYWORD_ID: {
                    **_base_competition_inputs(),
                    "competitor_profile": profile,
                }
            }
        ),
        config=_competition_config(use_competitor_profile=True),
    )
    assert result.score_components["avg_starting_price"].raw == 155.0


def test_seller_level_aliases_map_to_expected_signal_range() -> None:
    signal = compute_seller_level_competition_signal({"TRS": 0.5, "L1": 0.5, "unknown": 0.0})
    assert 50.0 <= signal <= 60.0


def test_competition_score_session_path_applies_competitor_profile() -> None:
    session, _niche, keyword = _build_session()
    try:
        _seed_competition_rows(session, keyword.id, run_id="run-profile-db")
        write_competitor_profile(
            niche_id="test_niche",
            run_id="run-profile-db",
            db=session,
            top_gig_count=3,
            median_price=140.0,
            mean_reviews=820.0,
            seller_level_distribution={"TOP_RATED": 0.8, "LEVEL_2": 0.2},
            new_seller_gap={"gap_flags": ["LOW_VIDEO_PRESENCE"]},
        )
        result = CompetitionScoreCalculator().calculate(
            keyword.id,
            session,
            config=_competition_config(use_competitor_profile=True),
        )
        assert result.score_components["avg_reviews"].raw == 820.0
        assert "competitor_profiles.mean_reviews" in result.source_evidence
    finally:
        session.close()


def test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch() -> None:
    session, _niche, keyword = _build_session()
    try:
        _seed_competition_rows(session, keyword.id, run_id="run-without-profile")
        write_competitor_profile(
            niche_id="test_niche",
            run_id="older-profile-run",
            db=session,
            top_gig_count=3,
            median_price=130.0,
            mean_reviews=640.0,
            seller_level_distribution={"TOP_RATED": 0.7, "LEVEL_2": 0.3},
            new_seller_gap={"gap_flags": []},
        )
        result = CompetitionScoreCalculator().calculate(
            keyword.id,
            session,
            config=_competition_config(use_competitor_profile=True),
        )
        assert result.score_components["avg_reviews"].raw == 640.0
        assert "competitor_profiles.mean_reviews" in result.source_evidence
    finally:
        session.close()


def test_seller_level_top_rated_raises_score() -> None:
    signal = compute_seller_level_competition_signal({"TOP_RATED": 0.8, "LEVEL_1": 0.2})
    assert signal > 75.0


def test_seller_level_new_sellers_lowers_score() -> None:
    signal = compute_seller_level_competition_signal({"LEVEL_1": 0.8, "NO_LEVEL": 0.2})
    assert signal < 30.0


def test_competition_config_guard_disabled() -> None:
    calculator = CompetitionScoreCalculator()
    base_inputs = _base_competition_inputs()
    profile = {
        "mean_reviews": 1000.0,
        "median_price": 200.0,
        "seller_level_distribution": {"TOP_RATED": 1.0},
    }
    db_with_profile = FakeScoringDB(
        competition_inputs={KEYWORD_ID: {**base_inputs, "competitor_profile": profile}},
    )
    db_without_profile = FakeScoringDB(competition_inputs={KEYWORD_ID: dict(base_inputs)})
    disabled = calculator.calculate(
        KEYWORD_ID,
        db_with_profile,
        config=_competition_config(use_competitor_profile=False),
    )
    baseline = calculator.calculate(
        KEYWORD_ID,
        db_without_profile,
        config=_competition_config(use_competitor_profile=False),
    )
    assert disabled.score_value == baseline.score_value
    assert disabled.score_components["avg_reviews"].raw == base_inputs["avg_review_count_top10"]


def test_competition_score_clamped_to_100() -> None:
    calculator = CompetitionScoreCalculator()
    profile = {
        "mean_reviews": 100000.0,
        "median_price": 1000.0,
        "seller_level_distribution": {"TOP_RATED": 1.0},
        "new_seller_gap": {"gap_flags": []},
    }
    inputs = {
        "total_result_count": 1_000_000,
        "avg_review_count_top10": 10_000.0,
        "avg_seller_level_top10": "TRS",
        "proportion_with_100_plus_reviews": 1.0,
        "pro_verified_presence_ratio": 1.0,
        "avg_starting_price_top10": 900.0,
        "llm_competitor_strength_rating": 10.0,
        "competitor_profile": profile,
    }
    result = calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(competition_inputs={KEYWORD_ID: inputs}),
        config=_competition_config(use_competitor_profile=True),
    )
    assert result.score_value is not None
    assert result.score_value <= 100.0


def test_opportunity_score_reflects_updated_competition() -> None:
    demand_result = replace(
        DemandScoreCalculator().calculate(
            KEYWORD_ID,
            FakeScoringDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
        ),
        score_value=80.0,
    )
    competition_calculator = CompetitionScoreCalculator()
    no_profile_competition = competition_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(competition_inputs={KEYWORD_ID: _base_competition_inputs()}),
        config=_competition_config(use_competitor_profile=True),
    )
    profiled_competition = competition_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(
            competition_inputs={
                KEYWORD_ID: {
                    **_base_competition_inputs(),
                    "competitor_profile": {
                        "mean_reviews": 900.0,
                        "median_price": 140.0,
                        "seller_level_distribution": {"TOP_RATED": 1.0},
                    },
                }
            }
        ),
        config=_competition_config(use_competitor_profile=True),
    )

    opportunity_calculator = OpportunityScoreCalculator()
    higher_opportunity = opportunity_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(),
        demand_result=demand_result,
        competition_result=no_profile_competition,
    )
    lower_opportunity = opportunity_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(),
        demand_result=demand_result,
        competition_result=profiled_competition,
    )

    assert higher_opportunity.score_value is not None
    assert lower_opportunity.score_value is not None
    assert lower_opportunity.score_value < higher_opportunity.score_value


def test_opportunity_score_unchanged_when_no_profile() -> None:
    demand_result = replace(
        DemandScoreCalculator().calculate(
            KEYWORD_ID,
            FakeScoringDB(demand_inputs={KEYWORD_ID: _base_demand_inputs()}),
        ),
        score_value=72.0,
    )
    competition_calculator = CompetitionScoreCalculator()
    inputs = _base_competition_inputs()
    competition_enabled = competition_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(competition_inputs={KEYWORD_ID: inputs}),
        config=_competition_config(use_competitor_profile=True),
    )
    competition_disabled = competition_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(competition_inputs={KEYWORD_ID: inputs}),
        config=_competition_config(use_competitor_profile=False),
    )
    assert competition_enabled.score_value == competition_disabled.score_value

    opportunity_calculator = OpportunityScoreCalculator()
    enabled_opportunity = opportunity_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(),
        demand_result=demand_result,
        competition_result=competition_enabled,
    )
    disabled_opportunity = opportunity_calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(),
        demand_result=demand_result,
        competition_result=competition_disabled,
    )
    assert enabled_opportunity.score_value == disabled_opportunity.score_value


def test_feasibility_boost_from_low_video_presence() -> None:
    session, _niche, _keyword = _build_session()
    try:
        write_competitor_profile(
            niche_id="test_niche",
            run_id="run-gap-video",
            db=session,
            new_seller_gap={"gap_flags": ["LOW_VIDEO_PRESENCE"]},
        )
        assert (
            get_feasibility_gap_signal(
                "test_niche",
                "run-gap-video",
                session,
                config=_feasibility_config(),
            )
            == 10.0
        )
    finally:
        session.close()


def test_feasibility_boost_from_multiple_gaps() -> None:
    session, _niche, _keyword = _build_session()
    try:
        write_competitor_profile(
            niche_id="test_niche",
            run_id="run-gap-many",
            db=session,
            new_seller_gap={
                "gap_flags": [
                    "LOW_VIDEO_PRESENCE",
                    "LOW_PORTFOLIO_PRESENCE",
                    "HIGH_PRICE_VARIANCE",
                ]
            },
        )
        assert (
            get_feasibility_gap_signal(
                "test_niche",
                "run-gap-many",
                session,
                config=_feasibility_config(),
            )
            == 30.0
        )
    finally:
        session.close()


def test_feasibility_boost_zero_when_no_profile() -> None:
    session, _niche, _keyword = _build_session()
    try:
        assert get_feasibility_gap_signal("test_niche", "missing", session) == 0.0
    finally:
        session.close()


def test_feasibility_score_applies_profile_gap_boost() -> None:
    calculator = NewSellerFeasibilityCalculator()
    baseline = calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(feasibility_inputs={KEYWORD_ID: _base_feasibility_inputs()}),
        config=_feasibility_config(),
    )
    boosted = calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(
            feasibility_inputs={
                KEYWORD_ID: {
                    **_base_feasibility_inputs(),
                    "feasibility_gap_signal": 20.0,
                    "feasibility_gap_flags": ["LOW_VIDEO_PRESENCE", "LOW_PORTFOLIO_PRESENCE"],
                }
            }
        ),
        config=_feasibility_config(),
    )
    assert baseline.score_value is not None
    assert boosted.score_value is not None
    assert boosted.score_value > baseline.score_value
    assert "profile_gap_boost" in boosted.score_components


def test_feasibility_score_derives_gap_boost_from_inline_profile_flags() -> None:
    calculator = NewSellerFeasibilityCalculator()
    result = calculator.calculate(
        KEYWORD_ID,
        FakeScoringDB(
            feasibility_inputs={
                KEYWORD_ID: {
                    **_base_feasibility_inputs(),
                    "competitor_profile": {
                        "new_seller_gap": {
                            "gap_flags": ["LOW_VIDEO_PRESENCE", "LOW_PORTFOLIO_PRESENCE"],
                        }
                    },
                }
            }
        ),
        config=_feasibility_config(),
    )
    assert result.score_components["profile_gap_boost"].value == 20.0


def test_feasibility_score_session_path_applies_profile_gap_flags() -> None:
    session, _niche, keyword = _build_session()
    try:
        _seed_competition_rows(session, keyword.id, run_id="run-feasibility-db")
        write_competitor_profile(
            niche_id="test_niche",
            run_id="run-feasibility-db",
            db=session,
            new_seller_gap={
                "gap_flags": ["LOW_VIDEO_PRESENCE", "HIGH_PRICE_VARIANCE"],
            },
        )
        result = NewSellerFeasibilityCalculator().calculate(
            keyword.id,
            session,
            config=_feasibility_config(gap_boost_per_flag=12.0, max_gap_boost=30.0),
        )
        assert result.score_components["profile_gap_boost"].value == 24.0
        assert "competitor_profiles.new_seller_gap.gap_flags" in result.source_evidence
    finally:
        session.close()


def test_top_rated_dominant_returns_high_signal() -> None:
    signal = compute_seller_level_competition_signal({"TOP_RATED": 0.7, "PRO": 0.3})
    assert signal >= 90.0


def test_new_seller_dominant_returns_low_signal() -> None:
    signal = compute_seller_level_competition_signal({"LEVEL_1": 0.9, "NO_LEVEL": 0.1})
    assert signal <= 20.0


def test_mixed_distribution_returns_moderate_signal() -> None:
    signal = compute_seller_level_competition_signal(
        {"TOP_RATED": 0.25, "LEVEL_2": 0.25, "LEVEL_1": 0.25, "NO_LEVEL": 0.25},
    )
    assert 35.0 <= signal <= 70.0


def test_competition_score_with_empty_db_no_crash() -> None:
    result = CompetitionScoreCalculator().calculate(
        KEYWORD_ID,
        FakeScoringDB(competition_inputs={KEYWORD_ID: {}}),
    )
    assert result.score_value is None


def test_opportunity_score_with_empty_db_no_crash() -> None:
    db = FakeScoringDB(
        demand_inputs={KEYWORD_ID: {}},
        competition_inputs={KEYWORD_ID: {}},
    )
    result = OpportunityScoreCalculator().calculate(KEYWORD_ID, db)
    assert result.score_value is None


def test_config_competition_profile_keys_valid(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source.setdefault("scoring", {})
    source["scoring"]["competition"] = {"use_competitor_profile": True}
    source["scoring"]["feasibility"] = {
        "gap_boost_per_flag": 10.0,
        "max_gap_boost": 30.0,
    }
    config_path = tmp_path / "config_competition_profile.yaml"
    config_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    config = ConfigLoader(config_path).load()
    assert config.scoring.competition.use_competitor_profile is True
    assert config.scoring.feasibility.gap_boost_per_flag == 10.0
    assert config.scoring.feasibility.max_gap_boost == 30.0


def test_config_feasibility_gap_bounds_reject_invalid_values(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source.setdefault("scoring", {})
    source["scoring"]["feasibility"] = {
        "gap_boost_per_flag": 20.0,
        "max_gap_boost": 10.0,
    }
    config_path = tmp_path / "config_invalid_feasibility_bounds.yaml"
    config_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValueError):
        ConfigLoader(config_path).load()


def test_competition_helper_guards_and_normalizers() -> None:
    assert _coerce_bool("yes", default=False) is True
    assert _coerce_bool("0", default=True) is False
    assert _coerce_float(None, 4.0) == 4.0
    assert _coerce_float("bad", 5.0) == 5.0
    assert _normalize_gap_flags(["low_video_presence", 7, "  "]) == ["LOW_VIDEO_PRESENCE"]

    calculator = CompetitionScoreCalculator()
    assert calculator._normalize_count(0.0) == 0.0
    assert calculator._normalize_review_count(0.0) == 0.0
    assert calculator._normalize_seller_level(3) == 60.0
    assert calculator._normalize_seller_level({"x": 1}) is None
    assert calculator._normalize_price(0.0) == 0.0
    assert calculator._normalize_llm_competitor_strength(50.0) == 50.0
    assert calculator._load_signals(KEYWORD_ID, None) == {}
    assert calculator._as_float("bad-value") is None
    assert calculator._seller_level_value(None) is None
    assert calculator._derive_profile_llm_rating(profile_inputs={}, existing_rating=None) == (None, "")


def test_competition_seller_level_signal_guard_paths() -> None:
    assert compute_seller_level_competition_signal({}) == 50.0
    assert compute_seller_level_competition_signal({"LEVEL_1": 0.0}) == 50.0
    assert compute_seller_level_competition_signal(cast(dict[str, float], {1: 1.0})) == 50.0
    assert compute_seller_level_competition_signal({"TOP-TIER": 1.0}) == 95.0
    assert compute_seller_level_competition_signal({"NOVICE": 1.0}) == 50.0


def test_competitor_profile_inputs_supports_provider_object() -> None:
    class _Provider:
        @staticmethod
        def get_competitor_profile_inputs(_niche_id: str, _run_id: str) -> dict[str, Any]:
            return {"mean_reviews": 77.0, "median_price": 55.0}

    payload = get_competitor_profile_inputs("test_niche", "run-provider", _Provider())
    assert payload["mean_reviews"] == 77.0
    assert payload["median_price"] == 55.0


def test_competition_marketplace_result_count_fallback_paths() -> None:
    session, _niche, keyword = _build_session()
    try:
        calculator = CompetitionScoreCalculator()
        assert calculator._resolve_marketplace_result_count(session, keyword.id) is None
        session.add(SearchResult(keyword_id=keyword.id, rank=1, title="fallback row", gig_id=None))
        session.commit()
        assert calculator._resolve_marketplace_result_count(session, keyword.id) is None

        for rank in range(2, 11):
            session.add(
                SearchResult(
                    keyword_id=keyword.id,
                    rank=rank,
                    title=f"fallback row {rank}",
                    gig_id=None,
                )
            )
        session.commit()
        assert calculator._resolve_marketplace_result_count(session, keyword.id) == 10.0
    finally:
        session.close()


def test_competition_is_pro_verified_requires_boolean_metadata() -> None:
    seller = Seller(seller_handle="bool_check", metadata_json={"is_pro": "true"})
    assert CompetitionScoreCalculator._is_pro_verified(seller) is False


def test_competition_filters_to_relevance_flag_when_rsv_below_080() -> None:
    session, _niche, keyword = _build_session()
    try:
        for rank in range(1, 6):
            seller = Seller(seller_handle=f"rel-seller-{rank}", level="LEVEL_1")
            session.add(seller)
            session.flush()
            gig = Gig(
                gig_url=f"https://fiverr.com/rel/{rank}",
                seller_username=seller.seller_handle,
                seller_id=seller.id,
                keyword_id=keyword.id,
                run_id="r1",
                title=f"gig {rank}",
                normalized_title=f"gig {rank}",
                review_count=100.0,
                starting_price=30.0,
                relevance_flag=(rank % 2 == 0),
            )
            session.add(gig)
            session.flush()
            session.add(SearchResult(keyword_id=keyword.id, run_id="r1", rank=rank, gig_id=gig.id, title=gig.title))
        session.add(
            ResultSetValidation(
                keyword_id=keyword.id,
                run_id="r1",
                result_set_relevance_score=0.60,
                relevance_deduction=-0.05,
            )
        )
        session.commit()
        signals = CompetitionScoreCalculator()._load_signals_from_db(keyword.id, session)
        assert signals["avg_review_count_top10"] == 100.0
    finally:
        session.close()


def test_competition_all_filtered_falls_back_to_full_set() -> None:
    session, _niche, keyword = _build_session()
    try:
        for rank in range(1, 4):
            seller = Seller(seller_handle=f"all-seller-{rank}", level="LEVEL_1")
            session.add(seller)
            session.flush()
            gig = Gig(
                gig_url=f"https://fiverr.com/all/{rank}",
                seller_username=seller.seller_handle,
                seller_id=seller.id,
                keyword_id=keyword.id,
                run_id="r1",
                title=f"all {rank}",
                normalized_title=f"all {rank}",
                review_count=50.0,
                starting_price=20.0,
                relevance_flag=False,
            )
            session.add(gig)
            session.flush()
            session.add(SearchResult(keyword_id=keyword.id, run_id="r1", rank=rank, gig_id=gig.id, title=gig.title))
        session.add(
            ResultSetValidation(
                keyword_id=keyword.id,
                run_id="r1",
                result_set_relevance_score=0.60,
                relevance_deduction=-0.05,
            )
        )
        session.commit()
        signals = CompetitionScoreCalculator()._load_signals_from_db(keyword.id, session)
        assert signals["avg_review_count_top10"] == 50.0
    finally:
        session.close()


def test_competition_no_rsv_no_filtering() -> None:
    session, _niche, keyword = _build_session()
    try:
        _seed_competition_rows(session, keyword.id, run_id="r1")
        result = CompetitionScoreCalculator().calculate(keyword.id, session)
        assert result.score_value is not None
    finally:
        session.close()
