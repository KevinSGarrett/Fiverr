"""Unit tests for recommendation export helpers."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import src.recommendations.export as export_module
import yaml
from src.recommendations.schemas import RecommendationOutput


def _full_output() -> RecommendationOutput:
    return RecommendationOutput.model_validate(
        {
            "gig_titles": {
                "titles": [
                    _gig_title_item(1),
                    _gig_title_item(2),
                    _gig_title_item(3),
                    _gig_title_item(4),
                    _gig_title_item(5),
                ]
            },
            "tag_sets": {
                "tag_sets": [
                    ["python workflow", "automation help", "api scripts", "task setup", "ops support"],
                    ["process audit", "workflow design", "business ops", "crm automation", "custom bot"],
                    ["saas workflow", "team automation", "delivery fast", "script support", "integration"],
                    ["ops playbook", "growth ops", "launch support", "task cleanup", "zapier flow"],
                    ["system build", "handoff docs", "support calls", "bug fixes", "workflow map"],
                ]
            },
            "package_structure": {
                "basic": {
                    "name": "Basic package",
                    "price": 95,
                    "deliverables": ["Scope audit", "Feature matrix"],
                    "delivery_days": 3,
                    "revisions": 1,
                },
                "standard": {
                    "name": "Standard package",
                    "price": 225,
                    "deliverables": ["Complete PRD", "User stories"],
                    "delivery_days": 5,
                    "revisions": 2,
                },
                "premium": {
                    "name": "Premium package",
                    "price": 395,
                    "deliverables": ["PRD", "Roadmap", "Architecture diagrams"],
                    "delivery_days": 7,
                    "revisions": 3,
                },
            },
            "description_outline": {
                "sections": [
                    {
                        "heading": "Outcome hook",
                        "copy_direction": "Lead with the buyer outcome and an immediate trust signal.",
                        "proof_elements": ["proof point"],
                        "estimated_words": 70,
                    },
                    {
                        "heading": "Scope and deliverables",
                        "copy_direction": "Outline exactly what the buyer receives in each milestone.",
                        "proof_elements": ["scope details"],
                        "estimated_words": 80,
                    },
                    {
                        "heading": "How I execute",
                        "copy_direction": "Show process checkpoints and communication cadence.",
                        "proof_elements": ["process map"],
                        "estimated_words": 75,
                    },
                    {
                        "heading": "Call to action",
                        "copy_direction": "Close with what inputs are needed to start quickly.",
                        "proof_elements": ["checklist"],
                        "estimated_words": 60,
                    },
                ]
            },
            "faq_entries": {
                "faq_entries": [
                    {
                        "question": "What do I need to provide before we begin?",
                        "answer": "Please share scope notes, references, and your preferred delivery timeline.",
                    },
                    {
                        "question": "How do revisions work for this offer?",
                        "answer": "Revisions follow package limits and focus on scoped clarifications and updates.",
                    },
                    {
                        "question": "Can you work with my current tooling stack?",
                        "answer": "Yes, I map your current stack first and recommend practical integration steps.",
                    },
                    {
                        "question": "Do you provide post-delivery support guidance?",
                        "answer": "Yes, I include handoff notes and support guidance based on your package tier.",
                    },
                    {
                        "question": "How fast can this be delivered?",
                        "answer": "Delivery depends on scope, but I provide timeline checkpoints early in the process.",
                    },
                ]
            },
            "differentiation_angle": {
                "positioning_statement": (
                    "Top competitors rely on generic language and thin proof blocks. "
                    "This offer leads with concrete outcomes, transparent process steps, "
                    "and trust-building proof assets from the first message."
                ),
                "differentiators": [
                    {
                        "action": "Include a buyer-ready implementation map in the first response.",
                        "competitor_weakness_exploited": "Competitors provide vague onboarding details.",
                        "buyer_pain_addressed": "Buyers worry about unclear post-purchase steps.",
                    }
                ],
                "one_sentence_pitch": "I turn vague scopes into clear execution-ready packages.",
            },
            "buyer_persona": {
                "name": "Alex",
                "role": "Product founder",
                "company_stage": "Pre-seed SaaS",
                "pain_points": ["Unclear scope", "Weak execution handoff"],
                "budget_range": "$100-$400",
                "decision_trigger": "Hiring first contractor to ship an MVP quickly.",
                "where_they_search": "Fiverr and startup communities",
                "what_makes_them_buy": "Clarity, trust signals, and concrete deliverables",
            },
            "thumbnail_direction": {
                "concept": "Show before-and-after clarity transformation for project planning.",
                "style": "Clean dark background with bright accent highlights",
                "elements_to_include": ["Checklist", "Roadmap icon"],
                "elements_to_avoid": ["Cluttered text"],
                "differentiation_note": "Highlight quantified outcome instead of generic promises.",
            },
            "upsell_structure": {
                "extras": [
                    {
                        "name": "Priority turnaround",
                        "price": 25,
                        "description": "Move your project to the front of the delivery queue.",
                    },
                    {
                        "name": "Post-launch review",
                        "price": 45,
                        "description": "Follow-up review with recommendations after delivery.",
                    },
                ]
            },
            "red_flags": {
                "red_flags": [
                    {
                        "flag_type": "market_competition",
                        "description": "Top sellers in this niche have strong review volume and authority.",
                        "severity": "MEDIUM",
                        "mitigation": "Lead with proof-rich assets and a narrower positioning angle.",
                    }
                ],
                "overall_risk_level": "MEDIUM",
                "proceed_recommendation": "Proceed with focused positioning and proof-first messaging.",
            },
            "niche_viability": {
                "viability_assessment": (
                    "Demand signal and buyer intent remain healthy in this niche, "
                    "and there is clear room for differentiated proof-driven positioning."
                ),
                "timing_assessment": "Current timing supports a focused new entrant strategy.",
                "risk_summary": "Main risk is high authority competitors with dense reviews.",
                "blunt_recommendation": "Proceed with a niche-specific launch strategy.",
            },
            "generation_complete": True,
            "total_llm_cost_usd": 0.4321,
        }
    )


def _gig_title_item(index: int) -> dict[str, object]:
    title = f"I will build your high-converting automation service package option {index}"
    return {
        "title": title,
        "positioning_angle": "outcome",
        "character_count": len(title),
        "primary_keyword_present": True,
    }


def _metadata(*, generation_complete: bool = True) -> export_module.RecommendationExportMetadata:
    return export_module.RecommendationExportMetadata(
        keyword_text="AI SaaS PRD",
        tag="STRONG GO",
        final_score=82.3,
        niche_name="PRD / AI SaaS MVP Roadmap",
        generated_at=datetime(2026, 5, 23, 12, 34, tzinfo=UTC),
        llm_cost_usd=0.4321,
        generation_complete=generation_complete,
    )


def _render_markdown(monkeypatch: Any, output: RecommendationOutput) -> str:
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda **_kwargs: _metadata())
    monkeypatch.setattr(export_module, "get_recommendation", lambda **_kwargs: output)
    return asyncio.run(export_module.export_recommendation_markdown("101", db=object()))


def test_export_markdown_returns_string(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    assert isinstance(markdown, str)
    assert markdown.strip()
    assert markdown.startswith("# Recommendation:")


def test_export_markdown_includes_viability_section(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    assert "## Viability Assessment" in markdown
    assert "Demand signal and buyer intent remain healthy" in markdown


def test_export_markdown_includes_gig_titles(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    for index in range(1, 6):
        assert f"{index}. I will build your high-converting automation service package option {index}" in markdown


def test_export_markdown_includes_package_table(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    assert "| Tier | Price | Deliverables | Delivery | Revisions |" in markdown
    assert "| Basic | $95 | Scope audit, Feature matrix | 3 days | 1 |" in markdown
    assert "| Standard | $225 | Complete PRD, User stories | 5 days | 2 |" in markdown
    assert "| Premium | $395 | PRD, Roadmap, Architecture diagrams | 7 days | 3 |" in markdown


def test_export_markdown_includes_faq(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    assert "## FAQ" in markdown
    assert "**Q: What do I need to provide before we begin?**" in markdown
    assert "A: Please share scope notes, references, and your preferred delivery timeline." in markdown


def test_export_markdown_handles_none_viability(monkeypatch: Any) -> None:
    output = _full_output()
    output.niche_viability = None
    markdown = _render_markdown(monkeypatch, output)
    assert "_Viability Assessment not available — task failed or data insufficient._" in markdown


def test_export_markdown_handles_none_package(monkeypatch: Any) -> None:
    output = _full_output()
    output.package_structure = None
    markdown = _render_markdown(monkeypatch, output)
    assert "_Packages not available — task failed or data insufficient._" in markdown


def test_export_markdown_includes_footer(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    assert "_Generated: 2026-05-23 12:34 | Estimated LLM Cost: $0.4321_" in markdown
    assert "**Completeness:** 100%" in markdown


def test_export_markdown_red_flags_match_spec_format(monkeypatch: Any) -> None:
    markdown = _render_markdown(monkeypatch, _full_output())
    assert "⚠ MEDIUM: Top sellers in this niche have strong review volume and authority." in markdown
    assert "  → Lead with proof-rich assets and a narrower positioning angle." in markdown


def test_export_markdown_returns_error_when_not_found(monkeypatch: Any) -> None:
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda **_kwargs: None)
    markdown = asyncio.run(export_module.export_recommendation_markdown("101", db=object()))
    assert markdown.startswith("# Recommendation Export Error")
    assert "not found" in markdown


def test_export_markdown_returns_error_when_not_complete(monkeypatch: Any) -> None:
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda **_kwargs: _metadata(generation_complete=False))
    markdown = asyncio.run(export_module.export_recommendation_markdown("101", db=object()))
    assert markdown.startswith("# Recommendation Export Error")
    assert "not generation_complete" in markdown


def test_export_by_keyword_returns_markdown_and_no_error(monkeypatch: Any) -> None:
    async def _fake_export(*_args: Any, **_kwargs: Any) -> str:
        return "# Recommendation: Export Ready"

    monkeypatch.setattr(export_module, "export_recommendation_markdown", _fake_export)
    markdown, error = asyncio.run(
        export_module.export_recommendation_by_keyword(
            keyword_id=1,
            niche_id="niche-1",
            run_id="run-1",
            db=object(),
        )
    )
    assert error is None
    assert markdown == "# Recommendation: Export Ready"


def test_export_by_keyword_returns_error_when_not_found(monkeypatch: Any) -> None:
    async def _fake_export(*_args: Any, **_kwargs: Any) -> str:
        return "# Recommendation Export Error\n\nRecommendation not found."

    monkeypatch.setattr(export_module, "export_recommendation_markdown", _fake_export)
    markdown, error = asyncio.run(
        export_module.export_recommendation_by_keyword(
            keyword_id=1,
            niche_id="niche-1",
            run_id="run-1",
            db=object(),
        )
    )
    assert markdown == ""
    assert error == "Recommendation not found."


def test_auto_export_markdown_config_key_valid() -> None:
    payload = yaml.safe_load(Path("config.yaml.example").read_text(encoding="utf-8"))
    recommendations = payload["recommendations"]
    assert recommendations["auto_export_markdown"] is False
    assert recommendations["min_tag"] == "CONDITIONAL GO"
