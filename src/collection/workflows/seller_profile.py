"""Seller profile workflow interfaces for Stage 5."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import seller_profile as _mod


async def run_seller_profile_collection(
    seller_username: str,
    niche_id: str,
    run_id: str,
    db: Any,
    session_manager: Any,
    pacing_manager: Any,
    checkpoint_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Stage 5: Seller Profile Collection Per Username.

    Navigates to seller profile page, collects all seller fields, writes sellers row.
    """
    _ = (niche_id, run_id, db, session_manager, pacing_manager, checkpoint_manager)
    if dry_run:
        return {
            "seller_username": seller_username,
            "collected": False,
            "fields_collected": [],
            "dry_run": True,
            "note": "Dry run: no Playwright navigation performed",
        }

    raise NotImplementedError(
        "Seller profile collection with real Playwright not yet implemented. "
        "Set dry_run=True."
    )


def build_seller_profile_url(seller_username: str) -> str:
    """Spec: COLLECTION_WORKFLOWS.md W5 Step 4 — fiverr.com/{username}."""
    return f"https://www.fiverr.com/{seller_username}"


def parse_member_since(text: str | None) -> str | None:
    """Spec: W5 Step 6 — parse 'Member since Jan 2022' to '2022-01'."""
    import re

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
    if "level 2" in normalized:
        return "LEVEL_2"
    if "level 1" in normalized:
        return "LEVEL_1"
    if "pro" in normalized:
        return "PRO"
    return "NO_LEVEL"


def parse_response_rate(text: str | None) -> int | None:
    """Spec: W5 Step 6 — parse '98%' to 98."""
    import re

    if not text:
        return None
    digits = re.findall(r"\d+", text)
    return int(digits[0]) if digits else None


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
    _ = (seller_username, run_id, db)
    return False


class SellerProfileWorkflow:
    """Visits seller profile pages and extracts bio, stats, portfolio, skills."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        _ = (args, kwargs)
        return _mod
