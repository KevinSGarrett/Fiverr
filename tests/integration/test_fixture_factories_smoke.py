"""Smoke tests confirming fixture factories produce valid, usable objects (R9.6)."""
from __future__ import annotations

from typing import cast

from tests.fixtures.contaminated_data_fixtures import (
    make_contaminated_keyword_set,
    make_niche_validation_input,
    make_rejection_band_dataset,
)
from tests.fixtures.relevance_fixtures import (
    make_clean_rsv,
    make_contaminated_rsv,
    make_ghost_market_rsv,
    make_mock_discovery_outcome,
    make_mock_result_set_validation,
)


def test_clean_rsv_high_score_and_no_flags() -> None:
    rsv = make_clean_rsv(keyword_id=99)
    assert rsv.result_set_relevance_score is not None
    assert rsv.keyword_id == 99
    assert rsv.result_set_relevance_score >= 0.80
    assert rsv.ghost_market_flag is False
    assert rsv.category_contamination_flag is False


def test_ghost_rsv_flags_correctly() -> None:
    rsv = make_ghost_market_rsv(keyword_id=1)
    assert rsv.result_set_relevance_score is not None
    assert rsv.keyword_id == 1
    assert rsv.ghost_market_flag is True
    assert rsv.category_contamination_flag is False
    assert rsv.result_set_relevance_score < 0.30


def test_contaminated_rsv_flags_correctly() -> None:
    rsv = make_contaminated_rsv(keyword_id=2)
    assert rsv.result_set_relevance_score is not None
    assert rsv.keyword_id == 2
    assert rsv.ghost_market_flag is False
    assert rsv.category_contamination_flag is True
    assert 0.30 <= rsv.result_set_relevance_score <= 0.60


def test_mock_discovery_outcome_defaults_and_overrides() -> None:
    default_outcome = make_mock_discovery_outcome()
    custom_outcome = make_mock_discovery_outcome(
        run_id="run-x",
        niche_id="mcp_ai_agent",
        keyword_text="mcp service",
        is_invalid=True,
        is_contaminated=True,
        relevance_score=0.4,
        contamination_reason="mixed_intent",
    )
    assert default_outcome.is_invalid is False
    assert default_outcome.niche_id == "python_automation"
    assert default_outcome.keyword_text == "python script"
    assert custom_outcome.run_id == "run-x"
    assert custom_outcome.is_invalid is True
    assert custom_outcome.contamination_reason == "mixed_intent"


def test_rejection_band_rate_in_range_and_subset() -> None:
    candidates, rejected = make_rejection_band_dataset(total=10, rejected=3)
    rate = len(rejected) / len(candidates)
    assert len(candidates) == 10
    assert len(rejected) == 3
    assert rejected == candidates[:3]
    assert rate == 0.30


def test_rejection_band_boundary_rates() -> None:
    c_low, r_low = make_rejection_band_dataset(total=10, rejected=2)
    c_high, r_high = make_rejection_band_dataset(total=10, rejected=4)
    assert len(c_low) == 10 and len(r_low) == 2
    assert len(c_high) == 10 and len(r_high) == 4
    assert len(r_low) / len(c_low) == 0.20
    assert len(r_high) / len(c_high) == 0.40


def test_all_niches_covered_in_niche_validation_input() -> None:
    niches = [
        "prd_ai_saas",
        "support_kb_readiness",
        "gumloop_lindy_workflow",
        "mcp_ai_agent",
        "python_automation",
        "ai_tool_llm_integration",
        "ai_agent_development",
        "workflow_automation",
        "python_web_scraping",
    ]
    for niche_id in niches:
        payload = make_niche_validation_input(niche_id)
        assert payload["niche_id"] == niche_id
        assert "keyword" in payload
        assert "gig_titles" in payload
        assert isinstance(payload["gig_titles"], list)
        assert len(payload["gig_titles"]) >= 3


def test_ghost_niche_input_uses_off_topic_titles() -> None:
    ghost = make_niche_validation_input("python_automation", ghost=True)
    clean = make_niche_validation_input("python_automation", ghost=False)
    ghost_titles = cast(list[str], ghost["gig_titles"])
    clean_titles = cast(list[str], clean["gig_titles"])
    assert ghost["niche_id"] == "python_automation"
    assert all("Python" not in title for title in ghost_titles)
    assert ghost_titles != clean_titles


def test_contaminated_keyword_set_structure() -> None:
    rows = make_contaminated_keyword_set(niche_id="mcp_ai_agent", count=3, rsv_score=0.25)
    assert len(rows) == 3
    assert all(row["is_contaminated"] is True for row in rows)
    assert all(row["niche_id"] == "mcp_ai_agent" for row in rows)
    assert all(row["rsv_score"] == 0.25 for row in rows)


def test_contaminated_keyword_set_default_niche() -> None:
    rows = make_contaminated_keyword_set()
    assert len(rows) == 5
    assert rows[0]["niche_id"] == "python_automation"
    assert str(rows[0]["keyword_text"]).startswith("contaminated_kw_")


def test_make_mock_result_set_validation_core_fields() -> None:
    rsv = make_mock_result_set_validation(
        keyword_id=8,
        relevance_score=0.55,
        ghost_market_flag=False,
        category_contamination_flag=True,
        run_id=7,
    )
    assert rsv.keyword_id == 8
    assert rsv.result_set_relevance_score == 0.55
    assert rsv.category_contamination_flag is True
    assert rsv.relevance_deduction == 0.45
    assert rsv.run_id == "7"
