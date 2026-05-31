"""Unit tests for Stage 3.5 result-set validator."""

from __future__ import annotations

import pytest
from src.analysis.result_set_validator import (
    NICHE_VALIDATION_CONFIG,
    NICHE_VALIDATION_CONFIG_NEXT_REVIEW,
    NICHE_VALIDATION_CONFIG_VERSION,
    compute_gig_relevance,
    get_validation_config,
    validate_result_set,
)


def _cfg() -> dict:
    cfg = get_validation_config("mcp_servers")
    cfg["relevance_flag_threshold"] = 0.35
    cfg["ghost_market_threshold"] = 0.10
    return cfg


def test_exact_match_keyword_relevant() -> None:
    result = compute_gig_relevance(
        "I will build mcp server integration and ai agent claude tool server api integration",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_score >= 0.60
    assert result.relevance_flag is True


def test_cross_category_gig_rejected_with_exclusion_term() -> None:
    result = compute_gig_relevance(
        "I will design a professional logo",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_score <= 0.35
    assert result.relevance_flag is False
    assert result.rejection_reason == "exclusion_term"


def test_generic_phrase_penalty_applied() -> None:
    result = compute_gig_relevance(
        "I will be a professional expert with fast delivery and best cheap any service",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_signals["generic_penalty"] == -0.15


def test_missing_title_returns_zero_false() -> None:
    result = compute_gig_relevance("", "mcp server integration", "mcp_servers", _cfg())
    assert result.relevance_score == 0.0
    assert result.relevance_flag is False
    assert result.rejection_reason == "missing_title"


def test_unicode_title_is_handled_without_error() -> None:
    result = compute_gig_relevance(
        "I will build MCP server integration 🚀 for café systems",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert 0.0 <= result.relevance_score <= 1.0
    assert result.relevance_flag is True


def test_whitespace_only_title_returns_missing_title() -> None:
    result = compute_gig_relevance("   \t  \n", "mcp server integration", "mcp_servers", _cfg())
    assert result.relevance_score == 0.0
    assert result.relevance_flag is False
    assert result.rejection_reason == "missing_title"


def test_clean_set_has_no_flags_and_zero_deduction() -> None:
    cards = [{"gig_title": "I will build mcp server integration and claude tool", "gig_url": f"https://x/{i}"} for i in range(9)]
    cards.append({"gig_title": "I will design logo", "gig_url": "https://x/off"})
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.result_set_relevance_score >= 0.80
    assert result.confidence_deduction == 0.0
    assert result.ghost_market_flag is False
    assert result.category_contamination_flag is False


def test_ghost_set_detected() -> None:
    cards = [{"gig_title": "logo design", "gig_url": f"https://x/{i}"} for i in range(11)]
    cards.append({"gig_title": "mcp server integration service", "gig_url": "https://x/ok"})
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.ghost_market_flag is True
    assert result.confidence_deduction == -0.50


def test_moderate_contamination_flag() -> None:
    cards = [{"gig_title": "mcp server integration service", "gig_url": f"https://x/{i}"} for i in range(5)]
    cards.extend([{"gig_title": "logo design", "gig_url": f"https://x/off{i}"} for i in range(5)])
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.result_set_relevance_score == 0.5
    assert result.category_contamination_flag is True
    assert result.confidence_deduction == -0.15


def test_sponsored_counted_not_in_relevant_numerator() -> None:
    cards = [
        {"gig_title": "mcp server integration service", "gig_url": "https://x/1", "sponsored": True},
        {"gig_title": "logo design", "gig_url": "https://x/2"},
    ]
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.sponsored_count == 1
    assert result.relevant_count == 1
    assert result.result_set_relevance_score == 0.5


def test_all_sponsored_all_relevant_is_not_ghost() -> None:
    cards = [{"gig_title": "mcp server integration service", "gig_url": f"https://x/{i}", "sponsored": True} for i in range(6)]
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.total_analyzed == 6
    assert result.sponsored_count == 6
    assert result.relevant_count == 6
    assert result.ghost_market_flag is False
    assert result.confidence_deduction == 0.0


def test_all_sponsored_all_off_topic_is_ghost() -> None:
    cards = [{"gig_title": "logo design", "gig_url": f"https://x/{i}", "sponsored": True} for i in range(6)]
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.total_analyzed == 6
    assert result.sponsored_count == 6
    assert result.relevant_count == 0
    assert result.ghost_market_flag is True
    assert result.confidence_deduction == -0.50


def test_zero_cards_returns_ghost_and_warning() -> None:
    result = validate_result_set([], "mcp server integration", "mcp_servers", _cfg())
    assert result.result_set_relevance_score == 0.0
    assert result.ghost_market_flag is True
    assert result.confidence_deduction == -0.50
    assert "no_results_to_validate" in result.warnings


def test_all_nine_niches_have_required_terms() -> None:
    assert len(NICHE_VALIDATION_CONFIG) == 9
    for entry in NICHE_VALIDATION_CONFIG.values():
        assert len(entry["core_terms"]) >= 5
        assert len(entry["exclusion_terms"]) >= 2


def test_unknown_niche_uses_default() -> None:
    config = get_validation_config("unknown_niche_slug")
    assert config["core_terms"] == []
    assert config["exclusion_terms"] == []
    assert config["ghost_market_threshold"] == 0.20


def test_deduction_tier_boundaries() -> None:
    cfg = _cfg()
    for relevant in [8, 6, 4, 2]:
        cards = [{"gig_title": "mcp server integration", "gig_url": f"https://x/{i}"} for i in range(relevant)]
        cards.extend([{"gig_title": "logo design", "gig_url": f"https://x/off{i}"} for i in range(10 - relevant)])
        result = validate_result_set(cards, "mcp server integration", "mcp_servers", cfg)
        if relevant == 8:
            assert result.confidence_deduction == 0.0
        if relevant == 6:
            assert result.confidence_deduction == -0.05
        if relevant == 4:
            assert result.confidence_deduction == -0.15
        if relevant == 2:
            assert result.confidence_deduction == -0.30


def test_max_deduction_below_point_two() -> None:
    cards = [{"gig_title": "logo design", "gig_url": f"https://x/{i}"} for i in range(12)]
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.result_set_relevance_score < 0.20
    assert result.confidence_deduction == -0.50


def test_relevance_flag_boundary_at_threshold() -> None:
    result = compute_gig_relevance(
        "mcp server integration",
        "mcp server integration",
        "mcp_servers",
        {"core_terms": [], "exclusion_terms": [], "relevance_flag_threshold": 0.35},
    )
    assert result.relevance_score >= 0.35
    assert result.relevance_flag is True


def test_partial_token_overlap_path_without_full_phrase() -> None:
    result = compute_gig_relevance(
        "I will build robust server integration tooling",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert 0.0 < result.relevance_signals["phrase_token"] < 0.40


def test_multiple_exclusion_terms_stack_to_minus_half() -> None:
    result = compute_gig_relevance(
        "logo and video package for brand launch",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_signals["exclusion_penalty"] == -0.50


def test_generic_penalty_suppressed_when_core_term_present() -> None:
    result = compute_gig_relevance(
        "I will provide professional expert best service with mcp support",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_signals["generic_phrases_hit"] >= 3
    assert result.relevance_signals["generic_penalty"] == 0.0


def test_score_clamps_to_zero() -> None:
    result = compute_gig_relevance(
        "logo video resume wordpress theme professional expert best",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_score == 0.0


def test_rejection_reason_low_score_branch() -> None:
    result = compute_gig_relevance(
        "mcp",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    assert result.relevance_flag is False
    assert result.rejection_reason == "low_score"


def test_flag_just_below_threshold_is_false() -> None:
    result = compute_gig_relevance(
        "mcp integration",
        "mcp server integration",
        "mcp_servers",
        {"core_terms": [], "exclusion_terms": [], "relevance_flag_threshold": 0.35},
    )
    assert result.relevance_score == pytest.approx(0.14, abs=1e-4)
    assert result.relevance_flag is False


@pytest.mark.parametrize(
    ("relevant", "total", "expected"),
    [
        (9, 10, 0.0),
        (8, 10, 0.0),
        (7, 10, -0.05),
        (6, 10, -0.05),
        (5, 10, -0.15),
        (4, 10, -0.15),
        (3, 10, -0.30),
        (2, 10, -0.30),
        (1, 10, -0.50),
        (0, 10, -0.50),
    ],
)
def test_deduction_tiers_parametrized(relevant: int, total: int, expected: float) -> None:
    cards = [{"gig_title": "mcp server integration", "gig_url": f"https://x/{i}"} for i in range(relevant)]
    cards.extend([{"gig_title": "logo design", "gig_url": f"https://x/off{i}"} for i in range(total - relevant)])
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.confidence_deduction == expected


def test_ghost_boundary_total_five_vs_six() -> None:
    cards5 = [{"gig_title": "logo design", "gig_url": f"https://x/five-{i}"} for i in range(5)]
    cards6 = [{"gig_title": "logo design", "gig_url": f"https://x/six-{i}"} for i in range(6)]
    result5 = validate_result_set(cards5, "mcp server integration", "mcp_servers", _cfg())
    result6 = validate_result_set(cards6, "mcp server integration", "mcp_servers", _cfg())
    assert result5.ghost_market_flag is False
    assert result6.ghost_market_flag is True


def test_contamination_edges_040_and_060() -> None:
    cards040 = [{"gig_title": "mcp server integration", "gig_url": f"https://x/040-{i}"} for i in range(4)]
    cards040.extend([{"gig_title": "logo design", "gig_url": f"https://x/040-off{i}"} for i in range(6)])
    cards060 = [{"gig_title": "mcp server integration", "gig_url": f"https://x/060-{i}"} for i in range(6)]
    cards060.extend([{"gig_title": "logo design", "gig_url": f"https://x/060-off{i}"} for i in range(4)])

    result040 = validate_result_set(cards040, "mcp server integration", "mcp_servers", _cfg())
    result060 = validate_result_set(cards060, "mcp server integration", "mcp_servers", _cfg())

    assert result040.result_set_relevance_score == 0.4
    assert result040.category_contamination_flag is True
    assert result040.confidence_deduction == -0.15
    assert result060.result_set_relevance_score == 0.6
    assert result060.category_contamination_flag is False
    assert result060.confidence_deduction == -0.05


def test_sponsored_count_denominator_not_numerator() -> None:
    cards = []
    for i in range(3):
        cards.append({"gig_title": "mcp server integration", "gig_url": f"https://x/s{i}", "sponsored": True})
    for i in range(3):
        cards.append({"gig_title": "mcp server integration", "gig_url": f"https://x/o{i}", "sponsored": False})
    result = validate_result_set(cards, "mcp server integration", "mcp_servers", _cfg())
    assert result.total_analyzed == 6
    assert result.sponsored_count == 3
    assert result.relevant_count == 6
    assert result.confidence_deduction == 0.0


def test_niche_threshold_overrides_and_defaults() -> None:
    assert get_validation_config("mcp_servers")["ghost_market_threshold"] == 0.10
    assert get_validation_config("devvit_apps")["ghost_market_threshold"] == 0.10
    assert get_validation_config("chatbot_build")["ghost_market_threshold"] == 0.20
    assert get_validation_config("unknown_slug") == {
        "core_terms": [],
        "exclusion_terms": [],
        "ghost_market_threshold": 0.20,
    }


def test_get_validation_config_supports_slug_and_numeric_aliases() -> None:
    by_slug = get_validation_config("support_kb_readiness")
    by_numeric = get_validation_config(1)
    assert by_slug["core_terms"] == by_numeric["core_terms"]
    assert by_slug["exclusion_terms"] == by_numeric["exclusion_terms"]


def test_niche_validation_version_stamps_present() -> None:
    assert isinstance(NICHE_VALIDATION_CONFIG_VERSION, str) and NICHE_VALIDATION_CONFIG_VERSION
    assert isinstance(NICHE_VALIDATION_CONFIG_NEXT_REVIEW, str) and NICHE_VALIDATION_CONFIG_NEXT_REVIEW


def test_clamp_upper_bound_one_documented_unreachable() -> None:
    result = compute_gig_relevance(
        "mcp server integration claude tool model context protocol",
        "mcp server integration",
        "mcp_servers",
        _cfg(),
    )
    # With current fixed weights, positive signals cap at 0.75. This documents why 1.0 is unreachable.
    assert result.relevance_score <= 0.75
