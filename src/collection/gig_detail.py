"""Fixture-backed parser for Fiverr gig detail HTML."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

from src.collection.html_text import clean_html_text, extract_data_testid_text
from src.collection.selectors import get_selector

_PRICE_RE = re.compile(r"([$\u20ac\u00a3])\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
_DELIVERY_RE = re.compile(r"(\d{1,2})\s*day", flags=re.IGNORECASE)
_REVIEW_RE = re.compile(r"([0-9][0-9,]*)")
_RATING_RE = re.compile(r"([0-5](?:\.[0-9])?)")


@dataclass(frozen=True, slots=True)
class GigPackage:
    """Parsed package-level details."""

    name: str
    price: str | None
    price_cents: int | None
    delivery_days: int | None


@dataclass(frozen=True, slots=True)
class GigDetailParseResult:
    """Parsed gig detail payload from fixture HTML."""

    title: str | None
    seller_name: str | None
    packages: list[GigPackage] = field(default_factory=list)
    description: str | None = None
    has_faq: bool = False
    rating: float | None = None
    review_count: int | None = None
    image_count: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _clean_text(value: str) -> str:
    return clean_html_text(value)


def _extract_text(html: str, test_id: str) -> str | None:
    return extract_data_testid_text(html, test_id)


def _extract_first_by_tag(html: str, tag: str) -> str | None:
    match = re.search(fr"<{tag}\b[^>]*>(.*?)</{tag}>", html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    text = _clean_text(match.group(1))
    return text or None


def _normalize_price_to_cents(price_text: str | None) -> int | None:
    if not price_text:
        return None
    match = _PRICE_RE.search(price_text)
    if not match:
        return None
    raw_amount = match.group(2).replace(",", "")
    try:
        amount = Decimal(raw_amount)
    except InvalidOperation:
        return None
    return int((amount * 100).quantize(Decimal("1")))


def _extract_review_count(value: str | None) -> int | None:
    if not value:
        return None
    match = _REVIEW_RE.search(value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _extract_rating(value: str | None) -> float | None:
    if not value:
        return None
    match = _RATING_RE.search(value)
    if not match:
        return None
    return float(match.group(1))


def _extract_delivery_days(value: str | None) -> int | None:
    if not value:
        return None
    match = _DELIVERY_RE.search(value)
    if not match:
        return None
    return int(match.group(1))


def parse_gig_detail_from_html(html: str) -> GigDetailParseResult:
    """Parse gig detail fixture HTML with safe warnings and no side effects."""

    warnings: list[str] = []
    errors: list[str] = []

    # Safe selector-registry boundary to keep parser aligned with Cycle 003 registry.
    _ = get_selector("gig_detail", "gig_detail_title")

    if "<" not in html or ">" not in html:
        return GigDetailParseResult(
            title=None,
            seller_name=None,
            warnings=["Gig detail HTML appears malformed; no tags detected."],
            errors=["malformed_html"],
            metadata={"mode": "fixture", "parsed": False},
        )

    title = _extract_text(html, "gig-title") or _extract_first_by_tag(html, "h1")
    if not title:
        warnings.append("Gig title was not found.")

    seller_name = _extract_text(html, "seller-name")
    if not seller_name:
        warnings.append("Seller name was not found.")

    description = _extract_text(html, "gig-description")
    if not description:
        warnings.append("Gig description was not found.")

    has_faq = bool(_extract_text(html, "faq-section") or re.search(r"\bfaq\b", html, flags=re.IGNORECASE))
    rating = _extract_rating(_extract_text(html, "gig-rating"))
    review_count = _extract_review_count(_extract_text(html, "gig-review-count"))

    package_blocks = re.findall(
        r"<(?:div|section)\b[^>]*data-testid=['\"]package-card['\"][^>]*>(.*?)</(?:div|section)>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    packages: list[GigPackage] = []
    for block in package_blocks:
        package_name = _extract_text(block, "package-name") or _extract_first_by_tag(block, "h3") or "Unnamed package"
        package_price_text = _extract_text(block, "package-price")
        if not package_price_text:
            price_match = _PRICE_RE.search(block)
            package_price_text = price_match.group(0) if price_match else None
        package_delivery_text = _extract_text(block, "delivery-days")
        packages.append(
            GigPackage(
                name=package_name,
                price=package_price_text,
                price_cents=_normalize_price_to_cents(package_price_text),
                delivery_days=_extract_delivery_days(package_delivery_text),
            )
        )

    if not packages:
        warnings.append("No package cards were found in gig detail fixture.")

    image_count = len(re.findall(r"<img\b", html, flags=re.IGNORECASE))
    if image_count == 0:
        warnings.append("No images were detected in gig detail fixture.")

    return GigDetailParseResult(
        title=title,
        seller_name=seller_name,
        packages=packages,
        description=description,
        has_faq=has_faq,
        rating=rating,
        review_count=review_count,
        image_count=image_count,
        warnings=warnings,
        errors=errors,
        metadata={
            "mode": "fixture",
            "selector_group": "gig_detail",
            "package_count": len(packages),
        },
    )
