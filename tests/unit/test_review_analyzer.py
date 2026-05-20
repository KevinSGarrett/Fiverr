"""Unit tests for Stage 12 review analyzer."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from src.analysis.review_analyzer import (
    detect_recurring_complaints,
    extract_review_signals,
    run_review_analysis_for_niche,
)
from src.models.database import create_session_factory, initialize_database
from src.models.gig import Gig
from src.models.market import Keyword, ReviewAnalysis
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


def _seed_review_gig(
    session,
    *,
    keyword: Keyword,
    run_id: str,
    gig_url: str,
    rank: int,
    review_count: int,
    avg_rating: float | None,
    review_snippets: list[dict[str, str]],
) -> None:
    gig = Gig(
        gig_url=gig_url,
        keyword_id=keyword.id,
        run_id=run_id,
        seller_username=f"seller-{rank}",
        gig_title_full=f"Gig {rank}",
        description_text="Detailed scope " * 12,
        faq_text="faq",
        review_count_exact=review_count,
        rating_exact=avg_rating,
        review_snippets=review_snippets,
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


def test_extract_review_signals_returns_velocity() -> None:
    signals = extract_review_signals(
        {
            "review_count": 10,
            "avg_rating": 4.8,
            "review_snippets": [
                {"snippet": "Great", "date": "2 days ago"},
                {"snippet": "Fast delivery", "date": "1 week ago"},
                {"snippet": "Solid", "date": "Mar 2025"},
            ],
        }
    )
    assert signals["review_count"] == 10
    assert signals["avg_rating"] == 4.8
    assert signals["review_velocity"] == 0.2


def test_extract_review_signals_handles_null() -> None:
    signals = extract_review_signals({"review_count": None, "avg_rating": None, "review_snippets": None})
    assert signals["review_count"] == 0
    assert signals["avg_rating"] is None
    assert signals["review_velocity"] == 0.0


def test_detect_complaints_returns_empty_without_llm() -> None:
    complaints = _run(
        detect_recurring_complaints(
            review_texts=["Seller delivered late and did not respond."],
            llm_client=None,
        )
    )
    assert complaints == []


def test_run_review_analysis_writes_results() -> None:
    session, niche = _build_session()
    try:
        keyword = _seed_keyword(session, niche, "python automation")
        _seed_review_gig(
            session,
            keyword=keyword,
            run_id="run-review-write",
            gig_url="https://fiverr.com/gig/review-1",
            rank=1,
            review_count=12,
            avg_rating=4.6,
            review_snippets=[
                {"snippet": "Great communication", "date": "2 days ago"},
                {"snippet": "Delivered quickly", "date": "1 week ago"},
            ],
        )

        result = _run(
            run_review_analysis_for_niche(
                niche_id="test_niche",
                run_id="run-review-write",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
                llm_client=None,
            )
        )
        rows = session.scalars(select(ReviewAnalysis)).all()
        assert result["analyzed"] is True
        assert result["gigs_analyzed"] == 1
        assert len(rows) == 1
        assert rows[0].avg_rating == 4.6
        assert rows[0].review_velocity > 0.0
    finally:
        session.close()


def test_run_review_analysis_empty_niche() -> None:
    session, _niche = _build_session()
    try:
        result = _run(
            run_review_analysis_for_niche(
                niche_id="test_niche",
                run_id="run-review-empty",
                db=session,
                config={"niches": [{"niche_id": "test_niche", "is_active": True}]},
                llm_client=None,
            )
        )
        assert result["analyzed"] is False
        assert result["reason"] == "no_review_data"
    finally:
        session.close()

