"""Stage 13 LLM recommendation task executors."""

from __future__ import annotations

import inspect
import json
import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypeVar

from jinja2 import Environment, FileSystemLoader, Template
from pydantic import BaseModel, ValidationError

from src.recommendations.contracts import RecommendationContext
from src.recommendations.schemas import (
    BuyerPersonaOutput,
    DescriptionOutlineOutput,
    DifferentiationAngleOutput,
    FaqEntriesOutput,
    GigTitlesOutput,
    NicheViabilityOutput,
    PackageStructureOutput,
    RedFlagsOutput,
    TagSetsOutput,
    ThumbnailDirectionOutput,
    UpsellStructureOutput,
)

logger = logging.getLogger(__name__)

_MODEL_NAME = "gpt-4o-mini"
_FENCED_BLOCK_RE = re.compile(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", re.IGNORECASE | re.DOTALL)
_DEFAULT_PROMPT_FIELDS: dict[str, Any] = {
    "cluster_label": "unknown topic cluster",
    "cluster_size": 0,
    "total_result_count": None,
    "starter_price_basic": 0,
    "starter_price_standard": 0,
    "starter_price_premium": 0,
    "hard_exclusions": [],
    "top_buyer_complaints": [],
    "top_buyer_praise": [],
    "positioning_gaps": [],
    "cluster_synthesis_narrative": "Not available",
    "trends_slope": "unknown",
    "reddit_intent_score": 0.0,
    "thumbnail_class_distribution": {},
    "competitor_extras": [],
    "trend_score": None,
    "profitability_score": None,
    "weakness_score": None,
    "opportunity_narrative": "Not available",
}

_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parents[1] / "llm" / "templates")),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)

ModelT = TypeVar("ModelT", bound=BaseModel)


def load_template(template_name: str) -> Template:
    """Load a Jinja template from the shared src/llm/templates tree."""
    return _TEMPLATE_ENV.get_template(template_name)


def _extract_response_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, Mapping) and isinstance(response.get("text"), str):
        return str(response["text"])
    text = getattr(response, "text", None)
    if isinstance(text, str):
        return text
    return str(response)


def _strip_markdown_fences(raw_text: str) -> str:
    candidate = raw_text.strip()
    match = _FENCED_BLOCK_RE.match(candidate)
    if match is None:
        return candidate
    return match.group(1).strip()


def validate_and_parse_llm_response(raw_text: str) -> dict[str, Any] | None:
    """Parse raw LLM text into a JSON object; supports fenced code blocks."""
    cleaned = _strip_markdown_fences(raw_text)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def estimate_llm_cost(prompt: str, response: str, model: str) -> float:
    """Estimate USD cost using simple character-length token heuristics."""
    input_tokens = max(0, len(prompt) // 4)
    output_tokens = max(0, len(response) // 4)
    pricing = {
        "gpt-4o-mini": {"input_per_1k": 0.000150, "output_per_1k": 0.000600},
    }
    model_pricing = pricing.get(model, pricing["gpt-4o-mini"])
    return ((input_tokens / 1000) * model_pricing["input_per_1k"]) + (
        (output_tokens / 1000) * model_pricing["output_per_1k"]
    )


async def _resolve_maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _coerce_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return dict(value)


def _score_component_value(context: RecommendationContext, name: str) -> float | None:
    direct_value = _coerce_float(getattr(context, name, None))
    if direct_value is not None:
        return direct_value

    score_data = _coerce_dict(getattr(context, "score_data", {}))
    score_data_value = score_data.get(name)
    if isinstance(score_data_value, dict):
        score_data_value = score_data_value.get("score_value")
    parsed_score_data_value = _coerce_float(score_data_value)
    if parsed_score_data_value is not None:
        return parsed_score_data_value

    score_components = _coerce_dict(getattr(context, "score_components", {}))
    score_component_value = score_components.get(name)
    if isinstance(score_component_value, dict):
        score_component_value = score_component_value.get("score_value")
    return _coerce_float(score_component_value)


def _market_price_value(context: RecommendationContext, tier_key: str) -> int:
    market_price_range = _coerce_dict(getattr(context, "market_price_range", None))
    if tier_key in market_price_range:
        return _coerce_int(market_price_range.get(tier_key), default=0)

    tier_dict = market_price_range.get(tier_key.replace("starter_price_", ""))
    if isinstance(tier_dict, dict):
        for nested_key in ("starter_price", "median", "price"):
            value = _coerce_int(tier_dict.get(nested_key), default=-1)
            if value >= 0:
                return value
    return 0


def context_to_dict(context: RecommendationContext) -> dict[str, Any]:
    """Map RecommendationContext to all variables required by the 11 templates."""
    competitor_data = _coerce_dict(getattr(context, "competitor_data", {}))
    review_insights = _coerce_dict(getattr(context, "review_insights", {}))
    external_signals = _coerce_dict(getattr(context, "external_signals", {}))
    top_competitor_weaknesses = getattr(context, "top_competitor_weaknesses", [])
    if not isinstance(top_competitor_weaknesses, list):
        top_competitor_weaknesses = []

    hard_exclusions = _coerce_list_of_str(
        competitor_data.get("hard_exclusions", _coerce_dict(getattr(context, "market_price_range", {})).get("hard_exclusions"))
    )
    top_buyer_complaints = _coerce_list_of_str(
        getattr(context, "top_buyer_complaints", None) or getattr(context, "reviewer_pain_points", None)
    )
    top_buyer_praise = _coerce_list_of_str(getattr(context, "top_buyer_praise", None))
    positioning_gaps = getattr(context, "positioning_gaps", None)
    if not isinstance(positioning_gaps, list):
        positioning_gaps = competitor_data.get("positioning_gaps", [])
    if not isinstance(positioning_gaps, list):
        positioning_gaps = []

    cluster_synthesis_narrative = (
        competitor_data.get("cluster_synthesis_narrative")
        or review_insights.get("cluster_synthesis_narrative")
        or review_insights.get("synthesis_narrative")
        or "Not available"
    )
    opportunity_narrative = (
        _coerce_dict(getattr(context, "score_data", {})).get("opportunity_narrative")
        or review_insights.get("opportunity_narrative")
        or "Not available"
    )

    template_context: dict[str, Any] = {
        "niche_name": getattr(context, "niche_name", "") or "",
        "keyword_text": getattr(context, "keyword_text", "") or "",
        "cluster_label": getattr(context, "cluster_label", None),
        "cluster_size": getattr(context, "cluster_size", None),
        "tag": getattr(context, "tag", "MONITOR") or "MONITOR",
        "final_score": _coerce_float(getattr(context, "final_score", 0.0)) or 0.0,
        "confidence_modifier": _coerce_float(getattr(context, "confidence_modifier", 0.0)) or 0.0,
        "demand_score": _score_component_value(context, "demand_score"),
        "competition_score": _score_component_value(context, "competition_score"),
        "opportunity_score": _score_component_value(context, "opportunity_score"),
        "feasibility_score": _score_component_value(context, "feasibility_score"),
        "saturation_score": _score_component_value(context, "saturation_score"),
        "trend_score": _score_component_value(context, "trend_score"),
        "profitability_score": _score_component_value(context, "profitability_score"),
        "weakness_score": _score_component_value(context, "weakness_score"),
        "top_competitor_weaknesses": top_competitor_weaknesses,
        "top_buyer_complaints": top_buyer_complaints,
        "top_buyer_praise": top_buyer_praise,
        "positioning_gaps": positioning_gaps,
        "cluster_synthesis_narrative": cluster_synthesis_narrative,
        "opportunity_narrative": opportunity_narrative,
        "thumbnail_class_distribution": _coerce_dict(
            competitor_data.get("thumbnail_class_distribution", {})
        ),
        "competitor_extras": competitor_data.get("competitor_extras", []),
        "trends_slope": external_signals.get("trends_slope", external_signals.get("google_trends_slope")),
        "reddit_intent_score": external_signals.get(
            "reddit_intent_score", external_signals.get("reddit_demand_intent_score")
        ),
        "total_result_count": _coerce_int(
            competitor_data.get("total_result_count", _coerce_dict(getattr(context, "score_data", {})).get("total_result_count")),
            default=0,
        )
        or None,
        "starter_price_basic": _market_price_value(context, "starter_price_basic"),
        "starter_price_standard": _market_price_value(context, "starter_price_standard"),
        "starter_price_premium": _market_price_value(context, "starter_price_premium"),
        "hard_exclusions": hard_exclusions,
    }

    for key, value in _DEFAULT_PROMPT_FIELDS.items():
        if template_context.get(key) in (None, "", {}, []) and value not in (None,):
            template_context[key] = value
    return template_context


async def _cache_get(cache: Any, cache_key: str) -> Any | None:
    if cache is None or not hasattr(cache, "get"):
        return None
    try:
        return await _resolve_maybe_await(cache.get(cache_key))
    except Exception:
        return None


async def _cache_set(cache: Any, cache_key: str, payload: str) -> None:
    if cache is None or not hasattr(cache, "set"):
        return
    try:
        await _resolve_maybe_await(cache.set(cache_key, payload))
        return
    except TypeError:
        pass
    except Exception:
        return

    try:
        await _resolve_maybe_await(
            cache.set(
                cache_key,
                payload,
                model=_MODEL_NAME,
                temperature=0.0,
                prompt_text=cache_key,
            )
        )
    except Exception:
        return


def _parse_cached_payload(output_model: type[ModelT], cached: Any) -> ModelT | None:
    if isinstance(cached, bytes):
        cached = cached.decode("utf-8")
    if isinstance(cached, str):
        return output_model.model_validate_json(cached)
    if isinstance(cached, Mapping):
        return output_model.model_validate(dict(cached))
    return None


async def _call_llm(
    llm_client: Any,
    *,
    prompt: str,
    model: str,
    max_tokens: int,
) -> str:
    complete_fn = getattr(llm_client, "complete", None)
    if complete_fn is None:
        raise AttributeError("llm_client.complete is required")
    try:
        response = complete_fn(prompt=prompt, model=model, max_tokens=max_tokens)
    except TypeError:
        response = complete_fn(prompt=prompt, model=model)
    resolved = await _resolve_maybe_await(response)
    return _extract_response_text(resolved)


async def _execute_task(
    *,
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
    task_name: str,
    template_file: str,
    output_model: type[ModelT],
    max_tokens: int,
) -> ModelT | None:
    cache_key = f"rec_{task_name}:{context.keyword_id}:{context.run_id}"
    cached = await _cache_get(cache, cache_key)
    if cached:
        try:
            cached_model = _parse_cached_payload(output_model, cached)
            if cached_model is not None:
                return cached_model
        except ValidationError as exc:
            logger.warning("Ignoring invalid cache payload for %s keyword=%s: %s", task_name, context.keyword_id, exc)

    if llm_client is None:
        logger.warning("LLM task %s failed keyword=%s: llm_client is None", task_name, context.keyword_id)
        return None

    try:
        template = load_template(f"stage13_recommendations/{template_file}")
        prompt = template.render(**context_to_dict(context))
        response_text = await _call_llm(llm_client, prompt=prompt, model=_MODEL_NAME, max_tokens=max_tokens)
        parsed = validate_and_parse_llm_response(response_text)
        if parsed is None:
            raise ValueError("Could not parse JSON object from LLM response.")
        result = output_model.model_validate(parsed)
        await _cache_set(cache, cache_key, result.model_dump_json())
        return result
    except Exception as exc:
        logger.warning("LLM task %s failed keyword=%s: %s", task_name, context.keyword_id, exc)
        return None


async def task_gig_titles(context: RecommendationContext, llm_client: Any, cache: Any) -> GigTitlesOutput | None:
    """Generates 5 gig title variants. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="gig_titles",
        template_file="gig_titles.j2",
        output_model=GigTitlesOutput,
        max_tokens=700,
    )


async def task_tag_sets(context: RecommendationContext, llm_client: Any, cache: Any) -> TagSetsOutput | None:
    """Generates 5 Fiverr tag-set options. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="tag_sets",
        template_file="tag_sets.j2",
        output_model=TagSetsOutput,
        max_tokens=500,
    )


async def task_package_structure(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> PackageStructureOutput | None:
    """Generates 3-tier package structure. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="package_structure",
        template_file="package_structure.j2",
        output_model=PackageStructureOutput,
        max_tokens=900,
    )


async def task_description_outline(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> DescriptionOutlineOutput | None:
    """Generates description section outline. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="description_outline",
        template_file="description_outline.j2",
        output_model=DescriptionOutlineOutput,
        max_tokens=900,
    )


async def task_faq_entries(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> FaqEntriesOutput | None:
    """Generates 5-7 FAQ entries. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="faq_entries",
        template_file="faq_entries.j2",
        output_model=FaqEntriesOutput,
        max_tokens=700,
    )


async def task_differentiation_angle(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> DifferentiationAngleOutput | None:
    """Generates differentiation strategy. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="differentiation_angle",
        template_file="differentiation_angle.j2",
        output_model=DifferentiationAngleOutput,
        max_tokens=900,
    )


async def task_buyer_persona(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> BuyerPersonaOutput | None:
    """Generates buyer persona profile. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="buyer_persona",
        template_file="buyer_persona.j2",
        output_model=BuyerPersonaOutput,
        max_tokens=700,
    )


async def task_thumbnail_direction(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> ThumbnailDirectionOutput | None:
    """Generates thumbnail creative direction. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="thumbnail_direction",
        template_file="thumbnail_direction.j2",
        output_model=ThumbnailDirectionOutput,
        max_tokens=600,
    )


async def task_upsell_structure(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> UpsellStructureOutput | None:
    """Generates gig-extra upsell structure. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="upsell_structure",
        template_file="upsell_structure.j2",
        output_model=UpsellStructureOutput,
        max_tokens=600,
    )


async def task_red_flags(context: RecommendationContext, llm_client: Any, cache: Any) -> RedFlagsOutput | None:
    """Generates market-entry red-flag assessment. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="red_flags",
        template_file="red_flags.j2",
        output_model=RedFlagsOutput,
        max_tokens=700,
    )


async def task_niche_viability(
    context: RecommendationContext,
    llm_client: Any,
    cache: Any,
) -> NicheViabilityOutput | None:
    """Generates niche viability narrative. Returns None on failure."""
    return await _execute_task(
        context=context,
        llm_client=llm_client,
        cache=cache,
        task_name="niche_viability",
        template_file="niche_viability.j2",
        output_model=NicheViabilityOutput,
        max_tokens=900,
    )


__all__ = [
    "context_to_dict",
    "estimate_llm_cost",
    "load_template",
    "task_buyer_persona",
    "task_description_outline",
    "task_differentiation_angle",
    "task_faq_entries",
    "task_gig_titles",
    "task_niche_viability",
    "task_package_structure",
    "task_red_flags",
    "task_tag_sets",
    "task_thumbnail_direction",
    "task_upsell_structure",
    "validate_and_parse_llm_response",
]

