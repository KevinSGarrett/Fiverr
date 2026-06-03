"""R11 edge-case tests for negation exclusion and emerging opportunity bonus."""

from __future__ import annotations

from src.analysis.emerging_bonus import (
    compute_emerging_opportunity_bonus,
)
from src.analysis.emerging_bonus import (
    negation_aware_exclusion as emerging_bonus_negation_aware_exclusion,
)
from src.analysis.negation_exclusion import negation_aware_exclusion


def test_negation_aware_excludes_term_without_negation() -> None:
    assert negation_aware_exclusion("python automation services", ["automation"]) is True


def test_negation_aware_does_not_exclude_negated_term() -> None:
    assert negation_aware_exclusion("not automation", ["automation"]) is False


def test_negation_aware_does_not_exclude_no_prefix() -> None:
    assert negation_aware_exclusion("no automation here", ["automation"]) is False


def test_negation_aware_term_absent_returns_false() -> None:
    assert negation_aware_exclusion("completely unrelated text", ["automation"]) is False


def test_negation_aware_empty_exclusions_returns_false() -> None:
    assert negation_aware_exclusion("automation", []) is False


def test_negation_aware_multilingual_passthrough() -> None:
    result = negation_aware_exclusion("automation 自动化", ["automation"])
    assert result is True


def test_negation_aware_double_negation_treated_as_bool_output() -> None:
    result = negation_aware_exclusion("not not automation", ["automation"])
    assert isinstance(result, bool)


def test_negation_aware_case_insensitive() -> None:
    assert negation_aware_exclusion("AUTOMATION services", ["automation"]) is True
    assert negation_aware_exclusion("NOT automation", ["automation"]) is False


def test_negation_aware_dont_contraction() -> None:
    result = negation_aware_exclusion("don't use automation", ["automation"])
    assert result is False


def test_emerging_bonus_negation_helper_empty_text_returns_false() -> None:
    assert emerging_bonus_negation_aware_exclusion("", ["automation"]) is False


def test_emerging_bonus_negation_helper_ignores_empty_exclusion_term() -> None:
    assert emerging_bonus_negation_aware_exclusion("exclude automation", ["", "automation"]) is True


def test_emerging_bonus_negation_helper_requires_exclusion_cue() -> None:
    result = emerging_bonus_negation_aware_exclusion("automation services", ["automation"])
    assert result is False


def test_emerging_bonus_negation_helper_ignores_negated_prefix() -> None:
    result = emerging_bonus_negation_aware_exclusion("do not exclude automation", ["automation"])
    assert result is False


def test_emerging_bonus_negation_helper_matches_with_exclusion_language() -> None:
    result = emerging_bonus_negation_aware_exclusion("please exclude automation work", ["automation"])
    assert result is True


def test_emerging_bonus_high_integrity_keyword() -> None:
    class MockKS:
        autocomplete_status = "emerging"
        ghost_market_flag = False

    class MockRSV:
        result_set_relevance_score = 0.85
        category_contamination_flag = False

    bonus = compute_emerging_opportunity_bonus(MockKS(), MockRSV())
    assert bonus > 0.0


def test_emerging_bonus_zero_for_ghost() -> None:
    class MockKS:
        autocomplete_status = "emerging"
        ghost_market_flag = True

    class MockRSV:
        result_set_relevance_score = 0.85
        category_contamination_flag = False

    assert compute_emerging_opportunity_bonus(MockKS(), MockRSV()) == 0.0


def test_emerging_bonus_zero_for_low_relevance() -> None:
    class MockKS:
        autocomplete_status = "emerging"
        ghost_market_flag = False

    class MockRSV:
        result_set_relevance_score = 0.60
        category_contamination_flag = False

    assert compute_emerging_opportunity_bonus(MockKS(), MockRSV()) == 0.0


def test_emerging_bonus_zero_for_contaminated() -> None:
    class MockKS:
        autocomplete_status = "emerging"
        ghost_market_flag = False

    class MockRSV:
        result_set_relevance_score = 0.85
        category_contamination_flag = True

    assert compute_emerging_opportunity_bonus(MockKS(), MockRSV()) == 0.0


def test_emerging_bonus_zero_for_non_emerging() -> None:
    class MockKS:
        autocomplete_status = "established"
        ghost_market_flag = False

    class MockRSV:
        result_set_relevance_score = 0.85
        category_contamination_flag = False

    assert compute_emerging_opportunity_bonus(MockKS(), MockRSV()) == 0.0


def test_emerging_bonus_zero_for_null_rsv() -> None:
    class MockKS:
        autocomplete_status = "emerging"
        ghost_market_flag = False

    assert compute_emerging_opportunity_bonus(MockKS(), None) == 0.0
