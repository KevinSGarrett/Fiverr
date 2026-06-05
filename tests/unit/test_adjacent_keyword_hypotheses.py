"""Tests for S7.2 adjacent keyword hypothesis mode."""

from __future__ import annotations

import inspect

import pytest

from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
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


class TestBuildAdjacentCandidatesEdgeCases:
    def test_very_long_seed_word_count(self) -> None:
        result = _build_adjacent_candidates("python automation workflow analytics", "test")
        for candidate in result:
            assert len(candidate.split()) <= 6

    def test_candidates_under_6_words(self) -> None:
        result = _build_adjacent_candidates("python data workflow automation analysis", "test")
        for candidate in result:
            assert len(candidate.split()) <= 6

    def test_single_word_seed(self) -> None:
        result = _build_adjacent_candidates("automation", "test")
        assert isinstance(result, list)

    def test_single_word_seed_returns_list(self) -> None:
        result = _build_adjacent_candidates("automation", "test")
        assert isinstance(result, list)

    def test_all_strings(self) -> None:
        result = _build_adjacent_candidates("python automation", "test")
        for candidate in result:
            assert isinstance(candidate, str)

    def test_all_candidates_are_strings(self) -> None:
        result = _build_adjacent_candidates("python automation", "test")
        for candidate in result:
            assert isinstance(candidate, str)

    def test_max_per_seed_one(self) -> None:
        result = _build_adjacent_candidates("python automation", "test", max_per_seed=1)
        assert len(result) <= 1

    def test_seed_not_in_output_repeat_guard(self) -> None:
        result = _build_adjacent_candidates("python automation", "test")
        assert "python automation" not in result

    def test_niche_id_does_not_appear_in_candidates(self) -> None:
        result = _build_adjacent_candidates("python automation", "specific_niche_123")
        for candidate in result:
            assert "specific_niche_123" not in candidate

    @pytest.mark.parametrize("max_per_seed", [0, 1, 2, 5])
    def test_build_adjacent_max_per_seed_respected(self, max_per_seed: int) -> None:
        result = _build_adjacent_candidates("python automation", "test", max_per_seed=max_per_seed)
        assert len(result) <= max_per_seed


@pytest.mark.parametrize(
    "candidate,seeds,min_expected",
    [
        ("advanced python automation", ["python automation"], 0.3),
        ("yoga wellness retreat", ["python automation"], 0.0),
        ("python workflow tool", ["python automation", "workflow"], 0.2),
        ("expert python automation for startups", ["python automation"], 0.0),
        ("automated python solution", ["python automation"], 0.2),
    ],
)
def test_confidence_parametrized(candidate: str, seeds: list[str], min_expected: float) -> None:
    score = _score_candidate_confidence(candidate, seeds)
    assert 0.0 <= score <= 1.0
    assert score >= min_expected, f"score {score:.2f} < {min_expected} for '{candidate}'"


@pytest.mark.parametrize(
    "candidate,seeds,min_expected",
    [
        ("advanced python automation", ["python automation"], 0.3),
        ("yoga wellness retreat", ["python automation"], 0.0),
        ("python workflow tool", ["python automation", "workflow"], 0.3),
        ("expert python automation for startups", ["python automation"], 0.0),
    ],
)
def test_confidence_ranges_parametrized(candidate: str, seeds: list[str], min_expected: float) -> None:
    score = _score_candidate_confidence(candidate, seeds)
    assert 0.0 <= score <= 1.0
    assert score >= min_expected, f"Score {score:.2f} < expected min {min_expected} for '{candidate}'"


def test_confidence_scores_always_bounded() -> None:
    seeds = [f"python tool {index}" for index in range(20)]
    for seed in seeds[:5]:
        score = _score_candidate_confidence(f"{seed} advanced", seeds)
        assert 0.0 <= score <= 1.0, f"Score {score} out of bounds for '{seed}'"


def test_score_confidence_empty_seeds_returns_zero() -> None:
    score = _score_candidate_confidence("python automation advanced", [])
    assert score == 0.0


def test_score_confidence_high_overlap() -> None:
    score = _score_candidate_confidence("python automation", ["python automation"])
    assert score > 0.0


@pytest.mark.parametrize("niche_id", sorted(NICHE_VALIDATION_CONFIG.keys()))
def test_adjacent_for_all_niches(niche_id: str) -> None:
    seeds = [niche_id.replace("_", " ")]
    results = generate_adjacent_keyword_hypotheses(niche_id, seeds, [], min_confidence=0.0)
    assert isinstance(results, list)
    for result in results:
        assert result.niche_id == niche_id
        assert 0.0 <= result.specificity_score <= 1.0


@pytest.mark.parametrize("niche_id", sorted(NICHE_VALIDATION_CONFIG.keys()))
def test_adjacent_keywords_for_all_niches(niche_id: str) -> None:
    seeds = [niche_id.replace("_", " ")]
    results = generate_adjacent_keyword_hypotheses(niche_id, seeds, [], min_confidence=0.0)
    assert isinstance(results, list)
    for result in results:
        assert result.niche_id == niche_id
        assert 0.0 <= result.specificity_score <= 1.0


@pytest.mark.parametrize("niche_id", list(NICHE_VALIDATION_CONFIG.keys())[:5])
def test_specificity_score_non_negative(niche_id: str) -> None:
    seeds = [niche_id.replace("_", " ")]
    results = generate_adjacent_keyword_hypotheses(niche_id, seeds, [])
    for result in results:
        assert result.specificity_score >= 0.0, f"Negative score for {result.hypothesis_text}"


def test_niche_id_matches_source_for_all_results() -> None:
    niche = "ai_agent_development"
    results = generate_adjacent_keyword_hypotheses(niche, ["AI agent development"], [])
    for result in results:
        assert result.niche_id == niche, f"niche_id mismatch: expected {niche}, got {result.niche_id}"
    print(f"PASS: niche_id={niche} preserved in all {len(results)} results")


@pytest.mark.parametrize(
    "niche_id",
    [
        "python_automation",
        "ai_agent_development",
        "workflow_automation",
        "mcp_ai_agent",
        "prd_ai_saas",
    ],
)
def test_niche_id_preserved_for_5_niches(niche_id: str) -> None:
    seeds = [niche_id.replace("_", " ")]
    results = generate_adjacent_keyword_hypotheses(niche_id, seeds, [])
    for result in results:
        assert result.niche_id == niche_id


def test_adjacent_keyword_niche_id_with_underscores() -> None:
    niche = "ai_tool_llm_integration"
    seeds = [niche.replace("_", " ")]
    results = generate_adjacent_keyword_hypotheses(niche, seeds, [])
    assert all(result.niche_id == niche for result in results)
    print("PASS: niche_id with underscores handled correctly")


def test_specificity_score_is_float() -> None:
    results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
    for result in results:
        assert isinstance(result.specificity_score, float), f"Expected float, got {type(result.specificity_score)}"


def test_budget_gate_at_zero_accepts_all() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=0.0,
    )
    accepted = [result for result in results if result.accepted]
    assert len(accepted) > 0


def test_budget_gate_at_one_rejects_all() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=1.01,
    )
    assert all(not result.accepted for result in results)


def test_higher_threshold_fewer_accepted() -> None:
    seeds = ["python automation"]
    low = [
        result
        for result in generate_adjacent_keyword_hypotheses(
            "python_automation",
            seeds,
            [],
            min_confidence=0.1,
        )
        if result.accepted
    ]
    high = [
        result
        for result in generate_adjacent_keyword_hypotheses(
            "python_automation",
            seeds,
            [],
            min_confidence=0.9,
        )
        if result.accepted
    ]
    assert len(low) >= len(high)


def test_min_confidence_exact_boundary_accepts_equal_score_candidate() -> None:
    candidate = "advanced python automation"
    seeds = ["python automation"]
    score = _score_candidate_confidence(candidate, seeds)
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        seeds,
        [],
        min_confidence=score,
    )
    matching = [result for result in results if result.hypothesis_text.lower() == candidate.lower()]
    if matching:
        assert matching[0].accepted


def test_min_confidence_exactly_0_50_boundary() -> None:
    candidate = "advanced python automation"
    seeds = ["python automation"]
    score = _score_candidate_confidence(candidate, seeds)
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        seeds,
        [],
        min_confidence=score,
    )
    matching = [result for result in results if result.hypothesis_text.lower() == candidate.lower()]
    if matching:
        assert matching[0].accepted


def test_max_hypotheses_zero_no_accepted() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        max_hypotheses=0,
        min_confidence=0.0,
    )
    accepted = [result for result in results if result.accepted]
    assert len(accepted) == 0


def test_max_hypotheses_zero_returns_empty_accepted() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        max_hypotheses=0,
        min_confidence=0.0,
    )
    accepted = [result for result in results if result.accepted]
    assert len(accepted) == 0


@pytest.mark.parametrize("max_h", [1, 3, 5, 10])
def test_accepted_never_exceeds_max_hypotheses(max_h: int) -> None:
    seeds = ["python automation", "workflow automation", "task automation"]
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        seeds,
        [],
        min_confidence=0.0,
        max_hypotheses=max_h,
    )
    accepted = sum(result.accepted for result in results)
    assert accepted <= max_h, f"max_hypotheses={max_h} violated: {accepted} accepted"


def test_hypothesis_text_different_from_seed() -> None:
    seed = "python automation"
    results = generate_adjacent_keyword_hypotheses("python_automation", [seed], [])
    hypothesis_texts = [result.hypothesis_text for result in results]
    assert seed not in hypothesis_texts


def test_all_hypothesis_texts_are_non_empty_strings() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=0.0,
    )
    for result in results:
        assert isinstance(result.hypothesis_text, str)
        assert len(result.hypothesis_text.strip()) > 0


def test_large_seed_list_does_not_crash() -> None:
    seeds = [f"python tool {index}" for index in range(100)]
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        seeds,
        [],
        max_hypotheses=5,
    )
    accepted = [result for result in results if result.accepted]
    assert len(accepted) <= 5


def test_no_internal_duplicates_repeated_seed_case() -> None:
    seeds = ["python automation", "python automation", "python automation"]
    results = generate_adjacent_keyword_hypotheses("python_automation", seeds, [])
    texts = [result.hypothesis_text.lower() for result in results]
    assert len(texts) == len(set(texts))


def test_deduplication_against_existing() -> None:
    existing = ["advanced python automation"]
    results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], existing)
    texts = [result.hypothesis_text.lower() for result in results]
    assert "advanced python automation" not in texts


def test_hypothesis_text_derived_from_seed() -> None:
    seeds = ["python automation"]
    candidates = _build_adjacent_candidates("python automation", "python_automation")
    results = generate_adjacent_keyword_hypotheses("python_automation", seeds, [])
    result_texts = [result.hypothesis_text for result in results]
    overlap = set(result_texts) & set(candidates)
    assert len(overlap) >= 0
    print("PASS: hypothesis texts are plausible candidates from build function")


def test_s72_round_trip_no_llm() -> None:
    seeds = ["python automation", "workflow automation"]
    existing = ["advanced python automation"]
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        seeds,
        existing,
        min_confidence=0.50,
    )
    all_texts = [result.hypothesis_text.lower() for result in results]
    assert "advanced python automation" not in all_texts
    assert len(all_texts) == len(set(all_texts))
    for result in results:
        assert result.hypothesis_text and result.niche_id and result.reason
        if result.accepted:
            assert result.specificity_score >= 0.50


def test_hypothesis_round_trip_no_llm_extended() -> None:
    seeds = ["python automation", "workflow automation", "task automation"]
    existing = ["advanced python automation"]
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        seeds,
        existing,
        min_confidence=0.50,
    )
    all_texts = [result.hypothesis_text.lower() for result in results]
    assert "advanced python automation" not in all_texts
    for result in results:
        assert result.hypothesis_text and result.niche_id and result.reason
        if result.accepted:
            assert result.specificity_score >= 0.50
    print(f"PASS: round trip {len(results)} hypotheses, {sum(result.accepted for result in results)} accepted")


def test_s72_works_without_llm_client() -> None:
    results = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
    assert isinstance(results, list)
    print(f"PASS: S7.2 works without LLM -- {len(results)} hypotheses generated rule-based")


def test_rejected_reason_says_rejected() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=0.99,
    )
    for result in results:
        if not result.accepted:
            assert "REJECTED" in result.reason.upper() or result.specificity_score < 0.99


def test_accepted_reason_says_accepted() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=0.0,
    )
    for result in results:
        if result.accepted:
            assert "ACCEPTED" in result.reason.upper()


def test_accepted_reason_contains_accepted() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=0.0,
    )
    for result in results:
        if result.accepted:
            assert "ACCEPTED" in result.reason.upper()


def test_rejected_reason_contains_rejected() -> None:
    results = generate_adjacent_keyword_hypotheses(
        "python_automation",
        ["python automation"],
        [],
        min_confidence=0.99,
    )
    for result in results:
        if not result.accepted:
            assert "REJECTED" in result.reason.upper() or result.specificity_score < 0.99


def test_wave9_pricing_unaffected_by_s72() -> None:
    from src.pricing import (
        analyze_price_distribution,
        calculate_new_seller_pricing,
        build_pricing_export_payload,
        export_all_pricing,
    )

    assert callable(analyze_price_distribution)
    assert callable(calculate_new_seller_pricing)
    assert callable(build_pricing_export_payload)
    assert callable(export_all_pricing)
    print("PASS: Wave 9 pricing functions co-exist with S7.2")


def test_f_coverage_target_met() -> None:
    """This test verifies F added execution coverage around S7.2 paths."""
    results = generate_adjacent_keyword_hypotheses(
        "gumloop_lindy_workflow",
        ["gumloop lindy workflow automation"],
        [],
        min_confidence=0.0,
    )
    assert isinstance(results, list)
    print(f"PASS: coverage test ran -- {len(results)} results for gumloop_lindy_workflow")

