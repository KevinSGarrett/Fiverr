"""Workflow 1: niche initialization (Stage 1)."""

from __future__ import annotations

from typing import Any


async def run_niche_initialization(
    config: dict[str, Any] | None,
    db: Any,
    run_id: str,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 1 niche initialization.

    Loads niches from config, resolves effective depth, applies gate checks,
    and returns normalized seed metadata.
    """
    if config is None:
        from src.config.loader import ConfigLoader

        loaded = ConfigLoader().load()
        config = loaded.model_dump() if hasattr(loaded, "model_dump") else dict(loaded)

    niches_processed = 0
    niche_specs: list[dict[str, Any]] = []
    seed_keywords: dict[str, list[str]] = {}

    niches = config.get("niches", [])
    if isinstance(niches, list):
        niche_list = niches
    elif isinstance(niches, dict):
        niche_list = list(niches.values())
    else:
        niche_list = []

    for niche in niche_list:
        niche_id = getattr(niche, "niche_id", None)
        if isinstance(niche, dict):
            niche_id = niche.get("niche_id")
        if not niche_id:
            continue

        depth = _resolve_niche_depth(str(niche_id), niche, db)
        depth = _apply_gate_check(str(niche_id), niche, depth, db)
        seeds = _load_seeds(niche)
        seed_keywords[str(niche_id)] = seeds

        niche_spec = {
            "niche_id": str(niche_id),
            "depth": depth,
            "seed_count": len(seeds),
            "seeds": seeds if not dry_run else seeds[:3],
            "run_id": run_id,
        }
        niche_specs.append(niche_spec)
        niches_processed += 1

    return {
        "niches_processed": niches_processed,
        "niche_specs": niche_specs,
        "seed_keywords": seed_keywords,
        "dry_run": dry_run,
    }


def _resolve_niche_depth(niche_id: str, niche: Any, db: Any) -> str:
    """Resolve depth from DB override if available, else config/default."""
    try:
        from sqlalchemy.orm import Session

        if isinstance(db, Session):
            from src.models.niche import NicheConfigRecord

            record = db.query(NicheConfigRecord).filter(NicheConfigRecord.niche_id == niche_id).first()
            if record and getattr(record, "depth", None):
                return str(record.depth)
    except Exception:
        pass

    depth = getattr(niche, "depth", None)
    if isinstance(niche, dict):
        depth = niche.get("depth", "standard")
    return str(depth or "standard")


def _apply_gate_check(_niche_id: str, niche: Any, depth: str, _db: Any) -> str:
    """Force keyword_only when gate is explicitly enabled and not passed."""
    gating: dict[str, Any] = getattr(niche, "gating", {}) if hasattr(niche, "gating") else {}
    if isinstance(niche, dict):
        maybe_gating = niche.get("gating", {})
        gating = maybe_gating if isinstance(maybe_gating, dict) else {}

    if gating.get("enabled", False) and not gating.get("gate_passed", True):
        return "keyword_only"
    return depth


def _load_seeds(niche: Any) -> list[str]:
    """Extract and normalize seed keywords from niche config."""
    seeds = getattr(niche, "seed_keywords", []) if hasattr(niche, "seed_keywords") else []
    if isinstance(niche, dict):
        seeds = niche.get("seed_keywords", [])

    deduped: list[str] = []
    seen: set[str] = set()
    for seed in seeds if isinstance(seeds, list) else []:
        if not seed:
            continue
        normalized = str(seed).strip()
        if not normalized:
            continue
        key = normalized.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped
