"""Unit tests for Stage 3.5 result-set validator."""

from __future__ import annotations

from src.analysis.result_set_validator import (
    NICHE_VALIDATION_CONFIG,
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
