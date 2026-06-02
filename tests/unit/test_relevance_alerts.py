"""Tests for R10 relevance alert generation. AC-R10.2."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.dashboard.alert_generator import ALERT_TYPES, generate_relevance_alerts_for_run
from src.models.external_signal import ExternalSignal
from src.models.market import Keyword
from src.models.niche import Niche
from src.models.result_set_validation import ResultSetValidation
from src.models.search_result import SearchResult


def _build_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    ResultSetValidation.__table__.create(bind=engine, checkfirst=True)
    ExternalSignal.__table__.create(bind=engine, checkfirst=True)
    SearchResult.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, future=True)()


def test_alert_catalog_has_6_types() -> None:
    assert len(ALERT_TYPES) == 6
    for key in [
        "ghost_market_detected",
        "relevance_deduction_applied",
        "llm_validation_triggered",
        "external_signal_partial",
        "contamination_flagged",
        "data_integrity_gap",
    ]:
        assert key in ALERT_TYPES
    assert {meta["severity"] for meta in ALERT_TYPES.values()} == {"critical", "warning", "info"}


def test_alerts_sorted_critical_first() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="niche", name="Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw_one = Keyword(niche_id=niche.id, keyword="kw one", normalized_keyword="kw one")
        kw_two = Keyword(niche_id=niche.id, keyword="kw two", normalized_keyword="kw two")
        session.add_all([kw_one, kw_two])
        session.commit()

        session.add_all(
            [
                ResultSetValidation(
                    keyword_id=kw_one.id,
                    run_id="run-1",
                    result_set_relevance_score=0.4,
                    relevance_deduction=-0.2,
                    ghost_market_flag=True,
                    category_contamination_flag=True,
                    validation_method="llm_stage_7_5",
                ),
                SearchResult(keyword_id=kw_one.id, run_id="run-1", page_collected=1, rank=1),
                SearchResult(keyword_id=kw_two.id, run_id="run-1", page_collected=2, rank=2),
                ExternalSignal(
                    keyword_id=kw_one.id,
                    run_id="run-1",
                    signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
                    signal_value=5.0,
                ),
                ExternalSignal(
                    keyword_id=kw_one.id,
                    run_id="run-1",
                    signal_type=ExternalSignal.SIGNAL_REDDIT_DEMAND,
                    signal_value=2.0,
                ),
            ]
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-1", session)

        assert alerts
        assert alerts[0]["severity"] == "critical"
        severities = [item["severity"] for item in alerts]
        assert severities == sorted(severities, key=lambda value: ["critical", "warning", "info"].index(value))
        types = {item["type"] for item in alerts}
        assert "ghost_market_detected" in types
        assert "data_integrity_gap" in types
        assert "external_signal_partial" in types
    finally:
        session.close()


def test_empty_run_returns_no_alerts() -> None:
    session = _build_session()
    try:
        alerts = generate_relevance_alerts_for_run("empty-run", session)
        assert alerts == []
    finally:
        session.close()


def test_ghost_market_produces_critical_alert() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="niche", name="Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="kw", normalized_keyword="kw")
        session.add(kw)
        session.commit()
        session.add(
            ResultSetValidation(
                keyword_id=kw.id,
                run_id="run-ghost",
                result_set_relevance_score=0.2,
                relevance_deduction=0.0,
                ghost_market_flag=True,
            )
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-ghost", session)

        assert any(item["type"] == "ghost_market_detected" for item in alerts)
        ghost = next(item for item in alerts if item["type"] == "ghost_market_detected")
        assert ghost["severity"] == "critical"
    finally:
        session.close()
