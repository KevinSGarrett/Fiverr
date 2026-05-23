"""Persistence helpers for generated recommendation payloads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.models import Recommendation, get_registered_model_classes

_OUTPUT_FIELDS = [
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
    "niche_viability_assessment",
    "pricing_strategy",
]


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
