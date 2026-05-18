"""Discovery candidate validation and persistence helpers."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models.discovery import DiscoveryCandidate

ALLOWED_HYPOTHESIS_TYPES = {
    "niche_expansion",
    "adjacent_keyword",
    "trend_signal",
    "reddit_thread",
    "manual_submission",
}
ALLOWED_STATUSES = {"PENDING", "EVALUATED", "ACCEPTED", "REJECTED", "MONITORING"}
BLOCKED_TERMS = {"adult", "spam", "scam", "nsfw", "porn"}


def is_valid_candidate(hypothesis_text: str, existing_niches: list[str]) -> tuple[bool, str]:
    """Return whether hypothesis text passes baseline candidate checks."""
    text = hypothesis_text.strip()
    if not text:
        return False, "empty_hypothesis"

    if len(text) > 100:
        return False, "hypothesis_too_long"

    if len(text.split()) < 3:
        return False, "hypothesis_too_short"

    normalized = text.lower()
    existing = {name.strip().lower() for name in existing_niches if name and name.strip()}
    if normalized in existing:
        return False, "matches_existing_niche"

    for blocked in BLOCKED_TERMS:
        if blocked in normalized:
            return False, "blocked_term"

    return True, "valid"


def create_discovery_candidate(
    hypothesis_text: str,
    hypothesis_type: str,
    source_signal: str | None,
    source_niche_id: str | None,
    run_id: str | None,
    db: Session | Any,
) -> DiscoveryCandidate | None:
    """Create a candidate and persist it when a SQLAlchemy Session is provided."""
    is_valid, _ = is_valid_candidate(hypothesis_text, [])
    if not is_valid:
        return None
    if hypothesis_type not in ALLOWED_HYPOTHESIS_TYPES:
        return None

    candidate = DiscoveryCandidate(
        candidate_id=_build_candidate_id(hypothesis_type=hypothesis_type, hypothesis_text=hypothesis_text),
        hypothesis_text=hypothesis_text.strip(),
        hypothesis_type=hypothesis_type,
        source_signal=source_signal,
        source_niche_id=source_niche_id,
        status="PENDING",
        run_id=run_id,
    )

    if isinstance(db, Session):
        try:
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
        except Exception:
            db.rollback()
            return None

    return candidate


def get_pending_candidates(db: Session | Any, limit: int = 50) -> list[DiscoveryCandidate]:
    """Return pending candidates ordered oldest-first."""
    if not isinstance(db, Session):
        return []
    return (
        db.query(DiscoveryCandidate)
        .filter(DiscoveryCandidate.status == "PENDING")
        .order_by(DiscoveryCandidate.created_at.asc())
        .limit(limit)
        .all()
    )


def update_candidate_status(candidate_id: str, new_status: str, db: Session | Any) -> bool:
    """Update candidate status and lifecycle timestamps."""
    if not isinstance(db, Session):
        return False
    if new_status not in ALLOWED_STATUSES:
        return False

    candidate = (
        db.query(DiscoveryCandidate)
        .filter(DiscoveryCandidate.candidate_id == candidate_id)
        .one_or_none()
    )
    if candidate is None:
        return False

    candidate.status = new_status
    now = datetime.now(UTC)
    if new_status == "EVALUATED":
        candidate.evaluated_at = now
    if new_status == "ACCEPTED":
        candidate.accepted_at = now

    try:
        db.commit()
    except Exception:
        db.rollback()
        return False
    return True


def _build_candidate_id(*, hypothesis_type: str, hypothesis_text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", hypothesis_text.lower()).strip("_")
    token = normalized[:40] if normalized else "candidate"
    date_token = datetime.now(UTC).strftime("%Y%m%d")
    return f"disc_{hypothesis_type}_{token}_{date_token}"
