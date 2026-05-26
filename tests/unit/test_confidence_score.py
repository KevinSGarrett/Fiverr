"""Targeted coverage tests for confidence score modifier helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Keyword, KeywordScore, Niche, NicheConfigRecord
from src.scoring.confidence import ConfidenceScoreModifier, compute_confidence_score


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


def test_compute_confidence_score_prefers_latest_persisted_modifier() -> None:
    session = _session()
    try:
        niche = Niche(slug="persisted-score", name="Persisted Score", category_path="Programming & Tech > AI")
        session.add(niche)
        session.flush()
        keyword = Keyword(
            niche_id=niche.id,
            keyword="persisted keyword",
            normalized_keyword="persisted keyword",
        )
        session.add(keyword)
        session.flush()

        session.add(
            KeywordScore(
                keyword_id=keyword.id,
                scored_at=datetime.now(UTC) - timedelta(minutes=1),
                final_score=35.0,
                confidence_modifier=0.62,
                tag="CAUTION",
                score_components={},
            )
        )
        session.add(
            KeywordScore(
                keyword_id=keyword.id,
                scored_at=datetime.now(UTC),
                final_score=38.0,
                confidence_modifier=0.75,
                tag="CAUTION",
                score_components={},
            )
        )
        session.commit()

        modifier = compute_confidence_score(keyword_id=keyword.id, db=session)
        assert modifier == 0.75
    finally:
        session.close()


def test_compute_confidence_score_uses_run_context_when_provided() -> None:
    session = _session()
    try:
        modifier = compute_confidence_score(
            keyword_id=999,
            db=session,
            run_context={
                "data_completeness_ratio": 1.0,
                "data_freshness_score": 1.0,
                "source_diversity_score": 1.0,
                "llm_analysis_completion_ratio": 1.0,
                "google_trends_available": True,
                "gig_detail_collected": True,
                "seller_profiles_collected": True,
                "reddit_signals_available": True,
            },
        )
        assert modifier == 1.0
    finally:
        session.close()


@pytest.mark.parametrize(
    ("raw_value", "default_value", "expected"),
    [
        (None, 0.0, 0.0),
        ("1", 0.0, 1.0),
        ("1.25", 0.0, 1.25),
        ("-2", 0.0, -2.0),
        ("nan", 5.0, float("nan")),
        ("inf", 1.0, float("inf")),
        ("-inf", 1.0, float("-inf")),
        ("0", 9.0, 0.0),
        ("0.5", 1.0, 0.5),
        ("42", 1.0, 42.0),
        (3.14, 0.0, 3.14),
        (10, 0.0, 10.0),
        (True, 0.0, 1.0),
        (False, 0.0, 0.0),
        (" 7 ", 0.0, 7.0),
        ("not-a-number", 2.5, 2.5),
        ({}, 4.0, 4.0),
        ([], 6.0, 6.0),
        ((), 8.0, 8.0),
        ("", 3.0, 3.0),
        ("+12", 0.0, 12.0),
        ("-0.25", 0.0, -0.25),
        ("1e2", 0.0, 100.0),
        ("-1e-2", 0.0, -0.01),
        ("3.1415926535", 0.0, 3.1415926535),
        ("2.0", 5.0, 2.0),
        ("  0.75  ", 9.0, 0.75),
        ("5e-1", 9.0, 0.5),
        (0, 9.0, 0.0),
        (1, 9.0, 1.0),
    ],
)
def test_confidence_as_float_parametrized(raw_value: Any, default_value: float, expected: float) -> None:
    calculator = ConfidenceScoreModifier()
    actual = calculator._as_float(raw_value, default_value)  # pylint: disable=protected-access
    if expected != expected:  # NaN check
        assert actual != actual
    else:
        assert actual == expected


@pytest.mark.parametrize(
    ("raw_value", "default_value", "expected"),
    [
        (None, True, True),
        (None, False, False),
        (True, False, True),
        (False, True, False),
        ("true", False, True),
        ("TRUE", False, True),
        ("True", False, True),
        ("  true  ", False, True),
        ("1", False, True),
        ("yes", False, True),
        ("YES", False, True),
        ("false", True, False),
        ("FALSE", True, False),
        ("False", True, False),
        ("  false  ", True, False),
        ("0", True, False),
        ("no", True, False),
        ("NO", True, False),
        ("y", True, True),
        ("n", False, False),
        ("t", True, True),
        ("f", False, False),
        ("enabled", True, True),
        ("disabled", False, False),
        ("", True, True),
        ("", False, False),
        (0, True, True),
        (1, False, False),
        ({}, True, True),
        ([], False, False),
    ],
)
def test_confidence_as_bool_parametrized(raw_value: Any, default_value: bool, expected: bool) -> None:
    calculator = ConfidenceScoreModifier()
    actual = calculator._as_bool(raw_value, default_value)  # pylint: disable=protected-access
    assert actual is expected
