"""Extended feasibility coverage tests for Cycle 047."""

from __future__ import annotations
from typing import Any

from sqlalchemy import select
from src.models import Gig, SearchResult
from src.scoring.feasibility import (
    NewSellerFeasibilityCalculator,
    _coerce_float,
    _feasibility_config,
    _get_feasibility_gap_signal_details,
    _normalize_gap_flags,
    _relevance_config,
    get_feasibility_gap_signal,
)
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
    assert NewSellerFeasibilityCalculator._normalize_gig_url_identity(123) is None


def test_feasibility_extract_top_card_urls_ignores_non_dict_cards() -> None:
    ranked_urls = NewSellerFeasibilityCalculator._extract_top_card_urls(
        [type("R", (), {"gig_cards": ["bad", {"position": 1, "gig_url": "https://fiverr.com/a"}]})()],
        limit=5,
    )
    assert ranked_urls == ["https://fiverr.com/a"]


def test_feasibility_price_diversity_none_for_single_price() -> None:
    calculator = NewSellerFeasibilityCalculator()
    score = calculator._resolve_price_diversity_score({"top10_prices": [10.0]})
    assert score is None


def test_feasibility_load_signals_from_db_recovers_missing_identity_candidates() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=True, run_id="identity-recovery")
    try:
        # Rewrite top card URLs with querystring identities so normalization path is exercised.
        search_row = session.execute(
            select(SearchResult).where(SearchResult.keyword_id == keyword_id)
        ).scalar_one()
        gig_cards = search_row.gig_cards if isinstance(search_row.gig_cards, list) else []
        search_row.gig_cards = [
            {"position": idx, "gig_url": f"{card['gig_url']}?source=cards"}
            for idx, card in enumerate(gig_cards, start=1)
        ]
        session.commit()

        signals = NewSellerFeasibilityCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["top10_prices"] is not None
        assert len(signals["top10_prices"]) == 10
    finally:
        session.close()


def test_zombie_gigs_never_used_in_feasibility_review_barrier() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=False, run_id="reg18-zombie")
    try:
        top_gig = (
            session.query(Gig)
            .filter(Gig.keyword_id == keyword_id)
            .order_by(Gig.position.asc())
            .first()
        )
        assert top_gig is not None
        top_gig.review_count = 0
        top_gig.is_zombie = True
        session.commit()

        calculator = NewSellerFeasibilityCalculator()
        filtered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_zombie_filter": True}},
        )
        unfiltered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_zombie_filter": False}},
        )
        assert filtered["lowest_ranked_review_count_page1"] > unfiltered["lowest_ranked_review_count_page1"]
    finally:
        session.close()


def test_feasibility_level_ratio_excludes_sponsored_and_zombie() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_for_feasibility_high_scores(session, use_card_path=False, run_id="reg18-sponsored")
    try:
        gigs = (
            session.query(Gig)
            .filter(Gig.keyword_id == keyword_id)
            .order_by(Gig.position.asc())
            .all()
        )
        gigs[0].is_sponsored = True
        gigs[1].is_zombie = True
        session.commit()
        calculator = NewSellerFeasibilityCalculator()
        filtered = calculator._load_signals_from_db(
            keyword_id,
            session,
            config={"relevance": {"enable_sponsored_exclusion": True, "enable_zombie_filter": True}},
        )
        assert filtered["level1_or_new_ratio_top10"] is not None
    finally:
        session.close()


def test_feasibility_helper_config_and_coercion_guards() -> None:
    assert _coerce_float(None, 1.5) == 1.5
    assert _coerce_float(True, 2.5) == 2.5
    assert _coerce_float("bad", 3.5) == 3.5
    assert _feasibility_config({"scoring": {"feasibility": "invalid"}}) == {}
    assert _relevance_config("invalid") == {  # type: ignore[arg-type]
        "enable_sponsored_exclusion": True,
        "enable_zombie_filter": True,
        "top_n_for_scoring": 10,
    }
    assert _normalize_gap_flags(["low video presence", 7, "", None]) == ["LOW_VIDEO_PRESENCE"]  # type: ignore[list-item]


def test_feasibility_gap_signal_blank_inputs_return_zero() -> None:
    assert get_feasibility_gap_signal("", "run", db={}) == 0.0
    assert get_feasibility_gap_signal("niche", "", db={}) == 0.0


def test_feasibility_gap_signal_provider_and_filtering() -> None:
    class _Provider:
        @staticmethod
        def get_competitor_profile_inputs(_niche_id: str, _run_id: str) -> dict[str, Any]:
            return {"gap_flags": ["LOW_VIDEO_PRESENCE", "UNSUPPORTED_FLAG", "LOW_VIDEO_PRESENCE"]}

    boost, flags = _get_feasibility_gap_signal_details(
        niche_id="niche",
        run_id="run",
        db=_Provider(),
        config={"scoring": {"feasibility": {"gap_boost_per_flag": 12.0, "max_gap_boost": 20.0}}},
    )
    assert boost == 12.0
    assert flags == ["LOW_VIDEO_PRESENCE"]


def test_feasibility_level_ratio_explicit_and_fallback_paths() -> None:
    calc = NewSellerFeasibilityCalculator()
    assert calc._resolve_level1_ratio({"level1_or_new_ratio_top10": 1.5}) == 1.0  # pylint: disable=protected-access
    assert calc._resolve_level1_ratio({"level1_or_new_ratio_top10": -0.2}) == 0.0  # pylint: disable=protected-access
    assert calc._resolve_level1_ratio({"top10_seller_levels": []}) is None  # pylint: disable=protected-access
    ratio = calc._resolve_level1_ratio(  # pylint: disable=protected-access
        {"top10_seller_levels": ["Level 1", "TRS", "new seller", "LEVEL_2"]}
    )
    assert ratio == 0.5


def test_feasibility_price_diversity_and_gap_signal_guards() -> None:
    calc = NewSellerFeasibilityCalculator()
    assert calc._resolve_price_diversity_score({"price_diversity_top10": 2.0}) == 2.0  # pylint: disable=protected-access
    assert calc._resolve_price_diversity_score({"top10_prices": [0, 0, 0]}) == 0.0  # pylint: disable=protected-access
    assert calc._resolve_price_diversity_score({"top10_prices": ["x", None]}) is None  # pylint: disable=protected-access
    boost, flags = calc._resolve_gap_signal(  # pylint: disable=protected-access
        signals={"feasibility_gap_signal": 999.0, "feasibility_gap_flags": ["LOW_VIDEO_PRESENCE"]},
        db={},
        config={"scoring": {"feasibility": {"max_gap_boost": 30.0}}},
    )
    assert boost == 30.0
    assert flags == ["LOW_VIDEO_PRESENCE"]
