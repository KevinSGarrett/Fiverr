"""Unit tests for CompetitorProfile integrations in Score 2/3/4."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.config import ConfigLoader
from src.models import Base, Keyword, Niche, write_competitor_profile
from src.scoring.competition import (
    CompetitionScoreCalculator,
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
