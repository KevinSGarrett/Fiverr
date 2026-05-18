"""Keyword expansion workflow interfaces for Stage 2."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import keyword_expansion as _mod


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
    _ = (seeds, depth, run_id, db, session_manager, pacing_manager)
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

    raise NotImplementedError(
        "Keyword expansion with real Playwright not yet implemented. "
        "Set dry_run=True for stub execution."
    )


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
