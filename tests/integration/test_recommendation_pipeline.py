"""Integration test for Stage 13 context + gate flow."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.models import (
    Base,
    ClusterAssignment,
    ClusterLabel,
    CompetitorProfile,
    GigQualityScore,
    Keyword,
    KeywordScore,
    Niche,
)
from src.recommendations.context_builder import build_recommendation_context
from src.recommendations.contracts import RecommendationContext
from src.recommendations.eligibility import (
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
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
from src.recommendations.storage import get_recommendation, save_recommendation


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)()


def test_recommendation_pipeline_context_and_gate_pass() -> None:
    db = _session()
    db.add(Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation"))
    db.add(
        Keyword(
            id=101,
            niche_id=1,
            keyword="python automation",
            normalized_keyword="python automation",
        )
    )
    db.add(
        KeywordScore(
            keyword_id=101,
            scoring_profile="default",
            score_depth="standard",
            demand_score=75.0,
            competition_score=40.0,
            opportunity_score=70.0,
            feasibility_score=66.0,
            saturation_score=35.0,
            final_score=82.0,
            confidence_modifier=0.88,
            tag="STRONG GO",
        )
    )
    db.add(ClusterAssignment(keyword_id=101, niche_id="1", cluster_id=3, run_id="run-int-1"))
    db.add(
        ClusterLabel(
            niche_id="1",
            cluster_id=3,
            run_id="run-int-1",
            label_text="Automation Workflows",
            keyword_count=9,
        )
    )
    db.add(
        CompetitorProfile(
            niche_id="1",
            run_id="run-int-1",
            top_gig_count=5,
            new_seller_gap={
                "top_competitor_weaknesses": [
                    {"gig_title": "I will automate business workflows", "weaknesses": [{"weakness": "slow turnaround"}]}
                ]
            },
        )
    )
    db.add(
        GigQualityScore(
            keyword_id=101,
            gig_url="https://fiverr.com/gig/1",
            run_id="run-int-1",
            analysis_complete=True,
        )
    )
    db.commit()

    context = build_recommendation_context(keyword_id=101, niche_id="1", run_id="run-int-1", db=db)
    assert context is not None
    assert context.keyword_text == "python automation"
    assert context.cluster_label == "Automation Workflows"
    assert context.cluster_size == 9
    assert context.top_competitor_weaknesses

    passes, reason = passes_recommendation_gates(
        {
            "keyword_id": context.keyword_id,
            "confidence_modifier": context.confidence_modifier,
            "demand_score": context.demand_score,
        },
        db,
    )
    assert passes is True
    assert reason == "All gates passed"
    db.close()


def _mocked_output_models() -> dict[str, object]:
    title = "I will build automation workflow package option 1 with clear outcomes"
    return {
        "gig_titles": GigTitlesOutput.model_validate(
            {
                "titles": [
                    {
                        "title": title.replace("option 1", f"option {index}"),
                        "positioning_angle": "outcome",
                        "character_count": len(title.replace("option 1", f"option {index}")),
                        "primary_keyword_present": True,
                    }
                    for index in range(1, 6)
                ]
            }
        ),
        "tag_sets": TagSetsOutput.model_validate(
            {
                "tag_sets": [
                    ["python automation", "workflow scripts", "api integration", "task bot", "etl setup"],
                    ["automation expert", "ops workflow", "crm workflow", "zapier flow", "notion setup"],
                    ["automation service", "python api", "business process", "data workflow", "automation audit"],
                    ["team automation", "saas operations", "process design", "ops support", "automation strategy"],
                    ["workflow mapping", "delivery fast", "support setup", "custom scripts", "integration help"],
                ]
            }
        ),
        "package_structure": PackageStructureOutput.model_validate(
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
        "description_outline": DescriptionOutlineOutput.model_validate(
            {
                "sections": [
                    {
                        "heading": "Benefit First Hook",
                        "copy_direction": "Lead with buyer outcome and reduced manual hours.",
                        "proof_elements": ["past results", "sample workflow"],
                        "estimated_words": 70,
                    },
                    {
                        "heading": "What You Receive",
                        "copy_direction": "List concrete deliverables with exact counts.",
                        "proof_elements": ["deliverable list"],
                        "estimated_words": 85,
                    },
                    {
                        "heading": "Why This Process Works",
                        "copy_direction": "Describe process checkpoints and communication rhythm.",
                        "proof_elements": ["timeline", "milestone updates"],
                        "estimated_words": 75,
                    },
                    {
                        "heading": "Call To Action",
                        "copy_direction": "Close with required inputs and next action.",
                        "proof_elements": ["ready checklist"],
                        "estimated_words": 60,
                    },
                ]
            }
        ),
        "faq_entries": FaqEntriesOutput.model_validate(
            {
                "faq_entries": [
                    {
                        "question": "Can you work with my existing automation stack?",
                        "answer": "Yes. I review your tools first and map compatible steps before delivery.",
                        "addresses_complaint": "tool-compatibility",
                    },
                    {
                        "question": "What do you need from me to get started?",
                        "answer": "I need process notes, tool access level, and target outcome before kickoff.",
                        "addresses_complaint": None,
                    },
                    {
                        "question": "Do you provide revisions if logic needs adjustment?",
                        "answer": "Yes. Revisions are included by package tier and scoped to agreed deliverables.",
                        "addresses_complaint": "revision-clarity",
                    },
                    {
                        "question": "Can you deliver quickly for urgent launches?",
                        "answer": "I can prioritize urgent timelines when scope and dependencies are clear.",
                        "addresses_complaint": "slow-delivery",
                    },
                    {
                        "question": "What is not included in this service?",
                        "answer": "I do not provide unrelated app development outside workflow scope.",
                        "addresses_complaint": "scope-creep",
                    },
                ]
            }
        ),
        "differentiation_angle": DifferentiationAngleOutput.model_validate(
            {
                "positioning_statement": (
                    "Most competitors offer generic bundles. This offer focuses on documented handoff, "
                    "transparent checkpoints, and practical workflow reliability from day one."
                ),
                "differentiators": [
                    {
                        "action": "Publish a clear implementation roadmap in the first message.",
                        "competitor_weakness_exploited": "Unclear onboarding expectations.",
                        "buyer_pain_addressed": "Buyers feel uncertain after ordering.",
                    }
                ],
                "one_sentence_pitch": "I turn messy recurring tasks into documented workflows buyers can trust.",
            }
        ),
        "buyer_persona": BuyerPersonaOutput.model_validate(
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
        "thumbnail_direction": ThumbnailDirectionOutput.model_validate(
            {
                "concept": "Show before-and-after workflow visibility with clean UI style.",
                "style": "Dark blue with bright accent highlights",
                "elements_to_include": ["workflow icons", "checklist", "timeline"],
                "elements_to_avoid": ["stock-photo faces"],
                "differentiation_note": "Use quantified outcomes to stand out from generic text-only thumbnails.",
            }
        ),
        "upsell_structure": UpsellStructureOutput.model_validate(
            {
                "extras": [
                    {
                        "name": "Priority 24h update",
                        "price": 25,
                        "description": "Priority response and update cycle.",
                    },
                    {
                        "name": "Post-launch tuning",
                        "price": 45,
                        "description": "Optimization pass after first week.",
                    },
                ]
            }
        ),
        "red_flags": RedFlagsOutput.model_validate(
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
        "niche_viability": NicheViabilityOutput.model_validate(
            {
                "viability_assessment": (
                    "Demand remains healthy and competitor weakness signals suggest room for a clear newcomer "
                    "position. Entry is viable when messaging stays specific and onboarding is structured."
                ),
                "timing_assessment": "Timing is favorable while buyer intent is still rising.",
                "risk_summary": "Primary risk is weak trust signals early in launch.",
                "blunt_recommendation": "Enter now with a focused scope and proof-first positioning.",
            }
        ),
    }


def test_recommendation_pipeline_full_mock_llm_task_run() -> None:
    context = RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-int-2",
        tag="STRONG GO",
        final_score=82.0,
        confidence_modifier=0.88,
        demand_score=75.0,
        competition_score=40.0,
        opportunity_score=70.0,
        saturation_score=35.0,
        feasibility_score=66.0,
        top_competitor_weaknesses=[{"gig_title": "I will automate business workflows", "weaknesses": []}],
    )
    mocked = _mocked_output_models()
    task_mocks = {name: AsyncMock(return_value=model) for name, model in mocked.items()}

    async def _run_all() -> dict[str, object]:
        return {
            "gig_titles": await task_mocks["gig_titles"](context, None, None),
            "tag_sets": await task_mocks["tag_sets"](context, None, None),
            "package_structure": await task_mocks["package_structure"](context, None, None),
            "description_outline": await task_mocks["description_outline"](context, None, None),
            "faq_entries": await task_mocks["faq_entries"](context, None, None),
            "differentiation_angle": await task_mocks["differentiation_angle"](context, None, None),
            "buyer_persona": await task_mocks["buyer_persona"](context, None, None),
            "thumbnail_direction": await task_mocks["thumbnail_direction"](context, None, None),
            "upsell_structure": await task_mocks["upsell_structure"](context, None, None),
            "red_flags": await task_mocks["red_flags"](context, None, None),
            "niche_viability": await task_mocks["niche_viability"](context, None, None),
        }

    task_results = asyncio.run(_run_all())
    assert all(value is not None for value in task_results.values())
    assert all(hasattr(value, "model_dump_json") for value in task_results.values())

    for value in task_results.values():
        dumped = value.model_dump_json()
        assert dumped.startswith("{")

    output = RecommendationOutput.model_validate(task_results)
    assert output.generation_complete is True


def test_recommendation_pipeline_full_mock_save_and_load() -> None:
    db = _session()
    db.add(Niche(id=1, slug="automation", name="Automation", category_path="programming-tech/automation"))
    db.add(
        Keyword(
            id=202,
            niche_id=1,
            keyword="python automation assistant",
            normalized_keyword="python automation assistant",
        )
    )
    db.add(
        KeywordScore(
            keyword_id=202,
            scoring_profile="default",
            score_depth="standard",
            demand_score=73.0,
            competition_score=44.0,
            opportunity_score=71.0,
            feasibility_score=65.0,
            saturation_score=38.0,
            final_score=80.0,
            confidence_modifier=0.86,
            tag="STRONG GO",
        )
    )
    db.add(ClusterAssignment(keyword_id=202, niche_id="1", cluster_id=5, run_id="run-int-save"))
    db.add(
        ClusterLabel(
            niche_id="1",
            cluster_id=5,
            run_id="run-int-save",
            label_text="Automation Assistants",
            keyword_count=11,
        )
    )
    db.add(
        CompetitorProfile(
            niche_id="1",
            run_id="run-int-save",
            top_gig_count=5,
            new_seller_gap={
                "top_competitor_weaknesses": [
                    {"gig_title": "I will automate operations", "weaknesses": [{"weakness": "slow communication"}]}
                ]
            },
        )
    )
    db.add(
        GigQualityScore(
            keyword_id=202,
            gig_url="https://fiverr.com/gig/202",
            run_id="run-int-save",
            analysis_complete=True,
        )
    )
    db.commit()

    context = build_recommendation_context(keyword_id=202, niche_id="1", run_id="run-int-save", db=db)
    assert context is not None

    passes, reason = passes_recommendation_gates(
        {
            "keyword_id": context.keyword_id,
            "confidence_modifier": context.confidence_modifier,
            "demand_score": context.demand_score,
        },
        db,
    )
    assert passes is True
    assert reason == "All gates passed"
    assert should_regenerate_recommendation(context.keyword_id, context.final_score, db) is True

    mocked = _mocked_output_models()
    task_mocks = {name: AsyncMock(return_value=model) for name, model in mocked.items()}

    async def _run_all() -> dict[str, object]:
        return {
            "gig_titles": await task_mocks["gig_titles"](context, None, None),
            "tag_sets": await task_mocks["tag_sets"](context, None, None),
            "package_structure": await task_mocks["package_structure"](context, None, None),
            "description_outline": await task_mocks["description_outline"](context, None, None),
            "faq_entries": await task_mocks["faq_entries"](context, None, None),
            "differentiation_angle": await task_mocks["differentiation_angle"](context, None, None),
            "buyer_persona": await task_mocks["buyer_persona"](context, None, None),
            "thumbnail_direction": await task_mocks["thumbnail_direction"](context, None, None),
            "upsell_structure": await task_mocks["upsell_structure"](context, None, None),
            "red_flags": await task_mocks["red_flags"](context, None, None),
            "niche_viability": await task_mocks["niche_viability"](context, None, None),
        }

    task_results = asyncio.run(_run_all())
    output = RecommendationOutput.model_validate(
        {
            **task_results,
            "generation_complete": True,
            "total_llm_cost_usd": 0.11,
        }
    )

    recommendation_id = save_recommendation(context=context, output=output, db=db)
    assert recommendation_id

    loaded = get_recommendation(keyword_id=context.keyword_id, db=db)
    assert loaded is not None
    assert loaded.generation_complete is True
    assert loaded.total_llm_cost_usd == 0.11
    assert loaded.gig_titles is not None
    assert loaded.niche_viability is not None
    db.close()
