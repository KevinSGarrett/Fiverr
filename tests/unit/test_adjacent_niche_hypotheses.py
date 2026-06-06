"""Tests for S7.3 Adjacent Niche Hypothesis Mode."""

from __future__ import annotations

import inspect

import pytest

from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
from src.discovery.hypothesis import (
    ADJACENT_NICHE_RELATIONSHIPS,
    HypothesisContract,
    _build_adjacent_niche_candidates,
    _score_niche_candidate_confidence,
    generate_adjacent_niche_hypotheses,
)


class TestAdjacentNicheRelationshipsMap:
    def test_all_9_niches_have_entries(self) -> None:
        expected = {
            "python_automation",
            "ai_agent_development",
            "workflow_automation",
            "gumloop_lindy_workflow",
            "prd_ai_saas",
            "mcp_ai_agent",
            "ai_tool_llm_integration",
            "python_web_scraping",
            "support_kb_readiness",
        }
        assert set(ADJACENT_NICHE_RELATIONSHIPS.keys()) == expected

    def test_no_self_referential_entries(self) -> None:
        for niche, adjacents in ADJACENT_NICHE_RELATIONSHIPS.items():
            assert niche not in adjacents, f"{niche} references itself"

    def test_all_adjacent_values_are_valid_niches(self) -> None:
        all_niches = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        for adjacents in ADJACENT_NICHE_RELATIONSHIPS.values():
            for adjacent in adjacents:
                assert adjacent in all_niches

    def test_all_sources_have_at_least_one_adjacent(self) -> None:
        for niche, adjacents in ADJACENT_NICHE_RELATIONSHIPS.items():
            assert len(adjacents) >= 1, f"{niche} has no adjacents"

    def test_niche_map_keys_match_validation_config(self) -> None:
        assert set(ADJACENT_NICHE_RELATIONSHIPS.keys()) == set(NICHE_VALIDATION_CONFIG.keys())


class TestBuildAdjacentNicheCandidates:
    def test_returns_list(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"])
        assert isinstance(result, list)

    def test_source_not_in_output(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"])
        assert "python_automation" not in result

    def test_unknown_niche_returns_empty(self) -> None:
        result = _build_adjacent_niche_candidates("unknown_niche_xyz", ["test"])
        assert result == []

    def test_max_per_niche_respected(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=1)
        assert len(result) <= 1

    def test_returns_valid_niche_ids(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python automation"])
        valid = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        for niche_id in result:
            assert niche_id in valid

    def test_all_9_sources_return_candidates(self) -> None:
        for niche in ADJACENT_NICHE_RELATIONSHIPS:
            result = _build_adjacent_niche_candidates(niche, [niche.replace("_", " ")])
            assert len(result) >= 1

    def test_non_positive_max_per_niche_returns_empty(self) -> None:
        assert _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=0) == []

    def test_build_returns_only_mapped_values(self) -> None:
        expected = ADJACENT_NICHE_RELATIONSHIPS["python_automation"]
        result = _build_adjacent_niche_candidates("python_automation", ["python automation"])
        for niche_id in result:
            assert niche_id in expected

    def test_max_per_niche_slices_from_start(self) -> None:
        full = ADJACENT_NICHE_RELATIONSHIPS["python_automation"]
        result = _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=1)
        assert result == full[:1]


class TestScoreNicheCandidateConfidence:
    def test_returns_float(self) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", ["python"])
        assert isinstance(score, float)

    def test_bounded_0_to_1(self) -> None:
        for niche in ADJACENT_NICHE_RELATIONSHIPS:
            score = _score_niche_candidate_confidence(niche, [niche.replace("_", " ")])
            assert 0.0 <= score <= 1.0

    def test_empty_seeds_returns_zero(self) -> None:
        assert _score_niche_candidate_confidence("ai_agent_development", []) == 0.0

    def test_base_adjacency_bonus_positive(self) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", ["python"])
        assert score > 0.0

    def test_exact_keyword_match_boosts_confidence(self) -> None:
        target = "ai_agent_development"
        cfg = NICHE_VALIDATION_CONFIG.get(target, {})
        seeds = cfg.get("seed_keywords", [target.replace("_", " ")])[:3]
        score = _score_niche_candidate_confidence(target, seeds)
        assert score >= 0.30

    def test_generic_terms_penalty_applies(self) -> None:
        generic = _score_niche_candidate_confidence("ai_agent_development", ["python automation support"])
        specific = _score_niche_candidate_confidence("ai_agent_development", ["ai agent development"])
        assert specific >= generic

    def test_missing_config_fallback_uses_candidate_tokens(self) -> None:
        score = _score_niche_candidate_confidence(
            "custom_unknown_niche",
            ["custom unknown niche"],
            niche_validation_config={},
        )
        assert 0.0 <= score <= 1.0

    @pytest.mark.parametrize("seed_keywords", [["python"], ["ai agent"], ["workflow automation"]])
    def test_parametrized_scores_bounded(self, seed_keywords: list[str]) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", seed_keywords)
        assert 0.0 <= score <= 1.0


class TestGenerateAdjacentNicheHypotheses:
    def test_returns_list(self) -> None:
        result = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], [])
        assert isinstance(result, list)

    def test_empty_source_niche_returns_empty(self) -> None:
        assert generate_adjacent_niche_hypotheses("", ["test"], []) == []

    def test_all_9_niche_sources(self) -> None:
        for niche in ADJACENT_NICHE_RELATIONSHIPS:
            results = generate_adjacent_niche_hypotheses(niche, [niche.replace("_", " ")], [])
            assert isinstance(results, list)

    def test_budget_gate_rejects_at_high_threshold(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.99,
        )
        assert all(not result.accepted for result in results)

    def test_budget_gate_accepts_at_zero_threshold(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        assert any(result.accepted for result in results)

    def test_no_duplicates_against_existing(self) -> None:
        existing = ["ai_agent_development"]
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], existing)
        assert "ai_agent_development" not in {result.hypothesis_text for result in results}

    def test_niche_id_preserved(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        for result in results:
            assert result.niche_id == "python_automation"

    def test_accepted_flag_matches_confidence(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python"],
            [],
            min_confidence=0.50,
        )
        for result in results:
            if result.accepted:
                assert result.specificity_score >= 0.50

    def test_reason_string_populated(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        for result in results:
            assert isinstance(result.reason, str) and len(result.reason) > 0

    def test_reason_contains_decision_token(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        for result in results:
            assert "ACCEPTED" in result.reason or "REJECTED" in result.reason

    def test_max_hypotheses_respected(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python"],
            [],
            max_hypotheses=1,
            min_confidence=0.0,
        )
        accepted = [result for result in results if result.accepted]
        assert len(accepted) <= 1

    def test_hypothesis_text_is_niche_id(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        valid_niches = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        for result in results:
            assert result.hypothesis_text in valid_niches

    def test_default_min_confidence_is_0_50(self) -> None:
        signature = inspect.signature(generate_adjacent_niche_hypotheses)
        assert signature.parameters["min_confidence"].default == 0.50

    def test_default_max_hypotheses_is_10(self) -> None:
        signature = inspect.signature(generate_adjacent_niche_hypotheses)
        assert signature.parameters["max_hypotheses"].default == 10

    def test_returns_hypothesis_contract_instances(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        for result in results:
            assert isinstance(result, HypothesisContract)

    def test_deliverable_humanized_from_candidate_niche(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        for result in results:
            assert "_" not in (result.deliverable or "")

    def test_hypothesis_text_differs_from_source_niche_id(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python"], [])
        for result in results:
            assert result.hypothesis_text != result.niche_id

    def test_returns_all_candidates_for_audit_even_when_rejected(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.99,
        )
        assert len(results) > 0
        assert all(not result.accepted for result in results)

    def test_all_scores_bounded_for_all_sources(self) -> None:
        for niche in ADJACENT_NICHE_RELATIONSHIPS:
            results = generate_adjacent_niche_hypotheses(
                niche,
                [niche.replace("_", " ")],
                [],
                min_confidence=0.0,
            )
            for result in results:
                assert 0.0 <= result.specificity_score <= 1.0

    def test_existing_all_niches_yields_zero_accepted(self) -> None:
        existing = list(ADJACENT_NICHE_RELATIONSHIPS.keys())
        results = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], existing)
        assert all(not result.accepted for result in results)

    @pytest.mark.parametrize("source_niche_id", sorted(ADJACENT_NICHE_RELATIONSHIPS.keys()))
    def test_source_never_appears_as_hypothesis(self, source_niche_id: str) -> None:
        results = generate_adjacent_niche_hypotheses(source_niche_id, [source_niche_id.replace("_", " ")], [])
        for result in results:
            assert result.hypothesis_text != source_niche_id
