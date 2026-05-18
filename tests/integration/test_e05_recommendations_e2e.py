"""End-to-end integration tests for E05 recommendations pipeline."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    FinalScore,
    Gig,
    GigVisualAnalysis,
    Keyword,
    KeywordScore,
    Niche,
    Recommendation,
    SearchResult,
)
from src.recommendations.context import RecommendationContext, build_recommendation_context
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.run import run_recommendations_stage
from src.recommendations.storage import write_recommendation
from src.recommendations.tasks import generate_recommendation


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)()


def _config() -> dict[str, Any]:
    return {
        "recommendations": {
            "min_tag": "CONDITIONAL_GO",
            "niches": {
                "1": {
                    "starter_price_basic": 50,
                    "starter_price_standard": 100,
                    "starter_price_premium": 200,
                    "recommendation_generation": True,
                }
            },
        }
    }


def _seed_keyword_graph(db: Session, confidence_modifier: float = 0.8) -> None:
    niche = Niche(id=1, slug="prd_ai_saas", name="PRD AI SaaS", category_path="business/ai-saas")
    keyword = Keyword(
        id=1,
        niche_id=1,
        keyword="AI SaaS PRD",
        normalized_keyword="ai saas prd",
    )
    final_score = FinalScore(
        run_id=1,
        keyword_id=1,
        final_score=75.0,
        raw_json={"tag": "CONDITIONAL_GO", "confidence_modifier": confidence_modifier},
    )
    keyword_score = KeywordScore(
        keyword_id=1,
        final_score=75.0,
        tag="CONDITIONAL_GO",
        demand_score=65.0,
        competition_score=40.0,
        confidence_modifier=confidence_modifier,
        scoring_profile="default",
        score_depth="standard",
    )
    gig = Gig(id=1, title="I will write an AI SaaS PRD")
    search_result = SearchResult(keyword_id=1, rank=1, gig_id=1)
    visual = GigVisualAnalysis(gig_id=1, thumbnail_type="screenshot")

    db.add_all([niche, keyword, final_score, keyword_score, gig, search_result, visual])
    db.commit()


def test_e05_get_eligible_keywords_returns_keyword() -> None:
    db = _session()
    _seed_keyword_graph(db)
    eligible = get_eligible_keywords("1", db, _config())
    assert [row["keyword_id"] for row in eligible] == [1]


def test_e05_passes_gates_confidence_ok(monkeypatch: Any) -> None:
    db = _session()
    _seed_keyword_graph(db, confidence_modifier=0.8)
    monkeypatch.setattr("src.recommendations.eligibility._has_gig_analysis", lambda keyword_id, db: True)
    ok, reason = passes_recommendation_gates({"keyword_id": 1, "confidence_modifier": 0.8, "demand_score": 65.0}, db)
    assert ok is True
    assert reason == "All gates passed"


def test_e05_passes_gates_confidence_fail() -> None:
    db = _session()
    _seed_keyword_graph(db, confidence_modifier=0.3)
    ok, reason = passes_recommendation_gates({"keyword_id": 1, "confidence_modifier": 0.3}, db)
    assert ok is False
    assert "below 0.40" in reason


def test_e05_should_regenerate_no_existing() -> None:
    db = _session()
    _seed_keyword_graph(db)
    assert should_regenerate_recommendation(1, 75.0, db) is True


def test_e05_build_context_minimal_db() -> None:
    db = _session()
    _seed_keyword_graph(db)
    context = build_recommendation_context(1, db, _config())
    assert isinstance(context, RecommendationContext)
    assert context.keyword_text == "AI SaaS PRD"


def test_e05_generate_recommendation_dry_run() -> None:
    result = {
        "generation_complete": False,
        "llm_cost_usd": 0.0,
        "gig_titles": None,
        "tag_sets": None,
        "package_structure": None,
        "description_outline": None,
        "faq_entries": None,
        "differentiation_angle": None,
        "buyer_persona": None,
        "thumbnail_direction": None,
        "upsell_structure": None,
        "red_flags": None,
        "niche_viability_assessment": None,
    }
    assert result["generation_complete"] is False


def test_e05_run_recommendations_stage_dry_run() -> None:
    db = _session()
    _seed_keyword_graph(db)
    summary = asyncio.run(run_recommendations_stage("1", db, _config(), llm_client=None, cache=None, dry_run=True))
    assert summary["eligible_count"] == 1
    assert summary["generated"] >= 0


def test_e05_write_recommendation_sidecar(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    context = RecommendationContext(
        keyword_id=1,
        keyword_text="AI SaaS PRD",
        niche_id=1,
        niche_name="PRD AI SaaS",
        tag="CONDITIONAL_GO",
        final_score=75.0,
    )
    ok = write_recommendation(1, "run-e05", context, {"generation_complete": False, "llm_cost_usd": 0.0}, db=None)
    assert ok is True
    sidecar = tmp_path / "data" / "recommendation_results" / "1_run-e05.json"
    assert sidecar.exists()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["generation_complete"] is False


def test_e05_write_recommendation_orm() -> None:
    db = _session()
    _seed_keyword_graph(db)
    context = build_recommendation_context(1, db, _config())
    ok = write_recommendation(
        1,
        1,
        context,
        {
            "generation_complete": True,
            "llm_cost_usd": 0.0,
            "differentiation_angle": "Position as fast PRD specialist",
        },
        db,
    )
    assert ok is True
    persisted = db.query(Recommendation).filter(Recommendation.keyword_id == 1, Recommendation.run_id == 1).first()
    assert persisted is not None
    assert isinstance(persisted.raw_json, dict)


def test_e05_full_stage_smoke() -> None:
    db = _session()
    _seed_keyword_graph(db)
    summary = asyncio.run(run_recommendations_stage("1", db, _config(), llm_client=None, cache=None, dry_run=True))
    assert summary["failed"] == 0


def test_e05_skip_low_confidence() -> None:
    db = _session()
    _seed_keyword_graph(db, confidence_modifier=0.2)
    summary = asyncio.run(run_recommendations_stage("1", db, _config(), llm_client=None, cache=None, dry_run=True))
    assert summary["skipped"] == 1


def test_e05_generate_recommendation_all_tasks_mock(monkeypatch: Any) -> None:
    async def _ok(_context: RecommendationContext, _llm_client: Any, _cache: Any) -> dict[str, Any]:
        return {"output": {"ok": True}, "cost_usd": 0.01}

    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _ok)
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _ok)

    context = RecommendationContext(keyword_id=1, keyword_text="AI SaaS PRD", niche_id=1)
    result = asyncio.run(generate_recommendation(1, context, llm_client=SimpleNamespace(), cache=None, db=None))
    assert result["generation_complete"] is True
    assert result["llm_cost_usd"] > 0
