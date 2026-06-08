"""Discovery keyword integration module.

Handles the INSERT stage of the Discovery Engine loop:
takes accepted hypothesis objects from generation and promotes them into the
keywords table for collection and scoring.

No new migration is required for S7.7 because migration_14 already added:
is_discovery, discovery_mode, hypothesis_confidence, hypothesis_rationale,
discovered_in_run, discovery_evaluated, is_retired.
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


def _resolve_keyword_column(Keyword: Any) -> Any:  # noqa: N803
    """Resolve repository keyword text column name at runtime.

    Prompt contracts use `keyword_text`; repository model uses `keyword`.
    This helper keeps behavior stable across naming variants.
    """
    if hasattr(Keyword, "keyword"):
        return Keyword.keyword
    return Keyword.keyword_text


def _resolve_keyword_field_name(Keyword: Any) -> str:  # noqa: N803
    """Resolve constructor field name for keyword text."""
    if hasattr(Keyword, "keyword"):
        return "keyword"
    return "keyword_text"


def _normalize_keyword(value: str | None) -> str:
    """Normalize hypothesis text for dedup checks."""
    return (value or "").strip()


def check_discovery_keyword_exists(
    keyword_text: str,
    niche_id: str | int,
    db: Any,
) -> int | None:
    """Return existing keyword id for keyword+niche (case-insensitive).

    The check intentionally applies to both discovery and seed keywords to
    prevent cross-type duplication.
    """
    from sqlalchemy import func

    from src.models import Keyword

    normalized = _normalize_keyword(keyword_text).lower()
    keyword_col = _resolve_keyword_column(Keyword)
    existing = (
        db.query(Keyword.id)
        .filter(
            func.lower(keyword_col) == normalized,
            Keyword.niche_id == niche_id,
        )
        .first()
    )
    return int(existing[0]) if existing else None


def insert_discovery_keyword(
    hypothesis: Any,
    run_id: str,
    db: Any,
    niche_id: str | int | None = None,
) -> int | None:
    """Insert one accepted discovery hypothesis into keywords table.

    Returns inserted `keyword.id`, or `None` when skipped (duplicate/invalid).
    """
    from src.models import Keyword

    resolved_niche = niche_id if niche_id is not None else getattr(hypothesis, "niche_id", None)
    if resolved_niche is None:
        log.warning("Cannot insert discovery hypothesis without niche_id")
        return None

    raw_text = getattr(hypothesis, "hypothesis_text", "")
    keyword_text = _normalize_keyword(raw_text)
    if not keyword_text:
        log.warning("Cannot insert discovery hypothesis with empty hypothesis_text")
        return None

    existing_id = check_discovery_keyword_exists(keyword_text, resolved_niche, db)
    if existing_id is not None:
        log.debug("Skipping duplicate discovery keyword: '%s' in '%s'", keyword_text, resolved_niche)
        return None

    discovery_mode = getattr(hypothesis, "discovery_mode", None)
    specificity_score = getattr(hypothesis, "specificity_score", None)
    rationale = (getattr(hypothesis, "reason", "") or "").strip()

    keyword_field_name = _resolve_keyword_field_name(Keyword)
    payload: dict[str, Any] = {
        keyword_field_name: keyword_text,
        "niche_id": resolved_niche,
        "is_discovery": True,
        "discovery_mode": str(discovery_mode) if discovery_mode else "unknown",
        "hypothesis_confidence": float(specificity_score) if specificity_score is not None else 0.0,
        "hypothesis_rationale": rationale[:1000],
        "discovered_in_run": run_id,
        "discovery_evaluated": False,
        "is_retired": False,
    }
    if hasattr(Keyword, "normalized_keyword"):
        payload["normalized_keyword"] = keyword_text.lower()

    keyword = Keyword(**payload)
    db.add(keyword)
    db.flush()

    confidence = payload["hypothesis_confidence"]
    log.info(
        "Inserted discovery keyword '%s' in '%s' (mode=%s, confidence=%.2f, run=%s)",
        keyword_text,
        resolved_niche,
        payload["discovery_mode"],
        confidence,
        run_id,
    )
    return int(keyword.id)


def queue_discovery_collection(
    keyword_id: int,
    run_id: str,
    db: Any,
) -> bool:
    """Mark a discovery keyword as pending collection."""
    from src.models import Keyword

    keyword = (
        db.query(Keyword)
        .filter(
            Keyword.id == keyword_id,
            Keyword.is_discovery.is_(True),
        )
        .first()
    )
    if keyword is None:
        log.warning("queue_discovery_collection: keyword_id=%s not found or not discovery", keyword_id)
        return False

    if bool(keyword.discovery_evaluated):
        log.debug("queue_discovery_collection: keyword_id=%s already evaluated", keyword_id)
        return False

    keyword.discovered_in_run = run_id
    keyword.discovery_evaluated = False
    log.debug("Queued discovery keyword_id=%s in run=%s", keyword_id, run_id)
    return True


def process_accepted_hypotheses(
    hypotheses: list[Any],
    run_id: str,
    db: Any,
) -> dict[str, Any]:
    """Batch insert accepted hypotheses and return insertion summary."""
    if not hypotheses:
        return {"inserted": 0, "skipped": 0, "run_id": run_id, "keyword_ids": []}

    accepted = [h for h in hypotheses if bool(getattr(h, "accepted", False))]
    if not accepted:
        return {"inserted": 0, "skipped": len(hypotheses), "run_id": run_id, "keyword_ids": []}

    inserted = 0
    skipped = 0
    keyword_ids: list[int] = []

    for hypothesis in accepted:
        keyword_id = insert_discovery_keyword(hypothesis, run_id, db)
        if keyword_id is None:
            skipped += 1
            continue
        keyword_ids.append(keyword_id)
        inserted += 1

    db.commit()
    log.info(
        "process_accepted_hypotheses: run=%s inserted=%s skipped=%s total_input=%s",
        run_id,
        inserted,
        skipped,
        len(hypotheses),
    )
    return {
        "inserted": inserted,
        "skipped": skipped,
        "run_id": run_id,
        "keyword_ids": keyword_ids,
    }


def get_pending_discovery_keywords(db: Any) -> list[Any]:
    """Return discovery keywords awaiting collection."""
    from src.models import Keyword

    pending = (
        db.query(Keyword)
        .filter(Keyword.is_discovery.is_(True))
        .filter(Keyword.discovery_evaluated.is_(False))
        .filter(Keyword.is_retired.is_(False))
        .order_by(Keyword.id)
        .all()
    )
    log.debug("get_pending_discovery_keywords: %s pending", len(pending))
    return pending


__all__ = [
    "insert_discovery_keyword",
    "queue_discovery_collection",
    "process_accepted_hypotheses",
    "get_pending_discovery_keywords",
    "check_discovery_keyword_exists",
]
