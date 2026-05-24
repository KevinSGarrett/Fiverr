"""Fiverr search workflow interfaces for Stage 3."""
from __future__ import annotations

import re
import urllib.parse
import uuid
from datetime import UTC, datetime
from typing import Any

from src.collection.fiverr_selectors import (
    GIG_CARD_CONTAINER,
    GIG_CARD_LINK,
    GIG_CARD_PRICE,
    GIG_CARD_REVIEW_COUNT,
    GIG_CARD_SELLER_LEVEL,
    GIG_CARD_SELLER_NAME,
    GIG_CARD_SPONSORED,
    GIG_CARD_TITLE,
    SEARCH_RESULT_COUNT,
)
from src.collection.workflows.autocomplete import enqueue_autocomplete_job
from src.models.job import Job
from src.models.search_result import write_search_result


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
    enqueue_autocomplete: bool = False,
    fetcher: Any | None = None,
) -> dict[str, Any]:
    """
    Stage 3: Fiverr Search Collection Per Keyword.

    Navigates to Fiverr search, collects gig cards, writes search_results row,
    and queues gig URLs for detail collection.
    """
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

    # ------------------------------------------------------------------
    # ScrapFly / fetcher path
    # ------------------------------------------------------------------
    if fetcher is not None:
        from src.collection.search_result_parser import parse_search_results_from_html

        url = build_fiverr_search_url(keyword_text)
        fetch_result = await fetcher.fetch(url, pacing_key="fiverr_search")
        parsed = parse_search_results_from_html(fetch_result.html)

        parsed_gig_cards = [
            {
                "position": card.position,
                "gig_url": card.gig_url,
                "gig_title": card.gig_title,
                "seller_username": card.seller_username,
                "seller_level": card.seller_level,
                "review_count_visible": card.review_count_visible,
                "starting_price": card.starting_price,
                "sponsored_flag": card.sponsored_flag,
            }
            for card in parsed.gig_cards
        ]

        write_search_result(
            keyword_id=keyword_id,
            run_id=run_id,
            total_result_count=parsed.total_result_count,
            pagination_depth=None,
            gig_cards=parsed_gig_cards,
            page_collected=1,
            db=db,
        )

        gig_urls_queued = _queue_gig_detail_jobs(
            keyword_id=keyword_id,
            niche_id=niche_id,
            run_id=run_id,
            gig_cards=parsed_gig_cards,
            depth=depth,
            db=db,
        )

        return {
            "keyword_id": keyword_id,
            "keyword_text": keyword_text,
            "niche_id": niche_id,
            "total_result_count": parsed.total_result_count,
            "gig_cards_collected": len(parsed_gig_cards),
            "gig_urls_queued": gig_urls_queued,
            "autocomplete_jobs_queued": 0,
            "pages_collected": 1,
            "dry_run": False,
            "backend": fetch_result.backend,
            "parse_warnings": parsed.warnings,
        }

    # ------------------------------------------------------------------
    # Playwright path (unchanged — existing code below)
    # ------------------------------------------------------------------

    url = build_fiverr_search_url(keyword_text)
    gig_cards: list[dict[str, Any]] = []
    total_result_count: int | None = None
    gig_urls_queued = 0
    autocomplete_jobs_queued = 0

    page = await session_manager.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await pacing_manager.wait("fiverr_search", dry_run=False)

        count_el = await page.query_selector(SEARCH_RESULT_COUNT)
        if count_el:
            total_result_count = _parse_result_count(await count_el.inner_text())

        card_els = await page.query_selector_all(GIG_CARD_CONTAINER)
        for index, card in enumerate(card_els[:20]):
            card_data = await _extract_gig_card(card, index + 1)
            if card_data:
                gig_cards.append(card_data)

        write_search_result(
            keyword_id=keyword_id,
            run_id=run_id,
            total_result_count=total_result_count,
            pagination_depth=None,
            gig_cards=gig_cards,
            page_collected=1,
            db=db,
        )

        gig_urls_queued = _queue_gig_detail_jobs(
            keyword_id=keyword_id,
            niche_id=niche_id,
            run_id=run_id,
            gig_cards=gig_cards,
            depth=depth,
            db=db,
        )
        if enqueue_autocomplete and depth != "keyword_only":
            if enqueue_autocomplete_job(
                keyword_id=keyword_id,
                keyword_text=keyword_text,
                niche_id=niche_id,
                run_id=run_id,
                db=db,
            ):
                autocomplete_jobs_queued = 1
    finally:
        await session_manager.close_page(page)

    return {
        "keyword_id": keyword_id,
        "keyword_text": keyword_text,
        "niche_id": niche_id,
        "total_result_count": total_result_count,
        "gig_cards_collected": len(gig_cards),
        "gig_urls_queued": gig_urls_queued,
        "autocomplete_jobs_queued": autocomplete_jobs_queued,
        "pages_collected": 1,
        "dry_run": False,
    }


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


async def _safe_text(card_element: Any, selector: str) -> str | None:
    node = await card_element.query_selector(selector)
    if node is None:
        return None
    text = (await node.inner_text()).strip()
    return text or None


async def _safe_attribute(card_element: Any, selector: str, attr_name: str) -> str | None:
    node = await card_element.query_selector(selector)
    if node is None:
        return None
    value = await node.get_attribute(attr_name)
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


async def _extract_gig_card(card_element: Any, position: int) -> dict[str, Any] | None:
    """Extract structured data from a single gig card element."""
    gig_url = await _safe_attribute(card_element, GIG_CARD_LINK, "href")
    gig_title = await _safe_text(card_element, GIG_CARD_TITLE)
    seller_username = await _safe_text(card_element, GIG_CARD_SELLER_NAME)
    seller_level = await _safe_text(card_element, GIG_CARD_SELLER_LEVEL)
    review_count_text = await _safe_text(card_element, GIG_CARD_REVIEW_COUNT)
    starting_price_text = await _safe_text(card_element, GIG_CARD_PRICE)
    sponsored_flag = bool(await card_element.query_selector(GIG_CARD_SPONSORED))

    if not gig_url and not gig_title:
        return None

    return {
        "position": position,
        "gig_url": gig_url,
        "gig_title": gig_title,
        "seller_username": seller_username,
        "seller_level": seller_level,
        "review_count_visible": _parse_result_count(review_count_text),
        "starting_price": _parse_price(starting_price_text),
        "sponsored_flag": sponsored_flag,
    }


def _parse_result_count(text: str | None) -> int | None:
    """Parses values like '1,234 results for X' into 1234."""
    if not text:
        return None
    nums = re.findall(r"[\d]+", text.replace(",", ""))
    return int(nums[0]) if nums else None


def _parse_price(text: str | None) -> float | None:
    """Parses values like '$95' into 95.0."""
    if not text:
        return None
    nums = re.findall(r"[\d.]+", text.replace(",", ""))
    return float(nums[0]) if nums else None


def _queue_gig_detail_jobs(
    keyword_id: int,
    niche_id: str,
    run_id: str,
    gig_cards: list[dict[str, Any]],
    depth: str,
    db: Any,
) -> int:
    """Create stage-4 GIG_DETAIL jobs from collected gig URLs."""
    from sqlalchemy.orm import Session

    if depth == "keyword_only" or not isinstance(db, Session):
        return 0

    top_n = {"full": 20, "standard": 10, "feasibility": 5}.get(depth, 10)
    queued = 0
    for card in gig_cards[:top_n]:
        gig_url = card.get("gig_url")
        if not gig_url:
            continue
        db.add(
            Job(
                job_id=f"gig_detail_{uuid.uuid4().hex[:12]}",
                run_id=run_id,
                job_type="GIG_DETAIL",
                stage=4,
                niche_id=niche_id,
                priority="STANDARD",
                status="QUEUED",
                payload={"gig_url": gig_url, "keyword_id": keyword_id},
                created_at=datetime.now(UTC),
            )
        )
        queued += 1
    db.commit()
    return queued


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
