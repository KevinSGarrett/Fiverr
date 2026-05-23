"""Integration test for Stage 14 E05 recommendation pipeline."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, Mock

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from src.models import Base, GigQualityScore, Keyword, KeywordScore, Niche
from src.recommendations import context_builder as context_builder_module
from src.recommendations import eligibility as eligibility_module
from src.recommendations.pipeline import run_recommendations_pipeline
from src.recommendations.schemas import RecommendationOutput


class OpportunityRanking(Base):
    """Test-only ranking model used to validate Stage 14 ranking path."""

    __tablename__ = "opportunity_rankings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    keyword_id: Mapped[int] = mapped_column(Integer, index=True)
    tag: Mapped[str] = mapped_column(String(32))
    final_score: Mapped[float] = mapped_column(Float)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def _seed_keyword(db: Session, *, keyword_id: int, run_id: str) -> None:
    niche = db.query(Niche).filter(Niche.id == 1).first()
    if niche is None:
        db.add(Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation"))
        db.flush()

    db.add(
        Keyword(
            id=keyword_id,
            niche_id=1,
            keyword=f"keyword-{keyword_id}",
            normalized_keyword=f"keyword-{keyword_id}",
        )
    )
    db.add(
        KeywordScore(
            keyword_id=keyword_id,
            scoring_profile="default",
            score_depth="standard",
            demand_score=68.0,
            competition_score=42.0,
            opportunity_score=75.0,
            feasibility_score=64.0,
            saturation_score=36.0,
            final_score=81.0,
            confidence_modifier=0.72,
            tag="STRONG GO",
        )
    )
    db.add(
        OpportunityRanking(
            run_id=run_id,
            keyword_id=keyword_id,
            tag="STRONG GO",
            final_score=81.0,
        )
    )
    db.add(
        GigQualityScore(
            keyword_id=keyword_id,
            gig_url=f"https://fiverr.com/gig/{keyword_id}",
            run_id=run_id,
            analysis_complete=True,
        )
    )


def test_e05_pipeline_processes_three_eligible_keywords(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-int-e05"
    _seed_keyword(db, keyword_id=101, run_id=run_id)
    _seed_keyword(db, keyword_id=102, run_id=run_id)
    _seed_keyword(db, keyword_id=103, run_id=run_id)
    db.commit()

    generate_mock = AsyncMock(
        return_value=RecommendationOutput(
            generation_complete=False,
            failed_tasks=["dry_run"],
            total_llm_cost_usd=0.11,
        )
    )
    save_mock = Mock(return_value="saved")
    monkeypatch.setattr(
        eligibility_module,
        "_model_by_name",
        lambda name: OpportunityRanking if name == "OpportunityRanking" else None,
    )
    monkeypatch.setattr(
        context_builder_module,
        "_model_by_name",
        lambda name: OpportunityRanking if name == "OpportunityRanking" else None,
    )
    monkeypatch.setattr("src.recommendations.pipeline.generate_recommendation_async", generate_mock)
    monkeypatch.setattr("src.recommendations.pipeline.save_recommendation", save_mock)

    result = asyncio.run(
        run_recommendations_pipeline(
            run_id=run_id,
            db=db,
            config={"recommendations": {"min_tag": "CONDITIONAL GO"}},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert result["eligible"] == 3
    assert result["generated"] == 3
    assert result["failed"] == 0
    assert generate_mock.await_count == 3
    assert save_mock.call_count == 3
    db.close()
