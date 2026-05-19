"""Keyword expansion workflow interfaces for Stage 2."""
from __future__ import annotations

import logging
from types import ModuleType
from typing import Any

import httpx

from src.collection import keyword_expansion as _mod

logger = logging.getLogger(__name__)

_FEATURE_FLAGS: dict[str, bool] = {
    "step_2a_fiverr_autocomplete": False,
    "step_2c_llm_generation": False,
    "step_2d_llm_relevance_filter": False,
    "step_2f_llm_intent_classification": False,
    "step_2g_embedding_generation": False,
}


async def _safe_pacing_wait(pacing_manager: Any, pacing_key: str, *, dry_run: bool) -> None:
    wait_fn = getattr(pacing_manager, "wait", None)
    if wait_fn is None:
        return
    await wait_fn(pacing_key, dry_run=dry_run)


async def _fetch_google_suggest(seed: str, pacing_manager: Any) -> list[str]:
    """Fetches Google Suggest completions for a seed keyword."""
    cleaned_seed = seed.strip()
    if not cleaned_seed:
        return []

    url = f"https://suggestqueries.google.com/complete/search?q={cleaned_seed}&client=firefox"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            data = resp.json()
            if not (isinstance(data, list) and len(data) > 1 and isinstance(data[1], list)):
                return []
            return [value.strip() for value in data[1] if isinstance(value, str) and value.strip()]
    except (httpx.HTTPError, TimeoutError, ValueError, TypeError):
        logger.warning("Google Suggest fetch failed for seed '%s'.", cleaned_seed)
        return []
    finally:
        await _safe_pacing_wait(pacing_manager, "external_default", dry_run=False)


def _deduplicate_keywords(keyword_list: list[str]) -> list[str]:
    """Case-insensitive deduplication with whitespace cleanup."""
    seen: set[str] = set()
    result: list[str] = []
    for kw in keyword_list:
        normalized = kw.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(kw.strip())
    return result


def _is_session(db: Any) -> bool:
    try:
        from sqlalchemy.orm import Session
    except Exception:
        return False
    return isinstance(db, Session)


def _resolve_niche_pk(niche_id: str, db: Any) -> int | None:
    try:
        from src.models.niche import Niche
    except Exception:
        return int(niche_id) if niche_id.isdigit() else None

    if niche_id.isdigit():
        return int(niche_id)

    try:
        record = db.query(Niche).filter(Niche.slug == niche_id).first()
    except Exception:
        return None
    if record is None:
        return None
    return int(record.id)


def _write_keywords_to_db(niche_id: str, keyword_list: list[str], db: Any) -> int:
    if not _is_session(db):
        return 0

    niche_pk = _resolve_niche_pk(niche_id, db)
    if niche_pk is None:
        logger.warning("Unable to resolve niche '%s' to a DB primary key; skipping keyword writes.", niche_id)
        return 0

    from src.collection.keyword_expansion import normalize_keyword
    from src.models.base import utc_now
    from src.models.market import Keyword

    try:
        existing_rows = (
            db.query(Keyword.normalized_keyword).filter(Keyword.niche_id == niche_pk).all()
        )
        existing_normalized = {row[0] for row in existing_rows if isinstance(row[0], str)}
    except Exception:
        db.rollback()
        logger.warning("Keyword table lookup failed; skipping DB writes for niche '%s'.", niche_id)
        return 0

    inserted = 0
    for keyword_text in keyword_list:
        normalized = normalize_keyword(keyword_text)
        if not normalized or normalized in existing_normalized:
            continue

        db.add(
            Keyword(
                niche_id=niche_pk,
                keyword=keyword_text,
                normalized_keyword=normalized,
                external_source="google_suggest",
                source_collected_at=utc_now(),
                metadata_json={"source": "google_suggest", "autocomplete_position": None},
            )
        )
        existing_normalized.add(normalized)
        inserted += 1

    if inserted > 0:
        db.commit()
    return inserted


async def run_keyword_expansion(
    niche_id: str,
    seeds: list[str],
    depth: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 2 keyword expansion stub.

    `dry_run=True` is smoke-safe and performs no live browser/LLM activity.
    """
    _ = (depth, run_id, session_manager)
    if dry_run:
        return {
            "niche_id": niche_id,
            "keywords_queued": 0,
            "sources": {
                "fiverr_autocomplete": 0,
                "google_suggest": 0,
                "llm_generated": 0,
            },
            "dry_run": True,
            "note": "Dry run: no real Playwright or LLM calls made",
        }

    if not _FEATURE_FLAGS["step_2a_fiverr_autocomplete"]:
        logger.warning("Workflow 2 Step 2a stubbed: Fiverr autocomplete is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2c_llm_generation"]:
        logger.warning("Workflow 2 Step 2c stubbed: LLM generation is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2d_llm_relevance_filter"]:
        logger.warning("Workflow 2 Step 2d stubbed: LLM relevance filter is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2f_llm_intent_classification"]:
        logger.warning("Workflow 2 Step 2f stubbed: LLM intent classification is feature-flagged off.")
    if not _FEATURE_FLAGS["step_2g_embedding_generation"]:
        logger.warning("Workflow 2 Step 2g stubbed: embedding generation is feature-flagged off.")

    fiverr_autocomplete_keywords: list[str] = []
    llm_generated_keywords: list[str] = []
    _ = (fiverr_autocomplete_keywords, llm_generated_keywords)

    google_suggest_keywords: list[str] = []
    for seed in seeds:
        if not isinstance(seed, str):
            continue
        google_suggest_keywords.extend(await _fetch_google_suggest(seed, pacing_manager))

    deduplicated_google = _deduplicate_keywords(google_suggest_keywords)

    keywords_queued = len(deduplicated_google)
    if _is_session(db):
        keywords_queued = _write_keywords_to_db(niche_id, deduplicated_google, db)

    return {
        "niche_id": niche_id,
        "keywords_queued": keywords_queued,
        "sources": {
            "fiverr_autocomplete": 0,
            "google_suggest": keywords_queued,
            "llm_generated": 0,
        },
        "dry_run": False,
    }


async def run_keyword_expansion_stub(
    niche_id: str,
    seeds: list[str],
    depth: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Alias required by workflow package exports."""
    return await run_keyword_expansion(
        niche_id=niche_id,
        seeds=seeds,
        depth=depth,
        run_id=run_id,
        db=db,
        session_manager=session_manager,
        pacing_manager=pacing_manager,
        dry_run=dry_run,
    )


class KeywordExpansionWorkflow:
    """Wraps keyword_expansion module; expands seed keywords via Fiverr autocomplete."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
