"""Unit tests for recommendation export helpers."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import run as run_module
import src.recommendations.export as export_module
import yaml
from click.testing import CliRunner
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
        keyword_id=101,
        keyword_text="AI SaaS PRD",
        niche_id="1",
        tag="STRONG GO",
        final_score=82.3,
        niche_name="PRD / AI SaaS MVP Roadmap",
        generated_at=datetime(2026, 5, 23, 12, 34, tzinfo=UTC),
        llm_cost_usd=0.4321,
        generation_complete=generation_complete,
        completeness_ratio=1.0 if generation_complete else 0.73,
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


def _render_json(monkeypatch: Any, output: RecommendationOutput) -> dict[str, Any]:
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda **_kwargs: _metadata())
    monkeypatch.setattr(export_module, "get_recommendation", lambda **_kwargs: output)
    return asyncio.run(export_module.export_recommendation_json("101", db=object()))


def test_export_json_returns_dict(monkeypatch: Any) -> None:
    exported = _render_json(monkeypatch, _full_output())
    assert isinstance(exported, dict)
    assert "metadata" in exported
    assert "outputs" in exported


def test_export_json_metadata_contains_required_fields(monkeypatch: Any) -> None:
    exported = _render_json(monkeypatch, _full_output())
    metadata = exported["metadata"]
    expected_keys = {
        "keyword_id",
        "keyword_text",
        "niche_id",
        "niche_name",
        "tag",
        "final_score",
        "generation_complete",
        "completeness_ratio",
        "llm_cost_usd",
        "generated_at",
        "export_schema_version",
    }
    assert expected_keys.issubset(set(metadata.keys()))


def test_export_json_outputs_contains_all_11_fields(monkeypatch: Any) -> None:
    exported = _render_json(monkeypatch, _full_output())
    outputs = exported["outputs"]
    expected_keys = {
        "gig_titles",
        "tag_sets",
        "package_structure",
        "description_outline",
        "faq_entries",
        "differentiation_angle",
        "buyer_persona",
        "thumbnail_direction",
        "upsell_structure",
        "red_flags",
        "niche_viability_assessment",
    }
    assert set(outputs.keys()) == expected_keys


def test_export_json_handles_none_output_fields(monkeypatch: Any) -> None:
    output = _full_output()
    output.faq_entries = None
    output.thumbnail_direction = None
    output.upsell_structure = None
    exported = _render_json(monkeypatch, output)
    outputs = exported["outputs"]
    assert "faq_entries" in outputs and outputs["faq_entries"] is None
    assert "thumbnail_direction" in outputs and outputs["thumbnail_direction"] is None
    assert "upsell_structure" in outputs and outputs["upsell_structure"] is None


def test_export_json_datetime_is_iso_string(monkeypatch: Any) -> None:
    exported = _render_json(monkeypatch, _full_output())
    generated_at = exported["metadata"]["generated_at"]
    assert isinstance(generated_at, str)
    assert generated_at.startswith("2026-05-23T12:34:00")


def test_export_json_serializable(monkeypatch: Any) -> None:
    exported = _render_json(monkeypatch, _full_output())
    dumped = json.dumps(exported)
    assert isinstance(dumped, str)
    assert dumped


def test_export_json_returns_error_when_not_found(monkeypatch: Any) -> None:
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda **_kwargs: None)
    exported = asyncio.run(export_module.export_recommendation_json("101", db=object()))
    assert exported["error"] == "recommendation not found"


def test_export_json_returns_error_when_not_complete(monkeypatch: Any) -> None:
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda **_kwargs: _metadata(generation_complete=False))
    exported = asyncio.run(export_module.export_recommendation_json("101", db=object()))
    assert exported["error"] == "generation not complete"
    assert exported["completeness"] == 0.73


def test_export_json_by_keyword_returns_dict_and_no_error(monkeypatch: Any) -> None:
    async def _fake_export(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"metadata": {}, "outputs": {}}

    monkeypatch.setattr(export_module, "export_recommendation_json", _fake_export)
    payload, error = asyncio.run(
        export_module.export_recommendation_json_by_keyword(
            keyword_id=1,
            niche_id="niche-1",
            run_id="run-1",
            db=object(),
        )
    )
    assert error is None
    assert payload == {"metadata": {}, "outputs": {}}


def test_export_json_by_keyword_returns_error_when_not_found(monkeypatch: Any) -> None:
    async def _fake_export(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"error": "recommendation not found", "keyword_id": 999}

    monkeypatch.setattr(export_module, "export_recommendation_json", _fake_export)
    payload, error = asyncio.run(
        export_module.export_recommendation_json_by_keyword(
            keyword_id=1,
            niche_id="niche-1",
            run_id="run-1",
            db=object(),
        )
    )
    assert payload == {}
    assert error == "recommendation not found"


def test_json_export_roundtrip_parseable(monkeypatch: Any) -> None:
    exported = _render_json(monkeypatch, _full_output())
    reparsed = json.loads(json.dumps(exported))
    assert reparsed["metadata"]["keyword_id"] == 101
    assert reparsed["outputs"]["gig_titles"] is not None
    assert reparsed["outputs"]["package_structure"] is not None
    assert reparsed["outputs"]["niche_viability_assessment"] is not None


class _FakeQuery:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def filter(self, *_args: Any, **_kwargs: Any) -> _FakeQuery:
        return self

    def order_by(self, *_args: Any, **_kwargs: Any) -> _FakeQuery:
        return self

    def all(self) -> list[Any]:
        return self._rows


class _FakeSessionContext:
    def __init__(self, db: Any) -> None:
        self._db = db

    def __enter__(self) -> Any:
        return self._db

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        del exc_type, exc, tb
        return None


def test_export_all_returns_dict_keyed_by_keyword(monkeypatch: Any) -> None:
    rows = [
        SimpleNamespace(keyword_id=11, run_id_text="run-1", run_id=None, generation_complete=True),
        SimpleNamespace(keyword_id=12, run_id_text="run-1", run_id=None, generation_complete=True),
    ]
    metadata_by_keyword = {
        11: export_module.RecommendationExportMetadata(
            keyword_id=11,
            keyword_text="keyword one",
            niche_id="1",
            tag="STRONG GO",
            final_score=80.0,
            niche_name="Niche 1",
            generated_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
            llm_cost_usd=0.1,
            generation_complete=True,
            completeness_ratio=1.0,
        ),
        12: export_module.RecommendationExportMetadata(
            keyword_id=12,
            keyword_text="keyword two",
            niche_id="1",
            tag="STRONG GO",
            final_score=81.0,
            niche_name="Niche 1",
            generated_at=datetime(2026, 5, 23, 12, 1, tzinfo=UTC),
            llm_cost_usd=0.1,
            generation_complete=True,
            completeness_ratio=1.0,
        ),
    }

    async def _fake_markdown(recommendation_id: str, db: Any) -> str:
        del db
        return f"# Recommendation: {recommendation_id}"

    monkeypatch.setattr(export_module, "_safe_query", lambda *_args, **_kwargs: _FakeQuery(rows))
    monkeypatch.setattr(export_module, "_load_export_metadata", lambda keyword_id, db: metadata_by_keyword[keyword_id])
    monkeypatch.setattr(export_module, "export_recommendation_markdown", _fake_markdown)

    exported = asyncio.run(
        export_module.export_all_recommendations(
            run_id="run-1",
            fmt="markdown",
            db=object(),
            config={},
        )
    )

    assert exported == {
        "keyword one": "# Recommendation: 11",
        "keyword two": "# Recommendation: 12",
    }


def test_export_all_skips_incomplete_recommendations(monkeypatch: Any) -> None:
    rows = [
        SimpleNamespace(keyword_id=21, run_id_text="run-2", run_id=None, generation_complete=False),
        SimpleNamespace(keyword_id=22, run_id_text="run-2", run_id=None, generation_complete=True),
    ]

    async def _fake_json(recommendation_id: str, db: Any) -> dict[str, Any]:
        del db
        return {"metadata": {"keyword_id": int(recommendation_id)}, "outputs": {}}

    monkeypatch.setattr(export_module, "_safe_query", lambda *_args, **_kwargs: _FakeQuery(rows))
    monkeypatch.setattr(
        export_module,
        "_load_export_metadata",
        lambda keyword_id, db: export_module.RecommendationExportMetadata(
            keyword_id=keyword_id,
            keyword_text=f"keyword-{keyword_id}",
            niche_id="1",
            tag="STRONG GO",
            final_score=80.0,
            niche_name="Niche",
            generated_at=datetime(2026, 5, 23, 12, 0, tzinfo=UTC),
            llm_cost_usd=0.2,
            generation_complete=True,
            completeness_ratio=1.0,
        ),
    )
    monkeypatch.setattr(export_module, "export_recommendation_json", _fake_json)

    exported = asyncio.run(
        export_module.export_all_recommendations(
            run_id="run-2",
            fmt="json",
            db=object(),
            config={},
        )
    )

    assert exported == {"keyword-22": {"metadata": {"keyword_id": 22}, "outputs": {}}}


def test_export_all_empty_run_returns_empty_dict(monkeypatch: Any) -> None:
    monkeypatch.setattr(export_module, "_safe_query", lambda *_args, **_kwargs: _FakeQuery([]))
    exported = asyncio.run(
        export_module.export_all_recommendations(
            run_id="missing-run",
            fmt="markdown",
            db=object(),
            config={},
        )
    )
    assert exported == {}


def test_export_recommendation_cli_markdown_format(monkeypatch: Any) -> None:
    export_mock = AsyncMock(return_value=("# Recommendation: keyword-1", None))
    monkeypatch.setattr(run_module, "export_recommendation_by_keyword", export_mock)
    monkeypatch.setattr(
        run_module,
        "_recommendation_db_session",
        lambda *_args, **_kwargs: _FakeSessionContext(object()),
    )

    runner = CliRunner()
    result = runner.invoke(
        run_module.cli,
        [
            "export-recommendation",
            "--keyword-id",
            "1",
            "--format",
            "markdown",
        ],
    )

    assert result.exit_code == 0
    assert "# Recommendation: keyword-1" in result.output
    assert export_mock.await_count == 1


def test_export_recommendation_cli_json_format(monkeypatch: Any) -> None:
    export_mock = AsyncMock(return_value=({"metadata": {"keyword_id": 2}, "outputs": {}}, None))
    monkeypatch.setattr(run_module, "export_recommendation_json_by_keyword", export_mock)
    monkeypatch.setattr(
        run_module,
        "_recommendation_db_session",
        lambda *_args, **_kwargs: _FakeSessionContext(object()),
    )

    runner = CliRunner()
    result = runner.invoke(
        run_module.cli,
        [
            "export-recommendation",
            "--keyword-id",
            "2",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert '"keyword_id": 2' in result.output
    assert export_mock.await_count == 1


def test_export_all_cli_creates_files_in_output_dir(monkeypatch: Any, tmp_path: Path) -> None:
    export_mock = AsyncMock(return_value={"keyword one": "# One", "keyword two": "# Two"})
    monkeypatch.setattr(run_module, "export_all_recommendations", export_mock)
    monkeypatch.setattr(run_module, "_load_recommendation_config", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(
        run_module,
        "_recommendation_db_session",
        lambda *_args, **_kwargs: _FakeSessionContext(object()),
    )

    runner = CliRunner()
    result = runner.invoke(
        run_module.cli,
        [
            "export-all-recommendations",
            "--run-id",
            "run-1",
            "--format",
            "markdown",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert len(list(tmp_path.glob("*.md"))) == 2
    assert export_mock.await_count == 1


def test_export_all_cli_uses_latest_run_when_no_run_id(monkeypatch: Any, tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    async def _fake_export_all(*, run_id: str, fmt: str, db: Any, config: dict[str, Any]) -> dict[str, Any]:
        captured["run_id"] = run_id
        captured["fmt"] = fmt
        captured["config"] = config
        del db
        return {"keyword latest": {"metadata": {"keyword_id": 9}, "outputs": {}}}

    monkeypatch.setattr(run_module, "export_all_recommendations", _fake_export_all)
    monkeypatch.setattr(run_module, "_resolve_latest_recommendation_run_id", lambda _db: "latest-run")
    monkeypatch.setattr(run_module, "_load_recommendation_config", lambda *_args, **_kwargs: {"recommendations": {}})
    monkeypatch.setattr(
        run_module,
        "_recommendation_db_session",
        lambda *_args, **_kwargs: _FakeSessionContext(object()),
    )

    runner = CliRunner()
    result = runner.invoke(
        run_module.cli,
        [
            "export-all-recommendations",
            "--format",
            "json",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert captured["run_id"] == "latest-run"
    assert captured["fmt"] == "json"
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_recommendations_summary_command_exists() -> None:
    runner = CliRunner()
    result = runner.invoke(run_module.cli, ["recommendations-summary", "--help"])
    assert result.exit_code == 0
    assert "Report recommendation totals and completion counts." in result.output


def test_recommendations_summary_output_format(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        run_module,
        "_recommendation_db_session",
        lambda *_args, **_kwargs: _FakeSessionContext(object()),
    )
    monkeypatch.setattr(
        run_module,
        "_recommendation_summary_counts",
        lambda _db: {
            "strong_go": 5,
            "conditional_go": 3,
            "total": 10,
            "complete": 8,
            "incomplete": 2,
        },
    )

    runner = CliRunner()
    result = runner.invoke(run_module.cli, ["recommendations-summary"])

    assert result.exit_code == 0
    assert "STRONG GO: 5, CONDITIONAL GO: 3, total: 10, complete: 8, incomplete: 2" in result.output
