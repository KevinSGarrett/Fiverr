"""Regression tests for Cycle 049 weakness multi-row OWS averaging fix."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session
from src.models import Gig, GigQualityAnalysis, Keyword, KeywordScore, Niche, SearchResult
from src.scoring.weakness import (
    GigQualityWeaknessScoreCalculator,
    aggregate_overall_weakness_scores,
)
from tests.unit.test_scoring_weakness_gqs import (
    _insert_gqa_row,
    _new_session,
    _seed_run_scoped_keyword,
)


def _seed_kw3_style_keyword(session: Session) -> int:
    """Two-gig keyword mirroring kw=3 Stage 11 weakness inputs."""
    niche = Niche(
        slug="support_kb_readiness",
        name="Support KB",
        category_path="Programming & Tech > Support",
    )
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="help desk software",
        normalized_keyword="help desk software",
    )
    session.add(keyword)
    session.flush()

    run_id = "cycle048_agent_e_kw3"
    urls = [
        "https://www.fiverr.com/gigs/kw3-one",
        "https://www.fiverr.com/gigs/kw3-two",
    ]
    for idx, gig_url in enumerate(urls, start=1):
        gig = Gig(
            gig_url=gig_url,
            keyword_id=keyword.id,
            run_id=run_id,
            seller_username=f"kw3_seller_{idx}",
            metadata_json={"has_video": False, "has_portfolio": False},
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                run_id=run_id,
                rank=idx,
                gig_id=gig.id,
                title=f"KW3 Gig {idx}",
                gig_cards=[{"gig_url": gig_url, "position": idx}],
            )
        )
        session.add(
            GigQualityAnalysis(
                gig_url=gig_url,
                niche_id=niche.slug,
                run_id=run_id,
                rubric_score=55.0,
                video_absent=True,
                portfolio_absent=False,
                description_thin=False,
                faq_absent=True,
                thumbnail_quality_flag=False,
                weakness_flags=["NO_FAQ", "NO_VIDEO"],
            )
        )

    session.commit()
    return keyword.id


def test_weakness_extreme_ows_row_does_not_dominate_average() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url_a = _seed_run_scoped_keyword(session, active_run_id="mix-run")
        gig_url_b = "https://www.fiverr.com/gigs/moderate-target"
        gig_b = Gig(
            gig_url=gig_url_b,
            keyword_id=keyword_id,
            run_id="mix-run",
            seller_username="moderate_seller",
            metadata_json={"has_video": True, "has_portfolio": True},
        )
        session.add(gig_b)
        session.flush()
        row = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).first()
        assert row is not None
        row.gig_cards = [
            {"gig_url": gig_url_a, "position": 1},
            {"gig_url": gig_url_b, "position": 2},
        ]
        session.commit()

        _insert_gqa_row(session, gig_url=gig_url_a, run_id="mix-run", rubric_score=0.0)
        _insert_gqa_row(session, gig_url=gig_url_b, run_id="mix-run", rubric_score=50.0)

        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["overall_weakness_score_avg"] == 7.5
    finally:
        session.close()


def test_weakness_multi_run_fallback_is_consistent_with_isolation() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url = _seed_run_scoped_keyword(session, active_run_id="active-empty")
        _insert_gqa_row(session, gig_url=gig_url, run_id="active-empty", rubric_score=46.48)
        _insert_gqa_row(
            session,
            gig_url=gig_url,
            run_id="fallback-extreme",
            rubric_score=0.0,
            analyzed_at=datetime.now(UTC) + timedelta(minutes=5),
        )

        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value < 90.0
        assert abs(result.score_components["overall_weakness_score"].value - 53.52) < 0.1
    finally:
        session.close()


def test_weakness_kw3_unchanged_after_multi_row_fix() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_kw3_style_keyword(session)
        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert abs(result.score_value - 46.25) < 0.5
    finally:
        session.close()


def test_weakness_penalty_only_rows_excluded_from_average() -> None:
    assert aggregate_overall_weakness_scores([5.35, 10.0]) == 7.675
    assert aggregate_overall_weakness_scores([10.0, 10.0]) == 10.0
    assert aggregate_overall_weakness_scores([2.0, 8.0, 9.0]) == 6.3333


def test_weakness_multi_row_fallback_does_not_produce_extreme_value() -> None:
    """Permanent regression name for AGENT_EXECUTION_STRATEGY Section 7."""
    session = _new_session()
    try:
        keyword_id, gig_url_a = _seed_run_scoped_keyword(session, active_run_id="extreme-run")
        gig_url_b = "https://www.fiverr.com/gigs/stable-target"
        gig_b = Gig(
            gig_url=gig_url_b,
            keyword_id=keyword_id,
            run_id="extreme-run",
            seller_username="stable_seller",
            metadata_json={"has_video": True, "has_portfolio": True},
        )
        session.add(gig_b)
        session.flush()
        row = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).first()
        assert row is not None
        row.gig_cards = [
            {"gig_url": gig_url_a, "position": 1},
            {"gig_url": gig_url_b, "position": 2},
        ]
        session.commit()

        _insert_gqa_row(session, gig_url=gig_url_a, run_id="extreme-run", rubric_score=0.0)
        _insert_gqa_row(session, gig_url=gig_url_b, run_id="extreme-run", rubric_score=53.52)

        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value < 90.0
    finally:
        session.close()


def test_weakness_kw96_equivalent_consistent_before_after_combined_state() -> None:
    session = _new_session()
    try:
        keyword_id, _ = _seed_run_scoped_keyword(
            session,
            active_run_id="kw96-run",
            metadata_json={},
        )
        session.add(
            KeywordScore(
                keyword_id=keyword_id,
                final_score=51.2,
                weakness_score=100.0,
                score_components={},
                tag="MONITOR",
                scored_at=datetime.now(UTC),
            )
        )
        session.add(
            KeywordScore(
                keyword_id=keyword_id,
                final_score=51.2,
                weakness_score=53.52,
                score_components={},
                tag="MONITOR",
                scored_at=datetime.now(UTC) + timedelta(seconds=1),
            )
        )
        session.commit()

        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value == 53.52
        assert "historical_weakness_fallback" in result.score_components
    finally:
        session.close()


def test_weakness_median_vs_mean_for_extreme_distributions() -> None:
    scores = [10.0, 6.0, 4.0]
    moderated_mean = aggregate_overall_weakness_scores(scores)
    assert moderated_mean == 6.6667
    assert moderated_mean != 6.0


def test_weakness_single_extreme_row_does_not_produce_100_score() -> None:
    session = _new_session()
    try:
        keyword_id, gig_url_a = _seed_run_scoped_keyword(session, active_run_id="single-extreme-row")
        gig_url_b = "https://www.fiverr.com/gigs/single-extreme-row-moderate"
        gig_b = Gig(
            gig_url=gig_url_b,
            keyword_id=keyword_id,
            run_id="single-extreme-row",
            seller_username="single_extreme_moderate",
            metadata_json={"has_video": True, "has_portfolio": True},
        )
        session.add(gig_b)
        session.flush()
        row = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).first()
        assert row is not None
        row.gig_cards = [
            {"gig_url": gig_url_a, "position": 1},
            {"gig_url": gig_url_b, "position": 2},
        ]
        session.commit()

        _insert_gqa_row(session, gig_url=gig_url_a, run_id="single-extreme-row", rubric_score=0.0)
        _insert_gqa_row(session, gig_url=gig_url_b, run_id="single-extreme-row", rubric_score=53.52)

        result = GigQualityWeaknessScoreCalculator().calculate(keyword_id, session)
        assert result.score_value is not None
        assert result.score_value < 100.0
    finally:
        session.close()
