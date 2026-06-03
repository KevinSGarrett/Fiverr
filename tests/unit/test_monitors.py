"""R11 monitor tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.base import Base
from src.models.result_set_validation import ResultSetValidation
from src.monitoring.monitors import (
    check_category_filter_health,
    detect_relevance_cliff,
    detect_stealth_sponsored,
)


def test_stealth_sponsored_monitor_fires_on_fixture() -> None:
    class MockComp:
        def __init__(self, sponsored: bool, excluded: bool) -> None:
            self.is_sponsored = sponsored
            self.sponsored_excluded = excluded

    rows = [MockComp(True, False), MockComp(False, False)]
    result = detect_stealth_sponsored(None, rows)
    assert result["detected"] is True
    assert result["count"] == 1
    assert result["severity"] == "info"


def test_relevance_cliff_fires_on_large_drop() -> None:
    result = detect_relevance_cliff(45.0, 75.0)
    assert result["detected"] is True
    assert result["drop_pct"] > 0


def test_relevance_cliff_does_not_fire_on_small_drop() -> None:
    result = detect_relevance_cliff(70.0, 75.0)
    assert result["detected"] is False


def test_category_filter_health_uses_none_rate_threshold() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    try:
        session.add_all(
            [
                ResultSetValidation(keyword_id=1, run_id="run-health", search_strictness_used="SUBCATEGORY"),
                ResultSetValidation(keyword_id=2, run_id="run-health", search_strictness_used="NONE"),
                ResultSetValidation(keyword_id=3, run_id="run-health", search_strictness_used="SUBCATEGORY"),
            ]
        )
        session.commit()
        result = check_category_filter_health(niche_id=1, run_id="run-health", db=session)
        assert result["none_count"] == 1
        assert result["total"] == 3
        assert result["healthy"] is False
    finally:
        session.close()


def test_stealth_sponsored_no_rows_returns_not_detected() -> None:
    result = detect_stealth_sponsored(None, [])
    assert result["detected"] is False
    assert result["count"] == 0
    assert result["severity"] == "none"


def test_stealth_sponsored_all_excluded_returns_not_detected() -> None:
    class MockComp:
        def __init__(self, sponsored: bool, excluded: bool) -> None:
            self.is_sponsored = sponsored
            self.sponsored_excluded = excluded

    rows = [MockComp(True, True), MockComp(True, True)]
    result = detect_stealth_sponsored(None, rows)
    assert result["detected"] is False
    assert result["count"] == 0


def test_stealth_sponsored_count_is_accurate() -> None:
    class MockComp:
        def __init__(self, sponsored: bool, excluded: bool) -> None:
            self.is_sponsored = sponsored
            self.sponsored_excluded = excluded

    rows = [
        MockComp(True, False),
        MockComp(True, False),
        MockComp(True, True),
        MockComp(False, False),
    ]
    result = detect_stealth_sponsored(None, rows)
    assert result["count"] == 2
    assert result["detected"] is True


def test_relevance_cliff_at_exact_threshold() -> None:
    result = detect_relevance_cliff(60.0, 75.0)
    assert result["detected"] is True


def test_relevance_cliff_below_threshold() -> None:
    result = detect_relevance_cliff(61.0, 75.0)
    assert result["detected"] is False


def test_relevance_cliff_zero_prev_score() -> None:
    result = detect_relevance_cliff(0.0, 0.0)
    assert result["detected"] is False
    assert result["drop_pct"] == 0.0


def test_category_filter_health_empty_run() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    try:
        result = check_category_filter_health(1, "no_run", session)
        assert result["healthy"] is True
        assert result["fallback_rate"] == 0.0
        assert result["total"] == 0
    finally:
        session.close()


def test_category_filter_health_all_none_strictness() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    try:
        for keyword_id in range(1, 6):
            session.add(
                ResultSetValidation(
                    run_id="run-all-none",
                    keyword_id=keyword_id,
                    search_strictness_used="NONE",
                )
            )
        session.commit()
        result = check_category_filter_health(1, "run-all-none", session)
        assert result["healthy"] is False
        assert result["fallback_rate"] == 1.0
        assert result["none_count"] == 5
        assert result["total"] == 5
    finally:
        session.close()


def test_category_filter_health_mixed_strictness() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()
    try:
        strictness_values = ["SUBCATEGORY", "CATEGORY", "SUBCATEGORY", "SUBCATEGORY", "NONE"]
        for keyword_id, strictness in enumerate(strictness_values, start=1):
            session.add(
                ResultSetValidation(
                    run_id="run-mixed",
                    keyword_id=keyword_id,
                    search_strictness_used=strictness,
                )
            )
        session.commit()
        result = check_category_filter_health(1, "run-mixed", session)
        assert result["none_count"] == 1
        assert result["total"] == 5
        assert abs(result["fallback_rate"] - 0.2) < 0.001
        assert result["healthy"] is False
    finally:
        session.close()
