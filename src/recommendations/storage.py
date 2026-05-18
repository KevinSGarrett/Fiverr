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
    payload = {
        "keyword_id": keyword_id,
        "niche_id": getattr(context, "niche_id", None),
        "run_id": str(run_id),
        "tag": getattr(context, "tag", None),
        "final_score": _to_float(getattr(context, "final_score", 0.0), 0.0),
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
        run_id_int = int(run_id) if str(run_id).isdigit() else None
        row = (
            db.query(Recommendation)
            .filter(Recommendation.keyword_id == keyword_id, Recommendation.run_id == run_id_int)
            .first()
        )
        if row is None:
            row = Recommendation(
                run_id=run_id_int,
                keyword_id=keyword_id,
                recommendation_type="keyword_recommendation",
                recommendation_text=_derive_recommendation_text(payload),
                confidence=payload["final_score"],
                raw_json=payload,
            )
            db.add(row)
        else:
            row.recommendation_type = "keyword_recommendation"
            row.recommendation_text = _derive_recommendation_text(payload)
            row.confidence = payload["final_score"]
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
