"""Concurrent Stage 13 recommendation executor."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from src.recommendations.contracts import RecommendationContext
from src.recommendations.llm_tasks import (
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
)
from src.recommendations.schemas import RecommendationOutput

_TASK_FIELD_ORDER: list[str] = [
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
    "niche_viability",
]

_TASK_COST_ESTIMATES_USD: dict[str, float] = {
    "gig_titles": 0.012,
    "tag_sets": 0.001,
    "package_structure": 0.018,
    "description_outline": 0.024,
    "faq_entries": 0.001,
    "differentiation_angle": 0.020,
    "buyer_persona": 0.001,
    "thumbnail_direction": 0.001,
    "upsell_structure": 0.001,
    "red_flags": 0.015,
    "niche_viability": 0.018,
}


def _run_async(coro: Any) -> Any:
    """Run coroutine safely from sync/async callers."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


async def generate_recommendation_async(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> RecommendationOutput:
    """Runs all 12 recommendation LLM tasks concurrently (including pricing strategy)."""
    tasks = [
        task_gig_titles(context, llm_client, cache),
        task_tag_sets(context, llm_client, cache),
        task_package_structure(context, llm_client, cache),
        task_description_outline(context, llm_client, cache),
        task_faq_entries(context, llm_client, cache),
        task_differentiation_angle(context, llm_client, cache),
        task_buyer_persona(context, llm_client, cache),
        task_thumbnail_direction(context, llm_client, cache),
        task_upsell_structure(context, llm_client, cache),
        task_red_flags(context, llm_client, cache),
        task_niche_viability(context, llm_client, cache),
    ]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    task_payload: dict[str, Any] = {}
    failed_tasks: list[str] = []
    normalized_outputs: list[Any] = []
    for field_name, result in zip(_TASK_FIELD_ORDER, raw_results, strict=False):
        if isinstance(result, Exception) or result is None:
            task_payload[field_name] = None
            failed_tasks.append(field_name)
            normalized_outputs.append(None)
            continue
        task_payload[field_name] = result
        normalized_outputs.append(result)

    generation_complete = len(failed_tasks) == 0 and len(raw_results) == len(_TASK_FIELD_ORDER)
    total_llm_cost_usd = track_llm_costs(normalized_outputs, context)
    return RecommendationOutput(
        **task_payload,
        generation_complete=generation_complete,
        failed_tasks=failed_tasks,
        total_llm_cost_usd=total_llm_cost_usd,
    )


def generate_recommendation(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> RecommendationOutput:
    """Synchronous wrapper around concurrent recommendation generation."""
    return _run_async(generate_recommendation_async(context=context, llm_client=llm_client, cache=cache))


def track_llm_costs(outputs: list[Any], context: RecommendationContext) -> float:
    """Estimate aggregate LLM cost for completed tasks."""
    del context
    total_cost = 0.0
    for field_name, output in zip(_TASK_FIELD_ORDER, outputs, strict=False):
        if output is None:
            continue
        explicit_cost = getattr(output, "cost_usd", None)
        if explicit_cost is not None:
            try:
                total_cost += float(explicit_cost)
                continue
            except (TypeError, ValueError):
                pass
        total_cost += _TASK_COST_ESTIMATES_USD.get(field_name, 0.0)
    return round(total_cost, 6)


__all__ = [
    "generate_recommendation",
    "generate_recommendation_async",
    "track_llm_costs",
]
