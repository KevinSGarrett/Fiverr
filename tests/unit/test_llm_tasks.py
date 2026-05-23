"""Unit tests for Stage 13 LLM task executors."""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import src.recommendations.llm_tasks as llm_tasks_module
from src.recommendations.contracts import RecommendationContext
from src.recommendations.llm_tasks import (
    context_to_dict,
    estimate_llm_cost,
    task_buyer_persona,
    task_description_outline,
    task_differentiation_angle,
    task_faq_entries,
    task_gig_titles,
    task_niche_viability,
    task_package_structure,
    task_red_flags,
    task_tag_sets,
    task_thumbnail_direction,
    task_upsell_structure,
    validate_and_parse_llm_response,
)
from src.recommendations.schemas import GigTitlesOutput


class _TemplateStub:
    def render(self, **_: Any) -> str:
        return "rendered prompt"


def _context() -> RecommendationContext:
    return RecommendationContext(
        keyword_id=101,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-101",
        tag="STRONG GO",
        final_score=82.3,
        confidence_modifier=0.9,
        demand_score=74.0,
        competition_score=41.0,
        opportunity_score=70.0,
        saturation_score=33.0,
        feasibility_score=63.0,
        top_competitor_weaknesses=[
            {
                "gig_title": "I will automate your business tasks",
                "weaknesses": [{"weakness": "slow communication", "severity": "HIGH"}],
                "tags": ["automation", "python", "workflow", "api", "scripts"],
            }
        ],
        reviewer_pain_points=["slow updates", "scope confusion"],
        market_price_range={
            "basic": {"median": 95},
            "standard": {"median": 210},
            "premium": {"median": 360},
            "hard_exclusions": ["full app development"],
        },
        top_buyer_complaints=["late delivery", "unclear process"],
        top_buyer_praise=["clear onboarding", "fast response"],
        score_data={
            "trend_score": 59.0,
            "profitability_score": 67.0,
            "weakness_score": 61.0,
            "total_result_count": 128,
            "opportunity_narrative": "Rising demand in operations automation services.",
        },
        competitor_data={
            "cluster_synthesis_narrative": "Most competitors over-index on generic messaging.",
            "thumbnail_class_distribution": {"text-heavy": 14, "minimal": 5},
            "competitor_extras": [{"name": "24h delivery", "price": 25}],
        },
        review_insights={"cluster_synthesis_narrative": "buyers want speed and predictability"},
        external_signals={"trends_slope": "up", "reddit_intent_score": 7.2},
        positioning_gaps=[{"gap": "proof-based messaging", "evidence": "few case studies"}],
    )


def _gig_titles_payload() -> dict[str, Any]:
    titles = []
    for index in range(1, 6):
        title = f"I will build automation workflow package option {index} with clear outcomes"
        titles.append(
            {
                "title": title,
                "positioning_angle": "outcome",
                "character_count": len(title),
                "primary_keyword_present": True,
            }
        )
    return {"titles": titles}


def _tag_sets_payload() -> dict[str, Any]:
    return {
        "tag_sets": [
            ["python automation", "workflow scripts", "api integration", "task bot", "etl setup"],
            ["automation expert", "ops workflow", "crm workflow", "zapier flow", "notion setup"],
            ["automation service", "python api", "business process", "data workflow", "automation audit"],
            ["team automation", "saas operations", "process design", "ops support", "automation strategy"],
            ["workflow mapping", "delivery fast", "support setup", "custom scripts", "integration help"],
        ]
    }


def _package_structure_payload() -> dict[str, Any]:
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


def _description_outline_payload() -> dict[str, Any]:
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


def _faq_entries_payload() -> dict[str, Any]:
    return {
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


def _differentiation_payload() -> dict[str, Any]:
    return {
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


def _buyer_persona_payload() -> dict[str, Any]:
    return {
        "name": "Alex",
        "role": "Operations Manager",
        "company_stage": "Early growth SaaS",
        "pain_points": ["manual handoffs", "missed updates"],
        "budget_range": "$150-$500",
        "decision_trigger": "Process failures are delaying customer onboarding.",
        "where_they_search": "Fiverr and operations communities",
        "what_makes_them_buy": "Clear scope and confidence in delivery speed.",
    }


def _thumbnail_direction_payload() -> dict[str, Any]:
    return {
        "concept": "Show before-and-after workflow visibility with clean UI style.",
        "style": "Dark blue with bright accent highlights",
        "elements_to_include": ["workflow icons", "checklist", "timeline"],
        "elements_to_avoid": ["stock-photo faces"],
        "differentiation_note": "Use quantified outcomes to stand out from generic text-only thumbnails.",
    }


def _upsell_structure_payload() -> dict[str, Any]:
    return {
        "extras": [
            {"name": "Priority 24h update", "price": 25, "description": "Priority response and update cycle."},
            {"name": "Post-launch tuning", "price": 45, "description": "Optimization pass after first week."},
        ]
    }


def _red_flags_payload() -> dict[str, Any]:
    return {
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


def _niche_viability_payload() -> dict[str, Any]:
    return {
        "viability_assessment": (
            "Demand remains healthy and competitor weakness signals suggest room for a clear newcomer "
            "position. Entry is viable when messaging stays specific and onboarding is structured."
        ),
        "timing_assessment": "Timing is favorable while buyer intent is still rising.",
        "risk_summary": "Primary risk is weak trust signals early in launch.",
        "blunt_recommendation": "Enter now with a focused scope and proof-first positioning.",
    }


def _run_success(task_fn: Any, payload: dict[str, Any]) -> tuple[Any, SimpleNamespace]:
    llm_client = SimpleNamespace(complete=AsyncMock(return_value=json.dumps(payload)))
    with patch("src.recommendations.llm_tasks.load_template", return_value=_TemplateStub()):
        result = asyncio.run(task_fn(_context(), llm_client, cache=None))
    return result, llm_client


def _run_failure(task_fn: Any, caplog: pytest.LogCaptureFixture) -> tuple[Any, SimpleNamespace]:
    llm_client = SimpleNamespace(complete=AsyncMock(side_effect=RuntimeError("llm exploded")))
    with patch("src.recommendations.llm_tasks.load_template", return_value=_TemplateStub()):
        with caplog.at_level(logging.WARNING):
            result = asyncio.run(task_fn(_context(), llm_client, cache=None))
    return result, llm_client


def test_task_gig_titles_returns_output_on_success() -> None:
    result, _ = _run_success(task_gig_titles, _gig_titles_payload())
    assert result is not None
    assert len(result.titles) == 5


def test_task_gig_titles_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_gig_titles, caplog)
    assert result is None
    assert "LLM task gig_titles failed" in caplog.text


def test_task_tag_sets_returns_output_on_success() -> None:
    result, _ = _run_success(task_tag_sets, _tag_sets_payload())
    assert result is not None
    assert len(result.tag_sets) == 5


def test_task_tag_sets_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_tag_sets, caplog)
    assert result is None
    assert "LLM task tag_sets failed" in caplog.text


def test_task_package_structure_returns_output_on_success() -> None:
    result, _ = _run_success(task_package_structure, _package_structure_payload())
    assert result is not None
    assert result.premium.price > result.standard.price > result.basic.price


def test_task_package_structure_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_package_structure, caplog)
    assert result is None
    assert "LLM task package_structure failed" in caplog.text


def test_task_description_outline_returns_output_on_success() -> None:
    result, _ = _run_success(task_description_outline, _description_outline_payload())
    assert result is not None
    assert len(result.sections) >= 4


def test_task_description_outline_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_description_outline, caplog)
    assert result is None
    assert "LLM task description_outline failed" in caplog.text


def test_task_faq_entries_returns_output_on_success() -> None:
    result, _ = _run_success(task_faq_entries, _faq_entries_payload())
    assert result is not None
    assert len(result.faq_entries) >= 5


def test_task_faq_entries_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_faq_entries, caplog)
    assert result is None
    assert "LLM task faq_entries failed" in caplog.text


def test_task_differentiation_angle_returns_output_on_success() -> None:
    result, _ = _run_success(task_differentiation_angle, _differentiation_payload())
    assert result is not None
    assert result.positioning_statement


def test_task_differentiation_angle_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_differentiation_angle, caplog)
    assert result is None
    assert "LLM task differentiation_angle failed" in caplog.text


def test_task_buyer_persona_returns_output_on_success() -> None:
    result, _ = _run_success(task_buyer_persona, _buyer_persona_payload())
    assert result is not None
    assert result.name == "Alex"


def test_task_buyer_persona_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_buyer_persona, caplog)
    assert result is None
    assert "LLM task buyer_persona failed" in caplog.text


def test_task_thumbnail_direction_returns_output_on_success() -> None:
    result, _ = _run_success(task_thumbnail_direction, _thumbnail_direction_payload())
    assert result is not None
    assert result.concept


def test_task_thumbnail_direction_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_thumbnail_direction, caplog)
    assert result is None
    assert "LLM task thumbnail_direction failed" in caplog.text


def test_task_upsell_structure_returns_output_on_success() -> None:
    result, _ = _run_success(task_upsell_structure, _upsell_structure_payload())
    assert result is not None
    assert len(result.extras) == 2


def test_task_upsell_structure_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_upsell_structure, caplog)
    assert result is None
    assert "LLM task upsell_structure failed" in caplog.text


def test_task_red_flags_returns_output_on_success() -> None:
    result, _ = _run_success(task_red_flags, _red_flags_payload())
    assert result is not None
    assert result.overall_risk_level == "MEDIUM"


def test_task_red_flags_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_red_flags, caplog)
    assert result is None
    assert "LLM task red_flags failed" in caplog.text


def test_task_niche_viability_returns_output_on_success() -> None:
    result, _ = _run_success(task_niche_viability, _niche_viability_payload())
    assert result is not None
    assert "Demand remains healthy" in result.viability_assessment


def test_task_niche_viability_returns_none_on_llm_failure(caplog: pytest.LogCaptureFixture) -> None:
    result, _ = _run_failure(task_niche_viability, caplog)
    assert result is None
    assert "LLM task niche_viability failed" in caplog.text


def test_task_uses_cache_hit() -> None:
    cached_json = GigTitlesOutput.model_validate(_gig_titles_payload()).model_dump_json()
    llm_client = SimpleNamespace(complete=AsyncMock(return_value=json.dumps(_gig_titles_payload())))
    cache = SimpleNamespace(get=AsyncMock(return_value=cached_json), set=AsyncMock())
    result = asyncio.run(task_gig_titles(_context(), llm_client, cache=cache))
    assert result is not None
    assert len(result.titles) == 5
    assert llm_client.complete.await_count == 0
    assert cache.set.await_count == 0


def test_task_cache_miss_then_hit_across_calls() -> None:
    class _Cache:
        def __init__(self) -> None:
            self._payloads: dict[str, str] = {}

        async def get(self, cache_key: str) -> str | None:
            return self._payloads.get(cache_key)

        async def set(self, cache_key: str, payload: str) -> None:
            self._payloads[cache_key] = payload

    llm_client = SimpleNamespace(complete=AsyncMock(return_value=json.dumps(_gig_titles_payload())))
    cache = _Cache()
    with patch("src.recommendations.llm_tasks.load_template", return_value=_TemplateStub()):
        first = asyncio.run(task_gig_titles(_context(), llm_client, cache=cache))
        second = asyncio.run(task_gig_titles(_context(), llm_client, cache=cache))

    assert first is not None
    assert second is not None
    assert llm_client.complete.await_count == 1


def test_task_returns_none_when_llm_client_is_none() -> None:
    result = asyncio.run(task_gig_titles(_context(), llm_client=None, cache=None))
    assert result is None


def test_context_to_dict_includes_all_required_fields() -> None:
    mapped = context_to_dict(_context())
    required_fields = {
        "niche_name",
        "keyword_text",
        "total_result_count",
        "competition_score",
        "demand_score",
        "top_competitor_weaknesses",
        "starter_price_basic",
        "starter_price_standard",
        "starter_price_premium",
        "hard_exclusions",
        "top_buyer_complaints",
        "positioning_gaps",
        "cluster_synthesis_narrative",
        "top_buyer_praise",
        "trends_slope",
        "reddit_intent_score",
        "thumbnail_class_distribution",
        "competitor_extras",
        "trend_score",
        "profitability_score",
        "weakness_score",
        "opportunity_narrative",
    }
    assert required_fields.issubset(mapped.keys())


def test_context_to_dict_covers_all_template_variables() -> None:
    sparse = RecommendationContext(
        keyword_id=1,
        keyword_text="automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-sparse",
        top_competitor_weaknesses=[],
    )
    mapped = context_to_dict(sparse)
    assert mapped["starter_price_basic"] == 0
    assert mapped["starter_price_standard"] == 0
    assert mapped["starter_price_premium"] == 0
    assert mapped["hard_exclusions"] == []
    assert mapped["cluster_synthesis_narrative"] == "Not available"
    assert mapped["thumbnail_class_distribution"] == {}
    assert mapped["competitor_extras"] == []


def test_parse_strips_markdown_fences() -> None:
    raw = """```json\n{"value": 1}\n```"""
    assert validate_and_parse_llm_response(raw) == {"value": 1}


def test_parse_nested_markdown_fences_returns_none() -> None:
    raw = """```json
```json
{"value": 1}
```
```"""
    assert validate_and_parse_llm_response(raw) is None


def test_parse_returns_none_on_invalid_json() -> None:
    assert validate_and_parse_llm_response("not-json") is None


def test_parse_valid_json_returns_dict() -> None:
    assert validate_and_parse_llm_response('{"status":"ok"}') == {"status": "ok"}


def test_estimate_cost_returns_float() -> None:
    cost = estimate_llm_cost("prompt text", "response text", "gpt-4o-mini")
    assert isinstance(cost, float)
    assert cost >= 0.0


def test_estimate_cost_with_empty_strings_is_zero() -> None:
    assert estimate_llm_cost("", "", "gpt-4o-mini") == 0.0


def test_estimate_cost_gpt4o_mini_pricing() -> None:
    prompt = "a" * 400
    response = "b" * 200
    expected = (100 / 1000) * 0.000150 + (50 / 1000) * 0.000600
    assert estimate_llm_cost(prompt, response, "gpt-4o-mini") == pytest.approx(expected)


def test_all_tasks_are_async_coroutines() -> None:
    task_functions = [
        task_gig_titles,
        task_tag_sets,
        task_package_structure,
        task_description_outline,
        task_faq_entries,
        task_differentiation_angle,
        task_buyer_persona,
        task_thumbnail_direction,
        task_upsell_structure,
        task_red_flags,
        task_niche_viability,
    ]
    assert all(inspect.iscoroutinefunction(task) for task in task_functions)


def test_recommendations_package_exports_all_tasks_and_schemas() -> None:
    import src.recommendations as recommendations

    expected_exports = [
        "task_gig_titles",
        "task_tag_sets",
        "task_package_structure",
        "task_description_outline",
        "task_faq_entries",
        "task_differentiation_angle",
        "task_buyer_persona",
        "task_thumbnail_direction",
        "task_upsell_structure",
        "task_red_flags",
        "task_niche_viability",
        "GigTitlesOutput",
        "TagSetsOutput",
        "PackageStructureOutput",
        "DescriptionOutlineOutput",
        "FaqEntriesOutput",
        "DifferentiationAngleOutput",
        "BuyerPersonaOutput",
        "ThumbnailDirectionOutput",
        "UpsellStructureOutput",
        "RedFlagsOutput",
        "NicheViabilityOutput",
        "RecommendationOutput",
    ]
    assert all(hasattr(recommendations, export_name) for export_name in expected_exports)


def test_extract_response_text_supports_mapping_and_attribute_sources() -> None:
    assert llm_tasks_module._extract_response_text({"text": "from-mapping"}) == "from-mapping"
    assert llm_tasks_module._extract_response_text(SimpleNamespace(text="from-attr")) == "from-attr"
    assert llm_tasks_module._extract_response_text(42) == "42"


def test_validate_and_parse_rejects_non_object_json() -> None:
    assert validate_and_parse_llm_response("[1, 2, 3]") is None


def test_resolve_maybe_await_and_coerce_float_helpers() -> None:
    assert asyncio.run(llm_tasks_module._resolve_maybe_await(7)) == 7
    assert llm_tasks_module._coerce_float("not-a-number") is None


def test_context_to_dict_handles_non_list_weaknesses_and_nested_scores() -> None:
    context = RecommendationContext(
        keyword_id=901,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id="run-nested",
        top_competitor_weaknesses="unexpected-string",  # type: ignore[arg-type]
        market_price_range={
            "starter_price_basic": "120",
            "standard": {"starter_price": 230},
            "premium": {"median": 310},
        },
        score_data={
            "trend_score": {"score_value": "58.5"},
            "profitability_score": {"score_value": 61.0},
            "weakness_score": {"score_value": "invalid"},
        },
        score_components={"weakness_score": {"score_value": "44.0"}},
    )

    mapped = context_to_dict(context)
    assert mapped["top_competitor_weaknesses"] == []
    assert mapped["trend_score"] == 58.5
    assert mapped["profitability_score"] == 61.0
    assert mapped["weakness_score"] == 44.0
    assert mapped["starter_price_basic"] == 120
    assert mapped["starter_price_standard"] == 230
    assert mapped["starter_price_premium"] == 310


def test_cache_get_returns_none_on_cache_exception() -> None:
    class _FailingCache:
        async def get(self, _cache_key: str) -> Any:
            raise RuntimeError("cache unavailable")

    assert asyncio.run(llm_tasks_module._cache_get(_FailingCache(), "cache-key")) is None


def test_cache_set_falls_back_after_type_error() -> None:
    class _LegacyCache:
        def __init__(self) -> None:
            self.calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

        async def set(self, *args: Any, **kwargs: Any) -> None:
            self.calls.append((args, kwargs))
            if len(self.calls) == 1:
                raise TypeError("legacy signature")

    cache = _LegacyCache()
    asyncio.run(llm_tasks_module._cache_set(cache, "cache-key", "payload"))

    assert len(cache.calls) == 2
    assert cache.calls[1][1]["model"] == "gpt-4o-mini"
    assert cache.calls[1][1]["temperature"] == 0.0
    assert cache.calls[1][1]["prompt_text"] == "cache-key"


def test_parse_cached_payload_supports_mapping_input() -> None:
    parsed = llm_tasks_module._parse_cached_payload(GigTitlesOutput, _gig_titles_payload())
    assert parsed is not None
    assert len(parsed.titles) == 5


def test_call_llm_requires_complete_and_supports_typeerror_fallback() -> None:
    with pytest.raises(AttributeError):
        asyncio.run(llm_tasks_module._call_llm(object(), prompt="prompt", model="gpt-4o-mini", max_tokens=50))

    class _LegacyClient:
        def __init__(self) -> None:
            self.calls: list[int | None] = []

        def complete(self, *, prompt: str, model: str, max_tokens: int | None = None) -> Any:
            del prompt, model
            self.calls.append(max_tokens)
            if max_tokens is not None:
                raise TypeError("max_tokens not accepted")
            return {"text": "ok"}

    client = _LegacyClient()
    response = asyncio.run(llm_tasks_module._call_llm(client, prompt="prompt", model="gpt-4o-mini", max_tokens=50))
    assert response == "ok"
    assert client.calls == [50, None]


def test_execute_task_handles_parse_failures_and_invalid_cache_payloads() -> None:
    bad_json_client = SimpleNamespace(complete=AsyncMock(return_value="not-json"))
    with patch("src.recommendations.llm_tasks.load_template", return_value=_TemplateStub()):
        parse_failure_result = asyncio.run(
            llm_tasks_module._execute_task(
                context=_context(),
                llm_client=bad_json_client,
                cache=None,
                task_name="gig_titles",
                template_file="gig_titles.j2",
                output_model=GigTitlesOutput,
                max_tokens=200,
            )
        )
    assert parse_failure_result is None

    cache = SimpleNamespace(get=AsyncMock(return_value='{"titles": []}'), set=AsyncMock())
    good_json_client = SimpleNamespace(complete=AsyncMock(return_value=json.dumps(_gig_titles_payload())))
    with patch("src.recommendations.llm_tasks.load_template", return_value=_TemplateStub()):
        recovered = asyncio.run(
            llm_tasks_module._execute_task(
                context=_context(),
                llm_client=good_json_client,
                cache=cache,
                task_name="gig_titles",
                template_file="gig_titles.j2",
                output_model=GigTitlesOutput,
                max_tokens=200,
            )
        )
    assert recovered is not None
    assert good_json_client.complete.await_count == 1

