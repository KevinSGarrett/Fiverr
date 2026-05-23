"""Integration validation suite for E05 Definition-of-Done criteria."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

from sqlalchemy import Float, Integer, String, create_engine
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker
from src.models import Base, GigQualityScore, Keyword, KeywordScore, Niche, Recommendation
from src.recommendations import context_builder as context_builder_module
from src.recommendations import eligibility as eligibility_module
from src.recommendations import llm_tasks
from src.recommendations.contracts import RecommendationContext
from src.recommendations.eligibility import (
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.executor import generate_recommendation_async
from src.recommendations.export import export_recommendation_json, export_recommendation_markdown
from src.recommendations.pipeline import run_recommendations_pipeline
from src.recommendations.schemas import (
    BuyerPersonaOutput,
    DescriptionOutlineOutput,
    DifferentiationAngleOutput,
    FaqEntriesOutput,
    GigTitlesOutput,
    NicheViabilityOutput,
    PackageStructureOutput,
    RecommendationOutput,
    RedFlagsOutput,
    TagSetsOutput,
    ThumbnailDirectionOutput,
    UpsellStructureOutput,
)


class OpportunityRanking(Base):
    """Test-only ranking model used by recommendation eligibility."""

    __tablename__ = "opportunity_rankings_dod"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    keyword_id: Mapped[int] = mapped_column(Integer, index=True)
    tag: Mapped[str] = mapped_column(String(32))
    final_score: Mapped[float] = mapped_column(Float)


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def _register_ranking_model(monkeypatch: Any) -> None:
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


def _seed_keyword(
    db: Session,
    *,
    keyword_id: int,
    run_id: str,
    tag: str,
    final_score: float = 81.0,
    demand_score: float = 67.0,
    confidence_modifier: float = 0.84,
    include_gig_quality: bool = True,
) -> None:
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
            demand_score=demand_score,
            competition_score=42.0,
            opportunity_score=76.0,
            feasibility_score=64.0,
            saturation_score=31.0,
            final_score=final_score,
            confidence_modifier=confidence_modifier,
            tag=tag,
        )
    )
    db.add(
        OpportunityRanking(
            run_id=run_id,
            keyword_id=keyword_id,
            tag=tag,
            final_score=final_score,
        )
    )
    if include_gig_quality:
        db.add(
            GigQualityScore(
                keyword_id=keyword_id,
                gig_url=f"https://fiverr.com/gig/{keyword_id}",
                run_id=run_id,
                analysis_complete=True,
            )
        )
    db.commit()


def _context(keyword_id: int, run_id: str, *, tag: str = "STRONG GO", final_score: float = 81.0) -> RecommendationContext:
    return RecommendationContext(
        keyword_id=keyword_id,
        keyword_text=f"keyword-{keyword_id}",
        niche_id="1",
        niche_name="Automation",
        run_id=run_id,
        tag=tag,
        final_score=final_score,
        confidence_modifier=0.84,
        top_competitor_weaknesses=[],
    )


def _full_output(*, total_cost: float = 0.31) -> RecommendationOutput:
    return RecommendationOutput(
        gig_titles=GigTitlesOutput.model_validate(
            {
                "titles": [
                    {
                        "title": f"I will build automation workflow package option {index} with clear outcomes",
                        "positioning_angle": "outcome",
                        "character_count": 70,
                        "primary_keyword_present": True,
                    }
                    for index in range(1, 6)
                ]
            }
        ),
        tag_sets=TagSetsOutput.model_validate(
            {
                "tag_sets": [
                    ["python automation", "workflow scripts", "api integration", "task bot", "etl setup"],
                    ["automation expert", "ops workflow", "crm workflow", "zapier flow", "notion setup"],
                    ["automation service", "python api", "business process", "data workflow", "audit setup"],
                    ["team automation", "saas operations", "process design", "ops support", "automation plan"],
                    ["workflow mapping", "delivery fast", "support setup", "custom scripts", "integration help"],
                ]
            }
        ),
        package_structure=PackageStructureOutput.model_validate(
            {
                "basic": {
                    "name": "Starter Automation",
                    "price": 90,
                    "deliverables": ["workflow discovery", "one automation flow"],
                    "delivery_days": 3,
                    "revisions": 1,
                },
                "standard": {
                    "name": "Core Automation Build",
                    "price": 210,
                    "deliverables": ["workflow map", "two automation flows", "handoff doc"],
                    "delivery_days": 5,
                    "revisions": 2,
                },
                "premium": {
                    "name": "Automation System Package",
                    "price": 360,
                    "deliverables": ["full map", "four automation flows", "training video"],
                    "delivery_days": 8,
                    "revisions": 3,
                },
            }
        ),
        description_outline=DescriptionOutlineOutput.model_validate(
            {
                "sections": [
                    {
                        "heading": "Benefit First Hook",
                        "copy_direction": "Lead with reduced manual work and faster delivery outcomes.",
                        "proof_elements": ["past results", "sample workflow"],
                        "estimated_words": 70,
                    },
                    {
                        "heading": "What You Receive",
                        "copy_direction": "List concrete deliverables and exact implementation scope.",
                        "proof_elements": ["deliverable list"],
                        "estimated_words": 80,
                    },
                    {
                        "heading": "Process Walkthrough",
                        "copy_direction": "Explain checkpoints and communication timing for predictability.",
                        "proof_elements": ["timeline", "milestone updates"],
                        "estimated_words": 75,
                    },
                    {
                        "heading": "Call To Action",
                        "copy_direction": "Close with required inputs and next action to start quickly.",
                        "proof_elements": ["ready checklist"],
                        "estimated_words": 60,
                    },
                ]
            }
        ),
        faq_entries=FaqEntriesOutput.model_validate(
            {
                "faq_entries": [
                    {
                        "question": "Can you work with my existing automation stack?",
                        "answer": "Yes. I review your tools first and map compatible steps before delivery.",
                    },
                    {
                        "question": "What do you need from me to get started?",
                        "answer": "I need process notes, access details, and desired outcomes before kickoff.",
                    },
                    {
                        "question": "Do you provide revisions if logic needs adjustment?",
                        "answer": "Yes. Revisions are included by package tier and scoped to agreed deliverables.",
                    },
                    {
                        "question": "Can you deliver quickly for urgent launches?",
                        "answer": "I can prioritize urgent timelines when dependencies are clear in advance.",
                    },
                    {
                        "question": "What is not included in this service?",
                        "answer": "I do not provide unrelated app development outside workflow scope.",
                    },
                ]
            }
        ),
        differentiation_angle=DifferentiationAngleOutput.model_validate(
            {
                "positioning_statement": (
                    "This offer focuses on practical workflow reliability, clear scope, and documented handoff "
                    "so buyers can implement confidently from day one."
                ),
                "differentiators": [
                    {
                        "action": "Publish a clear implementation roadmap in the first message.",
                        "competitor_weakness_exploited": "Unclear onboarding expectations.",
                        "buyer_pain_addressed": "Buyers feel uncertain after ordering.",
                    }
                ],
                "one_sentence_pitch": "I turn repetitive tasks into documented workflows teams can trust.",
            }
        ),
        buyer_persona=BuyerPersonaOutput.model_validate(
            {
                "name": "Alex",
                "role": "Operations Manager",
                "company_stage": "Early growth SaaS",
                "pain_points": ["manual handoffs", "missed updates"],
                "budget_range": "$150-$500",
                "decision_trigger": "Process failures are delaying customer onboarding.",
                "where_they_search": "Fiverr and operations communities",
                "what_makes_them_buy": "Clear scope and confidence in delivery speed.",
            }
        ),
        thumbnail_direction=ThumbnailDirectionOutput.model_validate(
            {
                "concept": "Show before-and-after workflow visibility with clean UI style.",
                "style": "Dark blue with bright accent highlights",
                "elements_to_include": ["workflow icons", "checklist", "timeline"],
                "elements_to_avoid": ["stock-photo faces"],
                "differentiation_note": "Use quantified outcomes to stand out from generic text-only thumbnails.",
            }
        ),
        upsell_structure=UpsellStructureOutput.model_validate(
            {
                "extras": [
                    {"name": "Priority 24h update", "price": 25, "description": "Priority response and update cycle."},
                    {"name": "Post-launch tuning", "price": 45, "description": "Optimization pass after first week."},
                ]
            }
        ),
        red_flags=RedFlagsOutput.model_validate(
            {
                "red_flags": [
                    {
                        "flag_type": "proof_gap",
                        "description": "Top competitors have long review history and strong social proof.",
                        "severity": "MEDIUM",
                        "mitigation": "Publish case-study assets and milestone updates.",
                    }
                ],
                "overall_risk_level": "MEDIUM",
                "proceed_recommendation": "Proceed with a focused launch and tightly scoped packages.",
            }
        ),
        niche_viability=NicheViabilityOutput.model_validate(
            {
                "viability_assessment": (
                    "Demand remains healthy and competitor weakness signals suggest room for a clear newcomer "
                    "position. Entry is viable with focused messaging and reliable delivery."
                ),
                "timing_assessment": "Timing is favorable while buyer intent remains steady.",
                "risk_summary": "Primary risk is weak trust signals early in launch.",
                "blunt_recommendation": "Enter now with focused scope and proof-first positioning.",
            }
        ),
        generation_complete=True,
        failed_tasks=[],
        total_llm_cost_usd=total_cost,
    )


def _partial_output() -> RecommendationOutput:
    output = _full_output(total_cost=0.05)
    output.tag_sets = None
    output.generation_complete = False
    output.failed_tasks = ["tag_sets"]
    return output


def _run_pipeline_for_one_keyword(
    db: Session,
    *,
    run_id: str,
    monkeypatch: Any,
    output_factory: Callable[[], RecommendationOutput],
) -> dict[str, Any]:
    generate_mock = AsyncMock(side_effect=lambda **_kwargs: output_factory())
    monkeypatch.setattr("src.recommendations.pipeline.generate_recommendation_async", generate_mock)
    return asyncio.run(
        run_recommendations_pipeline(
            run_id=run_id,
            db=db,
            config={"recommendations": {"min_tag": "CONDITIONAL GO"}},
            llm_client=object(),
            cache=object(),
            dry_run=False,
        )
    )


def test_recommendations_only_generates_for_strong_go_keywords(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-dod-strong"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=101, run_id=run_id, tag="STRONG GO")

    summary = _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_partial_output)

    assert summary["eligible"] == 1
    assert summary["generated"] == 1
    db.close()


def test_recommendations_only_generates_for_conditional_go_keywords(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-dod-conditional"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=102, run_id=run_id, tag="CONDITIONAL GO")

    summary = _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_partial_output)

    assert summary["eligible"] == 1
    assert summary["generated"] == 1
    db.close()


def test_eligibility_gates_block_low_confidence() -> None:
    db = _session()
    _seed_keyword(db, keyword_id=201, run_id="run-low-confidence", tag="STRONG GO")

    ok, reason = passes_recommendation_gates(
        {"keyword_id": 201, "confidence_modifier": 0.39, "demand_score": 65.0},
        db,
    )

    assert ok is False
    assert "below 0.40" in reason
    db.close()


def test_eligibility_gates_block_low_demand() -> None:
    db = _session()
    _seed_keyword(db, keyword_id=202, run_id="run-low-demand", tag="STRONG GO")

    ok, reason = passes_recommendation_gates(
        {"keyword_id": 202, "confidence_modifier": 0.85, "demand_score": 19.0},
        db,
    )

    assert ok is False
    assert "Demand score" in reason
    db.close()


def test_force_override_bypasses_gates(monkeypatch: Any) -> None:
    db = _session()
    _seed_keyword(db, keyword_id=203, run_id="run-force", tag="STRONG GO")
    monkeypatch.setattr(eligibility_module, "is_keyword_force_recommended", lambda *_args, **_kwargs: True)

    ok, reason = passes_recommendation_gates(
        {"keyword_id": 203, "confidence_modifier": 0.0, "demand_score": 0.0},
        db,
    )

    assert ok is True
    assert "forced recommendation" in reason
    db.close()


def test_failed_task_does_not_crash_pipeline(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-failed-task"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=301, run_id=run_id, tag="STRONG GO")

    summary = _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_partial_output)

    assert summary["generated"] == 1
    assert summary["failed"] == 0
    db.close()


def test_partial_output_persisted_with_generation_complete_false(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-partial-persisted"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=302, run_id=run_id, tag="STRONG GO")

    _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_partial_output)

    row = db.query(Recommendation).filter(Recommendation.keyword_id == 302).first()
    assert row is not None
    assert row.generation_complete is False
    assert isinstance(row.raw_json, dict)
    assert row.raw_json.get("generation_complete") is False
    db.close()


def test_all_11_outputs_present_when_all_tasks_succeed(monkeypatch: Any) -> None:
    context = _context(401, "run-all-success")
    output = _full_output()
    task_mocks = {
        "task_gig_titles": AsyncMock(return_value=output.gig_titles),
        "task_tag_sets": AsyncMock(return_value=output.tag_sets),
        "task_package_structure": AsyncMock(return_value=output.package_structure),
        "task_description_outline": AsyncMock(return_value=output.description_outline),
        "task_faq_entries": AsyncMock(return_value=output.faq_entries),
        "task_differentiation_angle": AsyncMock(return_value=output.differentiation_angle),
        "task_buyer_persona": AsyncMock(return_value=output.buyer_persona),
        "task_thumbnail_direction": AsyncMock(return_value=output.thumbnail_direction),
        "task_upsell_structure": AsyncMock(return_value=output.upsell_structure),
        "task_red_flags": AsyncMock(return_value=output.red_flags),
        "task_niche_viability": AsyncMock(return_value=output.niche_viability),
    }
    for task_name, task_mock in task_mocks.items():
        monkeypatch.setattr(f"src.recommendations.executor.{task_name}", task_mock)

    generated = asyncio.run(generate_recommendation_async(context=context, llm_client=object(), cache=object()))

    assert generated.generation_complete is True
    assert generated.completeness_ratio() == 1.0


def test_pydantic_validation_catches_malformed_output() -> None:
    template_stub = SimpleNamespace(render=lambda **_kwargs: "prompt")
    llm_client = SimpleNamespace(complete=AsyncMock(return_value="```json\n{bad-json}\n```"))

    with patch.object(llm_tasks, "load_template", return_value=template_stub):
        result = asyncio.run(llm_tasks.task_gig_titles(_context(402, "run-malformed"), llm_client, cache=None))

    assert result is None


def test_markdown_export_produces_non_empty_string(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-markdown-export"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=501, run_id=run_id, tag="STRONG GO")
    _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_full_output)

    markdown = asyncio.run(export_recommendation_markdown("501", db))

    assert markdown.strip()
    assert not markdown.startswith("# Recommendation Export Error")
    db.close()


def test_json_export_is_serializable(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-json-export"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=502, run_id=run_id, tag="STRONG GO")
    _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_full_output)

    payload = asyncio.run(export_recommendation_json("502", db))

    assert "error" not in payload
    json.dumps(payload)
    db.close()


def test_cost_tracking_present(monkeypatch: Any) -> None:
    db = _session()
    run_id = "run-cost-tracking"
    _register_ranking_model(monkeypatch)
    _seed_keyword(db, keyword_id=601, run_id=run_id, tag="STRONG GO")
    _run_pipeline_for_one_keyword(db, run_id=run_id, monkeypatch=monkeypatch, output_factory=_partial_output)

    row = db.query(Recommendation).filter(Recommendation.keyword_id == 601).first()
    assert row is not None
    assert row.llm_cost_usd >= 0.0
    db.close()


def test_score_change_threshold() -> None:
    db = _session()
    _seed_keyword(db, keyword_id=701, run_id="run-threshold", tag="STRONG GO")
    db.add(
        Recommendation(
            keyword_id=701,
            run_id=1,
            run_id_text="run-threshold",
            recommendation_type="keyword_recommendation",
            recommendation_text="stable recommendation",
            final_score=80.0,
            score_at_generation=80.0,
            generation_complete=True,
        )
    )
    db.commit()

    assert should_regenerate_recommendation(701, 84.9, db) is False
    assert should_regenerate_recommendation(701, 85.0, db) is True
    db.close()
