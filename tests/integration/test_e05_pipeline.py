"""Integration test for Stage 14 E05 recommendation pipeline."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from src.models import Base, GigQualityScore, Keyword, KeywordScore, Niche
from src.recommendations import context_builder as context_builder_module
from src.recommendations import eligibility as eligibility_module
from src.recommendations.contracts import RecommendationContext
from src.recommendations.export import export_recommendation_json, export_recommendation_markdown
from src.recommendations.pipeline import run_recommendations_pipeline
from src.recommendations.schemas import RecommendationOutput
from src.recommendations.storage import save_recommendation


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


def _complete_output() -> RecommendationOutput:
    return RecommendationOutput.model_validate(
        {
            "gig_titles": {
                "titles": [
                    {
                        "title": f"I will build automation workflow package option {index} with clear delivery scope",
                        "positioning_angle": "outcome-driven",
                        "character_count": 77,
                        "primary_keyword_present": True,
                    }
                    for index in range(1, 6)
                ]
            },
            "tag_sets": {
                "tag_sets": [
                    ["python automation", "workflow setup", "api scripts", "ops support", "task cleanup"],
                    ["automation audit", "crm workflow", "business ops", "fast delivery", "integration help"],
                    ["zapier flow", "notion setup", "saas operations", "custom scripts", "process design"],
                    ["ops automation", "workflow map", "growth systems", "delivery plan", "automation expert"],
                    ["team workflow", "process optimization", "task system", "backend support", "automation"],
                ]
            },
            "package_structure": {
                "basic": {
                    "name": "Starter Automation",
                    "price": 95,
                    "deliverables": ["scope review", "single workflow"],
                    "delivery_days": 3,
                    "revisions": 1,
                },
                "standard": {
                    "name": "Core Automation Build",
                    "price": 225,
                    "deliverables": ["workflow map", "two workflows", "handoff notes"],
                    "delivery_days": 5,
                    "revisions": 2,
                },
                "premium": {
                    "name": "Automation System Package",
                    "price": 395,
                    "deliverables": ["full workflow map", "four workflows", "training guide"],
                    "delivery_days": 7,
                    "revisions": 3,
                },
            },
            "description_outline": {
                "sections": [
                    {
                        "heading": "Outcome Hook",
                        "copy_direction": "Lead with reduced manual work and predictable delivery outcomes.",
                        "proof_elements": ["before-after summary"],
                        "estimated_words": 50,
                    },
                    {
                        "heading": "Scope",
                        "copy_direction": "List exactly what is delivered at each milestone.",
                        "proof_elements": ["milestone list"],
                        "estimated_words": 50,
                    },
                    {
                        "heading": "Process",
                        "copy_direction": "Explain implementation checkpoints and communication rhythm.",
                        "proof_elements": ["timeline", "status updates"],
                        "estimated_words": 50,
                    },
                    {
                        "heading": "Next Step",
                        "copy_direction": "Close with required buyer inputs and onboarding steps.",
                        "proof_elements": ["onboarding checklist"],
                        "estimated_words": 50,
                    },
                ]
            },
            "faq_entries": {
                "faq_entries": [
                    {
                        "question": "Can this work with my existing tools?",
                        "answer": "Yes. I map your stack first and only implement compatible workflow steps.",
                        "addresses_complaint": "tool fit",
                    },
                    {
                        "question": "What do you need to start?",
                        "answer": "I need process notes, access level, and the target outcome to start safely.",
                        "addresses_complaint": "onboarding clarity",
                    },
                    {
                        "question": "Do revisions include workflow tweaks?",
                        "answer": "Yes. Package revisions include agreed workflow adjustments within scope.",
                        "addresses_complaint": "revision policy",
                    },
                    {
                        "question": "How fast can you deliver?",
                        "answer": "Delivery depends on scope, but each package includes clear timeline milestones.",
                        "addresses_complaint": "timeline certainty",
                    },
                    {
                        "question": "What is excluded from this service?",
                        "answer": "Unrelated product development is excluded so delivery stays focused.",
                        "addresses_complaint": "scope clarity",
                    },
                ]
            },
            "differentiation_angle": {
                "positioning_statement": (
                    "Most competitors provide generic automation offers. This package emphasizes documented "
                    "handoff, practical implementation checkpoints, and reliable communication from kickoff."
                ),
                "differentiators": [
                    {
                        "action": "Send a structured implementation roadmap before work starts.",
                        "competitor_weakness_exploited": "Competitors often start without clear onboarding.",
                        "buyer_pain_addressed": "Buyers are unsure what happens after ordering.",
                    }
                ],
                "one_sentence_pitch": "I turn messy recurring tasks into reliable automation workflows.",
            },
            "buyer_persona": {
                "name": "Alex",
                "role": "Operations Manager",
                "company_stage": "Early growth SaaS",
                "pain_points": ["manual handoffs", "unclear ownership"],
                "budget_range": "$150-$500",
                "decision_trigger": "Delivery issues are slowing down customer onboarding.",
                "where_they_search": "Fiverr and operations communities",
                "what_makes_them_buy": "Clear scope, confidence, and predictable updates.",
            },
            "thumbnail_direction": {
                "concept": "Show before-versus-after process clarity with simple visual hierarchy.",
                "style": "Dark base palette with bright accent markers",
                "elements_to_include": ["workflow icons", "timeline", "checklist"],
                "elements_to_avoid": ["busy stock photos"],
                "differentiation_note": "Highlight concrete outcome metrics rather than generic promises.",
            },
            "upsell_structure": {
                "extras": [
                    {
                        "name": "Priority update",
                        "price": 25,
                        "description": "Priority response and update cycle within agreed scope.",
                    },
                    {
                        "name": "Post-launch tuning",
                        "price": 45,
                        "description": "Optimization review after launch week based on usage feedback.",
                    },
                ]
            },
            "red_flags": {
                "red_flags": [
                    {
                        "flag_type": "trust_gap",
                        "description": "Top competitors have extensive social proof and long review history.",
                        "severity": "MEDIUM",
                        "mitigation": "Lead with proof assets and specific onboarding deliverables.",
                    }
                ],
                "overall_risk_level": "MEDIUM",
                "proceed_recommendation": "Proceed with focused positioning and evidence-first messaging.",
            },
            "niche_viability": {
                "viability_assessment": (
                    "Demand and buyer intent remain healthy in this niche, and competitor gaps in onboarding "
                    "clarity create room for differentiated, process-first offers."
                ),
                "timing_assessment": "Timing is favorable while buyer demand remains stable.",
                "risk_summary": "Main risk is competing against established sellers with stronger authority.",
                "blunt_recommendation": "Enter with narrow scope and proof-based messaging now.",
            },
            "generation_complete": True,
            "total_llm_cost_usd": 0.321,
        }
    )


def _seed_complete_recommendation(db: Session, *, keyword_id: int, run_id: str) -> None:
    _seed_keyword(db, keyword_id=keyword_id, run_id=run_id)
    db.commit()

    context = RecommendationContext(
        keyword_id=keyword_id,
        keyword_text=f"keyword-{keyword_id}",
        niche_id="1",
        niche_name="Automation",
        run_id=run_id,
        tag="STRONG GO",
        final_score=84.2,
        confidence_modifier=0.88,
        top_competitor_weaknesses=[],
    )
    save_recommendation(context=context, output=_complete_output(), db=db)


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


def test_recommendations_only_with_auto_export_writes_files(monkeypatch: Any, tmp_path: Path) -> None:
    db = _session()
    run_id = "run-int-e05-export"
    _seed_keyword(db, keyword_id=901, run_id=run_id)
    db.commit()

    generate_mock = AsyncMock(
        return_value=RecommendationOutput(
            generation_complete=False,
            failed_tasks=["dry_run"],
            total_llm_cost_usd=0.09,
        )
    )
    save_mock = Mock(return_value="saved")
    export_mock = AsyncMock(return_value=("# Recommendation: keyword-901", None))

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
    monkeypatch.setattr("src.recommendations.pipeline.export_recommendation_by_keyword", export_mock)

    result = asyncio.run(
        run_recommendations_pipeline(
            run_id=run_id,
            db=db,
            config={
                "recommendations": {
                    "min_tag": "CONDITIONAL GO",
                    "auto_export_markdown": True,
                    "export_dir": str(tmp_path),
                }
            },
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )

    assert result["generated"] == 1
    assert len(result["export_paths"]) == 1
    export_path = Path(result["export_paths"][0])
    assert export_path.exists()
    assert export_path.read_text(encoding="utf-8") == "# Recommendation: keyword-901"
    db.close()


def test_markdown_export_end_to_end_with_complete_recommendation() -> None:
    db = _session()
    run_id = "run-int-e05-export-md"
    keyword_id = 981
    _seed_complete_recommendation(db, keyword_id=keyword_id, run_id=run_id)

    markdown = asyncio.run(export_recommendation_markdown(str(keyword_id), db=db))

    assert markdown.startswith("# Recommendation:")
    assert "## Viability Assessment" in markdown
    assert "## Gig Title Options" in markdown
    assert "## Packages" in markdown
    assert "## Differentiation Angle" in markdown
    assert "## FAQ" in markdown
    assert "## Buyer Persona" in markdown
    assert "## Thumbnail Direction" in markdown
    assert "## Red Flags" in markdown
    assert "**Completeness:** 100%" in markdown
    db.close()


def test_json_export_end_to_end_with_complete_recommendation() -> None:
    db = _session()
    run_id = "run-int-e05-export-json"
    keyword_id = 982
    _seed_complete_recommendation(db, keyword_id=keyword_id, run_id=run_id)

    exported = asyncio.run(export_recommendation_json(str(keyword_id), db=db))
    serialized = json.dumps(exported, indent=2)

    assert "metadata" in exported
    assert "outputs" in exported
    assert exported["metadata"]["keyword_id"] == keyword_id
    assert exported["metadata"]["generation_complete"] is True
    assert isinstance(exported["outputs"]["gig_titles"], list)
    assert isinstance(exported["outputs"]["tag_sets"], list)
    assert isinstance(exported["outputs"]["faq_entries"], list)
    assert isinstance(exported["outputs"]["upsell_structure"], list)
    assert serialized.startswith("{")
    db.close()
