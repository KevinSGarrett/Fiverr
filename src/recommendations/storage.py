"""Persistence helpers for generated recommendation payloads."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from itertools import zip_longest
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from src.models import Recommendation, get_registered_model_classes
from src.recommendations.contracts import RecommendationContext
from src.recommendations.schemas import RecommendationOutput

_STAGE13_OUTPUT_FIELDS = [
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

_OUTPUT_FIELDS = [
    *_STAGE13_OUTPUT_FIELDS,
    "niche_viability_assessment",
    "pricing_strategy",
]


def save_recommendation(context: RecommendationContext, output: RecommendationOutput, db: Any) -> str:
    """Persist a Stage 13 recommendation row and return its identifier."""
    query = _safe_query(db, Recommendation)
    if query is None:
        raise ValueError("Database session does not support Recommendation persistence.")

    run_id_text = str(context.run_id) if context.run_id is not None else ""
    run_id_int = _to_optional_int(context.run_id)

    row = _load_existing_recommendation(
        keyword_id=context.keyword_id,
        run_id_int=run_id_int,
        run_id_text=run_id_text,
        db=db,
    )
    if row is None:
        row = Recommendation(
            run_id=run_id_int,
            run_id_text=run_id_text or None,
            keyword_id=context.keyword_id,
            recommendation_type="keyword_recommendation",
            recommendation_text=_derive_recommendation_text_from_output(output),
            confidence=_to_float(context.confidence_modifier, _to_float(context.final_score, 0.0)),
            raw_json={},
        )
        db.add(row)

    output_payload = output.model_dump(mode="json")
    generated_at = datetime.now(UTC)
    row.run_id = run_id_int
    row.run_id_text = run_id_text or None
    row.keyword_id = context.keyword_id
    row.niche_id = str(context.niche_id) if context.niche_id not in ("", None) else None
    row.tag = context.tag
    row.final_score = _to_float(context.final_score, 0.0)
    row.score_at_generation = _to_float(context.final_score, 0.0)
    row.generation_complete = bool(output.generation_complete)
    row.llm_cost_usd = _to_float(output.total_llm_cost_usd, 0.0)
    row.generated_at = generated_at
    row.recommendation_type = "keyword_recommendation"
    row.recommendation_text = _derive_recommendation_text_from_output(output)
    row.confidence = _to_float(context.confidence_modifier, _to_float(context.final_score, 0.0))

    for field_name in _STAGE13_OUTPUT_FIELDS:
        setattr(row, field_name, output_payload.get(field_name))

    row.raw_json = {
        **output_payload,
        "keyword_id": context.keyword_id,
        "run_id": context.run_id,
        "niche_id": context.niche_id,
        "tag": context.tag,
        "final_score": context.final_score,
        "generated_at": generated_at.isoformat(),
    }

    try:
        db.commit()
        db.refresh(row)
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise

    recommendation_id = getattr(row, "id", None)
    return str(recommendation_id if recommendation_id is not None else "")


def run_save_recommendations(eligible_keywords: Any, outputs: Any, db: Any) -> dict[str, int]:
    """Batch-save recommendation outputs and return status counters."""
    summary = {"saved": 0, "failed": 0, "skipped": 0}

    for context, raw_output in _iter_context_output_pairs(eligible_keywords, outputs):
        if context is None or raw_output is None:
            summary["skipped"] += 1
            continue
        output = _coerce_recommendation_output(raw_output)
        if output is None:
            summary["failed"] += 1
            continue
        try:
            save_recommendation(context=context, output=output, db=db)
            summary["saved"] += 1
        except Exception:
            summary["failed"] += 1
    return summary


def get_recommendation(keyword_id: int, db: Any) -> RecommendationOutput | None:
    """Load the latest completed recommendation for a keyword."""
    query = _safe_query(db, Recommendation)
    if query is None:
        return None

    rows = query.filter(Recommendation.keyword_id == keyword_id).order_by(Recommendation.created_at.desc()).all()
    for row in rows:
        raw_json = getattr(row, "raw_json", {})
        generation_complete = _is_row_generation_complete(row=row, raw_json=raw_json)
        if not generation_complete:
            continue
        payload: dict[str, Any] = {
            field_name: getattr(row, field_name, None)
            for field_name in _STAGE13_OUTPUT_FIELDS
        }
        payload["generation_complete"] = generation_complete
        payload["failed_tasks"] = _extract_failed_tasks(raw_json)
        payload["total_llm_cost_usd"] = _to_float(getattr(row, "llm_cost_usd", 0.0), 0.0)
        try:
            return RecommendationOutput.model_validate(payload)
        except ValidationError:
            continue
    return None


def write_recommendation(
    keyword_id: int,
    run_id: str | int,
    context: Any,
    recommendation_data: dict[str, Any],
    db: Any,
) -> bool:
    """Persist recommendation payload to DB when available, otherwise to sidecar JSON."""
    generated_at = datetime.now(UTC).isoformat()
    run_id_text = str(run_id)
    run_id_int = _to_optional_int(run_id)
    payload = {
        "keyword_id": keyword_id,
        "niche_id": getattr(context, "niche_id", None),
        "run_id": run_id_text,
        "tag": getattr(context, "tag", None),
        "final_score": _to_float(getattr(context, "final_score", 0.0), 0.0),
        "score_at_generation": _to_float(getattr(context, "final_score", 0.0), 0.0),
        "generation_complete": bool(recommendation_data.get("generation_complete", False)),
        "llm_cost_usd": _to_float(recommendation_data.get("llm_cost_usd", 0.0), 0.0),
        "generated_at": generated_at,
    }
    for field in _OUTPUT_FIELDS:
        payload[field] = recommendation_data.get(field)

    recommendation_model = _model_by_name("Recommendation")
    if recommendation_model is None:
        return _write_sidecar(keyword_id=keyword_id, run_id=run_id, payload=payload)

    try:
        row = _load_existing_recommendation(
            keyword_id=keyword_id,
            run_id_int=run_id_int,
            run_id_text=run_id_text,
            db=db,
        )
        if row is None:
            row = Recommendation(
                run_id=run_id_int,
                run_id_text=run_id_text,
                keyword_id=keyword_id,
                recommendation_type="keyword_recommendation",
                recommendation_text=_derive_recommendation_text(payload),
                confidence=payload["final_score"],
                niche_id=str(payload["niche_id"]) if payload["niche_id"] is not None else None,
                tag=payload["tag"],
                final_score=payload["final_score"],
                score_at_generation=payload["score_at_generation"],
                generation_complete=payload["generation_complete"],
                llm_cost_usd=payload["llm_cost_usd"],
                gig_titles=payload.get("gig_titles"),
                tag_sets=payload.get("tag_sets"),
                package_structure=payload.get("package_structure"),
                description_outline=payload.get("description_outline"),
                faq_entries=payload.get("faq_entries"),
                differentiation_angle=payload.get("differentiation_angle"),
                buyer_persona=payload.get("buyer_persona"),
                thumbnail_direction=payload.get("thumbnail_direction"),
                upsell_structure=payload.get("upsell_structure"),
                red_flags=payload.get("red_flags"),
                niche_viability=payload.get("niche_viability")
                if payload.get("niche_viability") is not None
                else payload.get("niche_viability_assessment"),
                generated_at=_coerce_datetime(payload.get("generated_at")),
                raw_json=payload,
            )
            db.add(row)
        else:
            row.recommendation_type = "keyword_recommendation"
            row.recommendation_text = _derive_recommendation_text(payload)
            row.confidence = payload["final_score"]
            row.run_id = run_id_int
            row.run_id_text = run_id_text
            row.niche_id = str(payload["niche_id"]) if payload["niche_id"] is not None else None
            row.tag = payload["tag"]
            row.final_score = payload["final_score"]
            row.score_at_generation = payload["score_at_generation"]
            row.generation_complete = payload["generation_complete"]
            row.llm_cost_usd = payload["llm_cost_usd"]
            row.gig_titles = payload.get("gig_titles")
            row.tag_sets = payload.get("tag_sets")
            row.package_structure = payload.get("package_structure")
            row.description_outline = payload.get("description_outline")
            row.faq_entries = payload.get("faq_entries")
            row.differentiation_angle = payload.get("differentiation_angle")
            row.buyer_persona = payload.get("buyer_persona")
            row.thumbnail_direction = payload.get("thumbnail_direction")
            row.upsell_structure = payload.get("upsell_structure")
            row.red_flags = payload.get("red_flags")
            row.niche_viability = payload.get("niche_viability")
            if row.niche_viability is None:
                row.niche_viability = payload.get("niche_viability_assessment")
            row.generated_at = _coerce_datetime(payload.get("generated_at"))
            row.raw_json = payload
        db.commit()
        return True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return _write_sidecar(keyword_id=keyword_id, run_id=run_id, payload=payload)


def _write_sidecar(keyword_id: int, run_id: str | int, payload: dict[str, Any]) -> bool:
    output_dir = Path("data/recommendation_results")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{keyword_id}_{run_id}.json"
    try:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return True
    except Exception:
        return False


def _derive_recommendation_text(payload: dict[str, Any]) -> str:
    angle = payload.get("differentiation_angle")
    if isinstance(angle, str) and angle.strip():
        return angle
    return "Generated recommendation package"


def _load_existing_recommendation(
    *,
    keyword_id: int,
    run_id_int: int | None,
    run_id_text: str,
    db: Any,
) -> Any | None:
    query = db.query(Recommendation).filter(Recommendation.keyword_id == keyword_id)
    if run_id_int is not None:
        row = query.filter(Recommendation.run_id == run_id_int).first()
        if row is not None:
            return row
    return query.filter(Recommendation.run_id_text == run_id_text).first()


def _model_by_name(name: str) -> Any | None:
    for cls in get_registered_model_classes():
        if cls.__name__ == name:
            return cls
    return None


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _safe_query(db: Any, model: Any) -> Any | None:
    query_fn = getattr(db, "query", None)
    if query_fn is None:
        return None
    try:
        return query_fn(model)
    except Exception:
        return None


def _coerce_recommendation_output(raw_output: Any) -> RecommendationOutput | None:
    if isinstance(raw_output, RecommendationOutput):
        return raw_output
    if isinstance(raw_output, Mapping):
        try:
            return RecommendationOutput.model_validate(dict(raw_output))
        except ValidationError:
            return None
    return None


def _iter_context_output_pairs(eligible_keywords: Any, outputs: Any) -> Iterable[tuple[RecommendationContext | None, Any]]:
    contexts = list(eligible_keywords) if isinstance(eligible_keywords, Iterable) else []
    if isinstance(outputs, Mapping):
        for item in contexts:
            context = _extract_context(item)
            if context is None:
                yield None, None
                continue
            output = outputs.get(context.keyword_id, outputs.get(str(context.keyword_id)))
            yield context, output
        return

    output_values = list(outputs) if isinstance(outputs, Iterable) else []
    for context_item, output_item in zip_longest(contexts, output_values, fillvalue=None):
        yield _extract_context(context_item), output_item


def _extract_context(candidate: Any) -> RecommendationContext | None:
    if isinstance(candidate, RecommendationContext):
        return candidate
    if isinstance(candidate, Mapping):
        embedded = candidate.get("context")
        if isinstance(embedded, RecommendationContext):
            return embedded
    return None


def _extract_failed_tasks(raw_json: Any) -> list[str]:
    if not isinstance(raw_json, Mapping):
        return []
    failed_tasks = raw_json.get("failed_tasks")
    if not isinstance(failed_tasks, list):
        return []
    return [task for task in failed_tasks if isinstance(task, str) and task.strip()]


def _is_row_generation_complete(row: Any, raw_json: Any) -> bool:
    explicit_complete = getattr(row, "generation_complete", None)
    if isinstance(explicit_complete, bool) and explicit_complete:
        return True
    if isinstance(raw_json, Mapping) and "generation_complete" in raw_json:
        return bool(raw_json.get("generation_complete"))
    return bool(explicit_complete)


def _derive_recommendation_text_from_output(output: RecommendationOutput) -> str:
    if output.niche_viability is not None and output.niche_viability.blunt_recommendation.strip():
        return output.niche_viability.blunt_recommendation.strip()
    if output.differentiation_angle is not None and output.differentiation_angle.one_sentence_pitch.strip():
        return output.differentiation_angle.one_sentence_pitch.strip()
    return "Generated recommendation package"
