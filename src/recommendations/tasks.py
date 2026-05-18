"""Async LLM task executors for recommendations."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

from src.llm import TemplateRenderer
from src.recommendations.context import RecommendationContext
from src.utils.json import safe_json_loads

_RENDERER = TemplateRenderer()


async def generate_gig_titles(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate title candidates from recommendation context."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="gig_titles.j2",
        model="gpt-4o",
        parser=_parse_titles,
    )


async def generate_tag_sets(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate SEO tag sets from recommendation context."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="tag_sets.j2",
        model="gpt-4o-mini",
        parser=_parse_tag_sets,
    )


async def generate_differentiation_angle(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate a positioning statement for a new seller."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="differentiation_angle.j2",
        model="gpt-4o",
        parser=_parse_differentiation_angle,
    )


async def generate_red_flags(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate market-entry red flags."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="red_flags.j2",
        model="gpt-4o",
        parser=_parse_red_flags,
    )


async def _generate_task(
    *,
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
    template_name: str,
    model: str,
    parser: Any,
) -> dict[str, Any]:
    if llm_client is None:
        return {"output": None, "cost_usd": 0.0}
    prompt = _RENDERER.render_template(template_name, _task_context(context))
    try:
        response = await asyncio.to_thread(_complete_with_optional_cache, llm_client, prompt, model, cache)
        parsed = parser(_extract_llm_text(response))
    except Exception:
        return {"output": None, "cost_usd": 0.0}
    return {"output": parsed, "cost_usd": _extract_cost_usd(response)}


def _task_context(context: RecommendationContext) -> dict[str, Any]:
    return {
        "keyword": context.keyword_text,
        "niche_id": context.niche_id,
        "demand_score": context.demand_score,
        "competition_score": context.competition_score,
        "opportunity_score": context.opportunity_score,
        "saturation_score": context.score_components.get("saturation_score", {}).get("score_value")
        if isinstance(context.score_components, Mapping)
        else None,
        "opportunity_tag": context.tag,
        "competitor_titles": [
            item.get("gig_title", "") for item in context.top_competitor_weaknesses if isinstance(item, Mapping)
        ],
        "positioning_gaps": context.positioning_gaps or [],
        "dominant_competitors": context.dominant_sellers or [],
        "top_seller_reviews": context.score_components.get("top_seller_reviews")
        if isinstance(context.score_components, Mapping)
        else None,
    }


def _parse_titles(raw_text: str) -> list[str]:
    payload = safe_json_loads(raw_text)
    titles = payload.get("titles") if isinstance(payload, Mapping) else None
    if not isinstance(titles, list):
        return []
    result: list[str] = []
    for item in titles:
        if isinstance(item, Mapping) and isinstance(item.get("title"), str):
            result.append(item["title"])
    return result


def _parse_tag_sets(raw_text: str) -> list[list[str]]:
    payload = safe_json_loads(raw_text)
    sets = payload.get("tag_sets") if isinstance(payload, Mapping) else None
    if not isinstance(sets, list):
        return []
    parsed: list[list[str]] = []
    for item in sets:
        if isinstance(item, Mapping) and isinstance(item.get("tags"), list):
            parsed.append([str(tag) for tag in item["tags"] if isinstance(tag, str)])
    return parsed


def _parse_differentiation_angle(raw_text: str) -> str:
    payload = safe_json_loads(raw_text)
    if isinstance(payload, Mapping) and isinstance(payload.get("positioning_statement"), str):
        return payload["positioning_statement"]
    return ""


def _parse_red_flags(raw_text: str) -> list[str]:
    payload = safe_json_loads(raw_text)
    risks = payload.get("risks") if isinstance(payload, Mapping) else None
    if not isinstance(risks, list):
        return []
    return [str(item) for item in risks if isinstance(item, str)]


def _extract_cost_usd(response: Any) -> float:
    metadata = getattr(response, "metadata", None)
    if isinstance(metadata, Mapping):
        value = metadata.get("estimated_cost_usd")
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def _complete_with_optional_cache(llm_client: Any, prompt: str, model: str, cache: Any | None) -> Any:
    try:
        return llm_client.complete(prompt=prompt, model=model, cache=cache)
    except TypeError:
        return llm_client.complete(prompt=prompt, model=model)


def _extract_llm_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    text = getattr(response, "text", None)
    return text if isinstance(text, str) else str(response)
