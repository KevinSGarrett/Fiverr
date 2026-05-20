"""Unit tests for Stage 11 gig quality rubric analysis."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from src.analysis.gig_quality_rubric import (
    compute_rubric_score,
    load_gig_quality_scores_for_niche,
    run_gig_quality_analysis_for_niche,
)
from src.models.database import create_session_factory, initialize_database
from src.models.gig import Gig
from src.models.gig_quality_score import GigQualityScore
from src.models.market import GigQualityAnalysis, Keyword
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


def test_rubric_scores_low_for_missing_video_and_portfolio() -> None:
    score = compute_rubric_score(
        gig_row={"description_text": "thin", "faq_text": None, "thumbnail_url": None},
        gig_quality_score_row={"video_present": False, "portfolio_count": 0, "thumbnail_quality_score": 1.0},
    )
    assert score["rubric_score"] <= 30.0
    assert score["video_absent"] is True
    assert score["portfolio_absent"] is True


def test_rubric_scores_high_for_complete_gig() -> None:
    score = compute_rubric_score(
        gig_row={
            "description_text": "Detailed scope " * 20,
            "faq_text": "Q: timeline? A: 2 days",
            "thumbnail_url": "https://img.example/thumb.png",
        },
        gig_quality_score_row={
            "video_present": True,
            "portfolio_count": 4,
            "description_quality_score": 8.5,
            "faq_completeness_score": 8.0,
            "thumbnail_quality_score": 8.0,
        },
    )
    assert score["rubric_score"] >= 80.0
    assert score["weakness_flags"] == []


def test_rubric_weakness_flags_populated() -> None:
    score = compute_rubric_score(
        gig_row={"description_text": "short", "faq_text": "", "thumbnail_url": ""},
        gig_quality_score_row={"video_present": False, "portfolio_count": 0, "thumbnail_quality_score": 2.0},
    )
    assert "video_absent" in score["weakness_flags"]
    assert "portfolio_absent" in score["weakness_flags"]
    assert "description_thin" in score["weakness_flags"]
    assert "faq_absent" in score["weakness_flags"]


def test_load_gig_quality_returns_data() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "python automation")
        gig = _seed_gig(
            session,
            keyword=keyword,
            run_id="run-load",
            gig_url="https://fiverr.com/gig/load-1",
            rank=1,
            description_text="Detailed scope " * 12,
            faq_text="faq",
            video_present=True,
            portfolio_count=3,
        )
        _seed_gqs(
            session,
            gig=gig,
            keyword=keyword,
            run_id="run-load",
            video_present=True,
            portfolio_count=3,
        )
        rows = load_gig_quality_scores_for_niche("test_niche", "run-load", session)
        assert len(rows) == 1
        assert rows[0]["gig_url"] == gig.gig_url
    finally:
        session.close()


def test_run_analysis_writes_rows() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "workflow automation")
        gig_one = _seed_gig(
            session,
            keyword=keyword,
            run_id="run-write",
            gig_url="https://fiverr.com/gig/write-1",
            rank=1,
            description_text="Detailed scope " * 15,
            faq_text="faq one",
            video_present=True,
            portfolio_count=3,
        )
        gig_two = _seed_gig(
            session,
            keyword=keyword,
            run_id="run-write",
            gig_url="https://fiverr.com/gig/write-2",
            rank=2,
            description_text="short",
            faq_text="",
            video_present=False,
            portfolio_count=0,
        )
        _seed_gqs(
            session,
            gig=gig_one,
            keyword=keyword,
            run_id="run-write",
            video_present=True,
            portfolio_count=3,
            thumbnail_quality_score=8.0,
        )
        _seed_gqs(
            session,
            gig=gig_two,
            keyword=keyword,
            run_id="run-write",
            video_present=False,
            portfolio_count=0,
            thumbnail_quality_score=2.0,
        )

        result = _run(
            run_gig_quality_analysis_for_niche(
                niche_id="test_niche",
                run_id="run-write",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )

        rows = session.scalars(select(GigQualityAnalysis)).all()
        assert result["analyzed"] is True
        assert result["gigs_analyzed"] == 2
        assert len(rows) == 2
        assert all(row.rubric_score >= 0.0 for row in rows)
    finally:
        session.close()


def test_run_analysis_empty_niche_skips() -> None:
    session, _niche = _build_session()
    try:
        result = _run(
            run_gig_quality_analysis_for_niche(
                niche_id="test_niche",
                run_id="run-empty",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        assert result["analyzed"] is False
        assert result["reason"] == "no_gig_quality_scores"
    finally:
        session.close()


def test_rubric_scoped_to_current_run() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "run scope")
        current_gig = _seed_gig(
            session,
            keyword=keyword,
            run_id="run-current",
            gig_url="https://fiverr.com/gig/current",
            rank=1,
            description_text="Detailed scope " * 12,
            faq_text="faq current",
            video_present=True,
            portfolio_count=2,
        )
        old_gig = _seed_gig(
            session,
            keyword=keyword,
            run_id="run-old",
            gig_url="https://fiverr.com/gig/old",
            rank=2,
            description_text="old",
            faq_text=None,
            video_present=False,
            portfolio_count=0,
        )
        _seed_gqs(
            session,
            gig=current_gig,
            keyword=keyword,
            run_id="run-current",
            video_present=True,
            portfolio_count=2,
        )
        _seed_gqs(
            session,
            gig=old_gig,
            keyword=keyword,
            run_id="run-old",
            video_present=False,
            portfolio_count=0,
        )

        result = _run(
            run_gig_quality_analysis_for_niche(
                niche_id="test_niche",
                run_id="run-current",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )
        rows = session.scalars(select(GigQualityAnalysis)).all()
        assert result["gigs_analyzed"] == 1
        assert len(rows) == 1
        assert rows[0].gig_url == current_gig.gig_url
    finally:
        session.close()


def test_rubric_excludes_stale_gqs_rows() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "stale rows")
        gig = _seed_gig(
            session,
            keyword=keyword,
            run_id="run-current",
            gig_url="https://fiverr.com/gig/stale-check",
            rank=1,
            description_text="Detailed scope " * 12,
            faq_text="faq current",
            video_present=True,
            portfolio_count=3,
        )
        _seed_gqs(
            session,
            gig=gig,
            keyword=keyword,
            run_id="run-current",
            video_present=True,
            portfolio_count=3,
        )
        _seed_gqs(
            session,
            gig=gig,
            keyword=keyword,
            run_id="run-legacy",
            video_present=False,
            portfolio_count=0,
        )

        _run(
            run_gig_quality_analysis_for_niche(
                niche_id="test_niche",
                run_id="run-current",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
            )
        )

        row = session.scalars(select(GigQualityAnalysis)).one()
        assert row.video_absent is False
        assert row.portfolio_absent is False
    finally:
        session.close()

