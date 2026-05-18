"""Stage 13 recommendations orchestration runner."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from src.recommendations.context import build_recommendation_context
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.storage import write_recommendation
from src.recommendations.tasks import generate_recommendation

logger = logging.getLogger(__name__)

_DRY_RUN_RESULT: dict[str, Any] = {
    "generation_complete": False,
    "llm_cost_usd": 0.0,
    "gig_titles": None,
    "tag_sets": None,
    "package_structure": None,
    "description_outline": None,
    "faq_entries": None,
    "differentiation_angle": None,
    "buyer_persona": None,
    "thumbnail_direction": None,
    "upsell_structure": None,
    "red_flags": None,
    "niche_viability_assessment": None,
}


async def run_recommendations_stage(
    run_id: str,
    db: Any,
    config: Mapping[str, Any],
    llm_client: Any,
    cache: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Execute Stage 13 recommendations for eligible keywords and return a run summary."""
    eligible = get_eligible_keywords(run_id, db, config)
    summary: dict[str, Any] = {
        "eligible_count": len(eligible),
        "generated": 0,
        "skipped": 0,
        "failed": 0,
        "total_cost_usd": 0.0,
    }
    for keyword_data in eligible:
        passes, _reason = passes_recommendation_gates(keyword_data, db)
        if not passes:
            summary["skipped"] += 1
            continue

        keyword_id = int(keyword_data.get("keyword_id", 0) or 0)
        if keyword_id <= 0:
            summary["failed"] += 1
            continue

        should_regen = should_regenerate_recommendation(
            keyword_id,
            float(keyword_data.get("final_score", 0.0) or 0.0),
            db,
        )
        if not should_regen:
            summary["skipped"] += 1
            continue

        try:
            context = build_recommendation_context(keyword_id, db, config)
            result = dict(_DRY_RUN_RESULT) if dry_run else await generate_recommendation(
                keyword_id,
                context,
                llm_client,
                cache,
                db,
            )
            wrote = write_recommendation(keyword_id, run_id, context, result, db)
            if not wrote:
                summary["failed"] += 1
                continue
            summary["generated"] += 1
            summary["total_cost_usd"] += float(result.get("llm_cost_usd", 0.0) or 0.0)
        except Exception:
            logger.exception("Recommendation stage failed for keyword_id=%s", keyword_data.get("keyword_id"))
            summary["failed"] += 1

    return summary
