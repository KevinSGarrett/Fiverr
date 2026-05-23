"""Stage 14 recommendations-only orchestration pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.recommendations.context_builder import build_recommendation_context
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.executor import generate_recommendation_async
from src.recommendations.storage import save_recommendation


async def run_recommendations_pipeline(
    run_id: str,
    db: Any,
    config: Mapping[str, Any] | dict[str, Any],
    llm_client: Any,
    cache: Any,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute full E05 recommendation orchestration for one run."""
    config_payload = config if isinstance(config, Mapping) else {}
    eligible_keywords = get_eligible_keywords(run_id, db, config_payload)
    summary: dict[str, Any] = {
        "run_id": str(run_id),
        "eligible": len(eligible_keywords),
        "gates_passed": 0,
        "generated": 0,
        "skipped": 0,
        "failed": 0,
        "total_cost_usd": 0.0,
    }

    for keyword_data in eligible_keywords:
        passes, _reason = passes_recommendation_gates(keyword_data, db)
        if not passes:
            summary["skipped"] += 1
            continue
        summary["gates_passed"] += 1

        keyword_id = _to_positive_int(keyword_data.get("keyword_id"))
        if keyword_id is None:
            summary["failed"] += 1
            continue

        final_score = _to_float(keyword_data.get("final_score"), default=0.0)
        if not should_regenerate_recommendation(keyword_id, final_score, db):
            summary["skipped"] += 1
            continue

        context = build_recommendation_context(
            keyword_id=keyword_id,
            niche_id=keyword_data.get("niche_id"),
            run_id=run_id,
            db=db,
        )
        if context is None:
            summary["failed"] += 1
            continue

        if dry_run:
            summary["generated"] += 1
            continue

        try:
            output = await generate_recommendation_async(
                context=context,
                llm_client=llm_client,
                cache=cache,
            )
            save_recommendation(context=context, output=output, db=db)
            summary["generated"] += 1
            summary["total_cost_usd"] += float(output.total_llm_cost_usd)
        except Exception:
            summary["failed"] += 1

    summary["total_cost_usd"] = round(float(summary["total_cost_usd"]), 6)
    return summary


def _to_positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _to_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


__all__ = ["run_recommendations_pipeline"]
