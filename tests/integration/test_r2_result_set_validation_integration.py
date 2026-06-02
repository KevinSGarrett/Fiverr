"""Integration tests for R2 result-set validation and downstream flags."""
from __future__ import annotations

from src.analysis.result_set_validator import get_validation_config, validate_result_set

from tests.fixtures.contaminated_data_fixtures import make_niche_validation_input


def _cards_from_titles(titles: list[str]) -> list[dict[str, object]]:
    return [{"gig_title": title, "gig_url": f"https://example.test/{index}"} for index, title in enumerate(titles, 1)]


def test_validate_result_set_clean_payload_stays_above_relevance_gate() -> None:
    payload = {
        "niche_id": "mcp_ai_agent",
        "keyword": "mcp server integration",
        "gig_titles": [
            "I will build mcp server integration and ai agent tooling",
            "I will deliver model context protocol server integration",
            "I will implement mcp server integration for claude",
            "I will create mcp server integration and tool orchestration",
            "I will build mcp server integration stack",
            "I will optimize mcp server integration workflows",
        ],
    }
    result = validate_result_set(
        _cards_from_titles(payload["gig_titles"]),
        str(payload["keyword"]),
        str(payload["niche_id"]),
        get_validation_config(str(payload["niche_id"])),
    )
    assert result.total_analyzed == 6
    assert result.result_set_relevance_score >= 0.70
    assert result.ghost_market_flag is False
    assert result.category_contamination_flag is False


def test_validate_result_set_ghost_payload_sets_ghost_flag() -> None:
    payload = make_niche_validation_input("mcp_ai_agent", ghost=True)
    result = validate_result_set(
        _cards_from_titles(payload["gig_titles"] + payload["gig_titles"]),
        str(payload["keyword"]),
        str(payload["niche_id"]),
        get_validation_config(str(payload["niche_id"])),
    )
    assert result.total_analyzed >= 6
    assert result.result_set_relevance_score <= 0.20
    assert result.ghost_market_flag is True
    assert result.confidence_deduction == -0.50


def test_validate_result_set_mixed_payload_sets_contamination_band() -> None:
    on_topic = [
        "I will build mcp server integration and ai agent tooling",
        "I will deliver model context protocol server integration",
        "I will implement mcp server integration for claude",
    ]
    off_topic = ["Logo design service", "Social media marketing", "Video editing professional"]
    mixed_titles = on_topic + off_topic
    result = validate_result_set(
        _cards_from_titles(mixed_titles),
        "mcp server integration",
        "mcp_ai_agent",
        get_validation_config("mcp_ai_agent"),
    )
    assert result.total_analyzed == 6
    assert 0.40 <= result.result_set_relevance_score < 0.60
    assert result.category_contamination_flag is True
    assert result.ghost_market_flag is False
