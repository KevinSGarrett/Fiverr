"""Gig detail workflow interfaces for Stage 4."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import gig_detail as _mod


async def run_gig_detail_collection(
    gig_url: str,
    keyword_id: int,
    niche_id: str,
    depth: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    checkpoint_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 4: Gig Detail Collection Per Gig URL.

    Navigates to a gig URL, collects all gig detail fields, updates gig row in DB,
    queues seller username for Stage 5.
    """
    _ = (niche_id, depth, run_id, db, session_manager, pacing_manager, checkpoint_manager)
    if dry_run:
        return {
            "gig_url": gig_url,
            "keyword_id": keyword_id,
            "collected": False,
            "seller_queued": False,
            "fields_collected": [],
            "dry_run": True,
            "note": "Dry run: no Playwright navigation performed",
        }

    raise NotImplementedError(
        "Gig detail collection with real Playwright not yet implemented. "
        "Set dry_run=True."
    )


def get_top_n_gig_urls_for_keyword(keyword_id: int, depth: str, db: Any) -> list[str]:
    """
    Return top-N gig URLs for a keyword based on depth.

    Depth: full=20, standard=10, feasibility=5, keyword_only=0.
    """
    _ = keyword_id
    top_n = {"full": 20, "standard": 10, "feasibility": 5, "keyword_only": 0}
    n = top_n.get(depth, 10)
    if n == 0:
        return []

    try:
        from sqlalchemy.orm import Session

        if not isinstance(db, Session):
            return []
        # Stub: real impl will query SearchResult.gig_cards JSON.
        return []
    except Exception:
        return []


def parse_gig_detail_fields(page_data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse all gig detail fields from page data.

    Stub returns all expected keys as None.
    """
    _ = page_data
    return {
        "gig_title_full": None,
        "description_text": None,
        "packages": None,
        "gig_extras": None,
        "tags": None,
        "faq_text": None,
        "faq_entries": None,
        "video_present": None,
        "portfolio_count": None,
        "review_count_exact": None,
        "rating_exact": None,
        "review_snippets": None,
        "orders_in_queue": None,
        "thumbnail_url": None,
    }


def is_gig_removed(page_data: dict[str, Any]) -> bool:
    """Return True when page indicates 404/removed gig."""
    return page_data.get("status_code") == 404 or page_data.get("gig_removed", False)


def should_skip_gig_detail(gig_url: str, run_id: str, db: Any) -> bool:
    """Return True when gig detail was already collected for this run."""
    _ = (gig_url, run_id, db)
    # Stub: real implementation checks gig table state for this run.
    return False


class GigDetailWorkflow:
    """Visits each gig page and extracts full detail including packages, FAQ, extras."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        _ = (args, kwargs)
        return _mod
