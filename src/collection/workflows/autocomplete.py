"""Autocomplete workflow implementation and queue helpers."""
from __future__ import annotations

import inspect
import logging
import uuid
from datetime import UTC, datetime
from types import ModuleType
from typing import Any
from urllib.parse import quote

from src.collection import autocomplete as _mod
from src.collection.fiverr_selectors import AUTOCOMPLETE_ITEM, AUTOCOMPLETE_ITEM_TEXT, SEARCH_BOX
from src.models.job import Job
from src.models.market import write_autocomplete_suggestion

logger = logging.getLogger(__name__)


def build_autocomplete_search_url(keyword_text: str) -> str:
    """Build Fiverr search URL used to surface autocomplete suggestions."""
    return f"https://www.fiverr.com/search/gigs?query={quote(keyword_text)}"


async def _safe_pacing_wait(pacing_manager: Any, *, dry_run: bool) -> None:
    wait_fn = getattr(pacing_manager, "wait", None)
    if wait_fn is None:
        return
    await wait_fn("fiverr_search", dry_run=dry_run)


async def _write_stage08_checkpoint(
    checkpoint_manager: Any,
    *,
    keyword_id: int,
    niche_id: str,
    suggestions_collected: int,
    collected: bool,
) -> None:
    if checkpoint_manager is None:
        return
    write_fn = getattr(checkpoint_manager, "write", None)
    if write_fn is None:
        return
    payload = {
        "keyword_id": keyword_id,
        "suggestions_collected": suggestions_collected,
        "collected": collected,
    }
    try:
        maybe = write_fn("stage08", niche_id, payload)
        if inspect.isawaitable(maybe):
            await maybe
        return
    except TypeError:
        legacy_key = f"stage08_autocomplete_{niche_id}"
        maybe = write_fn(str(keyword_id), legacy_key, payload)
        if inspect.isawaitable(maybe):
            await maybe
    except Exception:
        logger.debug("Autocomplete checkpoint write failed.", exc_info=True)


async def _extract_suggestions(page: Any, keyword_text: str) -> list[dict[str, Any]]:
    items = await page.query_selector_all(AUTOCOMPLETE_ITEM)
    if not items:
        search_box = await page.query_selector(SEARCH_BOX)
        if search_box is not None:
            await search_box.click()
            await page.keyboard.type(keyword_text, delay=100)
            await page.wait_for_timeout(1_000)
            items = await page.query_selector_all(AUTOCOMPLETE_ITEM)

    suggestions: list[dict[str, Any]] = []
    for position, item in enumerate(items[:10], start=1):
        text_el = await item.query_selector(AUTOCOMPLETE_ITEM_TEXT)
        raw_text = await text_el.inner_text() if text_el else await item.inner_text()
        suggestion_text = raw_text.strip() if isinstance(raw_text, str) else ""
        if suggestion_text:
            suggestions.append({"suggestion_text": suggestion_text, "position": position})
    return suggestions


async def run_autocomplete_collection(
    *,
    keyword_id: int,
    keyword_text: str,
    niche_id: str,
    run_id: str,
    session_manager: Any,
    pacing_manager: Any,
    db: Any,
    checkpoint_manager: Any = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 8: collect Fiverr autocomplete suggestions for one keyword.

    This workflow is distinct from Workflow 2 Step 2a: it is queue-driven and
    persists stage-specific suggestion records for run-time analytics.
    """
    if dry_run:
        return {
            "keyword_id": keyword_id,
            "keyword_text": keyword_text,
            "niche_id": niche_id,
            "run_id": run_id,
            "suggestions_collected": 0,
            "collected": False,
            "dry_run": True,
            "note": "Dry run: W8 autocomplete collection not executed",
        }

    if session_manager is None:
        return {
            "keyword_id": keyword_id,
            "keyword_text": keyword_text,
            "niche_id": niche_id,
            "run_id": run_id,
            "suggestions_collected": 0,
            "collected": False,
            "dry_run": False,
            "error": "session_manager_unavailable",
        }

    page: Any = None
    suggestions: list[dict[str, Any]] = []
    collected = False
    error: str | None = None
    try:
        page = await session_manager.new_page()
        await page.goto(
            build_autocomplete_search_url(keyword_text),
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        suggestions = await _extract_suggestions(page, keyword_text)

        for suggestion in suggestions:
            write_autocomplete_suggestion(
                keyword_id=keyword_id,
                niche_id=niche_id,
                suggestion_text=str(suggestion["suggestion_text"]),
                position=int(suggestion["position"]),
                source="fiverr_autocomplete",
                run_id=run_id,
                db=db,
            )
        collected = True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Autocomplete collection failed keyword_id=%s niche_id=%s run_id=%s: %s",
            keyword_id,
            niche_id,
            run_id,
            exc,
        )
        error = str(exc)
    finally:
        if page is not None:
            try:
                close_page = getattr(session_manager, "close_page", None)
                if callable(close_page):
                    maybe = close_page(page)
                    if inspect.isawaitable(maybe):
                        await maybe
                else:
                    await page.close()
            except Exception:
                logger.debug("Failed to close autocomplete page.", exc_info=True)
        await _safe_pacing_wait(pacing_manager, dry_run=False)
        await _write_stage08_checkpoint(
            checkpoint_manager,
            keyword_id=keyword_id,
            niche_id=niche_id,
            suggestions_collected=len(suggestions),
            collected=collected,
        )

    return {
        "keyword_id": keyword_id,
        "keyword_text": keyword_text,
        "niche_id": niche_id,
        "run_id": run_id,
        "suggestions_collected": len(suggestions),
        "collected": collected,
        "dry_run": False,
        "error": error,
    }


def enqueue_autocomplete_job(
    *,
    keyword_id: int,
    keyword_text: str,
    niche_id: str,
    run_id: str,
    db: Any,
    priority: str = "STANDARD",
) -> bool:
    """Queue a Stage-8 AUTOCOMPLETE job for downstream processing."""
    try:
        from sqlalchemy.orm import Session
    except Exception:
        return False

    if not isinstance(db, Session):
        return False

    db.add(
        Job(
            job_id=f"autocomplete_{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            job_type="AUTOCOMPLETE",
            stage=8,
            niche_id=niche_id,
            priority=priority,
            status="QUEUED",
            payload={
                "keyword_id": keyword_id,
                "keyword_text": keyword_text,
                "niche_id": niche_id,
            },
            created_at=datetime.now(UTC),
        )
    )
    db.commit()
    return True


class AutocompleteWorkflow:
    """Wraps legacy fixture autocomplete module for compatibility."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
