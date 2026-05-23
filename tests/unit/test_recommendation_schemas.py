"""Unit tests for Stage 13 recommendation output schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
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


def _gig_title_item(index: int) -> dict[str, object]:
    title = f"I will build automation workflow package option {index} with clear outcomes"
    return {
        "title": title,
        "positioning_angle": "outcome",
        "character_count": len(title),
        "primary_keyword_present": True,
    }


def _valid_gig_titles_payload() -> dict[str, object]:
    return {"titles": [_gig_title_item(i) for i in range(1, 6)]}


def _valid_tag_sets_payload() -> dict[str, object]:
    return {
        "tag_sets": [
            ["python automation", "workflow scripts", "api integration", "task bot", "etl setup"],
            ["automation expert", "ops workflow", "crm workflow", "zapier flow", "notion setup"],
            ["automation service", "python api", "business process", "data workflow", "automation audit"],
            ["team automation", "saas operations", "process design", "ops support", "automation strategy"],
            ["workflow mapping", "delivery fast", "support setup", "custom scripts", "integration help"],
        ]
    }


def _valid_package_structure_payload() -> dict[str, object]:
    return {
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


def _valid_description_outline_payload() -> dict[str, object]:
    return {
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


def _valid_faq_entries_payload() -> dict[str, object]:
    return {
        "faq_entries": [
            {
                "question": "Can you work with my existing automation stack?",
                "answer": "Yes. I review your current tools first and map compatible steps before delivery.",
                "addresses_complaint": "tool-compatibility",
            },
            {
                "question": "What do you need from me to get started?",
                "answer": "I need process notes, tool access level, and target outcome before kickoff.",
                "addresses_complaint": None,
            },
            {
                "question": "Do you provide revisions if flow logic needs adjustment?",
                "answer": "Yes. Revisions are included by package tier and focused on scoped improvements.",
                "addresses_complaint": "revision-clarity",
            },
            {
                "question": "Can you deliver quickly for urgent launches?",
                "answer": "I can prioritize urgent timelines when scope is clear and dependencies are ready.",
                "addresses_complaint": "slow-delivery",
            },
            {
                "question": "What is not included in this service?",
                "answer": "I do not provide unrelated app development outside the agreed workflow scope.",
                "addresses_complaint": "scope-creep",
            },
        ]
    }


def _valid_differentiation_payload() -> dict[str, object]:
    return {
        "positioning_statement": (
            "Most competitors offer generic automation bundles. This offer focuses on documented "
            "handoff, transparent checkpoints, and practical workflow reliability from day one."
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


def _valid_buyer_persona_payload() -> dict[str, object]:
    return {
        "name": "Alex",
        "role": "Operations Manager",
        "company_stage": "Early growth SaaS",
        "pain_points": ["manual handoffs", "missed updates"],
        "budget_range": "$150-$500",
        "decision_trigger": "Process failures are delaying customer onboarding.",
        "where_they_search": "Fiverr, Reddit, and product-ops communities",
        "what_makes_them_buy": "Clear scope and confidence in delivery speed.",
    }


def _valid_thumbnail_direction_payload() -> dict[str, object]:
    return {
        "concept": "Show before-and-after workflow visibility with clean UI style.",
        "style": "Dark blue with bright accent highlights",
        "elements_to_include": ["workflow icons", "checklist", "timeline"],
        "elements_to_avoid": ["stock-photo faces"],
        "differentiation_note": "Use quantified outcomes to stand out from generic text-only thumbnails.",
    }


def _valid_upsell_structure_payload() -> dict[str, object]:
    return {
        "extras": [
            {"name": "Priority 24h update", "price": 25, "description": "Priority response and update cycle."},
            {"name": "Post-launch tuning", "price": 45, "description": "Optimization pass after first week."},
        ]
    }


def _valid_red_flags_payload() -> dict[str, object]:
    return {
        "red_flags": [
            {
                "flag_type": "proof_gap",
                "description": "Top competitors have long review history and strong social proof.",
                "severity": "MEDIUM",
                "mitigation": "Publish case-study assets and guaranteed milestone updates.",
            }
        ],
        "overall_risk_level": "MEDIUM",
        "proceed_recommendation": "Proceed with a focused launch and tightly scoped packages.",
    }


def _valid_niche_viability_payload() -> dict[str, object]:
    return {
        "viability_assessment": (
            "Demand remains healthy and competitor weakness signals suggest room for a clear newcomer "
            "position. Entry is viable when messaging stays specific and onboarding is structured."
        ),
        "timing_assessment": "Timing is favorable while buyer intent is still rising.",
        "risk_summary": "Primary risk is weak trust signals early in launch.",
        "blunt_recommendation": "Enter now with a focused scope and proof-first positioning.",
    }


def _all_outputs_payload() -> dict[str, object]:
    return {
        "gig_titles": _valid_gig_titles_payload(),
        "tag_sets": _valid_tag_sets_payload(),
        "package_structure": _valid_package_structure_payload(),
        "description_outline": _valid_description_outline_payload(),
        "faq_entries": _valid_faq_entries_payload(),
        "differentiation_angle": _valid_differentiation_payload(),
        "buyer_persona": _valid_buyer_persona_payload(),
        "thumbnail_direction": _valid_thumbnail_direction_payload(),
        "upsell_structure": _valid_upsell_structure_payload(),
        "red_flags": _valid_red_flags_payload(),
        "niche_viability": _valid_niche_viability_payload(),
    }


def test_gig_titles_output_validates_5_titles() -> None:
    parsed = GigTitlesOutput.model_validate(_valid_gig_titles_payload())
    assert len(parsed.titles) == 5


def test_package_structure_output_has_three_tiers() -> None:
    parsed = PackageStructureOutput.model_validate(_valid_package_structure_payload())
    assert parsed.basic.price < parsed.standard.price < parsed.premium.price


def test_recommendation_output_accepts_partial_results() -> None:
    parsed = RecommendationOutput.model_validate({"gig_titles": _valid_gig_titles_payload()})
    assert parsed.gig_titles is not None
    assert parsed.generation_complete is False


def test_gig_titles_rejects_fewer_than_5_titles() -> None:
    payload = {"titles": [_gig_title_item(i) for i in range(1, 4)]}
    with pytest.raises(ValidationError):
        GigTitlesOutput.model_validate(payload)


def test_gig_titles_accepts_exactly_5_titles() -> None:
    GigTitlesOutput.model_validate(_valid_gig_titles_payload())


def test_package_structure_rejects_missing_tier() -> None:
    payload = _valid_package_structure_payload()
    payload.pop("premium")
    with pytest.raises(ValidationError):
        PackageStructureOutput.model_validate(payload)


def test_recommendation_output_partial_tasks() -> None:
    payload = _all_outputs_payload()
    payload.pop("red_flags")
    payload.pop("niche_viability")
    payload.pop("upsell_structure")
    parsed = RecommendationOutput.model_validate(payload)
    assert parsed.generation_complete is False


def test_recommendation_output_all_tasks_filled() -> None:
    parsed = RecommendationOutput.model_validate(_all_outputs_payload())
    assert parsed.generation_complete is True


def test_gig_titles_edge_case_empty_titles_rejected() -> None:
    with pytest.raises(ValidationError):
        GigTitlesOutput.model_validate({"titles": []})


def test_tag_sets_edge_case_invalid_tag_count_rejected() -> None:
    payload = _valid_tag_sets_payload()
    payload["tag_sets"] = [["one", "two", "three", "four"]] * 5
    with pytest.raises(ValidationError):
        TagSetsOutput.model_validate(payload)


def test_package_structure_edge_case_extra_field_ignored() -> None:
    payload = _valid_package_structure_payload()
    payload["unexpected"] = "ignored"
    parsed = PackageStructureOutput.model_validate(payload)
    assert not hasattr(parsed, "unexpected")


def test_description_outline_edge_case_empty_sections_rejected() -> None:
    with pytest.raises(ValidationError):
        DescriptionOutlineOutput.model_validate({"sections": []})


def test_faq_entries_edge_case_empty_list_rejected() -> None:
    with pytest.raises(ValidationError):
        FaqEntriesOutput.model_validate({"faq_entries": []})


def test_differentiation_angle_edge_case_no_differentiators_rejected() -> None:
    payload = _valid_differentiation_payload()
    payload["differentiators"] = []
    with pytest.raises(ValidationError):
        DifferentiationAngleOutput.model_validate(payload)


def test_buyer_persona_edge_case_extra_field_ignored() -> None:
    payload = _valid_buyer_persona_payload()
    payload["extra_field"] = "ignore me"
    parsed = BuyerPersonaOutput.model_validate(payload)
    assert not hasattr(parsed, "extra_field")


def test_thumbnail_direction_edge_case_extra_field_ignored() -> None:
    payload = _valid_thumbnail_direction_payload()
    payload["extra_field"] = "ignore me"
    parsed = ThumbnailDirectionOutput.model_validate(payload)
    assert not hasattr(parsed, "extra_field")


def test_upsell_structure_edge_case_empty_list_rejected() -> None:
    with pytest.raises(ValidationError):
        UpsellStructureOutput.model_validate({"extras": []})


def test_red_flags_edge_case_extra_field_ignored() -> None:
    payload = _valid_red_flags_payload()
    payload["unknown"] = 123
    parsed = RedFlagsOutput.model_validate(payload)
    assert not hasattr(parsed, "unknown")


def test_niche_viability_edge_case_extra_field_ignored() -> None:
    payload = _valid_niche_viability_payload()
    payload["unknown"] = 123
    parsed = NicheViabilityOutput.model_validate(payload)
    assert not hasattr(parsed, "unknown")

