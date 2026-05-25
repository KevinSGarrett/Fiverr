"""Fixture-backed parser for seller profile HTML."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_TAG_RE = re.compile(r"<[^>]+>")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", flags=re.IGNORECASE)
_API_KEYISH_RE = re.compile(
    r"\b(?:sk|api|key|token)[-_]?[A-Za-z0-9]{10,}\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class SellerProfileParseResult:
    """Parsed seller profile payload from fixture HTML."""

    username: str | None
    display_name: str | None
    level: str | None
    rating: float | None
    review_count: int | None
    country: str | None
    languages: list[str] = field(default_factory=list)
    member_since: str | None = None
    response_time: str | None = None
    last_delivery: str | None = None
    active_gig_count: int | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _clean_text(value: str) -> str:
    return " ".join(_TAG_RE.sub(" ", value).split())


def _extract_text(html: str, test_id: str) -> str | None:
    pattern = re.compile(
        fr"<[^>]*data-testid=['\"]{re.escape(test_id)}['\"][^>]*>(.*?)</[^>]+>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(html)
    if not match:
        return None
    text = _clean_text(match.group(1))
    return text or None


def _extract_text_any(html: str, test_ids: tuple[str, ...]) -> str | None:
    """Return first non-empty match across candidate data-testid values."""
    for test_id in test_ids:
        value = _extract_text(html, test_id)
        if value:
            return value
    return None


def _extract_number(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"([0-9][0-9,]*)", value)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def _extract_float(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"([0-5](?:\.[0-9])?)", value)
    if not match:
        return None
    return float(match.group(1))


def redact_sensitive_text(value: str) -> tuple[str, bool]:
    """Redact suspicious email/API-key-like patterns from scraped text."""

    redacted = _EMAIL_RE.sub("[redacted]", value)
    redacted = _API_KEYISH_RE.sub("[redacted]", redacted)
    return redacted, redacted != value


def parse_seller_profile_from_html(html: str) -> SellerProfileParseResult:
    """Parse seller profile fixture HTML safely and deterministically."""

    warnings: list[str] = []
    if "<" not in html or ">" not in html:
        return SellerProfileParseResult(
            username=None,
            display_name=None,
            level=None,
            rating=None,
            review_count=None,
            country=None,
            warnings=["Seller profile HTML appears malformed; no tags detected."],
            metadata={"mode": "fixture", "parsed": False},
        )

    username = _extract_text(html, "seller-username")
    display_name = _extract_text(html, "seller-display-name") or _extract_text(html, "seller-name")
    level = _extract_text_any(html, ("seller-level", "seller-overview-level"))
    rating = _extract_float(_extract_text(html, "seller-rating"))
    review_count = _extract_number(
        _extract_text_any(
            html,
            ("seller-review-count", "seller-reviews-count"),
        )
    )
    country = _extract_text(html, "seller-country")
    member_since = _extract_text_any(html, ("member-since", "seller-member-since"))
    response_time = _extract_text(html, "response-time")
    last_delivery = _extract_text(html, "last-delivery")
    active_gig_count = _extract_number(
        _extract_text_any(
            html,
            ("active-gig-count", "seller-active-gigs"),
        )
    )

    if rating is None:
        warnings.append("Seller rating was not found.")
    if review_count is None:
        warnings.append("Seller review count was not found.")

    language_blocks = re.findall(
        r"<[^>]*data-testid=['\"]seller-language['\"][^>]*>(.*?)</[^>]+>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    languages: list[str] = []
    for block in language_blocks:
        language = _clean_text(block)
        if language:
            languages.append(language)

    redacted = False
    candidate_fields = [username, display_name, country, member_since, response_time, last_delivery] + languages
    for candidate in candidate_fields:
        if candidate is None:
            continue
        _, field_redacted = redact_sensitive_text(candidate)
        redacted = redacted or field_redacted

    if redacted:
        warnings.append("Sensitive-looking text patterns were redacted.")
        username = redact_sensitive_text(username)[0] if username else None
        display_name = redact_sensitive_text(display_name)[0] if display_name else None
        country = redact_sensitive_text(country)[0] if country else None
        member_since = redact_sensitive_text(member_since)[0] if member_since else None
        response_time = redact_sensitive_text(response_time)[0] if response_time else None
        last_delivery = redact_sensitive_text(last_delivery)[0] if last_delivery else None
        languages = [redact_sensitive_text(language)[0] for language in languages]

    return SellerProfileParseResult(
        username=username,
        display_name=display_name,
        level=level,
        rating=rating,
        review_count=review_count,
        country=country,
        languages=languages,
        member_since=member_since,
        response_time=response_time,
        last_delivery=last_delivery,
        active_gig_count=active_gig_count,
        warnings=warnings,
        metadata={"mode": "fixture"},
    )
