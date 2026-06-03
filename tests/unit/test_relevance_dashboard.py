"""Tests for R10 relevance dashboard aggregation/display helpers."""

from __future__ import annotations

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.dashboard.relevance_dashboard import (
    build_data_integrity_block,
    calculate_niche_relevance_quality_score,
    get_opportunities_for_display,
    run_summary_relevance_block,
)
from src.models.base import Base
from src.models.market import Keyword
from src.models.niche import Niche
from src.models.result_set_validation import ResultSetValidation


def _build_session() -> Session:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
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


def test_quality_score_computed_from_rsv_rows() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="score-niche", name="Score Niche", category_path="x/y")
        session.add(niche)
        session.commit()
        kw_one = Keyword(niche_id=niche.id, keyword="score one", normalized_keyword="score one")
        kw_two = Keyword(niche_id=niche.id, keyword="score two", normalized_keyword="score two")
        session.add_all([kw_one, kw_two])
        session.commit()
        session.add_all(
            [
                ResultSetValidation(
                    keyword_id=kw_one.id,
                    run_id="run-score",
                    result_set_relevance_score=0.80,
                ),
                ResultSetValidation(
                    keyword_id=kw_two.id,
                    run_id="run-score",
                    result_set_relevance_score=0.60,
                ),
            ]
        )
        session.commit()

        score = calculate_niche_relevance_quality_score(niche.id, "run-score", session)
        assert abs(score - 0.70) < 0.01
    finally:
        session.close()


def test_quality_score_excludes_other_niche_rows() -> None:
    session = _build_session()
    try:
        niche_one = Niche(slug="niche-one", name="Niche One", category_path="x/y")
        niche_two = Niche(slug="niche-two", name="Niche Two", category_path="x/y")
        session.add_all([niche_one, niche_two])
        session.commit()
        kw_one = Keyword(niche_id=niche_one.id, keyword="one", normalized_keyword="one")
        kw_two = Keyword(niche_id=niche_two.id, keyword="two", normalized_keyword="two")
        session.add_all([kw_one, kw_two])
        session.commit()
        session.add_all(
            [
                ResultSetValidation(
                    keyword_id=kw_one.id,
                    run_id="run-multi-niche",
                    result_set_relevance_score=0.80,
                ),
                ResultSetValidation(
                    keyword_id=kw_two.id,
                    run_id="run-multi-niche",
                    result_set_relevance_score=0.20,
                ),
            ]
        )
        session.commit()

        score_one = calculate_niche_relevance_quality_score(niche_one.id, "run-multi-niche", session)
        score_two = calculate_niche_relevance_quality_score(niche_two.id, "run-multi-niche", session)
        assert abs(score_one - 0.80) < 0.01
        assert abs(score_two - 0.20) < 0.01
    finally:
        session.close()


def test_quality_score_is_clamped_to_upper_bound() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="clamp-niche", name="Clamp Niche", category_path="x/y")
        session.add(niche)
        session.commit()
        kw = Keyword(niche_id=niche.id, keyword="clamp", normalized_keyword="clamp")
        session.add(kw)
        session.commit()
        session.add(
            ResultSetValidation(
                keyword_id=kw.id,
                run_id="run-clamp",
                result_set_relevance_score=1.5,
            )
        )
        session.commit()

        score = calculate_niche_relevance_quality_score(niche.id, "run-clamp", session)
        assert score == 1.0
    finally:
        session.close()


def test_run_summary_clean_run_shows_no_ghost() -> None:
    session = _build_session()
    try:
        summary = run_summary_relevance_block("clean-run", session)
        assert summary["ghost_market_count"] == 0
        assert summary["alert_count"] == 0
        assert "No ghost" in summary["ghost_market_print"] or "0 ghost" in summary["ghost_market_print"]
    finally:
        session.close()


def test_run_summary_has_alert_count_and_ghost_print() -> None:
    session = _build_session()
    try:
        niche = Niche(slug="summary-niche", name="Summary Niche", category_path="x/y")
        session.add(niche)
        session.commit()
        kw = Keyword(
            niche_id=niche.id,
            keyword="summary-ghost",
            normalized_keyword="summary-ghost",
            ghost_market_flag=True,
        )
        session.add(kw)
        session.commit()
        session.add(ResultSetValidation(keyword_id=kw.id, run_id="summary-run", ghost_market_flag=True))
        session.commit()

        summary = run_summary_relevance_block("summary-run", session)
        assert summary["ghost_market_count"] == 1
        assert summary["alert_count"] >= 1
        assert "1 ghost" in summary["ghost_market_print"]
    finally:
        session.close()


def test_opportunities_filter_empty_run_returns_empty_list() -> None:
    session = _build_session()
    try:
        opportunities = get_opportunities_for_display("no-run", session)
        assert opportunities == []
    finally:
        session.close()


def test_opportunities_filter_none_db_returns_empty_list() -> None:
    assert get_opportunities_for_display("any-run", None) == []


def test_ghost_filter_handles_null_and_legacy_rows() -> None:
    """REG-37: Ghost filter excludes TRUE only; NULL/FALSE legacy rows remain visible."""
    session = _build_session()
    try:
        niche = Niche(slug="legacy-ghost", name="Legacy Ghost", category_path="x/y")
        session.add(niche)
        session.commit()
        ghost_kw = Keyword(
            niche_id=niche.id,
            keyword="ghost-row",
            normalized_keyword="ghost-row",
            ghost_market_flag=True,
        )
        non_ghost_kw = Keyword(
            niche_id=niche.id,
            keyword="non-ghost-row",
            normalized_keyword="non-ghost-row",
            ghost_market_flag=False,
        )
        legacy_null_kw = Keyword(
            niche_id=niche.id,
            keyword="legacy-null-row",
            normalized_keyword="legacy-null-row",
            ghost_market_flag=None,
        )
        session.add_all([ghost_kw, non_ghost_kw, legacy_null_kw])
        session.commit()
        session.add_all(
            [
                ResultSetValidation(
                    keyword_id=ghost_kw.id,
                    run_id="run-reg-37",
                    ghost_market_flag=True,
                ),
                ResultSetValidation(
                    keyword_id=non_ghost_kw.id,
                    run_id="run-reg-37",
                    ghost_market_flag=False,
                ),
                ResultSetValidation(
                    keyword_id=legacy_null_kw.id,
                    run_id="run-reg-37",
                    ghost_market_flag=False,
                ),
            ]
        )
        session.commit()

        opportunities = get_opportunities_for_display("run-reg-37", session, show_ghost_markets=False)
        ids = {row.keyword_id for row in opportunities}
        assert ghost_kw.id not in ids, "ghost=True must be hidden"
        assert non_ghost_kw.id in ids, "ghost=False must be visible"
        assert legacy_null_kw.id in ids, "ghost=NULL must be visible (legacy rows)"
    finally:
        session.close()
