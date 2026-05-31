"""Extended opportunity qualifier tests."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from typing import Any

import pytest

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.demand import DemandScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator, _opportunity_relevance_qualifier


class _FakeDB:
    def __init__(self, payload: dict[int, dict[str, Any]]) -> None:
        self._payload = payload

    def get_demand_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))

    def get_competition_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))

    def get_opportunity_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))

    def get_intent_inputs(self, keyword_id: int) -> dict[str, Any]:
        return dict(self._payload.get(keyword_id, {}))


def _golden_score_with_overrides(*overrides: str) -> dict[str, Any]:
    command = [sys.executable, "run.py", "score", "--golden"]
    for override in overrides:
        command.extend(["--config-override", override])
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = completed.stdout.strip()
    start = payload.find("{")
    assert start >= 0
    return json.loads(payload[start:])


def _demand() -> Any:
    return replace(
        DemandScoreCalculator().calculate(1, _FakeDB({1: {"total_result_count": 1000, "autocomplete_position": 2}})),
        score_value=80.0,
    )


def _competition() -> Any:
    return replace(
        CompetitionScoreCalculator().calculate(
            1,
            _FakeDB(
                {
                    1: {
                        "total_result_count": 1000,
                        "avg_review_count_top10": 120.0,
                        "avg_seller_level_top10": "Level 2",
                        "proportion_with_100_plus_reviews": 0.4,
                        "pro_verified_presence_ratio": 0.2,
                        "avg_starting_price_top10": 40.0,
                        "llm_competitor_strength_rating": 5.0,
                    }
                }
            ),
        ),
        score_value=40.0,
    )


def test_opportunity_qualified_by_relevance() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.75}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.score_value == pytest.approx(64.0)


def test_opportunity_relevance_none_no_change() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.opportunity_relevance_factor == 1.0
    assert result.score_value == pytest.approx(72.0)


def test_opportunity_relevance_factor_recorded() -> None:
    result = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.75}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    assert result.opportunity_relevance_factor == pytest.approx(0.75)


def test_opportunity_qualifier_toggle_off_matches_legacy() -> None:
    legacy = OpportunityScoreCalculator().calculate(1, _FakeDB({1: {}}), demand_result=_demand(), competition_result=_competition())
    off = OpportunityScoreCalculator().calculate(
        1,
        _FakeDB({1: {"rsv_relevance": 0.3}}),
        demand_result=_demand(),
        competition_result=_competition(),
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    assert off.score_value == legacy.score_value


def test_opportunity_relevance_qualifier_clamps() -> None:
    assert _opportunity_relevance_qualifier(None) == 1.0
    assert _opportunity_relevance_qualifier(1.5) == 1.0
    assert _opportunity_relevance_qualifier(-0.5) == 0.0


def test_all_toggles_off_golden_equals_legacy_baseline() -> None:
    result = _golden_score_with_overrides(
        "relevance.enable_stage_3_5=true",
        "scoring.demand.use_trc_reliability=false",
        "scoring.demand.use_signal_qualifiers=false",
        "scoring.competition.use_per_keyword_profile=false",
        "scoring.competition.exclude_contaminated=false",
        "scoring.exclude_price_outliers=false",
        "scoring.feasibility.use_clean_gig_set=false",
        "scoring.opportunity.qualify_by_relevance=false",
    )
    assert result["status"] == "PASS"
    assert result["anchor_rows"]["110"]["final_score"] == pytest.approx(62.7)
    assert result["anchor_rows"]["96"]["final_score"] == pytest.approx(35.8)
    assert result["anchor_rows"]["3"]["final_score"] == pytest.approx(56.66)


def test_kw110_conditional_go_holds_with_all_toggles_on() -> None:
    result = _golden_score_with_overrides(
        "relevance.enable_stage_3_5=true",
        "scoring.demand.use_trc_reliability=true",
        "scoring.demand.use_signal_qualifiers=true",
        "scoring.competition.use_per_keyword_profile=true",
        "scoring.competition.exclude_contaminated=true",
        "scoring.exclude_price_outliers=true",
        "scoring.feasibility.use_clean_gig_set=true",
        "scoring.opportunity.qualify_by_relevance=true",
    )
    kw110 = result["anchor_rows"]["110"]
    assert result["status"] == "PASS"
    assert kw110["tag"] == "CONDITIONAL_GO"
    assert kw110["confidence_modifier"] == pytest.approx(1.0)
    assert kw110["final_score"] >= 60.0


def test_anchor_scores_drift_within_two_points_when_on() -> None:
    off_result = _golden_score_with_overrides(
        "relevance.enable_stage_3_5=true",
        "scoring.demand.use_trc_reliability=false",
        "scoring.demand.use_signal_qualifiers=false",
        "scoring.competition.use_per_keyword_profile=false",
        "scoring.competition.exclude_contaminated=false",
        "scoring.exclude_price_outliers=false",
        "scoring.feasibility.use_clean_gig_set=false",
        "scoring.opportunity.qualify_by_relevance=false",
    )
    on_result = _golden_score_with_overrides(
        "relevance.enable_stage_3_5=true",
        "scoring.demand.use_trc_reliability=true",
        "scoring.demand.use_signal_qualifiers=true",
        "scoring.competition.use_per_keyword_profile=true",
        "scoring.competition.exclude_contaminated=true",
        "scoring.exclude_price_outliers=true",
        "scoring.feasibility.use_clean_gig_set=true",
        "scoring.opportunity.qualify_by_relevance=true",
    )
    for keyword_id in ("110", "96", "3"):
        off_score = float(off_result["anchor_rows"][keyword_id]["final_score"])
        on_score = float(on_result["anchor_rows"][keyword_id]["final_score"])
        assert abs(on_score - off_score) <= 2.0
