"""Fixture-backed parser for seller profile HTML."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
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


def _extract_review_count_fallback(html: str) -> int | None:
    # Live seller markup often renders review totals as "156<!-- --> Reviews".
    rich_match = re.search(
        r">([0-9][0-9,]*)\s*(?:<!--.*?-->\s*)?</span>\s*Reviews\b",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if rich_match:
        return int(rich_match.group(1).replace(",", ""))
    plain_match = re.search(r"([0-9][0-9,]*)\s*reviews\b", html, flags=re.IGNORECASE)
    if plain_match:
        return int(plain_match.group(1).replace(",", ""))
    return None


def _extract_json_ld_objects(html: str) -> list[dict[str, Any]]:
    matches = re.findall(
        r"<script[^>]*type=['\"]application/ld\+json['\"][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    entries: list[dict[str, Any]] = []
    for block in matches:
        payload = block.strip()
        if not payload:
            continue
        try:
            decoded = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, dict):
            entries.append(decoded)
            graph = decoded.get("@graph")
            if isinstance(graph, list):
                entries.extend([item for item in graph if isinstance(item, dict)])
        elif isinstance(decoded, list):
            entries.extend([item for item in decoded if isinstance(item, dict)])
    return entries


def _extract_next_data_payload(html: str) -> dict[str, Any] | None:
    match = re.search(
        r"<script[^>]*id=['\"]__NEXT_DATA__['\"][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    payload = match.group(1).strip()
    if not payload:
        return None
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def _extract_json_script_payload(html: str, script_id: str) -> dict[str, Any] | None:
    match = re.search(
        rf"<script[^>]*id=['\"]{re.escape(script_id)}['\"][^>]*>(.*?)</script>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    payload = match.group(1).strip()
    if not payload:
        return None
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        return None
    return decoded if isinstance(decoded, dict) else None


def _walk_json_dicts(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        rows.append(value)
        for nested in value.values():
            rows.extend(_walk_json_dicts(nested))
    elif isinstance(value, list):
        for nested in value:
            rows.extend(_walk_json_dicts(nested))
    return rows


def _extract_seller_data_from_json_ld(html: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "username": None,
        "display_name": None,
        "level": None,
        "rating": None,
        "review_count": None,
        "country": None,
        "languages": [],
        "member_since": None,
        "response_time": None,
        "active_gig_count": None,
    }
    for entry in _extract_json_ld_objects(html):
        if result["display_name"] is None and isinstance(entry.get("name"), str):
            result["display_name"] = _clean_text(entry.get("name") or "")
        if result["rating"] is None and isinstance(entry.get("aggregateRating"), dict):
            result["rating"] = _extract_float(str(entry["aggregateRating"].get("ratingValue")))
            result["review_count"] = _extract_number(str(entry["aggregateRating"].get("reviewCount")))
        if result["country"] is None:
            area_served = entry.get("areaServed")
            if isinstance(area_served, str):
                result["country"] = _clean_text(area_served)
        if not result["languages"] and isinstance(entry.get("knowsLanguage"), list):
            result["languages"] = [str(item).strip() for item in entry["knowsLanguage"] if str(item).strip()]
    return result


def _extract_seller_data_from_next_data(html: str) -> dict[str, Any]:
    payloads = [value for value in (_extract_next_data_payload(html), _extract_json_script_payload(html, "perseus-initial-props")) if isinstance(value, dict)]
    if not payloads:
        return {}
    result: dict[str, Any] = {
        "username": None,
        "display_name": None,
        "level": None,
        "rating": None,
        "review_count": None,
        "country": None,
        "languages": [],
        "member_since": None,
        "response_time": None,
        "last_delivery": None,
        "active_gig_count": None,
    }
    for payload in payloads:
        seller = payload.get("seller")
        if isinstance(seller, dict):
            user = seller.get("user")
            if isinstance(user, dict):
                if result["username"] is None and isinstance(user.get("name"), str):
                    result["username"] = _clean_text(user.get("name") or "")
                profile = user.get("profile")
                if isinstance(profile, dict) and result["display_name"] is None and isinstance(profile.get("displayName"), str):
                    result["display_name"] = _clean_text(profile.get("displayName") or "")
                address = user.get("address")
                if isinstance(address, dict) and result["country"] is None and isinstance(address.get("countryName"), str):
                    result["country"] = _clean_text(address.get("countryName") or "")
                joined_at = user.get("joinedAt")
                if result["member_since"] is None and isinstance(joined_at, int):
                    try:
                        joined = datetime.fromtimestamp(joined_at, tz=UTC)
                        result["member_since"] = joined.strftime("%b %Y")
                    except (TypeError, ValueError, OSError):
                        pass
                languages_raw = user.get("languages")
                if not result["languages"] and isinstance(languages_raw, list):
                    languages: list[str] = []
                    for language in languages_raw:
                        if not isinstance(language, dict):
                            continue
                        code = language.get("code")
                        if isinstance(code, str) and code.strip():
                            languages.append(code.strip())
                    result["languages"] = languages

            if result["level"] is None and isinstance(seller.get("sellerLevel"), str):
                level_text = str(seller.get("sellerLevel")).replace("_", " ").strip()
                result["level"] = level_text
            if result["active_gig_count"] is None and seller.get("approvedGigsCount") is not None:
                parsed_count = _extract_number(str(seller.get("approvedGigsCount")))
                if parsed_count is not None:
                    result["active_gig_count"] = parsed_count

        reviews_data = payload.get("reviewsData")
        if isinstance(reviews_data, dict):
            selling_reviews = reviews_data.get("selling_reviews")
            if isinstance(selling_reviews, dict) and result["review_count"] is None:
                parsed_count = _extract_number(str(selling_reviews.get("total_count")))
                if parsed_count is not None:
                    result["review_count"] = parsed_count

    for payload in payloads:
        for entry in _walk_json_dicts(payload):
            if result["username"] is None:
                for key in ("sellerUsername", "username", "userName"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["username"] = _clean_text(entry.get(key) or "")
                        break
            if result["display_name"] is None:
                for key in ("displayName", "sellerName", "name"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["display_name"] = _clean_text(entry.get(key) or "")
                        break
            if result["level"] is None:
                for key in ("sellerLevel", "level", "levelName"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["level"] = _clean_text(entry.get(key) or "")
                        break
            if result["member_since"] is None:
                for key in ("memberSince", "member_since", "joinDate"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["member_since"] = _clean_text(entry.get(key) or "")
                        break
            if result["response_time"] is None:
                for key in ("responseTime", "response_time"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["response_time"] = _clean_text(entry.get(key) or "")
                        break
            if result["last_delivery"] is None:
                for key in ("lastDelivery", "last_delivery"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["last_delivery"] = _clean_text(entry.get(key) or "")
                        break
            if result["rating"] is None:
                for key in ("rating", "averageRating"):
                    if entry.get(key) is not None:
                        parsed_rating = _extract_float(str(entry.get(key)))
                        if parsed_rating is not None:
                            result["rating"] = parsed_rating
                            break
            if result["review_count"] is None:
                for key in ("reviewCount", "reviewsCount", "totalReviews"):
                    if entry.get(key) is not None:
                        parsed_count = _extract_number(str(entry.get(key)))
                        if parsed_count is not None:
                            result["review_count"] = parsed_count
                            break
            if result["active_gig_count"] is None:
                for key in ("activeGigCount", "active_gig_count", "totalGigs"):
                    if entry.get(key) is not None:
                        parsed_count = _extract_number(str(entry.get(key)))
                        if parsed_count is not None:
                            result["active_gig_count"] = parsed_count
                            break
            if result["country"] is None:
                for key in ("country", "countryName", "location"):
                    if isinstance(entry.get(key), str) and entry.get(key):
                        result["country"] = _clean_text(entry.get(key) or "")
                        break
            if not result["languages"]:
                for key in ("languages", "spokenLanguages"):
                    value = entry.get(key)
                    if isinstance(value, list):
                        result["languages"] = [str(item).strip() for item in value if str(item).strip()]
                        break
    return result


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

    json_ld = _extract_seller_data_from_json_ld(html)
    next_data = _extract_seller_data_from_next_data(html)

    username = _extract_text(html, "seller-username") or next_data.get("username") or json_ld.get("username")
    display_name = (
        _extract_text(html, "seller-display-name")
        or _extract_text(html, "seller-name")
        or next_data.get("display_name")
        or json_ld.get("display_name")
    )
    level = _extract_text_any(html, ("seller-level", "seller-overview-level")) or next_data.get("level") or json_ld.get("level")
    rating = _extract_float(_extract_text(html, "seller-rating")) or next_data.get("rating") or json_ld.get("rating")
    review_count = _extract_number(
        _extract_text_any(
            html,
            ("seller-review-count", "seller-reviews-count"),
        )
    )
    if review_count is None:
        review_count = next_data.get("review_count")
    if review_count is None:
        review_count = json_ld.get("review_count")
    if review_count is None:
        review_count = _extract_review_count_fallback(html)
    country = _extract_text(html, "seller-country") or next_data.get("country") or json_ld.get("country")
    member_since = _extract_text_any(html, ("member-since", "seller-member-since")) or next_data.get("member_since") or json_ld.get("member_since")
    response_time = _extract_text(html, "response-time") or next_data.get("response_time") or json_ld.get("response_time")
    last_delivery = _extract_text(html, "last-delivery") or next_data.get("last_delivery")
    active_gig_count = _extract_number(
        _extract_text_any(
            html,
            ("active-gig-count", "seller-active-gigs"),
        )
    )
    if active_gig_count is None:
        active_gig_count = next_data.get("active_gig_count")
    if active_gig_count is None:
        active_gig_count = json_ld.get("active_gig_count")

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
    if not languages:
        next_languages = next_data.get("languages")
        if isinstance(next_languages, list):
            languages = [str(language).strip() for language in next_languages if str(language).strip()]
    if not languages:
        json_ld_languages = json_ld.get("languages")
        if isinstance(json_ld_languages, list):
            languages = [str(language).strip() for language in json_ld_languages if str(language).strip()]

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
