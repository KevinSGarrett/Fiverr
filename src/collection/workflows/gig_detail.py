"""Gig detail workflow interfaces for Stage 4."""
from __future__ import annotations

import html
import json
import re
import uuid
from datetime import UTC, datetime, timedelta
from types import ModuleType
from typing import Any
from urllib.parse import urlparse

from src.analysis.zombie_gig_detector import (
    MIN_ACCOUNT_AGE_DAYS,
    ZOMBIE_THRESHOLD,
    compute_zombie_score,
)
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
    config: dict[str, Any] | None = None,
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
        tags = parsed.tags
        faq_text = parsed.faq_text
        video_present = parsed.video_present
        portfolio_count = parsed.image_count
        review_count = parsed.review_count
        rating = parsed.rating
        starting_price = _parse_starting_price(packages)
        fallback_seller_username = _extract_seller_username_from_gig_url(gig_url)
        _, seller_queued = _persist_gig_detail_and_backfill_search_results(
            gig_url=gig_url,
            keyword_id=keyword_id,
            niche_id=niche_id,
            depth=depth,
            run_id=run_id,
            db=db,
            title=title,
            description=description,
            packages=packages,
            tags=tags,
            faq_text=faq_text,
            video_present=video_present,
            portfolio_count=portfolio_count,
            review_count=review_count,
            rating=rating,
            starting_price=starting_price,
            fallback_seller_username=fallback_seller_username,
            config=config,
        )

        return {
            "gig_url": gig_url,
            "keyword_id": keyword_id,
            "collected": True,
            "detail_collected": True,
            "title": title,
            "description_length": len(description) if description else 0,
            "packages_count": len(packages),
            "tags_count": len(tags) if tags is not None else None,
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
        fallback_seller_username = _extract_seller_username_from_gig_url(gig_url)
        _, seller_queued = _persist_gig_detail_and_backfill_search_results(
            gig_url=gig_url,
            keyword_id=keyword_id,
            niche_id=niche_id,
            depth=depth,
            run_id=run_id,
            db=db,
            title=title,
            description=description,
            packages=packages,
            tags=tags,
            faq_text=faq_text,
            video_present=video_present,
            portfolio_count=portfolio_count,
            review_count=review_count,
            rating=rating,
            starting_price=starting_price,
            fallback_seller_username=fallback_seller_username,
            config=config,
        )

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


def _normalize_gig_identity(gig_url: str | None) -> str:
    if not isinstance(gig_url, str):
        return ""
    normalized_url = html.unescape(build_gig_detail_url(gig_url).strip())
    if not normalized_url:
        return ""
    parsed = urlparse(normalized_url)
    path = parsed.path.strip().rstrip("/")
    return path.lower()


def _urls_match(url_a: str | None, url_b: str | None) -> bool:
    if not url_a or not url_b:
        return False

    def _normalize(raw: str) -> str:
        cleaned = html.unescape(raw).strip().lower()
        cleaned = re.sub(r"^https?://", "", cleaned)
        cleaned = cleaned.split("?", 1)[0]
        return cleaned.rstrip("/")

    return _normalize(url_a) == _normalize(url_b)


def _propagate_sponsored_flag(gig: Any, gig_cards: list[dict[str, Any]] | None) -> bool:
    if not isinstance(gig_cards, list):
        gig.is_sponsored = None
        return False
    for card in gig_cards:
        if not isinstance(card, dict):
            continue
        card_url = card.get("gig_url") or card.get("url")
        if _urls_match(card_url, gig.gig_url):
            gig.is_sponsored = bool(card.get("sponsored_flag", False))
            return True
    return False


def _coerce_card_position(value: Any) -> int | None:
    if isinstance(value, int) and value > 0:
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            parsed = int(stripped)
            if parsed > 0:
                return parsed
    return None


def _search_result_match_data(
    *,
    result_url: str | None,
    gig_cards: list[dict[str, Any]] | None,
    target_identity: str,
) -> tuple[bool, int | None, str | None]:
    if isinstance(result_url, str) and _normalize_gig_identity(result_url) == target_identity:
        return True, None, result_url
    if not isinstance(gig_cards, list):
        return False, None, None
    for card in gig_cards:
        if not isinstance(card, dict):
            continue
        raw_gig_url = card.get("gig_url")
        if not isinstance(raw_gig_url, str):
            continue
        if _normalize_gig_identity(raw_gig_url) != target_identity:
            continue
        return True, _coerce_card_position(card.get("position")), raw_gig_url
    return False, None, None


def _backfill_search_result_gig_id(
    *,
    keyword_id: int,
    gig_id: int,
    gig_url: str,
    db: Any,
) -> int:
    from sqlalchemy.orm import Session

    from src.models.search_result import SearchResult

    if not isinstance(db, Session):
        return 0
    target_identity = _normalize_gig_identity(gig_url)
    if not target_identity:
        return 0

    rows = db.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).all()
    updates = 0
    for row in rows:
        matched, matched_position, matched_url = _search_result_match_data(
            result_url=row.result_url,
            gig_cards=row.gig_cards,
            target_identity=target_identity,
        )
        if not matched:
            continue
        changed = False
        if row.gig_id != gig_id:
            row.gig_id = gig_id
            changed = True
        if not row.result_url and isinstance(matched_url, str) and matched_url.strip():
            row.result_url = matched_url.strip()
            changed = True
        if row.rank is None and matched_position is not None:
            row.rank = matched_position
            changed = True
        if changed:
            updates += 1
    return updates


def _persist_gig_detail_and_backfill_search_results(
    *,
    gig_url: str,
    keyword_id: int,
    niche_id: str,
    depth: str,
    run_id: str,
    db: Any,
    title: str | None,
    description: str | None,
    packages: list[dict[str, Any]],
    tags: list[str] | None,
    faq_text: str | None,
    video_present: bool | None,
    portfolio_count: int | None,
    review_count: int | None,
    rating: float | None,
    starting_price: float | None,
    fallback_seller_username: str,
    config: dict[str, Any] | None = None,
) -> tuple[str, bool]:
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.orm import Session

    from src.models.gig import Gig
    from src.models.job import Job
    from src.models.search_result import SearchResult
    from src.models.seller import Seller

    seller_username = fallback_seller_username
    seller_queued = False
    if not isinstance(db, Session):
        return seller_username, seller_queued

    has_search_results_table = False
    has_jobs_table = False
    has_sellers_table = False
    if db.bind is not None:
        inspector = sa_inspect(db.bind)
        has_search_results_table = inspector.has_table("search_results")
        has_jobs_table = inspector.has_table("jobs")
        has_sellers_table = inspector.has_table("sellers")

    gig = db.query(Gig).filter(Gig.gig_url == gig_url).first()
    if gig is None:
        gig = Gig(gig_url=gig_url, seller_username=fallback_seller_username)
        db.add(gig)

    gig.keyword_id = keyword_id
    gig.run_id = run_id
    gig.gig_title_full = title
    gig.title = title
    gig.description_text = description
    gig.packages = packages
    if tags is not None:
        gig.tags = tags
    if faq_text is not None:
        gig.faq_text = faq_text
    if video_present is not None:
        gig.video_present = video_present
    gig.portfolio_count = portfolio_count
    gig.review_count_exact = review_count
    gig.rating_exact = rating
    gig.starting_price = starting_price
    gig.detail_collected = True
    gig.detail_collected_at = datetime.now(UTC)
    gig.last_reviewed_at = _extract_last_review_date(gig.review_snippets)

    seller_username = gig.seller_username or fallback_seller_username
    db.flush()
    matched_rows = db.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).all() if has_search_results_table else []
    matched_sponsored = False
    for row in matched_rows:
        cards = row.gig_cards if isinstance(row.gig_cards, list) else []
        if not matched_sponsored and _propagate_sponsored_flag(gig, cards):
            matched_sponsored = True
        sponsored_count = sum(1 for card in cards if isinstance(card, dict) and bool(card.get("sponsored_flag")))
        row.sponsored_gig_count = sponsored_count
        row.organic_gig_count = max(0, len(cards) - sponsored_count)
    if not matched_sponsored:
        gig.is_sponsored = None
    if has_search_results_table:
        _backfill_search_result_gig_id(
            keyword_id=keyword_id,
            gig_id=gig.id,
            gig_url=gig_url,
            db=db,
        )

    relevance_cfg = _relevance_config(config)
    if relevance_cfg["enable_zombie_filter"]:
        seller = None
        if has_sellers_table:
            seller = db.query(Seller).filter(Seller.seller_username == seller_username).one_or_none()
        score, signals = compute_zombie_score(
            gig,
            seller,
            min_account_age_days=relevance_cfg["min_account_age_days"],
        )
        gig.is_zombie = score >= relevance_cfg["zombie_threshold"]
        gig.zombie_score = score
        gig.zombie_signals = json.dumps(signals)

    if depth != "keyword_only" and has_jobs_table:
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
    return seller_username, seller_queued


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
    normalized = text.strip().replace(",", "")
    if not normalized:
        return None
    k_match = re.match(r"^([0-9.]+)[kK]\+?$", normalized)
    if k_match:
        return int(float(k_match.group(1)) * 1000)
    numeric_match = re.search(r"\d+", normalized)
    return int(numeric_match.group(0)) if numeric_match else None


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


def _extract_last_review_date(snippets: Any, now: datetime | None = None) -> datetime | None:
    anchor = now or datetime.now(UTC)
    if snippets is None:
        return None

    if isinstance(snippets, str):
        candidates = [snippets]
    elif isinstance(snippets, list):
        candidates = []
        for snippet in snippets:
            if isinstance(snippet, str):
                candidates.append(snippet)
            elif isinstance(snippet, dict):
                for key in ("date", "review_date", "created_at", "text"):
                    raw = snippet.get(key)
                    if isinstance(raw, str):
                        candidates.append(raw)
    else:
        return None

    for raw in candidates:
        value = raw.strip()
        if not value:
            continue
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%b %Y", "%B %Y", "%d %b %Y"):
            try:
                parsed = datetime.strptime(value, fmt)
                if fmt in ("%b %Y", "%B %Y"):
                    parsed = parsed.replace(day=1)
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                continue
        lowered = value.lower()
        if lowered == "yesterday":
            return anchor - timedelta(days=1)
        relative_match = re.match(r"^(a|\d+)\s+(day|week|month|year)s?\s+ago$", lowered)
        if relative_match:
            quantity = 1 if relative_match.group(1) == "a" else int(relative_match.group(1))
            unit = relative_match.group(2)
            if unit == "day":
                return anchor - timedelta(days=quantity)
            if unit == "week":
                return anchor - timedelta(weeks=quantity)
            if unit == "month":
                return anchor - timedelta(days=quantity * 30)
            return anchor - timedelta(days=quantity * 365)
    return None


def _relevance_config(config: dict[str, Any] | None) -> dict[str, Any]:
    relevance = config.get("relevance", {}) if isinstance(config, dict) else {}
    return {
        "enable_sponsored_exclusion": bool(relevance.get("enable_sponsored_exclusion", True)),
        "enable_zombie_filter": bool(relevance.get("enable_zombie_filter", True)),
        "zombie_threshold": float(relevance.get("zombie_threshold", ZOMBIE_THRESHOLD)),
        "min_account_age_days": int(relevance.get("min_account_age_days", MIN_ACCOUNT_AGE_DAYS)),
        "top_n_for_scoring": int(relevance.get("top_n_for_scoring", 10)),
    }


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
