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


async def generate_package_structure(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate package tier structure for basic/standard/premium."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="package_structure.j2",
        model="gpt-4o",
        parser=_parse_package_structure,
    )


async def generate_description_outline(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate an outline for a strong gig description."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="description_outline.j2",
        model="gpt-4o",
        parser=_parse_description_outline,
    )


async def generate_faq_entries(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate FAQ entries covering objections and expectations."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="faq_entries.j2",
        model="gpt-4o-mini",
        parser=_parse_faq_entries,
    )


async def generate_buyer_persona(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate an inferred buyer persona for this keyword."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="buyer_persona.j2",
        model="gpt-4o-mini",
        parser=_parse_buyer_persona,
    )


async def generate_thumbnail_direction(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate thumbnail creative direction guidance."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="thumbnail_direction.j2",
        model="gpt-4o-mini",
        parser=_parse_thumbnail_direction,
    )


async def generate_upsell_structure(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate upsell opportunities to increase AOV."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="upsell_structure.j2",
        model="gpt-4o-mini",
        parser=_parse_upsell_structure,
    )


async def generate_niche_viability(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
) -> dict[str, Any]:
    """Generate niche viability and execution posture assessment."""
    return await _generate_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        template_name="niche_viability.j2",
        model="gpt-4o",
        parser=_parse_niche_viability,
    )


RECOMMENDATION_FIELD_NAMES = [
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
]


async def generate_recommendation(
    keyword_id: int,
    context: RecommendationContext,
    llm_client: Any,
    cache: Any | None,
    db: Any,
) -> dict[str, Any]:
    """Run all 11 LLM tasks concurrently for a single keyword."""
    del keyword_id, db
    tasks = [
        generate_gig_titles(context, llm_client, cache),
        generate_tag_sets(context, llm_client, cache),
        generate_package_structure(context, llm_client, cache),
        generate_description_outline(context, llm_client, cache),
        generate_faq_entries(context, llm_client, cache),
        generate_differentiation_angle(context, llm_client, cache),
        generate_buyer_persona(context, llm_client, cache),
        generate_thumbnail_direction(context, llm_client, cache),
        generate_upsell_structure(context, llm_client, cache),
        generate_red_flags(context, llm_client, cache),
        generate_niche_viability(context, llm_client, cache),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    recommendation_data: dict[str, Any] = {}
    all_succeeded = True
    total_cost = 0.0

    for field_name, result in zip(RECOMMENDATION_FIELD_NAMES, results, strict=False):
        if isinstance(result, Exception) or not isinstance(result, Mapping):
            recommendation_data[field_name] = None
            all_succeeded = False
            continue

        output = result.get("output")
        recommendation_data[field_name] = output
        if output is None:
            all_succeeded = False
        total_cost += _to_float(result.get("cost_usd"), default=0.0)

    recommendation_data["generation_complete"] = all_succeeded
    recommendation_data["llm_cost_usd"] = total_cost
    return recommendation_data


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


def _parse_package_structure(raw_text: str) -> dict[str, Any]:
    payload = safe_json_loads(raw_text)
    return dict(payload) if isinstance(payload, Mapping) else {}


def _parse_description_outline(raw_text: str) -> dict[str, Any]:
    payload = safe_json_loads(raw_text)
    return dict(payload) if isinstance(payload, Mapping) else {}


def _parse_faq_entries(raw_text: str) -> list[dict[str, Any]]:
    payload = safe_json_loads(raw_text)
    entries = payload.get("faq_entries") if isinstance(payload, Mapping) else None
    if not isinstance(entries, list):
        return []
    return [dict(item) for item in entries if isinstance(item, Mapping)]


def _parse_buyer_persona(raw_text: str) -> dict[str, Any]:
    payload = safe_json_loads(raw_text)
    return dict(payload) if isinstance(payload, Mapping) else {}


def _parse_thumbnail_direction(raw_text: str) -> str:
    payload = safe_json_loads(raw_text)
    if isinstance(payload, Mapping):
        for key in ("thumbnail_direction", "creative_direction", "direction"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
    return ""


def _parse_upsell_structure(raw_text: str) -> list[Any]:
    payload = safe_json_loads(raw_text)
    if not isinstance(payload, Mapping):
        return []
    for key in ("upsells", "upsell_opportunities"):
        value = payload.get(key)
        if isinstance(value, list):
            return list(value)
    return []


def _parse_niche_viability(raw_text: str) -> dict[str, Any]:
    payload = safe_json_loads(raw_text)
    return dict(payload) if isinstance(payload, Mapping) else {}


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


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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
