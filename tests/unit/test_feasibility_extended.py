"""Extended feasibility coverage tests for Cycle 047."""

from __future__ import annotations

from sqlalchemy import select
from src.models import SearchResult
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from tests.unit.test_scoring_db_integration import (
    _seed_keyword_data_for_feasibility_high_scores,
    _session,
)


def test_feasibility_inline_profile_generates_gap_signal_from_mapping_inputs() -> None:
    calculator = NewSellerFeasibilityCalculator()
    keyword_id = 5510
    payload = {
        keyword_id: {
            "level1_or_new_ratio_top10": 0.7,
            "lowest_ranked_review_count_page1": 8.0,
            "price_diversity_top10": 0.5,
            "llm_gig_quality_weakness_avg_top10": 7.0,
            "llm_entry_gap_assessment": 6.0,
            "competitor_profile": {"gap_flags": ["LOW_VIDEO_PRESENCE", "HIGH_PRICE_VARIANCE"]},
        }
    }
    result = calculator.calculate(keyword_id, payload, config={"scoring": {"feasibility": {"gap_boost_per_flag": 12}}})
    assert result.score_value is not None
    assert "profile_gap_boost" in result.score_components


def test_feasibility_extract_top_card_urls_skips_invalid_entries() -> None:
    ranked_urls = NewSellerFeasibilityCalculator._extract_top_card_urls(
        [
            type("R", (), {"gig_cards": [{"position": "2", "gig_url": "https://fiverr.com/a"}, {"position": 0, "gig_url": "https://fiverr.com/b"}, {"position": 1, "gig_url": "https://fiverr.com/a"}, {"gig_url": "   "}, {"position": "x", "gig_url": "https://fiverr.com/c"}, {"position": 3, "gig_url": None}]})()
        ],
        limit=5,
    )
    assert ranked_urls == ["https://fiverr.com/a", "https://fiverr.com/b", "https://fiverr.com/c"]


def test_feasibility_normalize_gig_url_identity_falls_back_without_path() -> None:
    assert NewSellerFeasibilityCalculator._normalize_gig_url_identity("https://www.fiverr.com") == "https://www.fiverr.com"
    assert NewSellerFeasibilityCalculator._normalize_gig_url_identity("   ") is None


def test_feasibility_load_signals_from_db_recovers_missing_identity_candidates() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=True, run_id="identity-recovery")
    try:
        # Rewrite top card URLs with querystring identities so normalization path is exercised.
        search_row = session.execute(
            select(SearchResult).where(SearchResult.keyword_id == keyword_id)
        ).scalar_one()
        search_row.gig_cards = [
            {"position": idx, "gig_url": f"{card['gig_url']}?source=cards"}
            for idx, card in enumerate(search_row.gig_cards, start=1)
        ]
        session.commit()

        signals = NewSellerFeasibilityCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["top10_prices"] is not None
        assert len(signals["top10_prices"]) == 10
    finally:
        session.close()
