"""Tests for R10 relevance alert generation. AC-R10.2."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.dashboard.alert_generator import ALERT_TYPES, generate_relevance_alerts_for_run
from src.models.base import Base
from src.models.external_signal import ExternalSignal
from src.models.keyword_score import KeywordScore
from src.models.market import Keyword
from src.models.niche import Niche
from src.models.result_set_validation import ResultSetValidation
from src.models.search_result import SearchResult


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
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


def test_relevance_deduction_alert_generated() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="deduction-niche", name="Deduction Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="deduction kw", normalized_keyword="deduction kw")
        session.add(kw)
        session.commit()
        session.add(
            ResultSetValidation(
                keyword_id=kw.id,
                run_id="run-deduction",
                result_set_relevance_score=0.5,
                relevance_deduction=-0.25,
            )
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-deduction", session)
        types = {item["type"] for item in alerts}
        assert "relevance_deduction_applied" in types
    finally:
        session.close()


def test_llm_validation_alert_generated() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="llm-niche", name="LLM Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="llm kw", normalized_keyword="llm kw")
        session.add(kw)
        session.commit()
        session.add(ResultSetValidation(keyword_id=kw.id, run_id="run-llm", validation_method="llm_stage_7_5"))
        session.add(
            KeywordScore(
                keyword_id=kw.id,
                scoring_profile="default",
                score_depth="standard",
                final_score=60.0,
                tag="CONDITIONAL_GO",
                llm_inputs_used={"prompt_tokens": 20},
            )
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-llm", session)
        types = {item["type"] for item in alerts}
        assert "llm_validation_triggered" in types
    finally:
        session.close()


def test_external_signal_partial_alert_generated() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="signal-niche", name="Signal Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="signal kw", normalized_keyword="signal kw")
        session.add(kw)
        session.commit()
        session.add_all(
            [
                ExternalSignal(
                    keyword_id=kw.id,
                    run_id="run-signal",
                    signal_type=ExternalSignal.SIGNAL_GOOGLE_TRENDS,
                    signal_value=12.0,
                ),
                ExternalSignal(
                    keyword_id=kw.id,
                    run_id="run-signal",
                    signal_type=ExternalSignal.SIGNAL_REDDIT_DEMAND,
                    signal_value=5.0,
                ),
            ]
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-signal", session)
        partial = next(item for item in alerts if item["type"] == "external_signal_partial")
        assert partial["severity"] == "warning"
        assert partial["n_present"] == 2
    finally:
        session.close()


def test_contamination_alert_generated() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="contam-niche", name="Contam Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="contam kw", normalized_keyword="contam kw")
        session.add(kw)
        session.commit()
        session.add(
            ResultSetValidation(
                keyword_id=kw.id,
                run_id="run-contam",
                category_contamination_flag=True,
            )
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-contam", session)
        assert any(item["type"] == "contamination_flagged" for item in alerts)
    finally:
        session.close()


def test_info_only_alerts_stay_info_severity() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="info-niche", name="Info Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="info kw", normalized_keyword="info kw")
        session.add(kw)
        session.commit()
        session.add(
            ResultSetValidation(
                keyword_id=kw.id,
                run_id="run-info-only",
                validation_method="LLM_review",
                relevance_deduction=0.0,
                ghost_market_flag=False,
                category_contamination_flag=False,
            )
        )
        session.add(
            KeywordScore(
                keyword_id=kw.id,
                scoring_profile="default",
                score_depth="standard",
                final_score=55.0,
                tag="MONITOR",
                llm_inputs_used={"prompt_tokens": 9},
            )
        )
        session.add(SearchResult(keyword_id=kw.id, run_id="run-info-only", page_collected=1, rank=1))
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-info-only", session)
        assert alerts
        assert all(item["severity"] == "info" for item in alerts)
    finally:
        session.close()


def test_data_integrity_gap_alert_generated_for_missing_rsv() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="gap-niche", name="Gap Niche", category_path="A/B")
        session.add(niche)
        session.commit()
        kw_one = Keyword(niche_id=niche.id, keyword="gap one", normalized_keyword="gap one")
        kw_two = Keyword(niche_id=niche.id, keyword="gap two", normalized_keyword="gap two")
        session.add_all([kw_one, kw_two])
        session.commit()
        session.add_all(
            [
                SearchResult(keyword_id=kw_one.id, run_id="run-gap", page_collected=1, rank=1),
                SearchResult(keyword_id=kw_two.id, run_id="run-gap", page_collected=2, rank=2),
                ResultSetValidation(keyword_id=kw_one.id, run_id="run-gap"),
            ]
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-gap", session)
        gap = next(item for item in alerts if item["type"] == "data_integrity_gap")
        assert gap["count"] == 1
    finally:
        session.close()


def test_null_run_id_returns_empty_alerts() -> None:
    session = _build_session()
    try:
        alerts = generate_relevance_alerts_for_run(None, session)  # type: ignore[arg-type]
        assert alerts == []
    finally:
        session.close()


def test_none_db_returns_empty_alerts() -> None:
    assert generate_relevance_alerts_for_run("any-run", None) == []


def test_llm_alert_counts_actual_stage_7_5_executions() -> None:
    """REG-38: LLM alert counts rows with actual LLM inputs used."""
    session = _build_session()
    try:
        niche = Niche(slug="llm-stage-75", name="LLM Stage 7.5", category_path="A/B")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="llm-stage-keyword", normalized_keyword="llm-stage-keyword")
        session.add(kw)
        session.commit()

        session.add(ResultSetValidation(keyword_id=kw.id, run_id="run-reg-38"))
        session.add(
            KeywordScore(
                keyword_id=kw.id,
                scoring_profile="default",
                score_depth="standard",
                final_score=60.0,
                tag="CONDITIONAL_GO",
                llm_inputs_used={"prompt_tokens": 12, "completion_tokens": 8},
            )
        )
        session.commit()

        alerts = generate_relevance_alerts_for_run("run-reg-38", session)
        types = [item["type"] for item in alerts]
        assert "llm_validation_triggered" in types, "LLM alert must fire when llm_inputs_used exists"
        llm_alert = next(item for item in alerts if item["type"] == "llm_validation_triggered")
        assert llm_alert["count"] == 1
    finally:
        session.close()
