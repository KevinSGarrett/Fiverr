"""Stage 14 recommendations-only orchestration pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.recommendations.context_builder import build_recommendation_context
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.executor import generate_recommendation_async
from src.recommendations.export import export_recommendation_by_keyword
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
    recommendations_config = _recommendations_config(config_payload)
    auto_export_markdown = bool(recommendations_config.get("auto_export_markdown", False))
    eligible_keywords = get_eligible_keywords(run_id, db, config_payload)
    summary: dict[str, Any] = {
        "run_id": str(run_id),
        "eligible": len(eligible_keywords),
        "gates_passed": 0,
        "generated": 0,
        "skipped": 0,
        "failed": 0,
        "total_cost_usd": 0.0,
        "markdown_exports": {},
        "export_paths": [],
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
            if auto_export_markdown:
                markdown, export_error = await export_recommendation_by_keyword(
                    keyword_id=keyword_id,
                    niche_id=str(context.niche_id),
                    run_id=str(run_id),
                    db=db,
                )
                if export_error is None and markdown:
                    keyword_label = context.keyword_text.strip() or str(keyword_id)
                    summary["markdown_exports"][keyword_label] = markdown
                    export_path = _write_markdown_export(
                        keyword_label=keyword_label,
                        markdown=markdown,
                        recommendations_config=recommendations_config,
                    )
                    if export_path is not None:
                        summary["export_paths"].append(export_path)
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


def _recommendations_config(config_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    section = config_payload.get("recommendations", {})
    if isinstance(section, Mapping):
        return section
    return {}


def _write_markdown_export(
    *,
    keyword_label: str,
    markdown: str,
    recommendations_config: Mapping[str, Any],
) -> str | None:
    export_dir_raw = recommendations_config.get("export_dir", "data/exports")
    export_dir = Path(str(export_dir_raw))
    filename = f"{_safe_export_filename(keyword_label)}.md"
    target_path = export_dir / filename
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(markdown, encoding="utf-8")
    except OSError:
        return None
    return str(target_path)


def _safe_export_filename(keyword_label: str) -> str:
    filtered = [
        character.lower()
        if character.isalnum()
        else "_"
        for character in keyword_label.strip()
    ]
    safe_name = "".join(filtered).strip("_")
    while "__" in safe_name:
        safe_name = safe_name.replace("__", "_")
    return safe_name or "keyword"


__all__ = ["run_recommendations_pipeline"]
