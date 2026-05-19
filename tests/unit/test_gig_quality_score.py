"""Unit tests for GigQualityScore ORM model and helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    GigQualityScore,
    Keyword,
    Niche,
    get_analysis_complete_count,
    get_gig_quality_scores,
    write_gig_quality_score,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_factory()


def _keyword_id(session: Session, slug: str = "gig-quality") -> int:
    niche = Niche(slug=slug, name=f"{slug} niche", category_path=f"programming-tech/{slug}")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword=f"{slug} keyword",
        normalized_keyword=f"{slug} keyword",
    )
    session.add(keyword)
    session.commit()
    return int(keyword.id)


def test_gig_quality_score_table_name() -> None:
    assert GigQualityScore.__tablename__ == "gig_quality_scores"


def test_gig_quality_score_insert_minimal() -> None:
    session = _session()
    row = GigQualityScore(gig_url="https://fiverr.com/gigs/one", run_id="run-minimal")
    session.add(row)
    session.commit()
    fetched = session.query(GigQualityScore).filter(GigQualityScore.id == row.id).first()
    assert fetched is not None
    assert fetched.gig_url == "https://fiverr.com/gigs/one"
    assert fetched.run_id == "run-minimal"
    session.close()


def test_gig_quality_score_insert_full() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-full")
    row = GigQualityScore(
        gig_id=None,
        gig_url="https://fiverr.com/gigs/full",
        keyword_id=keyword_id,
        run_id="run-full",
        analysis_complete=True,
        description_quality_score=0.72,
        weakness_count=3,
        thumbnail_quality_score=0.81,
        faq_completeness_score=0.55,
        package_differentiation_score=0.43,
        niche_specificity_score=0.61,
        video_present=True,
        portfolio_count=6,
        llm_model_used="gpt-4o",
        llm_prompt_version="v1.0.0",
        analysis_notes="Looks good",
        ttl_hours=720,
    )
    session.add(row)
    session.commit()
    assert row.id is not None
    session.close()


def test_gig_quality_score_unique_constraint() -> None:
    session = _session()
    session.add(GigQualityScore(gig_url="https://fiverr.com/gigs/dup", run_id="run-dup"))
    session.commit()
    session.add(GigQualityScore(gig_url="https://fiverr.com/gigs/dup", run_id="run-dup"))
    try:
        session.commit()
        raise AssertionError("Expected unique constraint violation")
    except IntegrityError:
        session.rollback()
    session.close()


def test_gig_quality_score_nullable_scores() -> None:
    session = _session()
    row = GigQualityScore(
        gig_url="https://fiverr.com/gigs/nullable",
        run_id="run-nullable",
        description_quality_score=None,
        weakness_count=None,
        thumbnail_quality_score=None,
        faq_completeness_score=None,
        package_differentiation_score=None,
        niche_specificity_score=None,
    )
    session.add(row)
    session.commit()
    fetched = session.query(GigQualityScore).filter(GigQualityScore.id == row.id).first()
    assert fetched is not None
    assert fetched.description_quality_score is None
    assert fetched.weakness_count is None
    assert fetched.thumbnail_quality_score is None
    assert fetched.faq_completeness_score is None
    assert fetched.package_differentiation_score is None
    assert fetched.niche_specificity_score is None
    session.close()


def test_gig_quality_score_default_analysis() -> None:
    session = _session()
    row = GigQualityScore(gig_url="https://fiverr.com/gigs/default", run_id="run-default")
    session.add(row)
    session.commit()
    fetched = session.query(GigQualityScore).filter(GigQualityScore.id == row.id).first()
    assert fetched is not None
    assert fetched.analysis_complete is False
    session.close()


def test_write_giq_dict_db() -> None:
    result = write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/no-session",
        keyword_id=1,
        run_id="run-none",
        video_present=None,
        portfolio_count=None,
        analysis_complete=False,
        description_quality_score=None,
        weakness_count=None,
        db={},
    )
    assert result is None


def test_write_giq_orm() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-write")
    row = write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/write",
        keyword_id=keyword_id,
        run_id="run-write",
        video_present=True,
        portfolio_count=2,
        analysis_complete=True,
        description_quality_score=0.9,
        weakness_count=1,
        db=session,
    )
    assert row is not None
    assert session.query(GigQualityScore).count() == 1
    assert row.analysed_at is not None
    session.close()


def test_write_giq_upsert() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-upsert")
    first = write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/upsert",
        keyword_id=keyword_id,
        run_id="run-upsert",
        video_present=False,
        portfolio_count=0,
        analysis_complete=False,
        description_quality_score=0.2,
        weakness_count=7,
        db=session,
    )
    second = write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/upsert",
        keyword_id=keyword_id,
        run_id="run-upsert",
        video_present=True,
        portfolio_count=5,
        analysis_complete=True,
        description_quality_score=0.8,
        weakness_count=2,
        db=session,
    )
    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert session.query(GigQualityScore).count() == 1
    assert second.video_present is True
    assert second.portfolio_count == 5
    assert second.analysis_complete is True
    session.close()


def test_get_scores_empty() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-empty")
    assert get_gig_quality_scores(keyword_id, session) == []
    session.close()


def test_get_scores_for_keyword() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-get")
    other_keyword_id = _keyword_id(session, "gig-quality-other")
    write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/get-a",
        keyword_id=keyword_id,
        run_id="run-get",
        video_present=None,
        portfolio_count=None,
        analysis_complete=True,
        description_quality_score=0.5,
        weakness_count=5,
        db=session,
    )
    write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/get-b",
        keyword_id=other_keyword_id,
        run_id="run-get",
        video_present=None,
        portfolio_count=None,
        analysis_complete=False,
        description_quality_score=None,
        weakness_count=None,
        db=session,
    )
    rows = get_gig_quality_scores(keyword_id, session)
    assert len(rows) == 1
    assert rows[0].gig_url == "https://fiverr.com/gigs/get-a"
    session.close()


def test_get_analysis_complete_count_none() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-count-none")
    assert get_analysis_complete_count(keyword_id, session) == 0
    session.close()


def test_get_analysis_complete_count_some() -> None:
    session = _session()
    keyword_id = _keyword_id(session, "gig-quality-count-some")
    write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/count-a",
        keyword_id=keyword_id,
        run_id="run-count",
        video_present=None,
        portfolio_count=None,
        analysis_complete=True,
        description_quality_score=0.6,
        weakness_count=3,
        db=session,
    )
    write_gig_quality_score(
        gig_url="https://fiverr.com/gigs/count-b",
        keyword_id=keyword_id,
        run_id="run-count-2",
        video_present=None,
        portfolio_count=None,
        analysis_complete=False,
        description_quality_score=0.3,
        weakness_count=8,
        db=session,
    )
    assert get_analysis_complete_count(keyword_id, session) == 1
    session.close()


def test_gig_quality_score_in_base_metadata() -> None:
    assert "gig_quality_scores" in Base.metadata.tables
