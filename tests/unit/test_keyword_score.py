"""Unit tests for KeywordScore ORM model and scoring write path."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from src.models import Base, Keyword, KeywordScore, Niche
from src.models.keyword_score import get_latest_keyword_score
from src.scoring.pipeline import write_keyword_score


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory()


def _seed_keyword(session: Session) -> int:
    niche = Niche(slug="ks-test", name="Keyword Score Tests", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()
    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automations",
        normalized_keyword="python automations",
        metadata_json={},
    )
    session.add(keyword)
    session.commit()
    return int(keyword.id)


def test_keyword_score_table_name() -> None:
    assert KeywordScore.__tablename__ == "keyword_scores"


def test_keyword_score_create_all() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    assert "keyword_scores" in inspect(engine).get_table_names()


def test_keyword_score_insert_minimal() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    row = KeywordScore(keyword_id=keyword_id, scoring_profile="default", score_depth="standard")
    session.add(row)
    session.commit()
    fetched = session.query(KeywordScore).filter(KeywordScore.keyword_id == keyword_id).first()
    assert fetched is not None
    assert fetched.keyword_id == keyword_id
    session.close()


def test_keyword_score_insert_full() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    row = KeywordScore(
        keyword_id=keyword_id,
        scoring_profile="aggressive_new_seller",
        score_depth="full",
        scored_at=datetime.now(UTC),
        data_as_of=datetime.now(UTC) - timedelta(hours=12),
        demand_score=77.0,
        competition_score=55.0,
        opportunity_score=66.0,
        feasibility_score=88.0,
        profitability_score=61.0,
        intent_score=69.0,
        saturation_score=47.0,
        weakness_score=58.0,
        trend_score=72.0,
        final_score=73.0,
        confidence_modifier=0.91,
        tag="STRONG_GO",
        score_components={"demand_score": {"weight": 0.2, "value": 77.0}},
        confidence_breakdown={"remaining_modifier": 0.91},
        explanation_text="High feasibility and demand.",
        red_flags=[{"flag": "High competition", "severity": "MEDIUM"}],
        missing_data_warnings=[],
        source_evidence=["search_results", "external_signals"],
        llm_inputs_used={"score_explanation": True},
        niche_tier="tier1_full",
    )
    session.add(row)
    session.commit()
    assert row.id is not None
    session.close()


def test_keyword_score_nullable_json_fields() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    row = KeywordScore(
        keyword_id=keyword_id,
        scoring_profile="default",
        score_depth="standard",
        score_components=None,
        red_flags=None,
    )
    session.add(row)
    session.commit()
    assert row.score_components is None
    assert row.red_flags is None
    session.close()


def test_keyword_score_upsert_via_merge() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    base = KeywordScore(keyword_id=keyword_id, scoring_profile="default", score_depth="standard", final_score=40.0)
    session.add(base)
    session.commit()
    merged = KeywordScore(
        id=base.id,
        keyword_id=keyword_id,
        scoring_profile="default",
        score_depth="standard",
        final_score=90.0,
    )
    session.merge(merged)
    session.commit()
    refreshed = session.get(KeywordScore, base.id)
    assert refreshed is not None
    assert refreshed.final_score == 90.0
    session.close()


def test_write_keyword_score_orm_path() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    ok = write_keyword_score(
        keyword_id=keyword_id,
        scores={"demand_score": 80.0, "competition_score": 20.0},
        weighted_composite=79.0,
        confidence_modifier=0.9,
        final_score=71.1,
        tag="CONDITIONAL_GO",
        score_components={"demand_score": {"weight": 0.2, "value": 80.0}},
        confidence_breakdown={"remaining_modifier": 0.9},
        explanation_text="Strong demand, manageable competition.",
        red_flags=[],
        scoring_profile="default",
        score_depth="standard",
        db=session,
    )
    assert ok is True
    session.close()


def test_write_keyword_score_orm_persists() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    write_keyword_score(
        keyword_id=keyword_id,
        scores={"demand_score": 55.0, "competition_score": 45.0},
        weighted_composite=60.0,
        confidence_modifier=0.75,
        final_score=45.0,
        tag="MONITOR",
        score_components={},
        confidence_breakdown={},
        explanation_text="Balanced signals.",
        red_flags=[],
        scoring_profile="default",
        score_depth="standard",
        db=session,
    )
    row = session.query(KeywordScore).filter(KeywordScore.keyword_id == keyword_id).first()
    assert row is not None
    assert row.tag == "MONITOR"
    session.close()


def test_write_keyword_score_sidecar_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.scoring import pipeline

    monkeypatch.setattr(pipeline, "_SIDE_CAR_DIR", tmp_path)
    ok = write_keyword_score(
        keyword_id=222,
        scores={"demand_score": 10.0},
        weighted_composite=10.0,
        confidence_modifier=1.0,
        final_score=10.0,
        tag="PASS",
        score_components={},
        confidence_breakdown={},
        explanation_text="fallback",
        red_flags=[],
        scoring_profile="default",
        score_depth="standard",
        db={},
    )
    assert ok is True
    assert (tmp_path / "222.json").exists()


def test_get_latest_keyword_score_returns_newest() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    older = datetime.now(UTC) - timedelta(hours=1)
    newer = datetime.now(UTC)
    session.add(KeywordScore(keyword_id=keyword_id, scoring_profile="default", score_depth="standard", scored_at=older))
    session.add(
        KeywordScore(
            keyword_id=keyword_id,
            scoring_profile="default",
            score_depth="standard",
            scored_at=newer,
            final_score=88.0,
        )
    )
    session.commit()
    latest = get_latest_keyword_score(keyword_id=keyword_id, db=session)
    assert latest is not None
    assert latest.final_score == 88.0
    session.close()


def test_get_latest_keyword_score_none_for_missing() -> None:
    session = _session()
    assert get_latest_keyword_score(keyword_id=999999, db=session) is None
    session.close()


def test_get_latest_keyword_score_none_for_non_session_db() -> None:
    assert get_latest_keyword_score(keyword_id=1, db=object()) is None


def test_keyword_score_index_exists() -> None:
    names = {index.name for index in KeywordScore.__table__.indexes}
    assert "ix_keyword_scores_keyword_scored_at" in names


def test_keyword_score_unique_constraint() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    fixed_scored_at = datetime(2026, 1, 1, tzinfo=UTC)
    session.add(
        KeywordScore(
            keyword_id=keyword_id,
            scoring_profile="default",
            score_depth="standard",
            scored_at=fixed_scored_at,
        )
    )
    session.commit()
    session.add(
        KeywordScore(
            keyword_id=keyword_id,
            scoring_profile="default",
            score_depth="full",
            scored_at=fixed_scored_at,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
    session.close()


def test_keyword_score_all_score_fields_nullable() -> None:
    session = _session()
    keyword_id = _seed_keyword(session)
    row = KeywordScore(
        keyword_id=keyword_id,
        scoring_profile="default",
        score_depth="standard",
        demand_score=None,
        competition_score=None,
        opportunity_score=None,
        feasibility_score=None,
        profitability_score=None,
        intent_score=None,
        saturation_score=None,
        weakness_score=None,
        trend_score=None,
        final_score=None,
        confidence_modifier=None,
    )
    session.add(row)
    session.commit()
    assert row.id is not None
    session.close()
