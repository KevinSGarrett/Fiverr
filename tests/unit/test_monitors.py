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
