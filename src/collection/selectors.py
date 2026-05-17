"""Selector registry and static HTML parsing helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from html import unescape


@dataclass(frozen=True, slots=True)
class ParsedSearchCard:
    """Parsed search result card candidate from static HTML."""

    title: str
    url: str
    seller_name: str | None
    price: str | None


SELECTOR_REGISTRY: dict[str, dict[str, str]] = {
    "search_results": {
        "result_card": "article[data-testid='gig-card'], div[data-testid='gig-card'], section[data-gig-id]",
        "gig_title": "[data-testid='gig-title'], h3[data-testid='gig-title']",
        "gig_url": "a[href*='/services/']",
        "seller_name": "[data-testid='seller-name']",
        "price": "[data-testid='gig-price']",
        "rating": "[data-testid='gig-rating']",
        "review_count": "[data-testid='gig-review-count']",
    },
    "pagination": {
        "next_page": "a[aria-label='Next'], button[aria-label='Next page']",
    },
    "gig_detail": {
        "gig_detail_title": "h1[data-testid='gig-title'], h1",
        "package_cards": "[data-testid='package-card'], .package-card",
    },
    "seller_profile": {
        "seller_profile_name": "h1[data-testid='seller-name']",
        "seller_profile_level": "[data-testid='seller-level']",
        "seller_profile_rating": "[data-testid='seller-rating']",
        "seller_profile_response_time": "[data-testid='response-time']",
    },
    # AC-2.2.3: VISUAL group for Wave 11 thumbnail/gallery analysis
    "visual": {
        "gig_thumbnail": "img[data-testid='gig-thumbnail'], img.gig-package-image, img[class*='thumbnail']",
        "gallery_item": "[data-testid='gallery-item'], .gallery-slide img, .attachment-media img",
        "video_indicator": "[data-testid='video-overlay'], .video-gig-card, video, iframe[src*='youtube'], iframe[src*='vimeo']",
        "seller_avatar": "img[data-testid='seller-avatar'], .avatar-photo img, img[class*='avatar']",
        "gallery_count": "[data-testid='gallery-count'], .gallery-counter",
    },
    "page_state": {
        "unavailable_indicator": "[data-testid='page-unavailable'], .error-page",
        "blocked_indicator": "form[action*='challenge'], [data-testid='blocked-page']",
    },
}


REQUIRED_SELECTORS: dict[str, tuple[str, ...]] = {
    "search_results": (
        "result_card",
        "gig_title",
        "gig_url",
        "seller_name",
        "price",
        "rating",
        "review_count",
    ),
    "pagination": ("next_page",),
    "gig_detail": ("gig_detail_title", "package_cards"),
    "seller_profile": (
        "seller_profile_name",
        "seller_profile_level",
        "seller_profile_rating",
        "seller_profile_response_time",
    ),
    "visual": (
        "gig_thumbnail",
        "gallery_item",
        "video_indicator",
        "seller_avatar",
    ),
    "page_state": ("unavailable_indicator", "blocked_indicator"),
}


def get_selector(group: str, name: str) -> str:
    """Return selector by group and name."""

    selectors = SELECTOR_REGISTRY.get(group)
    if selectors is None:
        raise KeyError(f"Unknown selector group '{group}'.")
    selector = selectors.get(name)
    if selector is None:
        raise KeyError(f"Unknown selector '{name}' in group '{group}'.")
    return selector


def validate_selector_registry(
    registry: Mapping[str, Mapping[str, str]] | None = None,
) -> list[str]:
    """Validate registry for required groups, selectors, and values."""

    active_registry = registry or SELECTOR_REGISTRY
    errors: list[str] = []
    for group, required_names in REQUIRED_SELECTORS.items():
        if group not in active_registry:
            errors.append(f"Missing selector group '{group}'.")
            continue
        for name in required_names:
            if not active_registry[group].get(name):
                errors.append(f"Missing selector '{name}' in group '{group}'.")
    return errors


_CARD_BLOCK_RE = re.compile(
    r"<(?:article|div|section)\b[^>]*(?:data-testid=['\"]gig-card['\"]|data-gig-id=)[^>]*>.*?</(?:article|div|section)>",
    flags=re.IGNORECASE | re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


def _extract_attr(block: str, attr_name: str) -> str | None:
    pattern = re.compile(fr'{attr_name}=["\']([^"\']+)["\']', flags=re.IGNORECASE)
    match = pattern.search(block)
    return match.group(1).strip() if match else None


def _extract_text(block: str, test_id: str) -> str | None:
    pattern = re.compile(
        fr"<[^>]*data-testid=['\"]{re.escape(test_id)}['\"][^>]*>(.*?)</[^>]+>",
        flags=re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(block)
    if not match:
        return None
    cleaned = _TAG_RE.sub("", match.group(1))
    return unescape(" ".join(cleaned.split()))


def parse_search_result_cards_from_html(html: str) -> list[ParsedSearchCard]:
    """Parse static HTML and extract search result card candidates."""

    cards: list[ParsedSearchCard] = []
    for block in _CARD_BLOCK_RE.findall(html):
        title = _extract_text(block, "gig-title")
        url = _extract_attr(block, "href")
        if not title or not url:
            continue
        cards.append(
            ParsedSearchCard(
                title=title,
                url=url,
                seller_name=_extract_text(block, "seller-name"),
                price=_extract_text(block, "gig-price"),
            )
        )
    return cards
