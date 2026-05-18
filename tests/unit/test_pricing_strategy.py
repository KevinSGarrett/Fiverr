"""Unit tests for Task 12 pricing strategy schema and executor."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import ValidationError
from src.recommendations.context import RecommendationContext
from src.recommendations.tasks import (
    RECOMMENDATION_FIELD_NAMES,
    _complete_pricing_strategy,
    _extract_usage_cost,
    generate_pricing_strategy,
    generate_recommendation,
)
from src.schemas.pricing_output import EntryPrices, PricingStrategy


def _valid_strategy_payload() -> dict[str, Any]:
    return {
        "entry_prices": {
            "basic": 50,
            "standard": 100,
            "premium": 180,
            "lead_tier": "basic",
            "lead_tier_reasoning": "Lead with basic to maximize early conversion and collect first reviews quickly.",
        },
        "acquisition_prices": {
            "basic": 40,
            "standard": 80,
            "premium": 150,
            "acquisition_period": "first 5 orders",
        },
        "price_ladder": [
            {"milestone_reviews": 5, "basic": 50, "standard": 100, "premium": 180, "adjustment_rationale": "Initial baseline."},
            {"milestone_reviews": 10, "basic": 60, "standard": 120, "premium": 210, "adjustment_rationale": "Early proof gained."},
            {"milestone_reviews": 25, "basic": 75, "standard": 145, "premium": 250, "adjustment_rationale": "Demand improves and delivery confidence rises."},
            {"milestone_reviews": 50, "basic": 90, "standard": 170, "premium": 290, "adjustment_rationale": "Positioning strengthens with social proof."},
        ],
        "strategy_narrative": (
            "Set entry pricing in the lower-middle cluster to win first conversions while avoiding a pure bargain signal. "
            "Use a measured ladder tied to review milestones so each increase is justified by proven execution and buyer trust. "
            "Preserve perceived value by widening package separation and emphasizing faster turnaround plus optional extras."
        ),
        "pricing_risks": [
            {"risk": "Undercutting too hard can attract low-quality buyers.", "severity": "MEDIUM", "mitigation": "Keep scope tight and enforce revisions limits."}
        ],
        "recommended_extras": [
            {"name": "24-hour delivery", "price": 25, "rationale": "Captures urgent buyers and improves average order value."},
            {"name": "Source file handoff", "price": 20, "rationale": "Adds perceived professionalism and monetizes final assets."},
        ],
        "projected_aov": {"at_entry": 72.0, "at_50_reviews": 118.0, "aov_growth_pct": 63.9},
    }


def _pricing_context() -> RecommendationContext:
    return RecommendationContext(
        keyword_text="python automation",
        niche_id=12,
        niche_name="Automation",
        tag="STRONG_GO",
        final_score=83.2,
        price_distribution={
            "basic": {"median": 55, "mean": 60, "min": 20, "max": 180, "q1": 40, "q3": 85, "clusters": [], "gaps": []},
            "standard": {"median": 110, "min": 40, "max": 260},
            "premium": {"median": 190, "min": 80, "max": 500},
        },
        top_competitor_weaknesses=[],
    )


def _success_task(output: Any, cost: float = 0.01) -> Any:
    async def _inner(context: RecommendationContext, llm_client: Any, cache: Any) -> dict[str, Any]:
        del context, llm_client, cache
        return {"output": output, "cost_usd": cost}

    return _inner


def test_pricing_strategy_valid_construction() -> None:
    strategy = PricingStrategy(**_valid_strategy_payload())
    assert strategy.entry_prices.basic == 50


def test_entry_prices_standard_above_basic() -> None:
    prices = EntryPrices(
        basic=25,
        standard=40,
        premium=80,
        lead_tier="basic",
        lead_tier_reasoning="Basic is easier to close quickly for first reviews and conversion momentum.",
    )
    assert prices.standard > prices.basic


def test_entry_prices_premium_above_standard() -> None:
    prices = EntryPrices(
        basic=25,
        standard=40,
        premium=80,
        lead_tier="standard",
        lead_tier_reasoning="Standard remains the best margin package once trust starts to increase.",
    )
    assert prices.premium > prices.standard


def test_entry_prices_invalid_order() -> None:
    with pytest.raises(ValidationError):
        EntryPrices(
            basic=60,
            standard=50,
            premium=80,
            lead_tier="basic",
            lead_tier_reasoning="Broken ordering should fail validation in schema construction.",
        )


def test_price_ladder_ascending() -> None:
    strategy = PricingStrategy(**_valid_strategy_payload())
    assert [step.basic for step in strategy.price_ladder] == [50, 60, 75, 90]


def test_price_ladder_too_few_steps() -> None:
    payload = _valid_strategy_payload()
    payload["price_ladder"] = payload["price_ladder"][:3]
    with pytest.raises(ValidationError):
        PricingStrategy(**payload)


def test_generate_pricing_strategy_no_price_distribution() -> None:
    context = RecommendationContext(keyword_text="python automation", niche_id=12)
    result = asyncio.run(generate_pricing_strategy(context, llm_client=Mock(), cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_generate_pricing_strategy_mock_llm() -> None:
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(
        text=json.dumps({"pricing_strategy": _valid_strategy_payload()}),
        usage_cost=0.015,
    )
    result = asyncio.run(generate_pricing_strategy(_pricing_context(), llm_client=llm_client, cache=None))
    assert isinstance(result["output"], dict)
    assert result["output"]["entry_prices"]["basic"] == 50
    assert result["cost_usd"] == 0.015


def test_generate_pricing_strategy_llm_failure() -> None:
    llm_client = Mock()
    llm_client.complete.side_effect = RuntimeError("llm unavailable")
    result = asyncio.run(generate_pricing_strategy(_pricing_context(), llm_client=llm_client, cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_generate_pricing_strategy_invalid_json() -> None:
    llm_client = Mock()
    llm_client.complete.return_value = SimpleNamespace(text="not-json", usage_cost=0.01)
    result = asyncio.run(generate_pricing_strategy(_pricing_context(), llm_client=llm_client, cache=None))
    assert result["output"] is None


def test_generate_recommendation_12_tasks(monkeypatch: Any) -> None:
    context = _pricing_context()
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _success_task(["t1"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _success_task([["a", "b"]]))
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _success_task({"basic": {}}))
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _success_task({"overview": "x"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _success_task([{"question": "q", "answer": "a"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _success_task("angle"))
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _success_task({"persona": "ops"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _success_task("direction"))
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _success_task([{"name": "u1"}]))
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _success_task(["risk"]))
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _success_task({"verdict": "good"}))
    monkeypatch.setattr("src.recommendations.tasks.generate_pricing_strategy", _success_task({"entry_prices": {}}))
    result = asyncio.run(generate_recommendation(101, context, llm_client=Mock(), cache=None, db=Mock()))
    assert all(name in result for name in RECOMMENDATION_FIELD_NAMES)
    assert len([name for name in RECOMMENDATION_FIELD_NAMES if name in result]) == 12


def test_field_names_count() -> None:
    assert len(RECOMMENDATION_FIELD_NAMES) == 12


def test_entry_prices_premium_must_exceed_standard() -> None:
    with pytest.raises(ValidationError):
        EntryPrices(
            basic=25,
            standard=40,
            premium=40,
            lead_tier="basic",
            lead_tier_reasoning="This payload intentionally sets an invalid premium ordering for coverage.",
        )


def test_pricing_strategy_ladder_descending_rejected() -> None:
    payload = _valid_strategy_payload()
    payload["price_ladder"][1]["basic"] = 45
    with pytest.raises(ValidationError):
        PricingStrategy(**payload)


def test_generate_pricing_strategy_llm_none_with_price_distribution() -> None:
    context = _pricing_context()
    result = asyncio.run(generate_pricing_strategy(context, llm_client=None, cache=None))
    assert result == {"output": None, "cost_usd": 0.0}


def test_complete_pricing_strategy_requires_complete_method() -> None:
    class MissingComplete:
        pass

    with pytest.raises(AttributeError):
        asyncio.run(_complete_pricing_strategy(MissingComplete(), "prompt"))


def test_complete_pricing_strategy_falls_back_without_response_format() -> None:
    class StrictClient:
        def complete(self, **kwargs: Any) -> Any:
            if "response_format" in kwargs:
                raise TypeError("response_format unsupported")
            return SimpleNamespace(text='{"pricing_strategy": {}}')

    response = asyncio.run(_complete_pricing_strategy(StrictClient(), "prompt"))
    assert response.text == '{"pricing_strategy": {}}'


def test_complete_pricing_strategy_awaits_coroutine_result() -> None:
    class AsyncClient:
        async def complete(self, **kwargs: Any) -> Any:
            del kwargs
            return SimpleNamespace(text='{"pricing_strategy": {}}', usage_cost=0.02)

    response = asyncio.run(_complete_pricing_strategy(AsyncClient(), "prompt"))
    assert response.usage_cost == 0.02


def test_extract_usage_cost_falls_back_to_zero_on_bad_usage() -> None:
    response = SimpleNamespace(usage_cost="not-a-number", metadata={"estimated_cost_usd": "n/a"})
    assert _extract_usage_cost(response) == 0.0
