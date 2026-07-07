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
from src.collection.search_url_builder import (
    DEFAULT_MIN_RESULT_THRESHOLD,
    FALLBACK_MIN_RESULT_THRESHOLD_KEY,
    SearchStrictness,
    build_search_url,
    check_category_mapping_freshness,
    get_niche_mapping,
    search_with_fallback,
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
    search_config: dict[str, Any] | None = None,
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

    check_category_mapping_freshness()
    threshold = _resolve_result_threshold(search_config)
    strictness_used = SearchStrictness.NONE
    has_known_niche_mapping = get_niche_mapping(niche_id) is not None
    strictness_order = (
        (SearchStrictness.NONE,)
        if not has_known_niche_mapping
        else (
            SearchStrictness.SUBCATEGORY,
            SearchStrictness.CATEGORY,
            SearchStrictness.NONE,
        )
    )

    # ------------------------------------------------------------------
    # ScrapFly / fetcher path
    # ------------------------------------------------------------------
    if fetcher is not None:
        parsed_gig_cards: list[dict[str, Any]] = []
        total_result_count: int | None = None
        fetch_backend = "unknown"
        parse_warnings: list[str] = []
        collected_cards_by_url: dict[str, list[dict[str, Any]]] = {}
        collected_count_by_url: dict[str, int | None] = {}
        any_fetch_ok = False
        for strictness in strictness_order:
            candidate_url = build_search_url(keyword_text, niche_id, strictness)
            cards, total_count, backend, warnings, fetch_ok = await _collect_search_page_via_fetcher(
                candidate_url, fetcher
            )
            any_fetch_ok = any_fetch_ok or fetch_ok
            collected_cards_by_url[candidate_url] = cards
            collected_count_by_url[candidate_url] = total_count
            parsed_gig_cards = cards
            total_result_count = total_count
            fetch_backend = backend
            parse_warnings = warnings
            strictness_used = strictness
            if len(parsed_gig_cards) >= threshold:
                break

        if not any_fetch_ok:
            # Every strictness attempt failed to fetch. Persisting an empty result set
            # here would look identical to a genuinely-empty (ghost) market to
            # downstream result-set validation - return a visible failure instead
            # (Codex review, PR #170).
            return {
                "keyword_id": keyword_id,
                "keyword_text": keyword_text,
                "niche_id": niche_id,
                "total_result_count": None,
                "gig_cards_collected": 0,
                "gig_urls_queued": 0,
                "autocomplete_jobs_queued": 0,
                "pages_collected": 0,
                "dry_run": False,
                "backend": fetch_backend,
                "parse_warnings": parse_warnings,
                "fetch_failed": True,
                "search_strictness_used": strictness_used.value,
            }

        if has_known_niche_mapping:
            selected_cards, selected_strictness = search_with_fallback(
                keyword_text,
                niche_id,
                {FALLBACK_MIN_RESULT_THRESHOLD_KEY: threshold},
                lambda url: collected_cards_by_url.get(url, []),
            )
            strictness_used = selected_strictness
            selected_url = build_search_url(keyword_text, niche_id, strictness_used)
            parsed_gig_cards = selected_cards
            total_result_count = collected_count_by_url.get(selected_url)

        write_search_result(
            keyword_id=keyword_id,
            run_id=run_id,
            total_result_count=total_result_count,
            pagination_depth=None,
            gig_cards=parsed_gig_cards,
            page_collected=1,
            search_strictness_used=strictness_used.value,
            pages_collected=1,
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
            "total_result_count": total_result_count,
            "gig_cards_collected": len(parsed_gig_cards),
            "gig_urls_queued": gig_urls_queued,
            "autocomplete_jobs_queued": 0,
            "pages_collected": 1,
            "dry_run": False,
            "backend": fetch_backend,
            "parse_warnings": parse_warnings,
            "search_strictness_used": strictness_used.value,
        }

    # ------------------------------------------------------------------
    # Playwright path (unchanged — existing code below)
    # ------------------------------------------------------------------

    gig_cards: list[dict[str, Any]] = []
    playwright_total_result_count: int | None = None
    gig_urls_queued = 0
    autocomplete_jobs_queued = 0
    play_cards_by_url: dict[str, list[dict[str, Any]]] = {}
    play_count_by_url: dict[str, int | None] = {}

    page = await session_manager.new_page()
    try:
        for strictness in strictness_order:
            candidate_url = build_search_url(keyword_text, niche_id, strictness)
            gig_cards, playwright_total_result_count = await _collect_search_page_via_playwright(
                page=page,
                url=candidate_url,
                pacing_manager=pacing_manager,
            )
            play_cards_by_url[candidate_url] = gig_cards
            play_count_by_url[candidate_url] = playwright_total_result_count
            strictness_used = strictness
            if len(gig_cards) >= threshold:
                break
        if has_known_niche_mapping:
            selected_cards, selected_strictness = search_with_fallback(
                keyword_text,
                niche_id,
                {FALLBACK_MIN_RESULT_THRESHOLD_KEY: threshold},
                lambda url: play_cards_by_url.get(url, []),
            )
            strictness_used = selected_strictness
            selected_url = build_search_url(keyword_text, niche_id, strictness_used)
            gig_cards = selected_cards
            playwright_total_result_count = play_count_by_url.get(selected_url)

        write_search_result(
            keyword_id=keyword_id,
            run_id=run_id,
            total_result_count=playwright_total_result_count,
            pagination_depth=None,
            gig_cards=gig_cards,
            page_collected=1,
            search_strictness_used=strictness_used.value,
            pages_collected=1,
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
        "total_result_count": playwright_total_result_count,
        "gig_cards_collected": len(gig_cards),
        "gig_urls_queued": gig_urls_queued,
        "autocomplete_jobs_queued": autocomplete_jobs_queued,
        "pages_collected": 1,
        "dry_run": False,
        "search_strictness_used": strictness_used.value,
    }


def _resolve_result_threshold(config: dict[str, Any] | None) -> int:
    if not isinstance(config, dict):
        return DEFAULT_MIN_RESULT_THRESHOLD
    raw_value = config.get(FALLBACK_MIN_RESULT_THRESHOLD_KEY, DEFAULT_MIN_RESULT_THRESHOLD)
    try:
        return max(1, int(raw_value))
    except (TypeError, ValueError):
        return DEFAULT_MIN_RESULT_THRESHOLD


async def _collect_search_page_via_fetcher(
    url: str,
    fetcher: Any,
) -> tuple[list[dict[str, Any]], int | None, str, list[str], bool]:
    from src.collection.search_result_parser import parse_search_results_from_html

    fetch_result = await fetcher.fetch(url, pacing_key="fiverr_search")
    # A blocked/failed fetch must not be parsed as if it were a real results page.
    # The final fetch_ok flag lets the caller distinguish "fetched fine, genuinely
    # zero results" (real ghost-market evidence worth persisting) from "could not
    # fetch at all" (a transient failure that must NOT be persisted as market data,
    # since downstream result-set validation reads zero-card rows as ghost markets)
    # (SCRUM-1096 + Codex review, PR #170).
    if not getattr(fetch_result, "success", True) or not fetch_result.html:
        failure_note = (
            f"Fetch failed (success={getattr(fetch_result, 'success', True)}, "
            f"status={fetch_result.status_code}); page not parsed."
        )
        return [], None, fetch_result.backend, [failure_note], False
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
    return parsed_gig_cards, parsed.total_result_count, fetch_result.backend, parsed.warnings, True


async def _collect_search_page_via_playwright(
    page: Any,
    url: str,
    pacing_manager: Any,
) -> tuple[list[dict[str, Any]], int | None]:
    await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    await pacing_manager.wait("fiverr_search", dry_run=False)

    total_result_count: int | None = None
    count_el = await page.query_selector(SEARCH_RESULT_COUNT)
    if count_el:
        total_result_count = _parse_result_count(await count_el.inner_text())

    gig_cards: list[dict[str, Any]] = []
    card_els = await page.query_selector_all(GIG_CARD_CONTAINER)
    for index, card in enumerate(card_els[:20]):
        card_data = await _extract_gig_card(card, index + 1)
        if card_data:
            gig_cards.append(card_data)
    return gig_cards, total_result_count


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
                payload={
                    "gig_url": gig_url,
                    "keyword_id": keyword_id,
                    "niche_id": niche_id,
                    "depth": depth,
                },
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
