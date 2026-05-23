"""Unit tests for Stage 13 concurrent recommendation executor."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import src.recommendations.executor as executor
from src.recommendations.contracts import RecommendationContext
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


def _context() -> RecommendationContext:
    return RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-executor-1",
        tag="STRONG GO",
        final_score=82.0,
        confidence_modifier=0.84,
        top_competitor_weaknesses=[],
    )


def _valid_outputs() -> dict[str, Any]:
    base_title = "I will build automation workflow package option {idx} with clear outcomes"
    return {
        "gig_titles": GigTitlesOutput.model_validate(
            {
                "titles": [
                    {
                        "title": base_title.format(idx=index),
                        "positioning_angle": "outcome-focused",
                        "character_count": len(base_title.format(idx=index)),
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
                        "answer": "I need process notes, access details, and desired outcomes before kickoff.",
                        "addresses_complaint": None,
                    },
                    {
                        "question": "Do you provide revisions if logic needs adjustment?",
                        "answer": "Yes. Revisions are included by package tier and scoped to agreed deliverables.",
                        "addresses_complaint": "revision-clarity",
                    },
                    {
                        "question": "Can you deliver quickly for urgent launches?",
                        "answer": "I can prioritize urgent timelines when dependencies are clear in advance.",
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
                    "position. Entry is viable with focused messaging and reliable delivery."
                ),
                "timing_assessment": "Timing is favorable while buyer intent remains steady.",
                "risk_summary": "Primary risk is weak trust signals early in launch.",
                "blunt_recommendation": "Enter now with focused scope and proof-first positioning.",
            }
        ),
    }


def _patch_all_task_functions(monkeypatch: Any, outputs: dict[str, Any]) -> dict[str, AsyncMock]:
    task_mocks = {
        "task_gig_titles": AsyncMock(return_value=outputs["gig_titles"]),
        "task_tag_sets": AsyncMock(return_value=outputs["tag_sets"]),
        "task_package_structure": AsyncMock(return_value=outputs["package_structure"]),
        "task_description_outline": AsyncMock(return_value=outputs["description_outline"]),
        "task_faq_entries": AsyncMock(return_value=outputs["faq_entries"]),
        "task_differentiation_angle": AsyncMock(return_value=outputs["differentiation_angle"]),
        "task_buyer_persona": AsyncMock(return_value=outputs["buyer_persona"]),
        "task_thumbnail_direction": AsyncMock(return_value=outputs["thumbnail_direction"]),
        "task_upsell_structure": AsyncMock(return_value=outputs["upsell_structure"]),
        "task_red_flags": AsyncMock(return_value=outputs["red_flags"]),
        "task_niche_viability": AsyncMock(return_value=outputs["niche_viability"]),
    }
    for attr_name, mock in task_mocks.items():
        monkeypatch.setattr(executor, attr_name, mock)
    return task_mocks


def test_generate_recommendation_calls_all_11_tasks(monkeypatch: Any) -> None:
    outputs = _valid_outputs()
    task_mocks = _patch_all_task_functions(monkeypatch, outputs)

    result = executor.generate_recommendation(_context(), llm_client=object(), cache=object())

    assert isinstance(result, RecommendationOutput)
    assert len(task_mocks) == 11
    for task_mock in task_mocks.values():
        task_mock.assert_awaited_once()


def test_generate_recommendation_returns_output_object(monkeypatch: Any) -> None:
    _patch_all_task_functions(monkeypatch, _valid_outputs())

    result = executor.generate_recommendation(_context(), llm_client=object(), cache=object())

    assert isinstance(result, RecommendationOutput)
    assert result.gig_titles is not None
    assert result.niche_viability is not None
    assert result.total_llm_cost_usd > 0.0


def test_generate_recommendation_partial_failure_still_returns(monkeypatch: Any) -> None:
    outputs = _valid_outputs()
    _patch_all_task_functions(monkeypatch, outputs)
    monkeypatch.setattr(executor, "task_tag_sets", AsyncMock(side_effect=RuntimeError("task exploded")))
    monkeypatch.setattr(executor, "task_red_flags", AsyncMock(return_value=None))

    result = executor.generate_recommendation(_context(), llm_client=object(), cache=object())

    assert isinstance(result, RecommendationOutput)
    assert result.tag_sets is None
    assert result.red_flags is None
    assert set(result.failed_tasks) == {"tag_sets", "red_flags"}


def test_generate_recommendation_marks_generation_complete_when_all_succeed(monkeypatch: Any) -> None:
    _patch_all_task_functions(monkeypatch, _valid_outputs())

    result = executor.generate_recommendation(_context(), llm_client=object(), cache=object())

    assert result.generation_complete is True
    assert result.failed_tasks == []


def test_generate_recommendation_marks_incomplete_when_any_fail(monkeypatch: Any) -> None:
    outputs = _valid_outputs()
    _patch_all_task_functions(monkeypatch, outputs)
    monkeypatch.setattr(executor, "task_buyer_persona", AsyncMock(return_value=None))

    result = executor.generate_recommendation(_context(), llm_client=object(), cache=object())

    assert result.generation_complete is False
    assert "buyer_persona" in result.failed_tasks


def test_generate_recommendation_handles_existing_event_loop(monkeypatch: Any) -> None:
    _patch_all_task_functions(monkeypatch, _valid_outputs())

    async def _invoke() -> RecommendationOutput:
        return executor.generate_recommendation(_context(), llm_client=object(), cache=object())

    result = asyncio.run(_invoke())

    assert isinstance(result, RecommendationOutput)
    assert result.generation_complete is True


def test_track_llm_costs_uses_explicit_cost_when_available() -> None:
    output = type("Output", (), {"cost_usd": "0.5"})()

    total = executor.track_llm_costs([output], _context())

    assert total == 0.5


def test_track_llm_costs_falls_back_when_explicit_cost_is_invalid() -> None:
    output = type("Output", (), {"cost_usd": "not-a-number"})()

    total = executor.track_llm_costs([output], _context())

    assert total == 0.012
