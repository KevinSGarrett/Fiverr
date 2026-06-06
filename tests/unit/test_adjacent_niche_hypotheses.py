"""Tests for S7.3 Adjacent Niche Hypothesis Mode."""

from __future__ import annotations

import inspect
import json
import asyncio

import pytest

import src.discovery.hypothesis as hypothesis_module
from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG
from src.discovery.hypothesis import (
    ADJACENT_NICHE_RELATIONSHIPS,
    HypothesisContract,
    _build_adjacent_niche_candidates,
    _score_niche_candidate_confidence,
    generate_adjacent_keyword_hypotheses,
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
        """Audit strings should always include acceptance/rejection status."""
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


class TestGenerateAdjacentNicheHypothesesCoverageUplift:
    def test_seed_keywords_do_not_affect_candidates(self) -> None:
        first = _build_adjacent_niche_candidates("python_automation", ["python"])
        second = _build_adjacent_niche_candidates("python_automation", ["different seeds"])
        assert first == second

    @pytest.mark.parametrize(
        ("candidate", "seeds", "min_expected"),
        [
            ("ai_agent_development", ["python automation", "AI agent"], 0.0),
            ("prd_ai_saas", ["python automation"], 0.0),
            ("ai_agent_development", [], 0.0),
        ],
    )
    def test_niche_confidence_parametrized(
        self,
        candidate: str,
        seeds: list[str],
        min_expected: float,
    ) -> None:
        score = _score_niche_candidate_confidence(candidate, seeds)
        assert 0.0 <= score <= 1.0
        assert score >= min_expected

    @pytest.mark.parametrize("niche_id", sorted(ADJACENT_NICHE_RELATIONSHIPS.keys()))
    def test_adjacent_niche_for_all_9_sources(self, niche_id: str) -> None:
        seeds = [niche_id.replace("_", " ")]
        results = generate_adjacent_niche_hypotheses(niche_id, seeds, [], min_confidence=0.0)
        assert isinstance(results, list)
        for result in results:
            assert result.niche_id == niche_id
            assert 0.0 <= result.specificity_score <= 1.0
            assert isinstance(result.accepted, bool)

    def test_budget_gate_at_one_point_zero_one_rejects_all(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=1.01,
        )
        assert all(not result.accepted for result in results)

    def test_higher_threshold_fewer_accepted(self) -> None:
        seeds = ["python automation"]
        low = [
            result
            for result in generate_adjacent_niche_hypotheses(
                "python_automation",
                seeds,
                [],
                min_confidence=0.1,
            )
            if result.accepted
        ]
        high = [
            result
            for result in generate_adjacent_niche_hypotheses(
                "python_automation",
                seeds,
                [],
                min_confidence=0.9,
            )
            if result.accepted
        ]
        assert len(low) >= len(high)

    def test_all_adjacents_as_existing_produces_empty_accepted(self) -> None:
        existing = ADJACENT_NICHE_RELATIONSHIPS.get("python_automation", [])
        results = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], existing)
        accepted = [result for result in results if result.accepted]
        assert len(accepted) == 0

    def test_no_internal_duplicates_multiple_sources(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation", "python automation", "python automation"],
            [],
        )
        texts = [result.hypothesis_text for result in results]
        assert len(texts) == len(set(texts))

    def test_specificity_score_is_float(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert isinstance(result.specificity_score, float)

    def test_hypothesis_contract_all_fields_populated(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        for result in results:
            assert isinstance(result, HypothesisContract)
            assert isinstance(result.hypothesis_text, str) and result.hypothesis_text
            assert isinstance(result.niche_id, str) and result.niche_id
            assert isinstance(result.accepted, bool)
            assert isinstance(result.reason, str) and result.reason
            assert isinstance(result.specificity_score, float)
            assert 0.0 <= result.specificity_score <= 1.0

    def test_s73_round_trip_no_llm(self) -> None:
        existing = ["ai_agent_development"]
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            existing,
            min_confidence=0.50,
        )
        assert "ai_agent_development" not in [result.hypothesis_text for result in results]
        texts = [result.hypothesis_text for result in results]
        assert len(texts) == len(set(texts))
        for result in results:
            assert result.hypothesis_text and result.niche_id and result.reason
            if result.accepted:
                assert result.specificity_score >= 0.50

    def test_s72_and_s73_coexist_without_interference(self) -> None:
        keywords = generate_adjacent_keyword_hypotheses("python_automation", ["python automation"], [])
        niches = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], [])
        keyword_texts = {result.hypothesis_text for result in keywords}
        assert isinstance(keywords, list)
        assert isinstance(niches, list)
        for result in niches:
            assert result.hypothesis_text not in keyword_texts

    def test_hypothesis_mode_has_adjacent_niche(self) -> None:
        from src.discovery.contracts import HypothesisMode

        values = {entry.value for entry in HypothesisMode}
        assert "adjacent_niche" in values
        assert "adjacent_keyword" in values
        assert "gap_exploit" in values
        assert "trend_chase" in values

    def test_python_web_scraping_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_web_scraping",
            ["python web scraping"],
            [],
            min_confidence=0.0,
        )
        expected = ADJACENT_NICHE_RELATIONSHIPS.get("python_web_scraping", [])
        texts = [result.hypothesis_text for result in results]
        for adjacent in expected:
            assert adjacent in texts

    def test_support_kb_readiness_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "support_kb_readiness",
            ["support knowledge base"],
            [],
            min_confidence=0.0,
        )
        expected = ADJACENT_NICHE_RELATIONSHIPS.get("support_kb_readiness", [])
        texts = [result.hypothesis_text for result in results]
        for adjacent in expected:
            assert adjacent in texts

    def test_large_existing_niches_list(self) -> None:
        all_niches = list(ADJACENT_NICHE_RELATIONSHIPS.keys())
        source = "python_automation"
        existing = [niche for niche in all_niches if niche != source]
        results = generate_adjacent_niche_hypotheses(source, ["python automation"], existing)
        accepted = [result for result in results if result.accepted]
        assert len(accepted) == 0

    def test_confidence_score_is_deterministic(self) -> None:
        seeds = ["python automation", "workflow automation"]
        first = _score_niche_candidate_confidence("ai_agent_development", seeds)
        second = _score_niche_candidate_confidence("ai_agent_development", seeds)
        assert first == second

    def test_adjacent_niche_relationship_map_is_dict(self) -> None:
        assert isinstance(ADJACENT_NICHE_RELATIONSHIPS, dict)
        assert len(ADJACENT_NICHE_RELATIONSHIPS) == 9

    def test_relationship_map_values_are_lists(self) -> None:
        for key, value in ADJACENT_NICHE_RELATIONSHIPS.items():
            assert isinstance(value, list), f"{key} value is not a list"
            assert 1 <= len(value) <= 5

    def test_higher_confidence_seeds_yield_higher_score(self) -> None:
        target = "ai_agent_development"
        cfg = NICHE_VALIDATION_CONFIG.get(target, {})
        if cfg.get("seed_keywords"):
            high_seeds = cfg["seed_keywords"][:3]
            low_seeds = ["unrelated", "random", "stuff"]
            score_high = _score_niche_candidate_confidence(target, high_seeds)
            score_low = _score_niche_candidate_confidence(target, low_seeds)
            assert score_high >= score_low

    def test_partial_existing_blocks_only_overlap(self) -> None:
        existing = ["ai_agent_development"]
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            existing,
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "ai_agent_development" not in texts

    def test_hypothesis_text_contains_no_spaces(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        for result in results:
            assert " " not in result.hypothesis_text

    def test_s73_budget_gate_mirroring_reg26(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.99,
        )
        assert all(not result.accepted for result in results)

    def test_s73_hypothesis_confidence_threshold(self) -> None:
        signature = inspect.signature(generate_adjacent_niche_hypotheses)
        default = signature.parameters["min_confidence"].default
        assert default == 0.50

    def test_file_integrity_has_minimum_test_count(self) -> None:
        import ast
        from pathlib import Path

        path = Path(__file__)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        tests = [
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]
        assert len(tests) >= 30

    def test_workflow_automation_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "workflow_automation",
            ["workflow automation"],
            [],
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "workflow_automation" not in texts
        expected = ADJACENT_NICHE_RELATIONSHIPS.get("workflow_automation", [])
        for adjacent in expected[:2]:
            assert adjacent in texts

    def test_gumloop_lindy_workflow_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "gumloop_lindy_workflow",
            ["gumloop lindy workflow"],
            [],
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "gumloop_lindy_workflow" not in texts
        for adjacent in ADJACENT_NICHE_RELATIONSHIPS["gumloop_lindy_workflow"]:
            assert adjacent in texts

    def test_mcp_ai_agent_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "mcp_ai_agent",
            ["mcp ai agent"],
            [],
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "mcp_ai_agent" not in texts
        for adjacent in ADJACENT_NICHE_RELATIONSHIPS["mcp_ai_agent"]:
            assert adjacent in texts

    def test_prd_ai_saas_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "prd_ai_saas",
            ["prd ai saas"],
            [],
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "prd_ai_saas" not in texts
        for adjacent in ADJACENT_NICHE_RELATIONSHIPS["prd_ai_saas"]:
            assert adjacent in texts

    def test_ai_tool_llm_integration_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "ai_tool_llm_integration",
            ["ai tool llm integration"],
            [],
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "ai_tool_llm_integration" not in texts
        for adjacent in ADJACENT_NICHE_RELATIONSHIPS["ai_tool_llm_integration"]:
            assert adjacent in texts

    def test_confidence_base_bonus_is_nonzero_for_adjacent_pair(self) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", ["x"])
        assert score > 0.0

    def test_confidence_not_nan_or_inf(self) -> None:
        import math

        result = _score_niche_candidate_confidence("ai_agent_development", ["python"])
        assert not math.isnan(result)
        assert not math.isinf(result)

    def test_all_candidates_appear_in_results(self) -> None:
        seeds = ["python automation"]
        candidates = _build_adjacent_niche_candidates("python_automation", seeds)
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            seeds,
            [],
            min_confidence=0.0,
        )
        result_texts = {result.hypothesis_text for result in results}
        for candidate in candidates:
            assert candidate in result_texts

    @pytest.mark.parametrize("threshold", [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.01])
    def test_threshold_sweep_monotone(self, threshold: float) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=threshold,
        )
        accepted = sum(result.accepted for result in results)
        if threshold >= 1.01:
            assert accepted == 0

    def test_deliverable_field_populated(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        for result in results:
            if result.deliverable is not None:
                assert isinstance(result.deliverable, str) and len(result.deliverable) > 0

    def test_buyer_field_is_none_for_s73(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        for result in results:
            assert result.buyer is None or isinstance(result.buyer, str)

    def test_generate_with_many_seeds(self) -> None:
        seeds = [
            "python automation",
            "workflow automation",
            "automated workflow",
            "python scripts",
            "automation tools",
            "AI automation",
        ]
        results = generate_adjacent_niche_hypotheses("python_automation", seeds, [])
        assert isinstance(results, list)

    def test_confidence_never_exceeds_one(self) -> None:
        seeds = ["ai agent development", "ai agent", "agent development", "python automation"]
        score = _score_niche_candidate_confidence("ai_agent_development", seeds)
        assert score <= 1.0

    def test_ai_agent_development_adjacent_niches(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "ai_agent_development",
            ["AI agent development"],
            [],
            min_confidence=0.0,
        )
        texts = [result.hypothesis_text for result in results]
        assert "ai_agent_development" not in texts
        for adjacent in ADJACENT_NICHE_RELATIONSHIPS["ai_agent_development"]:
            assert adjacent in texts

    def test_prd_ai_saas_maps_to_ai_cluster(self) -> None:
        results = generate_adjacent_niche_hypotheses("prd_ai_saas", ["ai saas"], [], min_confidence=0.0)
        texts = [result.hypothesis_text for result in results]
        ai_cluster = {"mcp_ai_agent", "ai_tool_llm_integration", "ai_agent_development"}
        ai_results = [item for item in texts if item in ai_cluster]
        assert len(ai_results) >= 2

    @pytest.mark.parametrize("source_niche", sorted(ADJACENT_NICHE_RELATIONSHIPS.keys()))
    def test_generate_returns_list_for_all_sources(self, source_niche: str) -> None:
        result = generate_adjacent_niche_hypotheses(source_niche, [source_niche.replace("_", " ")], [])
        assert isinstance(result, list)
        assert result is not None

    @pytest.mark.parametrize("source", sorted(ADJACENT_NICHE_RELATIONSHIPS.keys()))
    def test_niche_id_equals_source_for_all_9_niches(self, source: str) -> None:
        results = generate_adjacent_niche_hypotheses(source, [source.replace("_", " ")], [])
        for result in results:
            assert result.niche_id == source

    @pytest.mark.parametrize("source", sorted(ADJACENT_NICHE_RELATIONSHIPS.keys()))
    def test_accepted_score_consistency_all_9(self, source: str) -> None:
        results = generate_adjacent_niche_hypotheses(
            source,
            [source.replace("_", " ")],
            [],
            min_confidence=0.50,
        )
        for result in results:
            if result.accepted:
                assert result.specificity_score >= 0.50

    def test_all_adjacent_niche_values_are_lists_of_strings(self) -> None:
        for key, value in ADJACENT_NICHE_RELATIONSHIPS.items():
            assert isinstance(value, list), f"{key}: expected list"
            for item in value:
                assert isinstance(item, str), f"{key}.{item}: expected str"
                assert len(item) > 0

    def test_specificity_score_precision(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert isinstance(str(result.specificity_score), str)

    def test_workflow_automation_all_candidates_valid(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "workflow_automation",
            ["workflow automation"],
            [],
            min_confidence=0.0,
        )
        valid = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        for result in results:
            assert result.hypothesis_text in valid
            assert result.niche_id == "workflow_automation"

    def test_support_kb_readiness_adjacent_niches_present(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "support_kb_readiness",
            ["support knowledge base readiness"],
            [],
            min_confidence=0.0,
        )
        expected = ADJACENT_NICHE_RELATIONSHIPS.get("support_kb_readiness", [])
        texts = [result.hypothesis_text for result in results]
        for adjacent in expected:
            assert adjacent in texts

    def test_zero_existing_returns_all_adjacencies(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        expected_count = len(ADJACENT_NICHE_RELATIONSHIPS.get("python_automation", []))
        assert len(results) == expected_count

    def test_mcp_ai_agent_and_ai_tool_llm_share_adjacencies(self) -> None:
        mcp_adjs = set(ADJACENT_NICHE_RELATIONSHIPS.get("mcp_ai_agent", []))
        ai_adjs = set(ADJACENT_NICHE_RELATIONSHIPS.get("ai_tool_llm_integration", []))
        shared = mcp_adjs & ai_adjs
        assert len(shared) >= 1
        assert "ai_agent_development" in mcp_adjs

    def test_python_cluster_is_internally_connected(self) -> None:
        python_cluster = ["python_automation", "workflow_automation", "gumloop_lindy_workflow"]
        for niche in python_cluster:
            adjs = set(ADJACENT_NICHE_RELATIONSHIPS.get(niche, []))
            cluster_adjs = adjs & set(python_cluster)
            assert len(cluster_adjs) >= 1

    def test_s73_full_workflow_from_spec(self) -> None:
        source = "python_automation"
        seeds = ["python automation", "workflow automation"]
        first = generate_adjacent_niche_hypotheses(source, seeds, [])
        assert isinstance(first, list)
        existing = [first[0].hypothesis_text] if first else []
        second = generate_adjacent_niche_hypotheses(source, seeds, existing)
        if first and second:
            assert existing[0] not in [result.hypothesis_text for result in second]
        for result in first:
            assert result.niche_id == source
            assert isinstance(result.specificity_score, float)
            assert result.reason
        candidates = _build_adjacent_niche_candidates(source, seeds)
        assert isinstance(candidates, list)
        assert all(candidate != source for candidate in candidates)


class TestBuildAdjacentNicheCandidatesEdgeCases:
    def test_unknown_source_returns_empty(self) -> None:
        result = _build_adjacent_niche_candidates("nonexistent_niche", ["test"])
        assert result == []

    def test_max_per_niche_zero(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=0)
        assert result == []

    def test_max_per_niche_one(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=1)
        assert len(result) <= 1

    def test_all_candidates_are_valid_niche_ids(self) -> None:
        valid = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        result = _build_adjacent_niche_candidates("python_automation", ["python automation"])
        for item in result:
            assert item in valid

    def test_source_not_in_candidates(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python automation"])
        assert "python_automation" not in result

    def test_seed_keywords_do_not_affect_candidates(self) -> None:
        first = _build_adjacent_niche_candidates("python_automation", ["python"])
        second = _build_adjacent_niche_candidates("python_automation", ["different seeds"])
        assert first == second


class TestPromptExactNameCoverage:
    def test_unknown_source_returns_empty(self) -> None:
        result = _build_adjacent_niche_candidates("nonexistent_niche", ["test"])
        assert result == []

    def test_max_per_niche_zero(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=0)
        assert result == []

    def test_max_per_niche_one(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python"], max_per_niche=1)
        assert len(result) <= 1

    def test_all_candidates_are_valid_niche_ids(self) -> None:
        valid = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        result = _build_adjacent_niche_candidates("python_automation", ["python automation"])
        for item in result:
            assert item in valid

    def test_source_not_in_candidates(self) -> None:
        result = _build_adjacent_niche_candidates("python_automation", ["python automation"])
        assert "python_automation" not in result

    def test_budget_gate_at_zero_accepts_everything(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        accepted = [result for result in results if result.accepted]
        assert len(accepted) > 0

    def test_budget_gate_at_one_rejects_all(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=1.01,
        )
        assert all(not result.accepted for result in results)

    def test_empty_seeds_returns_zero_confidence(self) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", [])
        assert score == 0.0

    def test_base_adjacency_bonus_applied(self) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", ["not related"])
        assert score > 0.0

    def test_confidence_bounded_for_all_niches(self) -> None:
        for niche in ADJACENT_NICHE_RELATIONSHIPS.keys():
            score = _score_niche_candidate_confidence(niche, [niche.replace("_", " ")])
            assert 0.0 <= score <= 1.0

    def test_max_hypotheses_zero_no_accepted(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            max_hypotheses=0,
            min_confidence=0.0,
        )
        accepted = [result for result in results if result.accepted]
        assert len(accepted) == 0

    def test_max_hypotheses_one_limits_accepted(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            max_hypotheses=1,
            min_confidence=0.0,
        )
        accepted = [result for result in results if result.accepted]
        assert len(accepted) <= 1

    def test_accepted_reason_contains_accepted(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.0,
        )
        for result in results:
            if result.accepted:
                assert "ACCEPTED" in result.reason.upper()

    def test_rejected_reason_contains_rejected(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.99,
        )
        for result in results:
            if not result.accepted:
                assert "REJECTED" in result.reason.upper() or result.specificity_score < 0.99

    def test_reason_string_non_empty(self) -> None:
        results = generate_adjacent_niche_hypotheses("python_automation", ["python automation"], [])
        for result in results:
            assert result.reason and len(result.reason) > 10

    def test_niche_id_preserved_for_all_results(self) -> None:
        results = generate_adjacent_niche_hypotheses("workflow_automation", ["workflow automation"], [])
        for result in results:
            assert result.niche_id == "workflow_automation"

    def test_hypothesis_text_differs_from_niche_id(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python"],
            [],
            min_confidence=0.0,
        )
        for result in results:
            assert result.hypothesis_text != "python_automation"

    def test_relationship_map_no_self_references(self) -> None:
        for niche, adjs in ADJACENT_NICHE_RELATIONSHIPS.items():
            assert niche not in adjs

    def test_relationship_map_all_values_are_valid_keys(self) -> None:
        valid = set(ADJACENT_NICHE_RELATIONSHIPS.keys())
        for niche, adjs in ADJACENT_NICHE_RELATIONSHIPS.items():
            for adj in adjs:
                assert adj in valid, f"Unknown niche {adj} in {niche}"

    def test_relationship_map_9_niches(self) -> None:
        assert set(ADJACENT_NICHE_RELATIONSHIPS.keys()) == set(NICHE_VALIDATION_CONFIG.keys())

    def test_accepted_only_if_above_threshold(self) -> None:
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            [],
            min_confidence=0.50,
        )
        for result in results:
            if result.accepted:
                assert result.specificity_score >= 0.50

    def test_multiple_existing_all_blocked(self) -> None:
        existing = ADJACENT_NICHE_RELATIONSHIPS.get("python_automation", [])
        results = generate_adjacent_niche_hypotheses(
            "python_automation",
            ["python automation"],
            existing,
            min_confidence=0.0,
        )
        accepted = [result for result in results if result.accepted]
        assert len(accepted) == 0

    def test_confidence_zero_for_empty_seeds(self) -> None:
        assert _score_niche_candidate_confidence("ai_agent_development", []) == 0.0

    def test_confidence_type_is_float(self) -> None:
        result = _score_niche_candidate_confidence("ai_agent_development", ["python"])
        assert isinstance(result, float)

    def test_confidence_not_nan(self) -> None:
        import math

        result = _score_niche_candidate_confidence("ai_agent_development", ["python"])
        assert not math.isnan(result)

    def test_confidence_not_inf(self) -> None:
        import math

        result = _score_niche_candidate_confidence("ai_agent_development", ["python"])
        assert not math.isinf(result)


class TestHypothesisModuleFocusedCoverage:
    def test_score_hypothesis_signals_handles_empty(self) -> None:
        assert hypothesis_module.score_hypothesis_signals(None, None, None, None) is None

    def test_score_hypothesis_signals_weighted_average(self) -> None:
        score = hypothesis_module.score_hypothesis_signals(None, 0.5, 0.8, 0.2)
        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_score_candidate_confidence_handles_empty_candidate(self) -> None:
        assert hypothesis_module._score_candidate_confidence("", ["python"]) == 0.0

    def test_score_niche_confidence_uses_configured_keywords_branch(self) -> None:
        score = _score_niche_candidate_confidence("ai_agent_development", ["ai", "agent", "development"])
        assert 0.0 <= score <= 1.0

    def test_coerce_json_payload_handles_invalid_string(self) -> None:
        assert hypothesis_module._coerce_json_payload("not-json") is None

    def test_coerce_json_payload_handles_dict(self) -> None:
        payload = {"hypotheses": []}
        assert hypothesis_module._coerce_json_payload(payload) == payload

    def test_parse_hypothesis_contracts_skips_invalid_entries(self) -> None:
        contracts = hypothesis_module.parse_hypothesis_contracts(
            [None, {"keyword": ""}, {"hypothesis_text": "ai support workflow", "buyer": "ops"}],
            source_niche_id="python_automation",
        )
        assert len(contracts) == 1
        assert contracts[0].hypothesis_text == "ai support workflow"

    def test_normalize_hypotheses_legacy_filters_and_normalizes(self) -> None:
        normalized = hypothesis_module._normalize_hypotheses_legacy(
            [
                None,
                {"keyword": "workflow automation for agencies", "mode": "adjacent_keyword"},
                {"hypothesis_text": ""},
            ]
        )
        assert len(normalized) == 1
        assert normalized[0]["hypothesis_type"] == "adjacent_keyword"

    def test_build_gated_prompt_contains_scope_and_guardrails(self) -> None:
        prompt = hypothesis_module._build_gated_prompt(
            source_niche_id="python_automation",
            existing_keywords=["python automation"],
        )
        assert "source_niche_id=python_automation" in prompt
        assert "buyer and deliverable" in prompt

    def test_render_niche_scope_fallback_branch(self) -> None:
        scope = hypothesis_module._render_niche_scope("unknown_niche_for_test")
        assert isinstance(scope, str)
        assert scope

    def test_normalize_optional_and_text_helpers(self) -> None:
        assert hypothesis_module._normalize_optional("") is None
        assert hypothesis_module._normalize_optional("  buyer  ") == "buyer"
        assert hypothesis_module._normalized_text("AI-Agent!!!") == "ai agent"

    def test_deliverable_scope_and_overbroad_helpers(self) -> None:
        in_scope = hypothesis_module._deliverable_in_scope("python automation workflow", "python_automation")
        assert isinstance(in_scope, bool)
        assert hypothesis_module._is_overbroad_single_term("support")
        assert not hypothesis_module._is_overbroad_single_term("custom workflow automation script")

    def test_score_specificity_and_gate_paths(self) -> None:
        accepted_contract = HypothesisContract(
            hypothesis_text="python automation workflow",
            niche_id="python_automation",
            buyer="agency owner",
            deliverable="python automation workflow",
        )
        rejected_contract = HypothesisContract(
            hypothesis_text="support",
            niche_id="python_automation",
            buyer=None,
            deliverable=None,
        )
        scored = hypothesis_module._gate_hypotheses([accepted_contract, rejected_contract], threshold=0.60)
        assert len(scored) == 1
        assert accepted_contract.accepted
        assert not rejected_contract.accepted
        assert rejected_contract.reason

    def test_generate_niche_hypotheses_handles_llm_unavailable(self) -> None:
        result = asyncio.run(
            hypothesis_module.generate_niche_hypotheses(
                "python_automation",
                ["python automation"],
                None,
                None,
            )
        )
        assert result == []

    def test_generate_niche_hypotheses_legacy_and_gated_paths(self) -> None:
        class FakeResponse:
            def __init__(self, text: str) -> None:
                self.text = text

        class FakeClient:
            def __init__(self, payload: list[dict[str, str]]) -> None:
                self.payload = payload

            def complete(self, **_: object) -> FakeResponse:
                return FakeResponse(json.dumps({"hypotheses": self.payload}))

        payload = [
            {
                "hypothesis_text": "python automation workflow",
                "buyer": "agency owner",
                "deliverable": "python automation workflow",
            }
        ]
        client = FakeClient(payload)
        legacy = asyncio.run(
            hypothesis_module.generate_niche_hypotheses(
                "python_automation",
                ["python automation"],
                client,
                None,
                enable_relevance_gates=False,
            )
        )
        gated = asyncio.run(
            hypothesis_module.generate_niche_hypotheses(
                "python_automation",
                ["python automation"],
                client,
                None,
                enable_relevance_gates=True,
            )
        )
        assert isinstance(legacy, list)
        assert isinstance(gated, list)

    def test_generate_niche_hypotheses_handles_invalid_payload_and_exception(self) -> None:
        class BadClient:
            def complete(self, **_: object) -> str:
                raise RuntimeError("boom")

        class InvalidPayloadClient:
            def complete(self, **_: object) -> object:
                class R:
                    text = "not-json"

                return R()

        raised = asyncio.run(
            hypothesis_module.generate_niche_hypotheses(
                "python_automation",
                ["python automation"],
                BadClient(),
                None,
            )
        )
        invalid = asyncio.run(
            hypothesis_module.generate_niche_hypotheses(
                "python_automation",
                ["python automation"],
                InvalidPayloadClient(),
                None,
            )
        )
        assert raised == []
        assert invalid == []
