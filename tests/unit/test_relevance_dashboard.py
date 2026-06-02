"""Tests for R10 relevance dashboard aggregation/display helpers."""

from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.dashboard.relevance_dashboard import (
    build_data_integrity_block,
    calculate_niche_relevance_quality_score,
    get_opportunities_for_display,
    run_summary_relevance_block,
)
from src.models.market import Keyword
from src.models.niche import Niche
from src.models.result_set_validation import ResultSetValidation


def _build_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Niche.__table__.create(bind=engine, checkfirst=True)
    Keyword.__table__.create(bind=engine, checkfirst=True)
    ResultSetValidation.__table__.create(bind=engine, checkfirst=True)
    return sessionmaker(bind=engine, future=True)()


def test_quality_score_returns_zero_for_missing_rows() -> None:
    session = _build_session()
    try:
        assert calculate_niche_relevance_quality_score(1, "missing-run", session) == 0.0
    finally:
        session.close()


def test_ghost_market_excluded_from_opportunities_by_default() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="n1", name="N1", category_path="x/y")
        session.add(niche)
        session.commit()
        normal_kw = Keyword(
            niche_id=niche.id,
            keyword="normal",
            normalized_keyword="normal",
            ghost_market_flag=False,
        )
        ghost_kw = Keyword(
            niche_id=niche.id,
            keyword="ghost",
            normalized_keyword="ghost",
            ghost_market_flag=True,
        )
        null_kw = Keyword(
            niche_id=niche.id,
            keyword="null-ghost",
            normalized_keyword="null-ghost",
            ghost_market_flag=None,
        )
        session.add_all([normal_kw, ghost_kw, null_kw])
        session.commit()
        session.add_all(
            [
                ResultSetValidation(keyword_id=normal_kw.id, run_id="run-1"),
                ResultSetValidation(keyword_id=ghost_kw.id, run_id="run-1"),
                ResultSetValidation(keyword_id=null_kw.id, run_id="run-1"),
            ]
        )
        session.commit()

        visible = get_opportunities_for_display("run-1", session)
        visible_ids = {row.keyword_id for row in visible}
        assert normal_kw.id in visible_ids
        assert null_kw.id in visible_ids
        assert ghost_kw.id not in visible_ids

        all_rows = get_opportunities_for_display("run-1", session, show_ghost_markets=True)
        all_ids = {row.keyword_id for row in all_rows}
        assert {normal_kw.id, ghost_kw.id, null_kw.id}.issubset(all_ids)
    finally:
        session.close()


def test_data_integrity_block_renders_na_for_missing_components() -> None:
    block = build_data_integrity_block(SimpleNamespace(score_components=None))
    assert block["status"] == "gap"
    assert block["score_components"] == "N/A"


def test_run_summary_relevance_block_has_human_readable_print() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="n1", name="N1", category_path="x/y")
        session.add(niche)
        session.commit()
        kw = Keyword(
            niche_id=niche.id,
            keyword="ghost",
            normalized_keyword="ghost",
            ghost_market_flag=True,
        )
        session.add(kw)
        session.commit()
        session.add(ResultSetValidation(keyword_id=kw.id, run_id="run-print", ghost_market_flag=True))
        session.commit()

        summary = run_summary_relevance_block("run-print", session)
        assert summary["ghost_market_count"] == 1
        assert "ghost market keyword(s) flagged" in summary["ghost_market_print"]
    finally:
        session.close()
