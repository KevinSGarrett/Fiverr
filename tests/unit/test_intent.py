"""Intent alignment tests."""

from __future__ import annotations

from src.scoring.intent import (
    ConversionIntentScoreCalculator,
    _opportunity_qualifier_enabled,
    compute_intent_alignment_factor,
)


def test_intent_alignment_applied_when_on() -> None:
    payload = {
        1: {
            "keyword": "hire python developer",
            "avg_review_count_top10": 120.0,
            "llm_buyer_intent_classification": "TRANSACTIONAL",
            "reddit_demand_intent_score": 0.9,
            "query_intent_class": "INFORMATIONAL",
            "service_intent_class": "TRANSACTIONAL",
        }
    }
    on_result = ConversionIntentScoreCalculator().calculate(
        1,
        payload,
        config={"scoring": {"opportunity": {"qualify_by_relevance": True}}},
    )
    off_result = ConversionIntentScoreCalculator().calculate(
        1,
        payload,
        config={"scoring": {"opportunity": {"qualify_by_relevance": False}}},
    )
    assert on_result.score_value is not None and off_result.score_value is not None
    assert on_result.score_value < off_result.score_value
    assert "intent_alignment" in on_result.score_components


def test_intent_alignment_factor_bounds() -> None:
    assert compute_intent_alignment_factor(None, "TRANSACTIONAL") == 1.0
    assert compute_intent_alignment_factor("TRANSACTIONAL", "TRANSACTIONAL") == 1.0
    assert 0.0 <= compute_intent_alignment_factor("INFORMATIONAL", "TRANSACTIONAL") <= 1.0


def test_intent_alignment_factor_expected_permutations() -> None:
    assert compute_intent_alignment_factor("TRANSACTIONAL", "HIGH_INTENT") == 0.9
    assert compute_intent_alignment_factor("HIGH_INTENT", "TRANSACTIONAL") == 0.9
    assert compute_intent_alignment_factor("INFORMATIONAL", "TRANSACTIONAL") == 0.6
    assert compute_intent_alignment_factor("INFORMATIONAL", "HIGH_INTENT") == 0.7


def test_opportunity_qualifier_enabled_guard_paths() -> None:
    assert _opportunity_qualifier_enabled(None) is False
    assert _opportunity_qualifier_enabled({"scoring": "bad"}) is False
    assert _opportunity_qualifier_enabled({"scoring": {"opportunity": "bad"}}) is False
    assert _opportunity_qualifier_enabled({"scoring": {"opportunity": {"qualify_by_relevance": True}}}) is True


def test_intent_alignment_factor_blank_inputs_return_one() -> None:
    assert compute_intent_alignment_factor("", "TRANSACTIONAL") == 1.0
    assert compute_intent_alignment_factor("TRANSACTIONAL", "") == 1.0
