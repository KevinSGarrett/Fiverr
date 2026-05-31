"""Integration tests for Stage 3.5 result-set validation workflow."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.collection.workflows.result_set_validation_workflow import run_stage_3_5_validation
from src.models import Base, Gig, Keyword, Niche, ResultSetValidation, SearchResult
from src.scoring.confidence import ConfidenceScoreModifier

GHOST_KW = 1002


@pytest.fixture
def scratch_db() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()

    niche = Niche(id=901, slug="mcp_servers", name="MCP", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()
    keyword_clean = Keyword(id=1001, niche_id=niche.id, keyword="mcp server integration", normalized_keyword="mcp server integration")
    keyword_ghost = Keyword(
        id=GHOST_KW,
        niche_id=niche.id,
        keyword="mcp server integration ghost",
        normalized_keyword="mcp server integration ghost",
    )
    session.add_all([keyword_clean, keyword_ghost])
    session.flush()

    clean_cards = [{"gig_title": "I will build mcp server integration", "gig_url": f"https://www.fiverr.com/gigs/clean-{i}"} for i in range(9)]
    clean_cards.append({"gig_title": "I will design logo", "gig_url": "https://www.fiverr.com/gigs/clean-off"})
    ghost_cards = [{"gig_title": "I will design logo", "gig_url": f"https://www.fiverr.com/gigs/ghost-{i}"} for i in range(11)]
    ghost_cards.append({"gig_title": "mcp server integration service", "gig_url": "https://www.fiverr.com/gigs/ghost-hit"})

    session.add(
        SearchResult(
            keyword_id=keyword_clean.id,
            run_id="run-1",
            page_collected=1,
            rank=1,
            title="clean",
            gig_cards=clean_cards,
            search_strictness_used="SUBCATEGORY",
        )
    )
    session.add(
        SearchResult(
            keyword_id=keyword_ghost.id,
            run_id="run-1",
            page_collected=1,
            rank=1,
            title="ghost",
            gig_cards=ghost_cards,
            search_strictness_used="NONE",
        )
    )

    for card in clean_cards + ghost_cards:
        session.add(
            Gig(
                gig_url=card["gig_url"],
                keyword_id=keyword_clean.id if "clean" in card["gig_url"] else keyword_ghost.id,
                run_id="run-1",
                seller_username="seller",
                title=card["gig_title"],
                normalized_title=card["gig_title"].lower(),
            )
        )
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_config_on() -> dict:
    return {
        "relevance": {
            "enable_stage_3_5": True,
            "relevance_flag_threshold": 0.35,
            "ghost_market_threshold_default": 0.20,
        }
    }


@pytest.fixture
def sample_config_off() -> dict:
    return {"relevance": {"enable_stage_3_5": False}}


def test_one_rsv_row_per_keyword_run(scratch_db: Session, sample_config_on: dict) -> None:
    stats = run_stage_3_5_validation(run_id="run-1", niche_id="mcp_servers", db=scratch_db, config=sample_config_on)
    rows = scratch_db.query(ResultSetValidation).filter_by(run_id="run-1").all()
    assert len(rows) == stats["keywords_validated"]


def test_ghost_keyword_links_ghost_rsv(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    sr = scratch_db.query(SearchResult).filter_by(keyword_id=GHOST_KW, run_id="run-1").first()
    assert sr is not None and sr.rsv_id is not None
    rsv = scratch_db.query(ResultSetValidation).filter(ResultSetValidation.id == sr.rsv_id).first()
    assert rsv is not None
    assert rsv.ghost_market_flag is True


def test_gig_flags_propagated(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    flagged = scratch_db.query(Gig).filter(Gig.relevance_flag.is_(True)).count()
    unflagged = scratch_db.query(Gig).filter(Gig.relevance_flag.is_(False)).count()
    assert flagged > 0
    assert unflagged > 0


def test_cm_deduction_reaches_final_scoring(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    modifier, breakdown = ConfidenceScoreModifier().calculate_with_breakdown(
        keyword_id=GHOST_KW,
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
        db=scratch_db,
    )
    assert breakdown["ghost_market"] == -0.50
    assert modifier == pytest.approx(0.5, abs=1e-4)


def test_upsert_updates_not_duplicates(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    n1 = scratch_db.query(ResultSetValidation).filter_by(run_id="run-1").count()
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    n2 = scratch_db.query(ResultSetValidation).filter_by(run_id="run-1").count()
    assert n1 == n2


def test_fail_soft_one_bad_keyword(scratch_db: Session, sample_config_on: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.collection.workflows import result_set_validation_workflow as workflow

    original = workflow.validate_result_set

    def _boom_once(cards, keyword_text, niche_id, validation_config):  # type: ignore[no-untyped-def]
        if len(cards) >= 10 and "ghost" in cards[0]["gig_url"]:
            raise RuntimeError("simulated keyword failure")
        return original(cards, keyword_text, niche_id, validation_config)

    monkeypatch.setattr(workflow, "validate_result_set", _boom_once)
    stats = run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    assert stats["keywords_validated"] == 1


def test_toggle_off_disables_stage_3_5(scratch_db: Session, sample_config_off: dict) -> None:
    stats = run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_off)
    assert stats == {"skipped": True}
    assert scratch_db.query(ResultSetValidation).filter_by(run_id="run-1").count() == 0


def test_backward_compat_no_rsv_equals_baseline(scratch_db: Session) -> None:
    context = {
        "data_completeness_ratio": 1.0,
        "data_freshness_score": 1.0,
        "source_diversity_score": 1.0,
        "llm_analysis_completion_ratio": 1.0,
        "google_trends_available": True,
        "gig_detail_collected": True,
        "seller_profiles_collected": True,
        "reddit_signals_available": True,
    }
    with_rsv_missing, breakdown_missing = ConfidenceScoreModifier().calculate_with_breakdown(
        keyword_id=1001,
        run_context=context,
        db=scratch_db,
    )
    assert with_rsv_missing == 1.0
    assert "result_set_relevance" not in breakdown_missing
    assert "ghost_market" not in breakdown_missing
