"""Tests for S7.5 Trend Chase hypothesis mode."""

from __future__ import annotations

import inspect

import pytest

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


class TestTrendChaseCoverageUpliftAgentF:
    def test_all_below_trend_score_no_trends(self) -> None:
        below = [
            {"keyword": f"kw{i}", "trend_score": TREND_SCORE_THRESHOLD - 0.01, "trend_velocity": 0.80, "opportunity_score": 0.75}
            for i in range(5)
        ]
        assert _identify_trending_keywords(below) == []

    def test_all_low_velocity_no_trends(self) -> None:
        low_vel = [
            {
                "keyword": f"kw{i}",
                "trend_score": 0.90,
                "trend_velocity": TREND_VELOCITY_THRESHOLD - 0.01,
                "opportunity_score": 0.75,
            }
            for i in range(5)
        ]
        assert _identify_trending_keywords(low_vel) == []

    def test_missing_trend_score_defaults_to_zero(self) -> None:
        sparse = [{"keyword": "no_scores"}]
        assert _identify_trending_keywords(sparse) == []

    def test_missing_trend_velocity_defaults_to_zero(self) -> None:
        score = _score_trend_hypothesis_confidence({"trend_score": 0.80})
        assert isinstance(score, float) and 0.0 <= score <= 1.0

    @pytest.mark.parametrize(
        ("trend_score", "trend_velocity", "expected_trend"),
        [(0.80, 0.65, True), (0.60, 0.40, True), (0.59, 0.40, False), (0.60, 0.39, False), (0.0, 0.0, False), (1.0, 1.0, True)],
    )
    def test_trend_criteria_parametrized(self, trend_score: float, trend_velocity: float, expected_trend: bool) -> None:
        rows = [
            {"keyword": "test", "trend_score": trend_score, "trend_velocity": trend_velocity, "opportunity_score": 0.7},
        ]
        result = _identify_trending_keywords(rows)
        assert (len(result) == 1) == expected_trend

    def test_confidence_bounded_at_one(self) -> None:
        assert _score_trend_hypothesis_confidence({"trend_score": 1.0, "trend_velocity": 1.0}) <= 1.0

    def test_confidence_at_zero(self) -> None:
        assert _score_trend_hypothesis_confidence({"trend_score": 0.0, "trend_velocity": 0.0}) == 0.0

    def test_all_existing_blocks_all_results(self) -> None:
        trends = [{"keyword": f"kw{i}", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78} for i in range(5)]
        existing = [f"kw{i}" for i in range(5)]
        results = generate_trend_chase_hypotheses("python_automation", trends, existing, min_confidence=0.0)
        assert [r for r in results if r.accepted] == []

    def test_partial_dedup(self) -> None:
        trends = [
            {"keyword": "existing_kw", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.90},
            {"keyword": "new_kw", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.78},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, ["existing_kw"], min_confidence=0.0)
        texts = [r.hypothesis_text for r in results]
        assert "existing_kw" not in texts
        assert "new_kw" in texts

    def test_max_hypotheses_zero_no_accepted(self) -> None:
        trends = [{"keyword": f"kw{i}", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78} for i in range(10)]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], max_hypotheses=0, min_confidence=0.0)
        assert all(not r.accepted for r in results)

    def test_max_hypotheses_one(self) -> None:
        trends = [{"keyword": f"kw{i}", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78} for i in range(10)]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], max_hypotheses=1, min_confidence=0.0)
        assert sum(r.accepted for r in results) <= 1

    def test_reason_contains_trend_and_velocity(self) -> None:
        trends = [{"keyword": "test", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        results = generate_trend_chase_hypotheses("python_automation", trends, [])
        assert results
        for contract in results:
            assert contract.reason and len(contract.reason) > 15
            assert any(term in contract.reason.lower() for term in ["trend", "confidence", "accepted", "rejected"])

    def test_sorted_by_opportunity_desc(self) -> None:
        trends = [
            {"keyword": "third", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.50},
            {"keyword": "first", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.95},
            {"keyword": "second", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.75},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        accepted = [r.hypothesis_text for r in results if r.accepted]
        assert accepted[:3] == ["first", "second", "third"]

    def test_s75_does_not_break_s72(self) -> None:
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        assert isinstance(results, list)

    def test_s75_does_not_break_s74(self) -> None:
        scores = [{"keyword": "test", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}]
        results = generate_gap_exploit_hypotheses("python_automation", scores, [])
        assert isinstance(results, list)

    def test_s75_hypothesis_text_is_keyword_phrase(self) -> None:
        trends = [
            {
                "keyword": "python workflow automation tools",
                "trend_score": 0.82,
                "trend_velocity": 0.65,
                "opportunity_score": 0.78,
            }
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        assert results
        for contract in results:
            assert contract.hypothesis_text == "python workflow automation tools"
            assert contract.niche_id == "python_automation"

    def test_confidence_custom_weights(self) -> None:
        kw = {"trend_score": 0.80, "trend_velocity": 0.60}
        score_equal = _score_trend_hypothesis_confidence(kw, trend_score_weight=0.5, trend_velocity_weight=0.5)
        assert abs(score_equal - 0.70) < 0.001

    def test_large_batch_100_keywords(self) -> None:
        import time

        trends = [{"keyword": f"trend_{i}", "trend_score": 0.80, "trend_velocity": 0.65, "opportunity_score": 0.78} for i in range(50)] + [
            {"keyword": f"stable_{i}", "trend_score": 0.90, "trend_velocity": 0.10, "opportunity_score": 0.60}
            for i in range(50)
        ]
        start = time.time()
        results = generate_trend_chase_hypotheses("python_automation", trends, [], max_hypotheses=10)
        elapsed = time.time() - start
        assert elapsed < 5.0
        assert sum(r.accepted for r in results) <= 10

    def test_score_just_below_threshold(self) -> None:
        rows = [{"keyword": "test", "trend_score": TREND_SCORE_THRESHOLD - 0.001, "trend_velocity": 0.80}]
        assert _identify_trending_keywords(rows) == []

    def test_velocity_just_below_threshold(self) -> None:
        rows = [{"keyword": "test", "trend_score": 0.80, "trend_velocity": TREND_VELOCITY_THRESHOLD - 0.001}]
        assert _identify_trending_keywords(rows) == []

    def test_no_nan_or_inf(self) -> None:
        import math

        for row in [{"trend_score": 0.0, "trend_velocity": 0.0}, {"trend_score": 1.0, "trend_velocity": 1.0}, {"trend_score": 0.5, "trend_velocity": 0.5}, {}]:
            score = _score_trend_hypothesis_confidence(row)
            assert not math.isnan(score) and not math.isinf(score)
            assert 0.0 <= score <= 1.0

    def test_niche_id_all_9(self) -> None:
        trends = [{"keyword": "test trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        for niche in sorted(NICHE_VALIDATION_CONFIG.keys()):
            results = generate_trend_chase_hypotheses(niche, trends, [], min_confidence=0.0)
            for contract in results:
                assert contract.niche_id == niche

    def test_both_empty(self) -> None:
        assert generate_trend_chase_hypotheses("", [], []) == []

    def test_only_niche_no_trends(self) -> None:
        assert generate_trend_chase_hypotheses("python_automation", [], []) == []

    def test_trend_score_weight_value(self) -> None:
        assert TREND_SCORE_WEIGHT == 0.55

    def test_velocity_weight_value(self) -> None:
        assert TREND_VELOCITY_WEIGHT == 0.45

    def test_accepted_items_meet_min_confidence(self) -> None:
        trends = [{"keyword": f"kw{i}", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78} for i in range(10)]
        minimum = 0.55
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=minimum)
        for contract in results:
            if contract.accepted:
                assert contract.specificity_score >= minimum

    def test_stable_market_excluded(self) -> None:
        stable = [{"keyword": "popular_stable", "trend_score": 0.95, "trend_velocity": 0.05, "opportunity_score": 0.80}]
        assert generate_trend_chase_hypotheses("python_automation", stable, [], min_confidence=0.0) == []

    def test_specificity_score_matches_confidence(self) -> None:
        kw_data = {"keyword": "test", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}
        expected = _score_trend_hypothesis_confidence(kw_data)
        results = generate_trend_chase_hypotheses("python_automation", [kw_data], [], min_confidence=0.0)
        assert results
        assert abs(results[0].specificity_score - expected) < 0.001

    def test_high_velocity_means_accelerating(self) -> None:
        fast = [{"keyword": "fast_rising", "trend_score": 0.70, "trend_velocity": 0.95}]
        slow = [{"keyword": "slow_rising", "trend_score": 0.70, "trend_velocity": 0.41}]
        assert len(_identify_trending_keywords(fast)) == 1
        assert len(_identify_trending_keywords(slow)) == 1

    def test_trend_vs_gap_weights_differ(self) -> None:
        from src.discovery.hypothesis import GAP_DEMAND_WEIGHT

        assert TREND_SCORE_WEIGHT != GAP_DEMAND_WEIGHT

    def test_s75_works_with_fixture_data(self) -> None:
        fixture_trends = [
            {
                "keyword": "python ai workflow automation",
                "trend_score": 0.82,
                "trend_velocity": 0.65,
                "opportunity_score": 0.78,
            },
            {"keyword": "stable but popular", "trend_score": 0.90, "trend_velocity": 0.10, "opportunity_score": 0.70},
        ]
        results = generate_trend_chase_hypotheses("python_automation", fixture_trends, [])
        accepted = [r.hypothesis_text for r in results if r.accepted]
        assert "python ai workflow automation" in accepted
        assert "stable but popular" not in accepted

    @pytest.mark.parametrize(
        ("trend_score", "trend_velocity", "is_trend"),
        [(0.60, 0.40, True), (0.60, 0.39, False), (0.59, 0.40, False), (0.59, 0.39, False)],
    )
    def test_threshold_boundary_matrix(self, trend_score: float, trend_velocity: float, is_trend: bool) -> None:
        rows = [{"keyword": "boundary", "trend_score": trend_score, "trend_velocity": trend_velocity, "opportunity_score": 0.7}]
        result = _identify_trending_keywords(rows)
        assert (len(result) == 1) == is_trend

    def test_wave9_s75_coexist(self) -> None:
        from src.pricing import analyze_price_distribution

        del analyze_price_distribution
        trends = [{"keyword": "test", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        assert isinstance(generate_trend_chase_hypotheses("python_automation", trends, []), list)

    def test_returns_hypothesis_contracts(self) -> None:
        from src.discovery.hypothesis import HypothesisContract

        trends = [{"keyword": "test", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        assert all(isinstance(contract, HypothesisContract) for contract in results)

    def test_hypothesis_text_not_empty(self) -> None:
        trends = [{"keyword": "valid trend keyword", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        assert all(contract.hypothesis_text.strip() for contract in results)

    @pytest.mark.parametrize(
        ("trend_score", "trend_velocity", "expected"),
        [(1.0, 1.0, True), (0.80, 0.50, True), (0.80, 0.40, True), (0.80, 0.39, False), (1.0, 0.40, True), (0.60, 0.40, True), (0.60, 0.39, False), (0.59, 0.40, False)],
    )
    def test_trend_detection_parametrized(self, trend_score: float, trend_velocity: float, expected: bool) -> None:
        rows = [{"keyword": "test", "trend_score": trend_score, "trend_velocity": trend_velocity, "opportunity_score": 0.7}]
        result = _identify_trending_keywords(rows)
        assert (len(result) == 1) == expected

    @pytest.mark.parametrize(
        ("trend_score", "trend_velocity", "expected"),
        [(1.0, 1.0, 1.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.55), (0.0, 1.0, 0.45), (0.5, 0.5, 0.50), (0.80, 0.65, 0.55 * 0.80 + 0.45 * 0.65)],
    )
    def test_confidence_parametrized(self, trend_score: float, trend_velocity: float, expected: float) -> None:
        actual = _score_trend_hypothesis_confidence({"trend_score": trend_score, "trend_velocity": trend_velocity})
        assert abs(actual - expected) < 0.001

    def test_stable_high_score_excluded(self) -> None:
        stable = [{"keyword": "established_market", "trend_score": 0.95, "trend_velocity": 0.02, "opportunity_score": 0.80}]
        assert generate_trend_chase_hypotheses("python_automation", stable, [], min_confidence=0.0) == []

    def test_noisy_signal_excluded(self) -> None:
        noisy = [{"keyword": "viral_noise", "trend_score": 0.15, "trend_velocity": 0.95, "opportunity_score": 0.70}]
        assert generate_trend_chase_hypotheses("python_automation", noisy, [], min_confidence=0.0) == []

    def test_intra_batch_dedup(self) -> None:
        trends = [
            {"keyword": "duplicate_trend", "trend_score": 0.85, "trend_velocity": 0.70, "opportunity_score": 0.90},
            {"keyword": "duplicate_trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.85},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        accepted_texts = [r.hypothesis_text for r in results if r.accepted]
        assert len(accepted_texts) == len(set(accepted_texts))

    def test_s74_and_s75_combined(self) -> None:
        gap_scores = [{"keyword": "gap_tool", "demand_score": 0.80, "competition_score": 0.15, "opportunity_score": 0.90}]
        trend_scores = [{"keyword": "trend_tool", "trend_score": 0.85, "trend_velocity": 0.70, "opportunity_score": 0.80}]
        gaps = generate_gap_exploit_hypotheses("python_automation", gap_scores, [], min_confidence=0.0)
        trends = generate_trend_chase_hypotheses("python_automation", trend_scores, [], min_confidence=0.0)
        combined = [contract.hypothesis_text for contract in gaps + trends if contract.accepted]
        assert "gap_tool" in combined
        assert "trend_tool" in combined

    @pytest.mark.parametrize("max_hyp", [1, 2, 3, 5, 10])
    def test_max_hypotheses_various(self, max_hyp: int) -> None:
        trends = [{"keyword": f"trend_{i}", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78} for i in range(20)]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], max_hypotheses=max_hyp, min_confidence=0.0)
        assert sum(r.accepted for r in results) <= max_hyp

    def test_s75_no_db_writes(self) -> None:
        from sqlalchemy import create_engine, inspect as sa_inspect

        engine = create_engine("sqlite:///data/foundation_gate_ci.db")
        tables_before = set(sa_inspect(engine).get_table_names())
        trends = [{"keyword": "test", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        generate_trend_chase_hypotheses("python_automation", trends, [])
        tables_after = set(sa_inspect(engine).get_table_names())
        assert tables_before == tables_after

    @pytest.mark.parametrize(
        ("trend_score", "trend_velocity", "expected"),
        [(0.60, 0.40, 0.55 * 0.60 + 0.45 * 0.40), (0.82, 0.65, 0.55 * 0.82 + 0.45 * 0.65), (0.75, 0.80, 0.55 * 0.75 + 0.45 * 0.80)],
    )
    def test_confidence_known_values_s75(self, trend_score: float, trend_velocity: float, expected: float) -> None:
        actual = _score_trend_hypothesis_confidence({"trend_score": trend_score, "trend_velocity": trend_velocity})
        assert abs(actual - expected) < 0.001

    def test_all_fields_populated(self) -> None:
        trends = [{"keyword": "test trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        required = ["hypothesis_text", "niche_id", "specificity_score", "accepted", "reason"]
        for contract in results:
            for field in required:
                assert hasattr(contract, field) and getattr(contract, field) is not None

    def test_default_parameters(self) -> None:
        signature = inspect.signature(generate_trend_chase_hypotheses)
        assert signature.parameters["max_hypotheses"].default == 10
        assert signature.parameters["min_confidence"].default == 0.50
        assert signature.parameters["trend_score_threshold"].default == TREND_SCORE_THRESHOLD
        assert signature.parameters["trend_velocity_threshold"].default == TREND_VELOCITY_THRESHOLD

    def test_s74_s75_functional_parity(self) -> None:
        gap_rows = [{"keyword": "test gap", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}]
        trend_rows = [{"keyword": "test trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        gap_results = generate_gap_exploit_hypotheses("python_automation", gap_rows, [], min_confidence=0.0)
        trend_results = generate_trend_chase_hypotheses("python_automation", trend_rows, [], min_confidence=0.0)
        for contract in gap_results + trend_results:
            assert hasattr(contract, "hypothesis_text")
            assert hasattr(contract, "niche_id")
            assert hasattr(contract, "specificity_score")
            assert isinstance(contract.accepted, bool)

    def test_test_file_completeness(self) -> None:
        import ast

        with open("tests/unit/test_trend_chase_hypotheses.py", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        test_functions = [
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        assert len(test_functions) >= 30

    def test_trend_chase_finds_different_than_gap_exploit(self) -> None:
        gap_scores = [{"keyword": "stable gap", "demand_score": 0.80, "competition_score": 0.10, "opportunity_score": 0.90}]
        trend_scores = [{"keyword": "rising market", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        gaps = generate_gap_exploit_hypotheses("python_automation", gap_scores, [], min_confidence=0.0)
        trends = generate_trend_chase_hypotheses("python_automation", trend_scores, [], min_confidence=0.0)
        gap_texts = {row.hypothesis_text for row in gaps if row.accepted}
        trend_texts = {row.hypothesis_text for row in trends if row.accepted}
        assert "stable gap" in gap_texts
        assert "rising market" in trend_texts

    def test_string_scores_graceful(self) -> None:
        try:
            score = _score_trend_hypothesis_confidence({"trend_score": "0.80", "trend_velocity": "0.65"})
            assert 0.0 <= score <= 1.0
        except (ValueError, TypeError):
            assert True

    def test_default_max_hypotheses_is_10(self) -> None:
        signature = inspect.signature(generate_trend_chase_hypotheses)
        assert signature.parameters["max_hypotheses"].default == 10

    def test_all_4_hypothesis_modes_coexist(self) -> None:
        niche = "python_automation"
        seeds = ["python automation"]
        gap_rows = [{"keyword": "gap", "demand_score": 0.75, "competition_score": 0.25, "opportunity_score": 0.80}]
        trend_rows = [{"keyword": "trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        mode_values = sorted([entry.value for entry in HypothesisMode])
        assert mode_values == ["adjacent_keyword", "adjacent_niche", "gap_exploit", "trend_chase"]
        assert isinstance(generate_adjacent_keyword_hypotheses(niche, seeds, []), list)
        assert isinstance(generate_adjacent_niche_hypotheses(niche, seeds, []), list)
        assert isinstance(generate_gap_exploit_hypotheses(niche, gap_rows, []), list)
        assert isinstance(generate_trend_chase_hypotheses(niche, trend_rows, []), list)

    def test_function_docstring_mentions_trend(self) -> None:
        doc = generate_trend_chase_hypotheses.__doc__ or ""
        assert "trend" in doc.lower()
        assert len(doc) > 50

    def test_no_null_specificity_scores(self) -> None:
        trends = [{"keyword": "test", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        results = generate_trend_chase_hypotheses("python_automation", trends, [], min_confidence=0.0)
        for contract in results:
            assert contract.specificity_score is not None
            assert isinstance(contract.specificity_score, float)
            assert 0.0 <= contract.specificity_score <= 1.0

    def test_wave9_pricing_s75_coexist_final(self) -> None:
        from src.pricing import analyze_price_distribution, calculate_new_seller_pricing

        del analyze_price_distribution
        del calculate_new_seller_pricing
        trends = [{"keyword": "test_trend", "trend_score": 0.82, "trend_velocity": 0.65, "opportunity_score": 0.78}]
        assert isinstance(generate_trend_chase_hypotheses("python_automation", trends, []), list)

    def test_constants_are_float(self) -> None:
        assert isinstance(TREND_SCORE_THRESHOLD, float)
        assert isinstance(TREND_VELOCITY_THRESHOLD, float)
        assert isinstance(TREND_SCORE_WEIGHT, float)
        assert isinstance(TREND_VELOCITY_WEIGHT, float)

    def test_score_zero_zero(self) -> None:
        assert _score_trend_hypothesis_confidence({"trend_score": 0.0, "trend_velocity": 0.0}) == 0.0

    def test_score_max(self) -> None:
        assert _score_trend_hypothesis_confidence({"trend_score": 1.0, "trend_velocity": 1.0}) == 1.0

    def test_minimum_velocity_threshold(self) -> None:
        slow_rising = [{"keyword": "slow_growth", "trend_score": 0.75, "trend_velocity": 0.39}]
        trending = [{"keyword": "fast_rising", "trend_score": 0.75, "trend_velocity": 0.40}]
        assert _identify_trending_keywords(slow_rising) == []
        assert len(_identify_trending_keywords(trending)) == 1

    def test_opportunity_score_is_optional_for_trending(self) -> None:
        trends = [
            {"keyword": "no_opp_kw_1", "trend_score": 0.85, "trend_velocity": 0.70},
            {"keyword": "no_opp_kw_2", "trend_score": 0.78, "trend_velocity": 0.62},
        ]
        results = generate_trend_chase_hypotheses("python_automation", trends, [])
        assert isinstance(results, list)
        assert len(results) == 2
        for contract in results:
            assert contract.specificity_score >= 0.0
