"""Extended Stage 11 rubric tests for Cycle 047 coverage expansion."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from src.analysis.gig_quality_rubric import compute_rubric_score, run_gig_quality_analysis_for_niche
from src.models.database import create_session_factory, initialize_database
from src.models.gig import Gig
from src.models.gig_quality_score import GigQualityScore
from src.models.market import GigQualityAnalysis
from src.models.market import Keyword
from src.models.niche import Niche
from src.models.search_result import SearchResult


def _run(coro):
    return asyncio.run(coro)


def _build_session():
    engine = initialize_database("sqlite:///:memory:")
    session_factory = create_session_factory(engine)
    session = session_factory()
    niche = Niche(slug="test_niche", name="Test Niche", category_path="programming-tech/testing")
    session.add(niche)
    session.commit()
    session.refresh(niche)
    return session, niche


def _seed_keyword(session, niche: Niche, keyword_text: str) -> Keyword:
    row = Keyword(
        niche_id=niche.id,
        keyword=keyword_text,
        normalized_keyword=keyword_text.lower(),
        external_source="seed",
        metadata_json={},
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _seed_gig(
    session,
    *,
    keyword: Keyword,
    run_id: str,
    gig_url: str,
    rank: int,
    description_text: str,
    faq_text: str | None,
    video_present: bool | None,
    portfolio_count: int | None,
) -> Gig:
    gig = Gig(
        gig_url=gig_url,
        keyword_id=keyword.id,
        run_id=run_id,
        seller_username=f"seller-{rank}",
        gig_title_full=f"Gig {rank}",
        description_text=description_text,
        faq_text=faq_text,
        video_present=video_present,
        portfolio_count=portfolio_count,
        review_count_exact=10 + rank,
        rating_exact=4.5,
        position=rank,
        detail_collected=True,
    )
    session.add(gig)
    session.flush()
    session.add(
        SearchResult(
            keyword_id=keyword.id,
            run_id=run_id,
            page_collected=rank,
            rank=rank,
            gig_id=gig.id,
        )
    )
    session.commit()
    session.refresh(gig)
    return gig


def _seed_gqs(
    session,
    *,
    gig: Gig,
    keyword: Keyword,
    run_id: str,
    video_present: bool | None,
    portfolio_count: int | None,
    description_quality_score: float | None = None,
    faq_completeness_score: float | None = None,
    thumbnail_quality_score: float | None = None,
) -> None:
    row = GigQualityScore(
        gig_id=gig.id,
        gig_url=gig.gig_url,
        keyword_id=keyword.id,
        run_id=run_id,
        analysis_complete=True,
        video_present=video_present,
        portfolio_count=portfolio_count,
        description_quality_score=description_quality_score,
        faq_completeness_score=faq_completeness_score,
        thumbnail_quality_score=thumbnail_quality_score,
    )
    session.add(row)
    session.commit()


def test_gig_quality_rubric_handles_empty_niche_gracefully() -> None:
    session, _niche = _build_session()
    try:
        payload = _run(
            run_gig_quality_analysis_for_niche(
                niche_id="missing-niche",
                run_id="rubric-empty-niche",
                db=session,
                config={"niches": [{"niche_id": "missing-niche", "is_active": True}]},
            )
        )
        assert payload["analyzed"] is False
        assert payload["reason"] == "no_gig_quality_scores"
    finally:
        session.close()


def test_gig_quality_rubric_processes_gig_with_no_description() -> None:
    score = compute_rubric_score(
        gig_row={"description_text": "", "faq_text": "faq", "thumbnail_url": "https://img.example/t.png"},
        gig_quality_score_row={"video_present": True, "portfolio_count": 2, "description_quality_score": 2.0},
    )
    assert score["description_thin"] is True
    assert "description_thin" in score["weakness_flags"]


def test_gig_quality_rubric_applies_all_criteria_when_data_complete() -> None:
    score = compute_rubric_score(
        gig_row={
            "description_text": "Detailed scope and deliverables " * 8,
            "faq_text": "Q: timeline A: 2 days",
            "thumbnail_url": "https://img.example/thumbnail.png",
        },
        gig_quality_score_row={
            "video_present": True,
            "portfolio_count": 5,
            "description_quality_score": 9.0,
            "faq_completeness_score": 8.0,
            "thumbnail_quality_score": 9.0,
        },
    )
    assert score["rubric_score"] == 100.0
    assert score["weakness_flags"] == []


def test_gig_quality_rubric_overall_weakness_score_formula() -> None:
    row = GigQualityAnalysis(
        gig_url="https://www.fiverr.com/rubric/ows",
        niche_id="rubric",
        run_id="rubric-run",
        rubric_score=55.0,
        video_absent=False,
        portfolio_absent=False,
        description_thin=False,
        faq_absent=False,
        thumbnail_quality_flag=False,
        weakness_flags=[],
    )
    assert row.overall_weakness_score == 4.5


def test_gig_quality_rubric_red_flag_extraction_from_low_criteria() -> None:
    score = compute_rubric_score(
        gig_row={"description_text": "thin", "faq_text": "", "thumbnail_url": ""},
        gig_quality_score_row={
            "video_present": False,
            "portfolio_count": 0,
            "description_quality_score": 1.0,
            "faq_completeness_score": 1.0,
            "thumbnail_quality_score": 1.0,
        },
    )
    assert set(score["weakness_flags"]) >= {"video_absent", "portfolio_absent", "description_thin", "faq_absent"}


def test_gig_quality_rubric_run_id_is_stored_with_result() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "rubric run id keyword")
        gig = _seed_gig(
            session,
            keyword=keyword,
            run_id="rubric-run-id",
            gig_url="https://fiverr.com/gig/rubric-run-id",
            rank=1,
            description_text="Detailed rubric run id coverage text " * 6,
            faq_text="faq",
            video_present=True,
            portfolio_count=2,
        )
        _seed_gqs(
            session,
            gig=gig,
            keyword=keyword,
            run_id="rubric-run-id",
            video_present=True,
            portfolio_count=2,
            description_quality_score=8.0,
            faq_completeness_score=8.0,
            thumbnail_quality_score=8.0,
        )

        _run(
            run_gig_quality_analysis_for_niche(
                niche_id="test_niche",
                run_id="rubric-run-id",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        row = session.scalars(select(GigQualityAnalysis).where(GigQualityAnalysis.gig_url == gig.gig_url)).one()
        assert row.run_id == "rubric-run-id"
    finally:
        session.close()
