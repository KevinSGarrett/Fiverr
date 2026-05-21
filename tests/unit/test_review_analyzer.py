"""Unit tests for Stage 12 review analyzer."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select
from src.analysis.review_analyzer import (
    _parse_complaint_payload,
    _resolve_maybe_await,
    _safe_float,
    _safe_int,
    detect_recurring_complaints,
    extract_review_signals,
    load_review_data_for_niche,
    run_review_analysis_for_all_niches,
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


def test_safe_numeric_helpers_handle_mixed_inputs() -> None:
    assert _safe_int(True) is None
    assert _safe_int(12.9) == 12
    assert _safe_int("1,200") == 1200
    assert _safe_int("bad") is None

    assert _safe_float(False) is None
    assert _safe_float(4) == 4.0
    assert _safe_float("4.75") == 4.75
    assert _safe_float("oops") is None


def test_load_review_data_returns_empty_for_missing_niche() -> None:
    session, _niche = _build_session()
    try:
        assert load_review_data_for_niche("missing-slug", "run-any", session) == []
    finally:
        session.close()


def test_parse_complaint_payload_supports_multiple_shapes() -> None:
    assert _parse_complaint_payload(["Late Delivery", "scope creep", ""]) == [
        "late_delivery",
        "scope_creep",
    ]
    assert _parse_complaint_payload({"complaints": ["Revision Dispute", "late delivery"]}) == [
        "late_delivery",
        "revision_dispute",
    ]
    assert _parse_complaint_payload('{"complaints":["quality mismatch"]}') == ["quality_mismatch"]
    assert _parse_complaint_payload("late delivery, revision dispute") == [
        "late_delivery",
        "revision_dispute",
    ]
    assert _parse_complaint_payload(None) == []


def test_detect_complaints_uses_cache_hit_before_llm() -> None:
    cache = SimpleNamespace(
        get=AsyncMock(return_value='{"complaints":["late delivery"]}'),
        set=AsyncMock(),
    )
    llm_client = SimpleNamespace(complete=AsyncMock(return_value='{"complaints":["scope creep"]}'))

    complaints = _run(
        detect_recurring_complaints(
            review_texts=["Seller was delayed and communication was weak."],
            llm_client=llm_client,
            cache=cache,
            niche_id="test_niche",
        )
    )
    assert complaints == ["late_delivery"]
    assert llm_client.complete.await_count == 0


def test_detect_complaints_falls_back_when_llm_and_cache_fail() -> None:
    cache = SimpleNamespace(
        get=AsyncMock(side_effect=RuntimeError("cache down")),
        set=AsyncMock(side_effect=RuntimeError("cache write failed")),
    )
    llm_client = SimpleNamespace(complete=AsyncMock(side_effect=RuntimeError("llm down")))

    complaints = _run(
        detect_recurring_complaints(
            review_texts=["The order was delayed and they charged more for revisions."],
            llm_client=llm_client,
            cache=cache,
            niche_id="test_niche",
        )
    )
    assert "late_delivery" in complaints
    assert "revision_dispute" in complaints or "scope_creep" in complaints


def test_detect_complaints_retries_without_response_format() -> None:
    class _NoResponseFormatClient:
        def complete(self, *, prompt: str, model: str) -> str:  # noqa: ARG002
            return '{"complaints":["quality mismatch"]}'

    complaints = _run(
        detect_recurring_complaints(
            review_texts=["The delivered work was not what I expected."],
            llm_client=_NoResponseFormatClient(),
            cache=None,
            niche_id="test_niche",
        )
    )
    assert complaints == ["quality_mismatch"]


def test_resolve_maybe_await_handles_awaitables_and_plain_values() -> None:
    async def _value() -> int:
        return 42

    assert _run(_resolve_maybe_await(_value())) == 42
    assert _run(_resolve_maybe_await("plain")) == "plain"


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


def test_run_review_analysis_for_all_niches_filters_active_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    async def _fake_run_review_analysis_for_niche(
        niche_id: str,
        run_id: str,  # noqa: ARG001
        db: object,  # noqa: ARG001
        config: dict[str, object],  # noqa: ARG001
        llm_client: object | None = None,  # noqa: ARG001
    ) -> dict[str, object]:
        calls.append(niche_id)
        return {"niche_id": niche_id, "analyzed": True}

    monkeypatch.setattr(
        "src.analysis.review_analyzer.run_review_analysis_for_niche",
        _fake_run_review_analysis_for_niche,
    )

    result = _run(
        run_review_analysis_for_all_niches(
            run_id="run-all-niches",
            db=object(),
            config={
                "niches": [
                    {"niche_id": "active-one", "is_active": True},
                    {"niche_id": "inactive-one", "is_active": False},
                    {"niche_id": "active-two"},
                    "not-a-dict",
                    {"niche_id": "  "},
                ]
            },
            llm_client=None,
        )
    )
    assert calls == ["active-one", "active-two"]
    assert result["niches_processed"] == 2
    assert result["niches_analyzed"] == 2


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

