"""Gig detail workflow interfaces for Stage 4."""
from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from types import ModuleType
from typing import Any
from urllib.parse import urlparse

from src.collection import gig_detail as _mod
from src.collection.fiverr_selectors import (
    GIG_DETAIL_DESCRIPTION,
    GIG_DETAIL_FAQ_ANSWER,
    GIG_DETAIL_FAQ_ITEMS,
    GIG_DETAIL_FAQ_QUESTION,
    GIG_DETAIL_PACKAGE_PRICE,
    GIG_DETAIL_PACKAGES,
    GIG_DETAIL_PORTFOLIO,
    GIG_DETAIL_RATING,
    GIG_DETAIL_REVIEW_COUNT,
    GIG_DETAIL_TAGS,
    GIG_DETAIL_TITLE,
    GIG_DETAIL_VIDEO,
)


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
    fetcher: Any | None = None,
) -> dict[str, Any]:
    """
    Stage 4: Gig Detail Collection Per Gig URL.

    Navigates to a gig URL, collects all gig detail fields, updates gig row in DB,
    queues seller username for Stage 5.
    """
    _ = (niche_id, depth, run_id, checkpoint_manager)
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

    # ------------------------------------------------------------------
    # ScrapFly / fetcher path — uses existing HTML parser, no Playwright
    # ------------------------------------------------------------------
    if fetcher is not None:
        from src.collection.gig_detail import parse_gig_detail_from_html
        detail_url = build_gig_detail_url(gig_url)
        fetch_result = await fetcher.fetch(detail_url, pacing_key="fiverr_gig_detail")
        parsed = parse_gig_detail_from_html(fetch_result.html)

        title = parsed.title
        description = parsed.description
        packages = [
            {"tier_index": i + 1, "price_text": pkg.price}
            for i, pkg in enumerate(parsed.packages)
        ]
        tags: list[str] = []
        faq_text = ""
        video_present = False
        portfolio_count = parsed.image_count
        review_count = parsed.review_count
        rating = parsed.rating
        starting_price = _parse_starting_price(packages)
        seller_username = _extract_seller_username_from_gig_url(gig_url)
        seller_queued = False

        from sqlalchemy.orm import Session

        from src.models.gig import Gig
        if isinstance(db, Session):
            from sqlalchemy import inspect as sa_inspect

            from src.models.job import Job

            gig = db.query(Gig).filter(Gig.gig_url == gig_url).first()
            if gig:
                gig.gig_title_full = title
                gig.description_text = description
                gig.packages = packages
                gig.tags = tags
                gig.faq_text = faq_text
                gig.video_present = video_present
                gig.portfolio_count = portfolio_count
                gig.review_count_exact = review_count
                gig.rating_exact = rating
                gig.starting_price = starting_price
                gig.detail_collected = True
                gig.detail_collected_at = datetime.now(UTC)
                seller_username = gig.seller_username or seller_username
            if depth != "keyword_only" and db.bind is not None and sa_inspect(db.bind).has_table("jobs"):
                db.add(
                    Job(
                        job_id=f"seller_profile_{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        job_type="SELLER_PROFILE",
                        stage=5,
                        niche_id=niche_id,
                        priority="STANDARD",
                        status="QUEUED",
                        payload={"seller_username": seller_username, "niche_id": niche_id},
                        created_at=datetime.now(UTC),
                    )
                )
                seller_queued = True
                db.commit()

        return {
            "gig_url": gig_url,
            "keyword_id": keyword_id,
            "collected": True,
            "detail_collected": True,
            "title": title,
            "description_length": len(description) if description else 0,
            "packages_count": len(packages),
            "tags_count": len(tags),
            "has_video": video_present,
            "portfolio_count": portfolio_count,
            "review_count": review_count,
            "rating": rating,
            "starting_price": starting_price,
            "seller_queued": seller_queued,
            "dry_run": False,
            "backend": fetch_result.backend,
            "fetch_warnings": parsed.warnings,
        }

    # ------------------------------------------------------------------
    # Playwright path (unchanged)
    # ------------------------------------------------------------------

    from sqlalchemy.orm import Session

    from src.models.gig import Gig

    detail_url = build_gig_detail_url(gig_url)
    page = await session_manager.new_page()
    try:
        await page.goto(detail_url, wait_until="domcontentloaded", timeout=30_000)
        await pacing_manager.wait("fiverr_gig_detail", dry_run=False)

        title = await _safe_inner_text(page, GIG_DETAIL_TITLE)
        description = await _safe_inner_text(page, GIG_DETAIL_DESCRIPTION)
        packages = await _extract_packages(page)
        tags = await _extract_tags(page)
        faq_text = await _extract_faq(page)

        video_present = await page.query_selector(GIG_DETAIL_VIDEO) is not None
        portfolio_count = len(await page.query_selector_all(GIG_DETAIL_PORTFOLIO))

        review_count_text = await _safe_inner_text(page, GIG_DETAIL_REVIEW_COUNT)
        rating_text = await _safe_inner_text(page, GIG_DETAIL_RATING)
        review_count = _parse_review_count(review_count_text)
        rating = _parse_rating(rating_text)
        starting_price = _parse_starting_price(packages)
        seller_username = _extract_seller_username_from_gig_url(gig_url)
        seller_queued = False

        if isinstance(db, Session):
            from sqlalchemy import inspect as sa_inspect

            from src.models.job import Job

            gig = db.query(Gig).filter(Gig.gig_url == gig_url).first()
            if gig:
                gig.gig_title_full = title
                gig.description_text = description
                gig.packages = packages
                gig.tags = tags
                gig.faq_text = faq_text
                gig.video_present = video_present
                gig.portfolio_count = portfolio_count
                gig.review_count_exact = review_count
                gig.rating_exact = rating
                gig.starting_price = starting_price
                gig.detail_collected = True
                gig.detail_collected_at = datetime.now(UTC)
                seller_username = gig.seller_username or seller_username
            if depth != "keyword_only" and db.bind is not None and sa_inspect(db.bind).has_table("jobs"):
                db.add(
                    Job(
                        job_id=f"seller_profile_{uuid.uuid4().hex[:12]}",
                        run_id=run_id,
                        job_type="SELLER_PROFILE",
                        stage=5,
                        niche_id=niche_id,
                        priority="STANDARD",
                        status="QUEUED",
                        payload={"seller_username": seller_username, "niche_id": niche_id},
                        created_at=datetime.now(UTC),
                    )
                )
                seller_queued = True
                db.commit()

        return {
            "gig_url": gig_url,
            "keyword_id": keyword_id,
            "collected": True,
            "detail_collected": True,
            "title": title,
            "description_length": len(description) if description else 0,
            "packages_count": len(packages),
            "tags_count": len(tags),
            "has_video": video_present,
            "portfolio_count": portfolio_count,
            "review_count": review_count,
            "rating": rating,
            "starting_price": starting_price,
            "seller_queued": seller_queued,
            "dry_run": False,
        }
    finally:
        await session_manager.close_page(page)


def build_gig_detail_url(gig_url: str) -> str:
    """Normalizes a gig URL for browser navigation."""
    cleaned = gig_url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme and parsed.netloc:
        return cleaned
    return f"https://www.fiverr.com{cleaned}" if cleaned.startswith("/") else cleaned


async def _safe_inner_text(page: Any, selector: str) -> str | None:
    node = await page.query_selector(selector)
    if node is None:
        return None
    text = (await node.inner_text()).strip()
    return text or None


async def _extract_packages(page: Any) -> list[dict[str, Any]]:
    """Extracts package tier pricing from gig detail page."""
    packages: list[dict[str, Any]] = []
    package_nodes = await page.query_selector_all(GIG_DETAIL_PACKAGES)
    for idx, package_node in enumerate(package_nodes, start=1):
        price_node = await package_node.query_selector(GIG_DETAIL_PACKAGE_PRICE)
        price_text = (await price_node.inner_text()).strip() if price_node else None
        packages.append({"tier_index": idx, "price_text": price_text})
    return packages


async def _extract_tags(page: Any) -> list[str]:
    """Extracts tags from gig detail page."""
    tags: list[str] = []
    tag_nodes = await page.query_selector_all(GIG_DETAIL_TAGS)
    for tag_node in tag_nodes:
        tag_text = (await tag_node.inner_text()).strip()
        if tag_text:
            tags.append(tag_text)
    return tags


async def _extract_faq(page: Any) -> str:
    """Extracts FAQ Q+A concatenated text."""
    faq_blocks = await page.query_selector_all(GIG_DETAIL_FAQ_ITEMS)
    entries: list[str] = []
    for faq in faq_blocks:
        question_node = await faq.query_selector(GIG_DETAIL_FAQ_QUESTION)
        answer_node = await faq.query_selector(GIG_DETAIL_FAQ_ANSWER)
        question = (await question_node.inner_text()).strip() if question_node else ""
        answer = (await answer_node.inner_text()).strip() if answer_node else ""
        pair = " ".join(part for part in [question, answer] if part).strip()
        if pair:
            entries.append(pair)
    return " | ".join(entries)


def _parse_review_count(text: str | None) -> int | None:
    if not text:
        return None
    nums = re.findall(r"[\d,]+", text)
    return int(nums[0].replace(",", "")) if nums else None


def _parse_rating(text: str | None) -> float | None:
    if not text:
        return None
    nums = re.findall(r"\d+\.\d+|\d+", text)
    return float(nums[0]) if nums else None


def _parse_starting_price(packages: list[dict[str, Any]]) -> float | None:
    prices: list[float] = []
    for package in packages:
        price_text = package.get("price_text")
        if not isinstance(price_text, str):
            continue
        nums = re.findall(r"[\d.]+", price_text.replace(",", ""))
        if nums:
            prices.append(float(nums[0]))
    return min(prices) if prices else None


def _extract_seller_username_from_gig_url(gig_url: str) -> str:
    parsed = urlparse(gig_url.strip())
    path = parsed.path if parsed.path else gig_url
    parts = [part for part in path.split("/") if part]
    return parts[0] if parts else "unknown_seller"


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
