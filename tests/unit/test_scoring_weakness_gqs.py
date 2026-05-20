"""Unit tests for GigQualityScore supplementation in weakness signals."""

from __future__ import annotations

import builtins

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Gig, GigQualityScore, Keyword, Niche, SearchResult
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


def _new_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _seed_keyword(
    session: Session,
    *,
    fallback_video: list[bool] | None = None,
    fallback_portfolio: list[bool] | None = None,
) -> int:
    fallback_video = fallback_video or ([True] * 10)
    fallback_portfolio = fallback_portfolio or ([True] * 10)

    niche = Niche(slug="weakness-niche", name="Weakness Niche", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="weakness keyword",
        normalized_keyword="weakness keyword",
    )
    session.add(keyword)
    session.flush()

    for idx in range(10):
        gig = Gig(
            gig_url=f"https://www.fiverr.com/gigs/{idx + 1}",
            seller_username=f"seller_{idx + 1}",
            metadata_json={
                "has_video": fallback_video[idx],
                "has_portfolio": fallback_portfolio[idx],
            },
        )
        session.add(gig)
        session.flush()
        session.add(
            SearchResult(
                keyword_id=keyword.id,
                rank=idx + 1,
                gig_id=gig.id,
                title=f"Gig {idx + 1}",
            )
        )

    session.commit()
    return keyword.id


def _insert_gqs_rows(
    session: Session,
    keyword_id: int,
    rows: list[tuple[bool | None, int | None, bool]],
    *,
    gig_urls: list[str] | None = None,
) -> None:
    resolved_urls = gig_urls or [f"https://www.fiverr.com/gigs/{idx}" for idx in range(1, len(rows) + 1)]
    for idx, (video_present, portfolio_count, analysis_complete) in enumerate(rows, start=1):
        session.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=resolved_urls[idx - 1],
                run_id="run-gqs",
                video_present=video_present,
                portfolio_count=portfolio_count,
                analysis_complete=analysis_complete,
            )
        )
    session.commit()


def test_weakness_gqs_no_rows() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
        assert signals["portfolio_absence_rate"] == 0.0
        assert "gig_quality_score_available" not in signals
    finally:
        session.close()


def test_weakness_gqs_video_present_all() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(True, 1, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
    finally:
        session.close()


def test_weakness_gqs_video_absent_all() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(False, 1, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 1.0
    finally:
        session.close()


def test_weakness_gqs_video_mixed() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        rows = [(True, 1, True)] * 3 + [(False, 1, True)] * 7
        _insert_gqs_rows(session, keyword_id, rows)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.7
    finally:
        session.close()


def test_weakness_gqs_portfolio_zero_all() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(True, 0, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["portfolio_absence_rate"] == 1.0
    finally:
        session.close()


def test_weakness_gqs_portfolio_nonzero() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        _insert_gqs_rows(session, keyword_id, [(True, 2, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["portfolio_absence_rate"] == 0.0
    finally:
        session.close()


def test_weakness_gqs_overrides_visual_analysis() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session, fallback_video=[True] * 10, fallback_portfolio=[True] * 10)
        _insert_gqs_rows(session, keyword_id, [(False, 0, True)] * 10)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 1.0
        assert signals["portfolio_absence_rate"] == 1.0
        assert signals["top10_has_video"] == [False] * 10
    finally:
        session.close()


def test_weakness_gqs_exception_safe(monkeypatch) -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        original_import = builtins.__import__

        def _raise_on_gqs(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
            if name == "src.models.gig_quality_score":
                raise ImportError("forced import failure")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _raise_on_gqs)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
        assert signals["portfolio_absence_rate"] == 0.0
    finally:
        session.close()


def test_weakness_gqs_analysis_complete() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        rows = [(True, 1, False)] * 9 + [(True, 1, True)]
        _insert_gqs_rows(session, keyword_id, rows)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["gig_quality_score_available"] is True
    finally:
        session.close()


def test_weakness_gqs_none_video_skipped() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session)
        rows = [
            (None, 1, True),
            (None, 1, True),
            (False, 1, True),
            (True, 1, True),
        ]
        _insert_gqs_rows(session, keyword_id, rows)
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.5
        assert signals["top10_has_video"] == [False, True]
    finally:
        session.close()


def test_weakness_gqs_ignores_rows_outside_current_top10() -> None:
    session = _new_session()
    try:
        keyword_id = _seed_keyword(session, fallback_video=[True] * 10, fallback_portfolio=[True] * 10)
        rows = [(False, 0, True), (False, 0, True)]
        _insert_gqs_rows(
            session,
            keyword_id,
            rows,
            gig_urls=[
                "https://www.fiverr.com/gigs/999",
                "https://www.fiverr.com/gigs/1000",
            ],
        )
        signals = GigQualityWeaknessScoreCalculator()._load_signals_from_db(keyword_id, session)
        assert signals["video_absence_rate"] == 0.0
        assert signals["portfolio_absence_rate"] == 0.0
        assert "gig_quality_score_available" not in signals
    finally:
        session.close()
