"""Unit tests for expanded SQLAlchemy foundation models."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.models import Base, naming_convention
from src.models.analysis import AnalysisResult, AnalysisRun
from src.models.database import (
    build_engine,
    create_session_factory,
    get_session,
    initialize_database,
)
from src.models.market import ExternalSignal, Gig, Keyword, Review, SearchResult, Seller
from src.models.niche import Niche, NicheConfigRecord
from src.models.runtime import RunLog
from src.models.scoring import FinalScore, Recommendation, ScoreComponent


def _init_session(tmp_path: Path, name: str) -> tuple[Session, Path]:
    db_path = tmp_path / name
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = initialize_database(database_url=db_url)
    session_factory = create_session_factory(engine)
    return session_factory(), db_path


def test_model_imports_do_not_create_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_engine(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("create_engine should not be called during model import")

    monkeypatch.setattr(sqlalchemy, "create_engine", _fail_engine)
    import src.models.base as base_module

    importlib.reload(base_module)


def test_timestamp_mixin_sets_non_null_timestamps_after_insert(tmp_path: Path) -> None:
    session, _ = _init_session(tmp_path, "timestamps.db")

    record = NicheConfigRecord(
        niche_id="ts_case",
        name="Timestamp Case",
        depth="standard",
        category_path="programming-tech/timestamps",
    )
    session.add(record)
    session.commit()
    session.refresh(record)

    assert record.created_at is not None
    assert record.updated_at is not None

    session.close()


def test_metadata_naming_convention_and_unique_table_names() -> None:
    assert naming_convention["pk"] == "pk_%(table_name)s"
    assert "fk" in naming_convention

    table_names = list(Base.metadata.tables.keys())
    assert len(table_names) == len(set(table_names))


def test_create_all_builds_expanded_table_set(tmp_path: Path) -> None:
    db_path = tmp_path / "expanded_tables.db"
    engine = build_engine(f"sqlite:///{db_path.as_posix()}")
    initialize_database(engine=engine)

    table_names = set(inspect(engine).get_table_names())
    required = {
        "niche_configs",
        "niches",
        "keywords",
        "search_results",
        "gigs",
        "sellers",
        "reviews",
        "external_signals",
        "analysis_runs",
        "analysis_results",
        "score_components",
        "final_scores",
        "recommendations",
        "run_logs",
    }
    assert required.issubset(table_names)


def test_market_entities_insert_and_query_roundtrip(tmp_path: Path) -> None:
    session, _ = _init_session(tmp_path, "market_roundtrip.db")

    niche = Niche(slug="ai-saas", name="AI SaaS", category_path="programming-tech/ai-saas")
    session.add(niche)
    session.flush()

    keyword = Keyword(niche_id=niche.id, keyword="ai saas mvp", normalized_keyword="ai saas mvp")
    session.add(keyword)
    session.flush()

    seller = Seller(seller_handle="seller_001", display_name="Seller One")
    session.add(seller)
    session.flush()

    gig = Gig(
        seller_id=seller.id,
        external_gig_id="gig_001",
        title="I will build your SaaS MVP",
        normalized_title="i will build your saas mvp",
    )
    session.add(gig)
    session.flush()

    search_result = SearchResult(keyword_id=keyword.id, rank=1, title="Top result", gig_id=gig.id)
    review = Review(gig_id=gig.id, rating=5.0, review_text="Excellent")
    signal = ExternalSignal(
        source_name="google-trends",
        signal_type="interest",
        keyword_id=keyword.id,
        raw_value_json={"score": 74},
        normalized_value=0.74,
    )
    session.add_all([search_result, review, signal])
    session.commit()

    fetched_keyword = session.execute(
        select(Keyword).where(Keyword.normalized_keyword == "ai saas mvp")
    ).scalar_one()
    fetched_signal = session.execute(select(ExternalSignal)).scalar_one()
    fetched_review = session.execute(select(Review)).scalar_one()

    assert fetched_keyword.niche_id == niche.id
    assert fetched_signal.raw_value_json["score"] == 74
    assert fetched_review.gig_id == gig.id

    # Nullable sparse data should be accepted in early collection cycles.
    sparse_gig = Gig(title="Sparse Gig")
    session.add(sparse_gig)
    session.commit()

    session.close()


def test_keyword_unique_constraint_per_niche(tmp_path: Path) -> None:
    session, _ = _init_session(tmp_path, "keyword_unique.db")

    niche = Niche(slug="qa", name="QA", category_path="programming-tech/qa")
    session.add(niche)
    session.flush()

    session.add_all(
        [
            Keyword(niche_id=niche.id, keyword="test automation", normalized_keyword="test automation"),
            Keyword(niche_id=niche.id, keyword="test automation", normalized_keyword="test automation"),
        ]
    )

    with pytest.raises(IntegrityError):
        session.commit()

    session.close()


def test_analysis_scoring_runtime_insert_and_json_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "analysis_scoring.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    engine = initialize_database(database_url=db_url)
    session_factory = create_session_factory(engine)

    with get_session(session_factory) as session:
        run = AnalysisRun(mode="full", run_label="integration")
        session.add(run)
        session.flush()

        result = AnalysisResult(
            run_id=run.id,
            analysis_type="market-gap",
            confidence=0.88,
            raw_json={"gaps": ["pricing", "positioning"]},
        )
        component = ScoreComponent(
            run_id=run.id,
            score_name="opportunity",
            score_value=0.8,
            raw_json={"details": {"trend": "up"}},
        )
        final_score = FinalScore(run_id=run.id, final_score=0.82, raw_json={"weights": {"trend": 0.2}})
        recommendation = Recommendation(
            run_id=run.id,
            recommendation_type="focus-keyword",
            recommendation_text="Prioritize transactional long-tail terms.",
            raw_json={"keyword": "ai saas mvp"},
        )
        run_log = RunLog(run_id=run.id, mode="full", stage="analysis", message="Analysis stage complete")

        session.add_all([result, component, final_score, recommendation, run_log])

    with get_session(session_factory) as session:
        result = session.execute(select(AnalysisResult)).scalar_one()
        component = session.execute(select(ScoreComponent)).scalar_one()
        recommendation = session.execute(select(Recommendation)).scalar_one()

        assert result.raw_json["gaps"][0] == "pricing"
        assert component.raw_json["details"]["trend"] == "up"
        assert recommendation.raw_json["keyword"] == "ai saas mvp"
