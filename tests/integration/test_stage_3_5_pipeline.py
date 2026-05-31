"""Integration tests for Stage 3.5 result-set validation workflow."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.collection.workflows import result_set_validation_workflow as workflow
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
    assert set(stats.keys()) == {"keywords_validated", "ghost_markets_detected", "contamination_flags"}


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


def test_gig_flag_set_true_for_relevant_match(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    gig = scratch_db.query(Gig).filter(Gig.gig_url.like("%clean-0%")).first()
    assert gig is not None
    assert gig.relevance_flag is True
    assert gig.relevance_score is not None


def test_gig_flag_set_false_for_irrelevant_match(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    gig = scratch_db.query(Gig).filter(Gig.gig_url.like("%clean-off%")).first()
    assert gig is not None
    assert gig.relevance_flag is False
    assert gig.relevance_score is not None


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
    clean_row = scratch_db.query(SearchResult).filter_by(keyword_id=1001, run_id="run-1").first()
    assert clean_row is not None
    clean_row.gig_cards = [{"gig_title": "logo design", "gig_url": f"https://www.fiverr.com/gigs/clean-mut-{i}"} for i in range(10)]
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    n2 = scratch_db.query(ResultSetValidation).filter_by(run_id="run-1").count()
    updated = scratch_db.query(ResultSetValidation).filter_by(keyword_id=1001, run_id="run-1").first()
    assert n1 == n2
    assert updated is not None
    assert updated.result_set_relevance_score == 0.0
    assert updated.ghost_market_flag is True


def test_fail_soft_one_bad_keyword(
    scratch_db: Session,
    sample_config_on: dict,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    original = workflow.validate_result_set

    def _boom_once(cards, keyword_text, niche_id, validation_config):  # type: ignore[no-untyped-def]
        if len(cards) >= 10 and "ghost" in cards[0]["gig_url"]:
            raise RuntimeError("simulated keyword failure")
        return original(cards, keyword_text, niche_id, validation_config)

    monkeypatch.setattr(workflow, "validate_result_set", _boom_once)
    with caplog.at_level(logging.WARNING):
        stats = run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    assert stats["keywords_validated"] == 1
    assert any("stage_3_5 keyword" in rec.message for rec in caplog.records)


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


def test_link_search_result_sets_rsv_id_for_clean_keyword(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    sr = scratch_db.query(SearchResult).filter_by(keyword_id=1001, run_id="run-1").first()
    assert sr is not None
    assert sr.rsv_id is not None


def test_write_gig_flags_tolerant_url_match_query_protocol_and_trailing_slash(
    scratch_db: Session,
    sample_config_on: dict,
) -> None:
    target = scratch_db.query(Gig).filter_by(run_id="run-1").filter(Gig.gig_url.like("%clean-0%")).first()
    assert target is not None
    target.gig_url = "http://www.fiverr.com/gigs/clean-0/?ref=abc"
    scratch_db.commit()

    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    scratch_db.refresh(target)
    assert target.relevance_flag is True
    assert target.relevance_score is not None


def test_url_match_ignores_query_and_protocol() -> None:
    assert workflow._normalize_url("http://www.fiverr.com/gigs/example?ref=abc") == workflow._normalize_url(
        "https://www.fiverr.com/gigs/example/"
    )


def test_gig_with_no_match_left_unchanged(scratch_db: Session, sample_config_on: dict) -> None:
    stray = Gig(
        gig_url="https://www.fiverr.com/gigs/not-in-result-set",
        keyword_id=1001,
        run_id="run-1",
        seller_username="stray",
        title="stray listing",
        normalized_title="stray listing",
        relevance_flag=None,
        relevance_score=None,
    )
    scratch_db.add(stray)
    scratch_db.commit()
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    scratch_db.refresh(stray)
    assert stray.relevance_flag is None
    assert stray.relevance_score is None


def test_used_fallback_strictness_true_when_relaxed(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    clean = scratch_db.query(ResultSetValidation).filter_by(keyword_id=1001, run_id="run-1").first()
    ghost = scratch_db.query(ResultSetValidation).filter_by(keyword_id=GHOST_KW, run_id="run-1").first()
    assert clean is not None and ghost is not None
    assert clean.search_strictness_used == "SUBCATEGORY"
    assert clean.used_fallback_strictness is False
    assert ghost.search_strictness_used == "NONE"
    assert ghost.used_fallback_strictness is True


def test_stats_dict_counts_ghost_and_contamination(scratch_db: Session, sample_config_on: dict) -> None:
    contaminated_keyword = Keyword(
        id=1003,
        niche_id=901,
        keyword="mcp server integration contamination",
        normalized_keyword="mcp server integration contamination",
    )
    scratch_db.add(contaminated_keyword)
    scratch_db.flush()
    mixed_cards = [
        {
            "gig_title": "mcp server integration contamination service",
            "gig_url": f"https://www.fiverr.com/gigs/mix-{i}",
        }
        for i in range(4)
    ]
    mixed_cards.extend([{"gig_title": "logo design", "gig_url": f"https://www.fiverr.com/gigs/mix-off-{i}"} for i in range(6)])
    scratch_db.add(
        SearchResult(
            keyword_id=1003,
            run_id="run-1",
            page_collected=1,
            rank=1,
            title="mixed",
            gig_cards=mixed_cards,
            search_strictness_used="SUBCATEGORY",
        )
    )
    scratch_db.commit()

    stats = run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    assert stats["keywords_validated"] == 3
    assert stats["ghost_markets_detected"] == 1
    assert stats["contamination_flags"] == 1


def test_per_gig_relevance_json_persisted(scratch_db: Session, sample_config_on: dict) -> None:
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    row = scratch_db.query(ResultSetValidation).filter_by(keyword_id=1001, run_id="run-1").first()
    assert row is not None
    assert isinstance(row.per_gig_relevance, list)
    assert len(row.per_gig_relevance) == 10
    first = row.per_gig_relevance[0]
    assert {"score", "flag", "reason"}.issubset(set(first.keys()))


def test_run_stage_3_5_skips_when_db_not_session(sample_config_on: dict) -> None:
    result = run_stage_3_5_validation("run-1", "mcp_servers", db=object(), config=sample_config_on)
    assert result == {"skipped": True}


def test_run_stage_3_5_works_with_object_config(scratch_db: Session) -> None:
    config = SimpleNamespace(
        relevance=SimpleNamespace(
            enable_stage_3_5=True,
            relevance_flag_threshold=0.35,
            ghost_market_threshold_default=0.20,
        )
    )
    stats = run_stage_3_5_validation("run-1", "mcp_servers", db=scratch_db, config=config)
    assert stats["keywords_validated"] == 2


def test_enable_stage_3_5_off_matches_legacy_scores(scratch_db: Session, sample_config_on: dict) -> None:
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
    baseline_modifier, _ = ConfidenceScoreModifier().calculate_with_breakdown(
        keyword_id=1001,
        run_context=context,
        db=scratch_db,
    )
    run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, sample_config_on)
    with_stage35, _ = ConfidenceScoreModifier().calculate_with_breakdown(
        keyword_id=1001,
        run_context=context,
        db=scratch_db,
    )
    skipped = run_stage_3_5_validation("run-1", "mcp_servers", scratch_db, {"relevance": {"enable_stage_3_5": False}})
    after_off, _ = ConfidenceScoreModifier().calculate_with_breakdown(
        keyword_id=1001,
        run_context=context,
        db=scratch_db,
    )
    assert skipped == {"skipped": True}
    assert with_stage35 == baseline_modifier
    assert after_off == baseline_modifier


def test_competition_all_filtered_fallback_emits_warning(
    scratch_db: Session,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from src.scoring.competition import CompetitionScoreCalculator

    niche = Niche(id=902, slug="fallback_niche", name="Fallback Niche", category_path="Programming & Tech > AI")
    scratch_db.add(niche)
    scratch_db.flush()
    keyword = Keyword(id=2001, niche_id=niche.id, keyword="fallback keyword", normalized_keyword="fallback keyword")
    scratch_db.add(keyword)
    scratch_db.flush()
    for rank in range(1, 4):
        gig = Gig(
            gig_url=f"https://www.fiverr.com/fallback/{rank}",
            keyword_id=keyword.id,
            run_id="fallback-run",
            seller_username=f"fallback-seller-{rank}",
            title=f"fallback gig {rank}",
            normalized_title=f"fallback gig {rank}",
            relevance_flag=False,
            review_count=20,
            starting_price=10,
        )
        scratch_db.add(gig)
        scratch_db.flush()
        scratch_db.add(SearchResult(keyword_id=keyword.id, run_id="fallback-run", rank=rank, gig_id=gig.id, title=gig.title))
    scratch_db.add(
        ResultSetValidation(
            keyword_id=keyword.id,
            run_id="fallback-run",
            result_set_relevance_score=0.60,
            relevance_deduction=-0.05,
        )
    )
    scratch_db.commit()
    with caplog.at_level(logging.WARNING):
        result = CompetitionScoreCalculator().calculate(keyword.id, scratch_db)
    assert result.score_value is not None
    assert any("all gigs filtered by relevance" in rec.message for rec in caplog.records)
