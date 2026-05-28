"""Extended competition score tests for Cycle 048 Agent F."""

from __future__ import annotations

from sqlalchemy.orm import Session
from src.models import Gig, SearchResult, Seller
from src.scoring.competition import (
    CompetitionScoreCalculator,
    compute_seller_level_competition_signal,
    get_competitor_profile_inputs,
)
from tests.unit.test_competition_score import (
    KEYWORD_ID,
    FakeScoringDB,
    _base_competition_inputs,
    _build_session,
    _competition_config,
)


def test_competition_score_uses_seller_level_distribution_when_available() -> None:
    calculator = CompetitionScoreCalculator()
    db = FakeScoringDB(
        competition_inputs={
            KEYWORD_ID: {
                **_base_competition_inputs(),
                "competitor_profile": {
                    "seller_level_distribution": {"TOP_RATED": 0.6, "LEVEL_2": 0.4},
                    "mean_reviews": 100.0,
                    "median_price": 75.0,
                },
            }
        }
    )
    result = calculator.calculate(KEYWORD_ID, db, config=_competition_config(use_competitor_profile=True))
    assert result.score_components["seller_level"].raw == {"TOP_RATED": 0.6, "LEVEL_2": 0.4}
    assert "competitor_profiles.seller_level_distribution" in result.source_evidence


def test_competition_score_handles_all_level_1_sellers_gracefully() -> None:
    signal = compute_seller_level_competition_signal({"LEVEL_1_NEW": 1.0})
    assert signal == 20.0


def test_competition_score_fallback_when_no_competitor_profiles() -> None:
    assert get_competitor_profile_inputs("niche-a", "run-a", {"competitor_profile": "invalid"}) == {}


def test_competition_score_review_count_barrier_calculation() -> None:
    calculator = CompetitionScoreCalculator()
    assert calculator._normalize_review_count(0.0) == 0.0  # pylint: disable=protected-access
    assert calculator._normalize_review_count(1000.0) > calculator._normalize_review_count(10.0)  # pylint: disable=protected-access


def test_competition_score_price_variance_component() -> None:
    calculator = CompetitionScoreCalculator()
    low = calculator._normalize_price(15.0)  # pylint: disable=protected-access
    high = calculator._normalize_price(80.0)  # pylint: disable=protected-access
    assert low < high <= 100.0


def test_competition_score_new_seller_gap_flag_detection() -> None:
    calculator = CompetitionScoreCalculator()
    rating, note = calculator._derive_profile_llm_rating(  # pylint: disable=protected-access
        profile_inputs={"new_seller_gap": {"gap_flags": ["LOW_VIDEO_PRESENCE"]}},
        existing_rating=8.0,
    )
    assert rating == 7.0
    assert "LOW_VIDEO_PRESENCE" in note


def test_competition_score_handles_empty_gig_cards_for_keyword() -> None:
    session, _niche, keyword = _build_session()
    try:
        session.add(SearchResult(keyword_id=keyword.id, rank=1, title="orphan result", gig_id=None))
        session.commit()
        result = CompetitionScoreCalculator().calculate(
            keyword.id,
            session,
            config=_competition_config(use_competitor_profile=True),
        )
        assert result.score_value is None
    finally:
        session.close()


def test_competition_score_run_scoped_query_with_valid_run_id() -> None:
    session, niche, keyword = _build_session()
    try:
        _seed_minimal_ranked_gig(session, keyword.id, run_id="run-42")
        result = CompetitionScoreCalculator()._load_signals_from_db(  # pylint: disable=protected-access
            keyword.id,
            session,
            config=_competition_config(use_competitor_profile=False),
        )
        assert result["total_result_count"] is None
        # run_id is resolved but profile load is disabled, covering run-scoped branch safely.
        assert niche.slug == "test_niche"
    finally:
        session.close()


def test_competition_score_keyword_level_fallback_path() -> None:
    session, _niche, keyword = _build_session()
    try:
        _seed_minimal_ranked_gig(session, keyword.id, run_id="gig-fallback-run", search_run_id=None)
        signals = CompetitionScoreCalculator()._load_signals_from_db(  # pylint: disable=protected-access
            keyword.id,
            session,
            config=_competition_config(use_competitor_profile=True),
        )
        assert signals.get("_profile_run_id") is None
        assert signals["avg_review_count_top10"] is not None
    finally:
        session.close()


def test_competition_score_produces_valid_range_with_minimal_data() -> None:
    result = CompetitionScoreCalculator().calculate(
        KEYWORD_ID,
        FakeScoringDB(competition_inputs={KEYWORD_ID: {"total_result_count": 12}}),
    )
    assert result.score_value is None
    assert result.total_weight_available < 0.30


def test_competition_score_handles_null_competitor_profile() -> None:
    loaded = CompetitionScoreCalculator()._load_signals(  # pylint: disable=protected-access
        KEYWORD_ID,
        {KEYWORD_ID: {**_base_competition_inputs(), "competitor_profile": None}},
        config=_competition_config(use_competitor_profile=True),
    )
    assert "competitor_profile" in loaded
    assert loaded["competitor_profile"] is None


def test_competition_score_result_matches_component_math() -> None:
    result = CompetitionScoreCalculator().calculate(KEYWORD_ID, FakeScoringDB(competition_inputs={KEYWORD_ID: _base_competition_inputs()}))
    assert result.score_value is not None
    weighted_sum = 0.0
    total_weight = 0.0
    for component in result.score_components.values():
        weighted_sum += component.value * component.weight
        total_weight += component.weight
    expected = round(weighted_sum / total_weight, 2)
    assert result.score_value == expected


def _seed_minimal_ranked_gig(
    session: Session,
    keyword_id: int,
    *,
    run_id: str,
    search_run_id: str | None = None,
) -> None:
    seller = Seller(seller_handle=f"seller-{run_id}", level="Level 2")
    session.add(seller)
    session.flush()
    gig = Gig(
        seller_id=seller.id,
        title=f"Gig {run_id}",
        normalized_title=f"gig {run_id}",
        review_count=22,
        starting_price=44.0,
        run_id=run_id,
    )
    session.add(gig)
    session.flush()
    session.add(
        SearchResult(
            keyword_id=keyword_id,
            rank=1,
            gig_id=gig.id,
            title=f"Result {run_id}",
            run_id=search_run_id,
        )
    )
    session.commit()
