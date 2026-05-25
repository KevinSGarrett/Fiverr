"""Seller profile workflow interfaces for Stage 5."""
from __future__ import annotations

import inspect
import logging
import re
from datetime import UTC, datetime, timedelta
from types import ModuleType
from typing import Any

from sqlalchemy.orm import Session

from src.collection import seller_profile as _mod
from src.collection.fiverr_selectors import (
    SELLER_BADGE,
    SELLER_BIO,
    SELLER_GIG_TITLE,
    SELLER_LANGUAGES,
    SELLER_LEVEL_BADGE,
    SELLER_MEMBER_SINCE,
    SELLER_PORTFOLIO_ITEM,
    SELLER_RESPONSE_RATE,
    SELLER_RESPONSE_TIME,
    SELLER_TOTAL_GIGS,
    SELLER_TOTAL_REVIEWS,
)
from src.models.seller import Seller, get_seller, write_seller_profile

logger = logging.getLogger(__name__)


async def run_seller_profile_collection(
    seller_username: str,
    niche_id: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    checkpoint_manager: Any,
    dry_run: bool = True,
    fetcher: Any | None = None,
) -> dict[str, Any]:
    """
    Stage 5: Seller Profile Collection Per Username.

    Navigates to seller profile page, collects all seller fields, writes sellers row.
    """
    if dry_run:
        return {
            "seller_username": seller_username,
            "collected": False,
            "fields_collected": [],
            "dry_run": True,
            "note": "Dry run: no Playwright navigation performed",
        }

    # ------------------------------------------------------------------
    # ScrapFly / fetcher path — uses existing HTML parser, no Playwright
    # ------------------------------------------------------------------
    if fetcher is not None:
        from src.collection.seller_profile import parse_seller_profile_from_html
        profile_url = build_seller_profile_url(seller_username)
        fetch_result = await fetcher.fetch(profile_url, pacing_key="fiverr_seller_profile")
        parsed = parse_seller_profile_from_html(fetch_result.html)

        seller_level = parse_seller_level(getattr(parsed, "level", None))
        member_since = parse_member_since(getattr(parsed, "member_since", None))
        total_reviews = getattr(parsed, "review_count", None)
        total_gigs = getattr(parsed, "active_gig_count", None)

        if isinstance(db, Session):
            write_seller_profile(
                seller_username=seller_username,
                run_id=run_id,
                seller_level=seller_level,
                member_since=member_since,
                response_time=getattr(parsed, "response_time", None),
                total_reviews=total_reviews,
                total_gigs=total_gigs,
                db=db,
            )

        if checkpoint_manager is not None:
            await _write_stage05_checkpoint(
                checkpoint_manager=checkpoint_manager,
                run_id=run_id,
                niche_id=niche_id,
                seller_username=seller_username,
            )

        return {
            "seller_username": seller_username,
            "collected": True,
            "skipped": False,
            "dry_run": False,
            "seller_level": seller_level,
            "member_since": member_since,
            "response_time": getattr(parsed, "response_time", None),
            "response_rate": getattr(parsed, "response_rate", None),
            "languages": getattr(parsed, "languages", []),
            "bio_text": getattr(parsed, "bio_text", None),
            "total_reviews": total_reviews,
            "total_gigs": total_gigs,
            "active_gig_titles": getattr(parsed, "active_gig_titles", []),
            "portfolio_count": getattr(parsed, "portfolio_count", 0),
            "badges": getattr(parsed, "badges", []),
            "profile_url": profile_url,
            "backend": fetch_result.backend,
            "fetch_warnings": getattr(parsed, "warnings", []),
        }

    # ------------------------------------------------------------------
    # Playwright path (unchanged)
    # ------------------------------------------------------------------
    if (
        not hasattr(session_manager, "new_page")
        or not hasattr(session_manager, "close_page")
        or not hasattr(pacing_manager, "wait")
    ):
        raise NotImplementedError(
            "Seller profile collection with real Playwright requires session_manager and pacing_manager."
        )

    if isinstance(db, Session):
        existing = get_seller(seller_username, db)
        if existing and existing.profile_collected and existing.profile_collected_at:
            collected_at = existing.profile_collected_at
            if isinstance(collected_at, datetime):
                if collected_at.tzinfo is None:
                    collected_at = collected_at.replace(tzinfo=UTC)
                ttl = timedelta(hours=existing.ttl_hours or 720)
                if datetime.now(UTC) < collected_at + ttl:
                    return {
                        "seller_username": seller_username,
                        "collected": False,
                        "skipped": True,
                        "reason": "fresh_row_exists",
                        "dry_run": False,
                    }

    if should_skip_seller_profile(seller_username, run_id, db):
        return {
            "seller_username": seller_username,
            "collected": False,
            "skipped": True,
            "reason": "already_collected_this_run",
            "dry_run": False,
        }

    page: Any | None = None
    profile_url = build_seller_profile_url(seller_username)
    try:
        page = await session_manager.new_page()
        await page.goto(
            profile_url,
            wait_until="domcontentloaded",
            timeout=30_000,
        )
        await pacing_manager.wait("fiverr_seller_profile", dry_run=False)

        seller_level_text = await _safe_text(page, SELLER_LEVEL_BADGE)
        member_since_text = await _safe_text(page, SELLER_MEMBER_SINCE)
        response_time_text = await _safe_text(page, SELLER_RESPONSE_TIME)
        response_rate_text = await _safe_text(page, SELLER_RESPONSE_RATE)
        total_reviews_text = await _safe_text(page, SELLER_TOTAL_REVIEWS)
        total_gigs_text = await _safe_text(page, SELLER_TOTAL_GIGS)
        bio_text = await _safe_text(page, SELLER_BIO)

        seller_level = parse_seller_level(seller_level_text)
        member_since = parse_member_since(member_since_text)
        response_rate = parse_response_rate(response_rate_text)
        total_reviews = _parse_int(total_reviews_text)
        total_gigs = _parse_int(total_gigs_text)

        languages = await _safe_text_list(page, SELLER_LANGUAGES)
        active_gig_titles = await _safe_text_list(page, SELLER_GIG_TITLE, limit=20)
        portfolio_count = await _safe_count(page, SELLER_PORTFOLIO_ITEM)
        badges = await _safe_text_list(page, SELLER_BADGE)

        write_seller_profile(
            seller_username=seller_username,
            run_id=run_id,
            seller_level=seller_level,
            member_since=member_since,
            response_time=response_time_text,
            total_reviews=total_reviews,
            total_gigs=total_gigs,
            db=db,
        )

        if checkpoint_manager is not None:
            await _write_stage05_checkpoint(
                checkpoint_manager=checkpoint_manager,
                run_id=run_id,
                niche_id=niche_id,
                seller_username=seller_username,
            )

        return {
            "seller_username": seller_username,
            "collected": True,
            "skipped": False,
            "dry_run": False,
            "seller_level": seller_level,
            "member_since": member_since,
            "response_time": response_time_text,
            "response_rate": response_rate,
            "languages": languages,
            "bio_text": bio_text,
            "total_reviews": total_reviews,
            "total_gigs": total_gigs,
            "active_gig_titles": active_gig_titles,
            "portfolio_count": portfolio_count,
            "badges": badges,
            "profile_url": profile_url,
        }
    except Exception as exc:
        err_str = str(exc).lower()
        if "404" in err_str or "not found" in err_str:
            logger.warning("Seller 404: %s", seller_username)
            return {
                "seller_username": seller_username,
                "collected": False,
                "error": "404",
                "dry_run": False,
            }
        if "private" in err_str or "deactivated" in err_str:
            logger.warning("Seller private/deactivated: %s", seller_username)
            return {
                "seller_username": seller_username,
                "collected": False,
                "error": "private_or_deactivated",
                "dry_run": False,
            }
        raise
    finally:
        if page is not None:
            await session_manager.close_page(page)


def build_seller_profile_url(seller_username: str) -> str:
    """Spec: COLLECTION_WORKFLOWS.md W5 Step 4 — fiverr.com/{username}."""
    return f"https://www.fiverr.com/{seller_username}"


def parse_member_since(text: str | None) -> str | None:
    """Spec: W5 Step 6 — parse 'Member since Jan 2022' to '2022-01'."""
    if not text:
        return None

    months = {
        "jan": "01",
        "feb": "02",
        "mar": "03",
        "apr": "04",
        "may": "05",
        "jun": "06",
        "jul": "07",
        "aug": "08",
        "sep": "09",
        "oct": "10",
        "nov": "11",
        "dec": "12",
    }
    match = re.search(r"(\w{3})\s+(\d{4})", text.lower())
    if match:
        return f"{match.group(2)}-{months.get(match.group(1), '01')}"
    return None


def parse_seller_level(level_text: str | None) -> str:
    """Spec: W5 Step 6 — normalize seller level badge text."""
    if not level_text:
        return "NO_LEVEL"

    normalized = level_text.lower()
    if "top rated" in normalized or "trs" in normalized:
        return "TRS"
    if "level 2" in normalized or "level two" in normalized or "level_two" in normalized:
        return "LEVEL_2"
    if "level 1" in normalized or "level one" in normalized or "level_one" in normalized:
        return "LEVEL_1"
    if "pro" in normalized:
        return "PRO"
    return "NO_LEVEL"


def parse_response_rate(text: str | None) -> int | None:
    """Spec: W5 Step 6 — parse '98%' to 98."""
    if not text:
        return None
    digits = re.findall(r"\d+", text)
    return int(digits[0]) if digits else None


def _parse_int(text: str | None) -> int | None:
    if not text:
        return None
    nums = re.findall(r"[\d]+", text.replace(",", ""))
    return int(nums[0]) if nums else None


async def _safe_text(page: Any, selector: str) -> str | None:
    """Extract inner_text from selector. Returns None on any error — spec: 'Store null, continue'."""
    try:
        el = await page.query_selector(selector)
        return (await el.inner_text()).strip() if el else None
    except Exception:
        return None


async def _safe_text_list(page: Any, selector: str, *, limit: int | None = None) -> list[str]:
    """Best-effort extraction for repeated selectors; skips unreadable elements."""
    try:
        elements = await page.query_selector_all(selector)
    except Exception:
        return []
    rows = elements[:limit] if limit is not None else elements
    values: list[str] = []
    for el in rows:
        try:
            text = (await el.inner_text()).strip()
        except Exception:
            continue
        if text:
            values.append(text)
    return values


async def _safe_count(page: Any, selector: str) -> int:
    try:
        return len(await page.query_selector_all(selector))
    except Exception:
        return 0


async def _write_stage05_checkpoint(
    checkpoint_manager: Any,
    run_id: str,
    niche_id: str,
    seller_username: str,
) -> None:
    payload = {"seller_username": seller_username, "collected": True}
    write = getattr(checkpoint_manager, "write", None)
    if write is None:
        return
    try:
        maybe_result = write("stage05", niche_id, payload)
    except TypeError:
        # Compatibility for older/mock signatures: (run_id, stage_key, payload).
        maybe_result = write(run_id, f"stage05_{niche_id}", payload)
    if inspect.isawaitable(maybe_result):
        await maybe_result


def parse_seller_profile_fields(page_data: dict[str, Any]) -> dict[str, Any]:
    """
    Parse seller profile fields from page data.

    Stub returns all expected fields as None.
    """
    _ = page_data
    return {
        "seller_level": None,
        "member_since": None,
        "response_time": None,
        "response_rate": None,
        "languages": None,
        "bio_text": None,
        "total_reviews": None,
        "total_gigs": None,
        "active_gig_titles": None,
        "portfolio_count": None,
        "badges": None,
    }


def should_skip_seller_profile(seller_username: str, run_id: str, db: Any) -> bool:
    """Return True when seller profile was already collected for this run."""
    if not isinstance(db, Session):
        return False
    existing = (
        db.query(Seller)
        .filter(
            Seller.seller_username == seller_username,
            Seller.run_id == run_id,
            Seller.profile_collected.is_(True),
        )
        .first()
    )
    return existing is not None


class SellerProfileWorkflow:
    """Visits seller profile pages and extracts bio, stats, portfolio, skills."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        _ = (args, kwargs)
        return _mod
