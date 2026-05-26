"""Targeted coverage tests for confidence score modifier helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Keyword, Niche, NicheConfigRecord
from src.scoring.confidence import ConfidenceScoreModifier


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_confidence_load_context_from_provider_and_mapping() -> None:
    calculator = ConfidenceScoreModifier()

    class _Provider:
        @staticmethod
        def get_confidence_inputs(_keyword_id: int) -> dict[str, Any]:
            return {"data_completeness_ratio": 0.75}

    loaded = calculator._load_context(11, None, _Provider())  # pylint: disable=protected-access
    assert loaded["data_completeness_ratio"] == 0.75

    mapping_loaded = calculator._load_context(11, None, {11: {"mode": "keyword_only"}})  # pylint: disable=protected-access
    assert mapping_loaded["mode"] == "keyword_only"

    empty_loaded = calculator._load_context(11, None, {11: "invalid"})  # pylint: disable=protected-access
    assert empty_loaded == {}


def test_confidence_signal_load_uses_niche_depth_from_config_record() -> None:
    session = _session()
    try:
        niche = Niche(slug="confidence-niche", name="Confidence Niche", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()

        keyword = Keyword(
            niche_id=niche.id,
            keyword="confidence keyword",
            normalized_keyword="confidence keyword",
        )
        session.add(keyword)
        session.flush()

        session.add(
            NicheConfigRecord(
                niche_id=str(niche.id),
                name="Confidence Config",
                category_path="Programming & Tech > AI",
                depth="feasibility",
            )
        )
        session.commit()

        signals = ConfidenceScoreModifier()._load_signals_from_db(keyword.id, session)  # pylint: disable=protected-access
        assert signals["mode"] == "feasibility"
    finally:
        session.close()


def test_confidence_parsers_cover_none_invalid_and_string_booleans() -> None:
    calculator = ConfidenceScoreModifier()

    assert calculator._as_float(None, 0.5) == 0.5  # pylint: disable=protected-access
    assert calculator._as_float("not-a-float", 0.7) == 0.7  # pylint: disable=protected-access
    assert calculator._as_bool(None, True) is True  # pylint: disable=protected-access
    assert calculator._as_bool("yes", False) is True  # pylint: disable=protected-access
    assert calculator._as_bool("0", True) is False  # pylint: disable=protected-access
    assert calculator._as_bool("unparsed", False) is False  # pylint: disable=protected-access


def test_confidence_latest_timestamp_returns_none_when_no_sources() -> None:
    session = _session()
    try:
        newest = ConfidenceScoreModifier()._latest_timestamp(  # pylint: disable=protected-access
            keyword=None,
            top_results=[],
            keyword_id=999,
            session=session,
        )
        assert newest is None
    finally:
        session.close()
