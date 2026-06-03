"""R11 emerging bonus and negation-aware exclusion tests."""

from __future__ import annotations

from src.analysis.emerging_bonus import compute_emerging_opportunity_bonus, negation_aware_exclusion


def test_emerging_bonus_returns_zero_for_ghost_keyword() -> None:
    class MockKS:
        ghost_market_flag = True
        autocomplete_status = "emerging"

    class MockRSV:
        result_set_relevance_score = 0.9
        category_contamination_flag = False

    assert compute_emerging_opportunity_bonus(MockKS(), MockRSV()) == 0.0


def test_negation_aware_exclusion_true_when_not_negated() -> None:
    assert negation_aware_exclusion("python automation", ["automation"]) is False


def test_negation_aware_exclusion_false_when_negated() -> None:
    assert negation_aware_exclusion("not automation", ["automation"]) is False


def test_negation_aware_exclusion_true_with_exclusion_cue() -> None:
    assert negation_aware_exclusion("exclude automation jobs", ["automation"]) is True
