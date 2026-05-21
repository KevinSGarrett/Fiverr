"""Unit tests for ExternalSignal ORM model and helpers."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    ExternalSignal,
    Keyword,
    Niche,
    get_all_signals,
    get_signal,
    write_external_signal,
)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return session_factory()


def _keyword_id(session: Session) -> int:
    niche = Niche(slug="ext-signals", name="External Signals", category_path="programming-tech/external-signals")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="google trends demand",
        normalized_keyword="google trends demand",
    )
    session.add(keyword)
    session.commit()
    return int(keyword.id)


def test_external_signal_table_name() -> None:
    assert ExternalSignal.__tablename__ == "external_signals"


def test_signal_type_constants() -> None:
    assert ExternalSignal.SIGNAL_GOOGLE_TRENDS == "google_trends"
    assert ExternalSignal.SIGNAL_REDDIT_DEMAND == "reddit_demand"
    assert ExternalSignal.SIGNAL_REDDIT_ACTIVITY == "reddit_activity"
    assert ExternalSignal.SIGNAL_YOUTUBE_COUNT == "youtube_count"
    assert ExternalSignal.SIGNAL_AUTOCOMPLETE_POSITION == "autocomplete_position"


def test_external_signal_insert_minimal() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    row = ExternalSignal(keyword_id=keyword_id, signal_type="google_trends", run_id="run-minimal")
    session.add(row)
    session.commit()
    fetched = session.query(ExternalSignal).filter(ExternalSignal.id == row.id).first()
    assert fetched is not None
    assert fetched.keyword_id == keyword_id
    session.close()


def test_external_signal_insert_full() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    row = ExternalSignal(
        keyword_id=keyword_id,
        signal_type="reddit_demand",
        signal_value=7.4,
        signal_json={"reddit_demand_intent_score": 7.4},
        source_url="https://example.com/reddit",
        ttl_hours=72,
        is_stale=False,
        run_id="run-full",
        collection_method="reddit_api",
        error_message=None,
    )
    session.add(row)
    session.commit()
    assert row.id is not None
    session.close()


def test_external_signal_nullable_json() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    row = ExternalSignal(keyword_id=keyword_id, signal_type="google_trends", signal_json=None, run_id="run-json")
    session.add(row)
    session.commit()
    fetched = session.query(ExternalSignal).filter(ExternalSignal.id == row.id).first()
    assert fetched is not None
    assert fetched.signal_json is None
    session.close()


def test_external_signal_unique_constraint() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    session.add(ExternalSignal(keyword_id=keyword_id, signal_type="google_trends", run_id="run-1"))
    session.commit()
    session.add(ExternalSignal(keyword_id=keyword_id, signal_type="google_trends", run_id="run-1"))
    try:
        session.commit()
        raise AssertionError("Expected unique constraint violation")
    except IntegrityError:
        session.rollback()
    session.close()


def test_external_signal_index_exists() -> None:
    index_columns = {tuple(col.name for col in idx.columns) for idx in ExternalSignal.__table__.indexes}
    assert ("keyword_id", "signal_type", "collected_at") in index_columns


def test_write_signal_dict_db() -> None:
    result = write_external_signal(
        keyword_id=1,
        signal_type="google_trends",
        signal_value=50.0,
        signal_json={"trends_12mo_score": 50},
        run_id="run-no-session",
        collection_method="pytrends_api",
        db={},
    )
    assert result is None


def test_write_signal_orm() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    row = write_external_signal(
        keyword_id=keyword_id,
        signal_type="google_trends",
        signal_value=62.0,
        signal_json={"trends_12mo_score": 62},
        run_id="run-write",
        collection_method="pytrends_api",
        db=session,
    )
    assert row is not None
    assert session.query(ExternalSignal).count() == 1
    session.close()


def test_write_signal_upsert() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    first = write_external_signal(
        keyword_id=keyword_id,
        signal_type="google_trends",
        signal_value=55.0,
        signal_json={"trends_12mo_score": 55},
        run_id="run-upsert",
        collection_method="pytrends_api",
        db=session,
    )
    second = write_external_signal(
        keyword_id=keyword_id,
        signal_type="google_trends",
        signal_value=70.0,
        signal_json={"trends_12mo_score": 70},
        run_id="run-upsert",
        collection_method="playwright",
        db=session,
    )
    assert first is not None
    assert second is not None
    assert first.id == second.id
    assert session.query(ExternalSignal).count() == 1
    assert second.signal_value == 70.0
    assert second.collection_method == "playwright"
    session.close()


def test_get_signal_found() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    write_external_signal(
        keyword_id=keyword_id,
        signal_type="google_trends",
        signal_value=80.0,
        signal_json={"trends_12mo_score": 80},
        run_id="run-found",
        collection_method="pytrends_api",
        db=session,
    )
    fetched = get_signal(keyword_id, "google_trends", session)
    assert fetched is not None
    assert fetched.signal_value == 80.0
    session.close()


def test_get_signal_missing() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    assert get_signal(keyword_id, "google_trends", session) is None
    session.close()


def test_get_all_signals_empty() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    assert get_all_signals(keyword_id, session) == []
    session.close()


def test_get_all_signals_multiple() -> None:
    session = _session()
    keyword_id = _keyword_id(session)
    write_external_signal(
        keyword_id=keyword_id,
        signal_type="reddit_demand",
        signal_value=7.0,
        signal_json={"reddit_demand_intent_score": 7.0},
        run_id="run-multi-1",
        collection_method="reddit_api",
        db=session,
    )
    write_external_signal(
        keyword_id=keyword_id,
        signal_type="google_trends",
        signal_value=60.0,
        signal_json={"trends_12mo_score": 60},
        run_id="run-multi-2",
        collection_method="pytrends_api",
        db=session,
    )
    rows = get_all_signals(keyword_id, session)
    assert len(rows) == 2
    assert [row.signal_type for row in rows] == ["google_trends", "reddit_demand"]
    session.close()


def test_external_signal_alias_properties_roundtrip() -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", run_id="alias-run")
    row.raw_value_json = {"trends_12mo_score": 42}
    row.normalized_value = 42.0
    row.source_name = "pytrends_api"
    assert row.raw_value_json == {"trends_12mo_score": 42}
    assert row.normalized_value == 42.0
    assert row.source_name == "pytrends_api"


def test_external_signal_raw_value_json_fallback_when_none() -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", signal_json=None, run_id="alias-null")
    assert row.raw_value_json == {}


def test_external_signal_has_timestamp_columns() -> None:
    row = ExternalSignal(keyword_id=1, signal_type="google_trends", run_id="alias-created")
    assert hasattr(row, "created_at")
    assert hasattr(row, "updated_at")


def test_get_signal_non_session_returns_none() -> None:
    assert get_signal(1, "google_trends", {}) is None


def test_get_all_signals_non_session_returns_empty_list() -> None:
    assert get_all_signals(1, {}) == []
