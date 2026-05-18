"""Fiverr search workflow interfaces for Stage 3."""
from __future__ import annotations

import urllib.parse
from typing import Any


async def run_fiverr_search_collection(
    keyword_id: int,
    keyword_text: str,
    niche_id: str,
    depth: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 3: Fiverr Search Collection Per Keyword.

    Navigates to Fiverr search, collects gig cards, writes search_results row,
    and queues gig URLs for detail collection.
    """
    _ = (depth, run_id, db, session_manager, pacing_manager)
    if dry_run:
        return {
            "keyword_id": keyword_id,
            "keyword_text": keyword_text,
            "niche_id": niche_id,
            "total_result_count": None,
            "gig_cards_collected": 0,
            "gig_urls_queued": 0,
            "pages_collected": 0,
            "dry_run": True,
            "note": "Dry run: no real Playwright navigation performed",
        }

    raise NotImplementedError(
        "Fiverr search collection with real Playwright not yet implemented. "
        "Set dry_run=True for stub execution."
    )


def build_fiverr_search_url(keyword_text: str) -> str:
    """Build the Fiverr search URL for a keyword."""
    encoded = urllib.parse.quote(keyword_text)
    return f"https://www.fiverr.com/search/gigs?query={encoded}"


def parse_gig_cards_from_page(page_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Parse gig card data from a collected page dictionary.

    Stub behavior: returns the `cards` list from the page payload.
    """
    return page_data.get("cards", [])


def should_collect_page_2(depth: str, intent_class: str) -> bool:
    """Return True when depth/intents require collecting page 2."""
    return depth == "full" and intent_class in ("HIGH_INTENT", "TRANSACTIONAL")


def is_keyword_only_depth(depth: str) -> bool:
    """Return True when depth is keyword_only."""
    return depth == "keyword_only"


class FiverrSearchWorkflow:
    """Searches each keyword on Fiverr and extracts gig cards."""

    def run(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("FiverrSearchWorkflow.run() — pending E02 implementation.")
