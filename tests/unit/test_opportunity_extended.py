"""Extended opportunity qualifier tests."""

from __future__ import annotations

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
