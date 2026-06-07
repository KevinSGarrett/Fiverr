"""Tests for S7.5 Trend Chase hypothesis mode."""

from __future__ import annotations

import inspect

from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
from src.discovery.contracts import HypothesisMode
from src.discovery.hypothesis import (
    GAP_OPPORTUNITY_WEIGHT,
    TREND_SCORE_THRESHOLD,
    TREND_SCORE_WEIGHT,
    TREND_VELOCITY_THRESHOLD,
    TREND_VELOCITY_WEIGHT,
    _identify_trending_keywords,
    _score_trend_hypothesis_confidence,
    generate_adjacent_keyword_hypotheses,
    generate_adjacent_niche_hypotheses,
    generate_gap_exploit_hypotheses,
    generate_trend_chase_hypotheses,
)

SAMPLE_TRENDS = [
    {"keyword": "python ai agent automation", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78},
    {"keyword": "workflow automation 2025", "trend_score": 0.75, "trend_velocity": 0.70, "opportunity_score": 0.72},
    {"keyword": "established stable tool", "trend_score": 0.85, "trend_velocity": 0.15, "opportunity_score": 0.60},
    {"keyword": "declining interest keyword", "trend_score": 0.30, "trend_velocity": 0.10, "opportunity_score": 0.20},
]


class TestIdentifyTrendingKeywords:
    def test_returns_list(self) -> None:
        result = _identify_trending_keywords(SAMPLE_TRENDS)
        assert isinstance(result, list)

    def test_high_score_high_velocity_included(self) -> None:
        result = _identify_trending_keywords(SAMPLE_TRENDS)
        keywords = [row["keyword"] for row in result]
        assert "python ai agent automation" in keywords
        assert "workflow automation 2025" in keywords

    def test_low_velocity_excluded(self) -> None:
        result = _identify_trending_keywords(SAMPLE_TRENDS)
        keywords = [row["keyword"] for row in result]
        assert "established stable tool" not in keywords

    def test_low_score_excluded(self) -> None:
        result = _identify_trending_keywords(SAMPLE_TRENDS)
        keywords = [row["keyword"] for row in result]
        assert "declining interest keyword" not in keywords

    def test_empty_input_returns_empty(self) -> None:
        assert _identify_trending_keywords([]) == []

    def test_trend_score_threshold_boundary_inclusive(self) -> None:
        rows = [{"keyword": "edge", "trend_score": TREND_SCORE_THRESHOLD, "trend_velocity": 0.80, "opportunity_score": 0.5}]
        assert len(_identify_trending_keywords(rows)) == 1

    def test_trend_velocity_threshold_boundary_inclusive(self) -> None:
        rows = [{"keyword": "edge", "trend_score": 0.80, "trend_velocity": TREND_VELOCITY_THRESHOLD, "opportunity_score": 0.5}]
        assert len(_identify_trending_keywords(rows)) == 1

    def test_missing_keys_default_to_zero(self) -> None:
        assert _identify_trending_keywords([{"keyword": "sparse"}]) == []

    def test_requires_both_score_and_velocity(self) -> None:
        score_only = [{"keyword": "popular_not_trending", "trend_score": 0.90, "trend_velocity": 0.10}]
        velocity_only = [{"keyword": "noisy_signal", "trend_score": 0.20, "trend_velocity": 0.90}]
        both = [{"keyword": "true_trend", "trend_score": 0.80, "trend_velocity": 0.65}]
        assert _identify_trending_keywords(score_only) == []
        assert _identify_trending_keywords(velocity_only) == []
        assert len(_identify_trending_keywords(both)) == 1

    def test_non_dict_rows_ignored(self) -> None:
        rows = [None, "oops", 42, {"keyword": "trend", "trend_score": 0.8, "trend_velocity": 0.7}]
        result = _identify_trending_keywords(rows)  # type: ignore[arg-type]
        assert len(result) == 1


class TestScoreTrendHypothesisConfidence:
    def test_returns_float(self) -> None:
        assert isinstance(_score_trend_hypothesis_confidence(SAMPLE_TRENDS[0]), float)

    def test_score_bounded_to_0_1(self) -> None:
        for row in SAMPLE_TRENDS:
            score = _score_trend_hypothesis_confidence(row)
            assert 0.0 <= score <= 1.0

    def test_empty_kw_data_returns_zero(self) -> None:
        assert _score_trend_hypothesis_confidence({}) == 0.0

    def test_trend_score_weight_applied(self) -> None:
        score = _score_trend_hypothesis_confidence({"trend_score": 1.0, "trend_velocity": 0.0})
        assert abs(score - TREND_SCORE_WEIGHT) < 0.001

    def test_trend_velocity_weight_applied(self) -> None:
        score = _score_trend_hypothesis_confidence({"trend_score": 0.0, "trend_velocity": 1.0})
        assert abs(score - TREND_VELOCITY_WEIGHT) < 0.001

    def test_weights_sum_to_one(self) -> None:
        assert abs(TREND_SCORE_WEIGHT + TREND_VELOCITY_WEIGHT - 1.0) < 0.001

    def test_formula_precision(self) -> None:
        expected = TREND_SCORE_WEIGHT * 0.80 + TREND_VELOCITY_WEIGHT * 0.70
        actual = _score_trend_hypothesis_confidence({"trend_score": 0.80, "trend_velocity": 0.70})
        assert abs(actual - expected) < 0.001

    def test_no_overflow_for_invalid_inputs(self) -> None:
        assert _score_trend_hypothesis_confidence({"trend_score": 2.0, "trend_velocity": 2.0}) == 1.0

    def test_no_base_bonus_zero_inputs(self) -> None:
        assert _score_trend_hypothesis_confidence({"trend_score": 0.0, "trend_velocity": 0.0}) == 0.0

    def test_score_weight_higher_than_velocity_weight(self) -> None:
        assert TREND_SCORE_WEIGHT > TREND_VELOCITY_WEIGHT
        assert TREND_VELOCITY_WEIGHT > GAP_OPPORTUNITY_WEIGHT


class TestGenerateTrendChaseHypotheses:
    def test_returns_list(self) -> None:
        result = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [])
        assert isinstance(result, list)

    def test_empty_source_returns_empty(self) -> None:
        assert generate_trend_chase_hypotheses("", SAMPLE_TRENDS, []) == []

    def test_empty_keyword_trends_returns_empty(self) -> None:
        assert generate_trend_chase_hypotheses("python_automation", [], []) == []

    def test_budget_gate_rejects_when_too_high(self) -> None:
        results = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [], min_confidence=0.99)
        assert results
        assert all(not r.accepted for r in results)

    def test_budget_gate_accepts_when_low(self) -> None:
        results = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [], min_confidence=0.0)
        accepted = [r for r in results if r.accepted]
        assert len(accepted) >= 2

    def test_deduplicates_against_existing_hypotheses_case_insensitive(self) -> None:
        existing = ["Python AI Agent Automation"]
        results = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, existing, min_confidence=0.0)
        texts = [r.hypothesis_text.lower() for r in results]
        assert "python ai agent automation" not in texts

    def test_niche_id_is_source(self) -> None:
        results = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [])
        assert all(r.niche_id == "python_automation" for r in results)

    def test_hypothesis_text_is_keyword(self) -> None:
        results = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [])
        expected = {row["keyword"] for row in SAMPLE_TRENDS}
        assert all(r.hypothesis_text in expected for r in results)

    def test_reason_string_present(self) -> None:
        results = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [])
        assert results
        assert all(len(r.reason) > 10 for r in results)

    def test_reason_contains_accepted_or_rejected(self) -> None:
        accepted = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [], min_confidence=0.0)
        rejected = generate_trend_chase_hypotheses("python_automation", SAMPLE_TRENDS, [], min_confidence=0.99)
        assert any("ACCEPTED" in row.reason for row in accepted)
        assert all("REJECTED" in row.reason for row in rejected)

    def test_max_hypotheses_respected(self) -> None:
        trends = SAMPLE_TRENDS * 20
        results = generate_trend_chase_hypotheses("python_automation", trends, [], max_hypotheses=2, min_confidence=0.0)
        accepted = [r for r in results if r.accepted]
        assert len(accepted) <= 2

    def test_default_min_confidence_is_point_five(self) -> None:
        sig = inspect.signature(generate_trend_chase_hypotheses)
        assert sig.parameters["min_confidence"].default == 0.50

    def test_default_trend_threshold_params_match_constants(self) -> None:
        sig = inspect.signature(generate_trend_chase_hypotheses)
        assert sig.parameters["trend_score_threshold"].default == TREND_SCORE_THRESHOLD
        assert sig.parameters["trend_velocity_threshold"].default == TREND_VELOCITY_THRESHOLD

    def test_sorting_by_opportunity_descending(self) -> None:
        trends = [
            {"keyword": "low_opp_trend", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.50},
            {"keyword": "high_opp_trend", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.95},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        accepted = [r for r in results if r.accepted]
        assert accepted
        assert accepted[0].hypothesis_text == "high_opp_trend"

    def test_skips_empty_string_keyword(self) -> None:
        trends = [
            {"keyword": "", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78},
            {"keyword": "valid_trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        texts = [r.hypothesis_text for r in results]
        assert "" not in texts
        assert "valid_trend" in texts

    def test_fixture_trends_accept_in_seed_style_format(self) -> None:
        fixture_trends = [
            {"keyword": "mcp agent builder tool", "trend_score": 0.85, "trend_velocity": 0.72, "opportunity_score": 0.80},
            {"keyword": "ai workflow automation n8n", "trend_score": 0.78, "trend_velocity": 0.55, "opportunity_score": 0.74},
        ]
        for niche in ["mcp_ai_agent", "workflow_automation"]:
            results = generate_trend_chase_hypotheses(niche, fixture_trends, [], min_confidence=0.50)
            accepted = [row for row in results if row.accepted]
            assert len(accepted) == 2

    def test_only_trending_rows_included_in_output(self) -> None:
        trends = [
            {"keyword": "true_trend", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.78},
            {"keyword": "low_velocity", "trend_score": 0.90, "trend_velocity": 0.10, "opportunity_score": 0.60},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        texts = [r.hypothesis_text for r in results]
        assert "true_trend" in texts
        assert "low_velocity" not in texts

    def test_budget_gate_accepts_confidence_meeting_threshold(self) -> None:
        trends = [{"keyword": "candidate", "trend_score": 0.65, "trend_velocity": 0.45, "opportunity_score": 0.50}]
        results = generate_trend_chase_hypotheses("python_automation", trends, [])
        assert results
        assert results[0].accepted is True
        assert results[0].specificity_score >= 0.50

    def test_hypothesis_mode_trend_chase_value(self) -> None:
        assert HypothesisMode.TREND_CHASE.value == "trend_chase"

    def test_s72_s73_s74_still_callable(self) -> None:
        kw = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        ni = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], [])
        gap = generate_gap_exploit_hypotheses(
            "python_automation",
            [{"keyword": "gap test", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}],
            [],
        )
        assert isinstance(kw, list)
        assert isinstance(ni, list)
        assert isinstance(gap, list)

    def test_all_niches_support_s75_call(self) -> None:
        trend = [{"keyword": "sample trend keyword", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        for niche in sorted(NICHE_VALIDATION_CONFIG.keys()):
            result = generate_trend_chase_hypotheses(niche, trend, [])
            assert isinstance(result, list)
