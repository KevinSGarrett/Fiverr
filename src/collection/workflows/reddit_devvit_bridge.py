"""Reddit Devvit bridge import pipeline for sanitized local payload files."""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import Keyword
from src.models.external_signal import ExternalSignal, write_external_signal
from src.models.niche import Niche

logger = logging.getLogger(__name__)

_PII_FIELDS = {
    "username",
    "user",
    "author",
    "author_id",
    "profile_url",
    "private_email",
    "account_id",
    "private_message",
    "saved_posts",
    "vote_history",
}

_REQUIRED_KEYS = (
    "niche_id",
    "keywords",
    "subreddits_searched",
    "posts_collected",
    "post_count_90d",
    "reddit_top_snippets",
)


def validate_devvit_payload(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate expected v1 schema and required keys."""
    errors: list[str] = []
    if payload.get("schema_version") != "reddit_devvit_signal_v1":
        errors.append("schema_version must be 'reddit_devvit_signal_v1'")
    for key in _REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"missing required key: {key}")
    return (not errors, errors)


def strip_pii_fields(payload: dict[str, Any]) -> dict[str, Any]:
    """Return payload copy with blocked PII fields removed."""
    sanitized = copy.deepcopy(payload)
    for field in _PII_FIELDS:
        sanitized.pop(field, None)
    snippets = sanitized.get("reddit_top_snippets")
    if isinstance(snippets, list):
        for snippet in snippets:
            if isinstance(snippet, dict):
                for field in _PII_FIELDS:
                    snippet.pop(field, None)
    return sanitized


def normalize_devvit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize optional fields and value types for downstream writes."""
    normalized = dict(payload)
    try:
        normalized["reddit_post_count_90d"] = int(normalized.get("reddit_post_count_90d", 0) or 0)
    except (TypeError, ValueError):
        normalized["reddit_post_count_90d"] = 0

    snippets = normalized.get("reddit_top_snippets")
    normalized["reddit_top_snippets"] = snippets if isinstance(snippets, list) else []

    intent_score = normalized.get("reddit_demand_intent_score")
    if intent_score is None:
        normalized["reddit_demand_intent_score"] = None
    else:
        try:
            normalized["reddit_demand_intent_score"] = float(intent_score)
        except (TypeError, ValueError):
            normalized["reddit_demand_intent_score"] = None

    confidence_metadata = normalized.get("confidence_metadata")
    normalized["confidence_metadata"] = confidence_metadata if isinstance(confidence_metadata, dict) else {}
    warnings = normalized.get("warnings")
    normalized["warnings"] = warnings if isinstance(warnings, list) else []
    errors = normalized.get("errors")
    normalized["errors"] = errors if isinstance(errors, list) else []
    return normalized


def _resolve_niche_pk(niche_id: str, db: Session) -> int | None:
    if niche_id.isdigit():
        return int(niche_id)
    row = db.query(Niche).filter(func.lower(Niche.slug) == niche_id.lower()).first()
    return int(row.id) if row is not None else None


def resolve_keyword_id(niche_id: str, keyword_text: str, db: Session) -> int | None:
    """Resolve keyword row by niche and case-insensitive keyword text."""
    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        logger.warning("Devvit bridge niche not found: %s", niche_id)
        return None
    cleaned = keyword_text.strip()
    if not cleaned:
        return None
    normalized = cleaned.lower()
    row = (
        db.query(Keyword)
        .filter(
            Keyword.niche_id == niche_pk,
            (func.lower(Keyword.keyword) == normalized) | (func.lower(Keyword.normalized_keyword) == normalized),
        )
        .first()
    )
    if row is None:
        logger.warning("Devvit bridge keyword unresolved: niche=%s keyword=%s", niche_id, keyword_text)
        return None
    return int(row.id)


def write_devvit_reddit_signals(payload: dict[str, Any], db: Session, run_id: str) -> dict[str, Any]:
    """Write external signal rows for all resolved payload keywords."""
    warnings: list[str] = []
    signals_written = 0
    keywords_resolved = 0
    niche_id = str(payload.get("niche_id", "")).strip()
    raw_keywords = payload.get("keywords")
    keywords = [item for item in raw_keywords if isinstance(item, str)] if isinstance(raw_keywords, list) else []
    for keyword_text in keywords:
        keyword_id = resolve_keyword_id(niche_id, keyword_text, db)
        if keyword_id is None:
            warnings.append(f"keyword unresolved: {keyword_text}")
            continue
        keywords_resolved += 1
        write_external_signal(
            keyword_id=keyword_id,
            signal_type=ExternalSignal.SIGNAL_REDDIT_DEMAND,
            signal_value=payload.get("reddit_demand_intent_score"),
            signal_json=payload,
            run_id=run_id,
            collection_method="reddit_devvit_bridge",
            db=db,
        )
        signals_written += 1
    return {
        "signals_written": signals_written,
        "keywords_resolved": keywords_resolved,
        "warnings": warnings,
    }


def load_devvit_signal_files(import_dir: Path) -> list[dict[str, Any]]:
    """Load raw JSON payloads from import directory."""
    payloads: list[dict[str, Any]] = []
    if not import_dir.exists() or not import_dir.is_dir():
        return payloads
    for file_path in sorted(import_dir.glob("*.json")):
        if file_path.name == ".gitkeep":
            continue
        try:
            parsed = json.loads(file_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Skipping unreadable Devvit payload file: %s", file_path)
            continue
        if isinstance(parsed, dict):
            payloads.append(parsed)
    return payloads


def run_devvit_bridge_import(
    niche_id: str,
    seed_keywords: list[str],
    run_id: str,
    db: Session,
    import_dir: Path,
) -> dict[str, Any]:
    """Run end-to-end payload import for Devvit bridge mode."""
    signals_written = 0
    keywords_resolved = 0
    warnings: list[str] = []
    errors: list[str] = []
    payloads = load_devvit_signal_files(import_dir)
    for raw_payload in payloads:
        is_valid, validation_errors = validate_devvit_payload(raw_payload)
        if not is_valid:
            errors.extend(validation_errors)
            continue
        stripped = strip_pii_fields(raw_payload)
        normalized = normalize_devvit_payload(stripped)
        write_summary = write_devvit_reddit_signals(normalized, db, run_id)
        signals_written += int(write_summary.get("signals_written", 0))
        keywords_resolved += int(write_summary.get("keywords_resolved", 0))
        warnings.extend([str(item) for item in write_summary.get("warnings", [])])
    return {
        "status": "ok" if not errors else "error",
        "source_mode": "devvit_bridge",
        "signals_written": signals_written,
        "keywords_resolved": keywords_resolved,
        "niche_id": niche_id,
        "run_id": run_id,
        "import_dir": str(import_dir),
        "payload_files": len(payloads),
        "seed_keywords": list(seed_keywords),
        "warnings": warnings,
        "errors": errors,
    }
