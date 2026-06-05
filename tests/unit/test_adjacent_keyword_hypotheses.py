"""Tests for S7.2 adjacent keyword hypothesis mode."""

from __future__ import annotations

import inspect

from src.discovery.hypothesis import (
    HypothesisContract,
    _build_adjacent_candidates,
    _score_candidate_confidence,
    generate_adjacent_keyword_hypotheses,
)


class TestBuildAdjacentCandidates:
    def test_returns_list(self) -> None:
        assert isinstance(_build_adjacent_candidates("python automation", "test"), list)

    def test_seed_not_in_output(self) -> None:
        result = _build_adjacent_candidates("python automation", "test")
        assert "python automation" not in result

    def test_candidates_contain_seed_terms(self) -> None:
        result = _build_adjacent_candidates("python automation", "test")
        for candidate in result:
            assert "python" in candidate or "automation" in candidate

    def test_max_per_seed_respected(self) -> None:
        result = _build_adjacent_candidates("python automation", "test", max_per_seed=2)
        assert len(result) <= 2

    def test_max_per_seed_zero(self) -> None:
        assert _build_adjacent_candidates("python", "test", max_per_seed=0) == []

    def test_empty_seed_returns_empty(self) -> None:
        assert _build_adjacent_candidates("   ", "test") == []

    def test_very_long_candidates_filtered(self) -> None:
        result = _build_adjacent_candidates("python workflow automation data", "test")
        for candidate in result:
            assert len(candidate.split()) <= 6

    def test_existing_qualifier_not_reapplied(self) -> None:
        result = _build_adjacent_candidates("advanced python automation", "test", max_per_seed=20)
        assert "advanced advanced python automation" not in result

    def test_default_limit_caps_to_five(self) -> None:
        result = _build_adjacent_candidates("python automation", "test")
        assert len(result) <= 5


class TestScoreCandidateConfidence:
    def test_returns_float(self) -> None:
        assert isinstance(_score_candidate_confidence("test", ["seed"]), float)

    def test_bounded_0_to_1(self) -> None:
        for seeds in [[], ["python"], ["python automation", "workflow"]]:
            score = _score_candidate_confidence("test candidate", seeds)
            assert 0.0 <= score <= 1.0

    def test_empty_seeds_returns_zero(self) -> None:
        assert _score_candidate_confidence("test", []) == 0.0

    def test_high_overlap_positive_score(self) -> None:
        score = _score_candidate_confidence("python automation", ["python automation"])
        assert score > 0.0

    def test_unrelated_candidate_lower_score(self) -> None:
        related = _score_candidate_confidence("python automation", ["python automation"])
        unrelated = _score_candidate_confidence("yoga instructor", ["python automation"])
        assert related > unrelated

    def test_length_bonus_applies_for_three_to_five_terms(self) -> None:
        score = _score_candidate_confidence("foo bar baz", ["qux"])
        assert score >= 0.1

    def test_generic_penalty_reduces_score(self) -> None:
        penalized = _score_candidate_confidence("python automation support", ["python automation support"])
        less_generic = _score_candidate_confidence("python workflow orchestration", ["python workflow orchestration"])
        assert penalized < less_generic


class TestGenerateAdjacentKeywordHypotheses:
    def test_returns_list(self) -> None:
        result = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        assert isinstance(result, list)

    def test_empty_seeds_returns_empty(self) -> None:
        assert generate_adjacent_keyword_hypotheses("python_automation", [], []) == []

    def test_all_results_are_hypothesis_contracts(self) -> None:
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert isinstance(result, HypothesisContract)

    def test_budget_gate_rejects_low_confidence(self) -> None:
        results = generate_adjacent_keyword_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.99,
        )
        assert all(not result.accepted for result in results)

    def test_budget_gate_accepts_at_zero_confidence(self) -> None:
        results = generate_adjacent_keyword_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        assert any(result.accepted for result in results)

    def test_no_duplicates_against_existing(self) -> None:
        existing = ["advanced python automation", "professional python automation"]
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], existing)
        result_texts = [result.hypothesis_text.lower() for result in results]
        for existing_keyword in existing:
            assert existing_keyword.lower() not in result_texts

    def test_no_internal_duplicates(self) -> None:
        results = generate_adjacent_keyword_hypotheses(
            "python_automation",
            ["python automation", "python automation"],
            [],
        )
        texts = [result.hypothesis_text.lower() for result in results]
        assert len(texts) == len(set(texts))

    def test_max_hypotheses_limits_accepted(self) -> None:
        results = generate_adjacent_keyword_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
            max_hypotheses=2,
        )
        accepted = [result for result in results if result.accepted]
        assert len(accepted) <= 2

    def test_niche_id_preserved(self) -> None:
        results = generate_adjacent_keyword_hypotheses("test_niche", ["test keyword"], [])
        for result in results:
            assert result.niche_id == "test_niche"

    def test_accepted_flag_matches_gate(self) -> None:
        results = generate_adjacent_keyword_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.50,
        )
        for result in results:
            if result.accepted:
                assert result.specificity_score >= 0.50
            else:
                assert result.specificity_score < 0.50 or "REJECTED" in result.reason

    def test_reason_string_populated(self) -> None:
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert isinstance(result.reason, str) and len(result.reason) > 0

    def test_hypothesis_text_is_string(self) -> None:
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert isinstance(result.hypothesis_text, str)

    def test_default_min_confidence_is_0_5(self) -> None:
        signature = inspect.signature(generate_adjacent_keyword_hypotheses)
        assert signature.parameters["min_confidence"].default == 0.50

    def test_default_max_hypotheses_is_10(self) -> None:
        signature = inspect.signature(generate_adjacent_keyword_hypotheses)
        assert signature.parameters["max_hypotheses"].default == 10

    def test_deliverable_mirrors_candidate_text(self) -> None:
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert result.deliverable == result.hypothesis_text

    def test_reason_includes_budget_comparison(self) -> None:
        results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert "confidence" in result.reason
            assert "ACCEPTED" in result.reason or "REJECTED" in result.reason

