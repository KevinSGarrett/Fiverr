"""Extended weakness score coverage tests for Cycle 047."""

from __future__ import annotations

from sqlalchemy.orm import Session
from src.models import Gig, GigQualityAnalysis, Keyword, Niche, SearchResult, Seller
from src.scoring.weakness import (
    GigQualityWeaknessScoreCalculator,
    compute_weakness_penalty_from_flags,
)
from tests.unit.test_scoring_db_integration import (
    _seed_keyword_data_with_unlinked_page_cards,
    _seed_keyword_data_without_search_links,
    _session,
)


def _seed_keyword_with_stage11_rows(session: Session) -> int:
    niche = Niche(slug="weakness-stage11", name="Weakness Stage11", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="weakness stage11 keyword",
        normalized_keyword="weakness stage11 keyword",
    )
    session.add(keyword)
    session.flush()

    urls = [
        "https://www.fiverr.com/weakness/stage11-one",
        "https://www.fiverr.com/weakness/stage11-two",
        "https://www.fiverr.com/weakness/stage11-three",
    ]
    ows_values = [2.0, 8.0, 9.0]
    flags = [
        ["video_absent"],
        ["video_absent", "faq_absent"],
        ["video_absent", "faq_absent", "portfolio_absent"],
    ]

    for idx, (gig_url, rubric_ows, weakness_flags) in enumerate(zip(urls, ows_values, flags, strict=True), start=1):
        seller = Seller(seller_handle=f"weakness_ext_seller_{idx}", level="Level 1")
        session.add(seller)
        session.flush()
        gig = Gig(
            gig_url=gig_url,
            keyword_id=keyword.id,
            run_id="weakness-stage11-run",
            seller_id=seller.id,
            seller_username=seller.seller_handle,
            title=f"Weakness Stage11 Gig {idx}",
            normalized_title=f"weakness stage11 gig {idx}",
            position=idx,
            starting_price=40.0 + idx,
            review_count=5 + idx,
            metadata_json={"has_video": idx != 1, "has_portfolio": idx == 3},
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id="weakness-stage11-run",
                rank=idx,
                gig_id=gig.id,
                title=f"Stage11 Result {idx}",
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id=niche.slug,
                run_id="weakness-stage11-run",
                rubric_score=100.0 - (rubric_ows * 10.0),
                video_absent="video_absent" in weakness_flags,
                portfolio_absent="portfolio_absent" in weakness_flags,
                description_thin=False,
                faq_absent="faq_absent" in weakness_flags,
                thumbnail_quality_flag=False,
                weakness_flags=weakness_flags,
            )
        )

    session.commit()
    return keyword.id


def test_weakness_video_absence_rate_computation_with_multiple_top_cards() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_unlinked_page_cards(session)
    try:
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["top10_has_video"] == [False, True]
        assert signals["video_absence_rate"] == 0.5
    finally:
        session.close()


def test_weakness_portfolio_absence_detection_for_all_missing() -> None:
    calculator = GigQualityWeaknessScoreCalculator()
    result = calculator.calculate(
        9901,
        {9901: {"top10_has_video": [True, True, True], "top10_has_portfolio": [False, False, False]}},
    )
    assert result.score_components["portfolio_absence_rate"].value == 100.0


def test_weakness_flag_penalty_calculation_with_known_flags() -> None:
    penalty = compute_weakness_penalty_from_flags(["video_absent", "faq_absent", "portfolio_absent"])
    assert penalty == 65.0


def test_weakness_overall_weakness_score_aggregation_from_stage11() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_with_stage11_rows(session)
    try:
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 6.3333
    finally:
        session.close()


def test_weakness_red_flag_boost_from_high_severity_flags() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_with_stage11_rows(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_components["weakness_flags_penalty"].value > 0.0
    finally:
        session.close()


def test_weakness_exploitable_distribution_when_variance_high() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_with_stage11_rows(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        # High variance OWS values should produce a non-trivial weakness score.
        assert result.score_value >= 50.0
    finally:
        session.close()


def test_weakness_graceful_fallback_when_zero_stage11_rows() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_without_search_links(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
    finally:
        session.close()


def test_weakness_graceful_fallback_when_zero_linked_gigs() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data_with_unlinked_page_cards(session)
    try:
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.source_evidence
    finally:
        session.close()
