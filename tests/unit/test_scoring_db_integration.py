"""Integration tests for SQLAlchemy-backed scoring calculator paths."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    ExternalSignal,
    Gig,
    GigVisualAnalysis,
    Keyword,
    Niche,
    SearchResult,
    Seller,
)
from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.orchestrator import ScoringOrchestrator
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator


def _session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _seed_keyword_data(session: Session) -> int:
    niche = Niche(slug="automation", name="Automation", category_path="Programming & Tech > AI")
    session.add(niche)
    session.flush()

    keyword = Keyword(
        niche_id=niche.id,
        keyword="python automation",
        normalized_keyword="python automation",
        metadata_json={"autocomplete_position": 2, "intent_classification": "HIGH_INTENT"},
    )
    session.add(keyword)
    session.flush()

    for rank in range(1, 11):
        seller = Seller(
            seller_handle=f"seller_{rank}",
            level="Level 1" if rank <= 5 else "Level 2",
            metadata_json={"is_pro": rank in {1, 2}},
        )
        session.add(seller)
        session.flush()
        gig = Gig(
            seller_id=seller.id,
            title=f"I will automate task {rank}",
            normalized_title=f"automate task {rank if rank <= 8 else 8}",
            starting_price=30.0 + rank,
            review_count=50 + (rank * 20),
            metadata_json={
                "premium_price": 120.0 + rank,
                "delivery_time_days": 1 + (rank % 3),
                "extras": [{"name": "fast_delivery"}] if rank % 2 == 0 else [],
                "has_portfolio": rank % 3 != 0,
            },
        )
        session.add(gig)
        session.flush()
        search_result = SearchResult(
            keyword_id=keyword.id,
            rank=rank,
            gig_id=gig.id,
            title=gig.title,
        )
        session.add(search_result)
        if rank <= 6:
            session.add(GigVisualAnalysis(gig_id=gig.id, has_video=(rank % 2 == 0)))

    session.add(
        ExternalSignal(
            source_name="google",
            signal_type="google_trends",
            keyword_id=keyword.id,
            raw_value_json={
                "trends_12mo_score": 64,
                "trends_3mo_score": 70,
                "trends_3mo_avg": 68,
                "trends_12mo_avg": 60,
                "google_trends_12mo_series": [45, 48, 50, 54, 58, 62, 64, 66, 67, 68, 69, 70],
                "google_trends_3mo_series": [66, 68, 70],
            },
            normalized_value=64.0,
        )
    )
    session.add(
        ExternalSignal(
            source_name="reddit",
            signal_type="reddit_demand",
            keyword_id=keyword.id,
            raw_value_json={
                "reddit_demand_intent_score": 7.5,
                "reddit_recent_post_volume": 20,
                "reddit_historical_post_volume": 15,
                "reddit_activity_trend_score": 62,
            },
            normalized_value=7.5,
        )
    )
    session.commit()
    return keyword.id


def test_demand_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = DemandScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_competition_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = CompetitionScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_opportunity_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = OpportunityScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_feasibility_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = NewSellerFeasibilityCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_profitability_calculator_sqlalchemy_path_returns_score() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    result = ProfitabilityScoreCalculator().calculate(keyword_id, session)
    assert result.score_value is not None
    session.close()


def test_intent_saturation_weakness_trend_sqlalchemy_paths_return_scores() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    assert ConversionIntentScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert SaturationScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert GigQualityWeaknessScoreCalculator().calculate(keyword_id, session).score_value is not None
    assert TrendScoreCalculator().calculate(keyword_id, session).score_value is not None
    session.close()


def test_confidence_modifier_sqlalchemy_context_returns_clamped_value() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    modifier = ConfidenceScoreModifier().calculate(keyword_id, None, session)
    assert 0.0 <= modifier <= 1.0
    session.close()


def test_orchestrator_run_with_sqlalchemy_session_returns_result() -> None:
    session = next(_session())
    keyword_id = _seed_keyword_data(session)
    run_result = ScoringOrchestrator().run([keyword_id], session)
    assert run_result.keyword_results
    assert run_result.keyword_results[0]["final_payload"]["final_score"] >= 0.0
    session.close()


def test_dict_proxy_path_still_works_after_sqlalchemy_changes() -> None:
    keyword_id = 999
    db_proxy = {
        keyword_id: {
            "total_result_count": 800,
            "autocomplete_position": 1,
            "trends_12mo_score": 60,
            "reddit_demand_intent_score": 7.0,
        }
    }
    result = DemandScoreCalculator().calculate(keyword_id, db_proxy)
    assert result.score_value is not None


def test_missing_keyword_id_returns_none_score_gracefully() -> None:
    session = next(_session())
    result = DemandScoreCalculator().calculate(123456, session)
    assert result.score_value is None
    session.close()
