"""HTML-based parser for Fiverr search result pages.

Used when ScrapFly (or PlaywrightFetcher) returns raw HTML and we need to
extract gig cards without Playwright selector calls.

Mirrors the field set extracted by _extract_gig_card() in workflows/fiverr_search.py
so downstream DB writes are identical regardless of which backend fetched the page.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, urlparse

# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SearchGigCard:
    """One gig card from a Fiverr search results page."""

    position: int
    gig_url: str | None
    gig_title: str | None
    seller_username: str | None
    seller_level: str | None
    review_count_visible: int | None
    starting_price: float | None
    sponsored_flag: bool


@dataclass(frozen=True, slots=True)
class SearchParseResult:
    """Output of parse_search_results_from_html()."""

    total_result_count: int | None
    gig_cards: list[SearchGigCard]
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

_PRICE_RE = re.compile(r"[$€£]\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
_NUM_RE = re.compile(r"[0-9][0-9,]*")
_SELLER_RE = re.compile(r"fiverr\.com/([a-zA-Z0-9_.-]+)")
_GIG_PATH_RE = re.compile(r"fiverr\.com/[a-zA-Z0-9_.-]+/[^\"'\s?#]+")
_GIG_PATH_REL_RE = re.compile(r"^/[a-zA-Z0-9_.-]+/[^\"'\s?#]+")
_HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
_TESTID_RE = re.compile(r'data-testid=["\']([^"\']+)["\']', re.IGNORECASE)


def _clean(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text).split())


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    m = _PRICE_RE.search(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def _parse_count(text: str | None) -> int | None:
    if not text:
        return None
    m = _NUM_RE.search(text.replace(",", ""))
    return int(m.group(0)) if m else None


def _extract_seller_from_url(href: str) -> str | None:
    m = _SELLER_RE.search(href)
    if not m:
        return None
    username = m.group(1)
    # Filter out known non-username path segments
    skip = {"search", "categories", "gigs", "login", "register", "about", "help"}
    return username if username not in skip else None


def _is_gig_url(href: str) -> bool:
    if "/search/" in href:
        return False
    return bool(_GIG_PATH_RE.search(href) or _GIG_PATH_REL_RE.search(href))


def _normalise_gig_url(href: str | None) -> str | None:
    if not href:
        return None
    if href.startswith("/"):
        return f"https://www.fiverr.com{href}"
    return href


def _fallback_cards_from_hrefs(html: str, max_cards: int) -> list[dict[str, str | bool | None]]:
    """Heuristic extraction when Fiverr removes stable data-testid hooks."""
    cards: list[dict[str, str | bool | None]] = []
    seen_paths: set[str] = set()

    for href in _HREF_RE.findall(html):
        if not _is_gig_url(href):
            continue
        normalised = _normalise_gig_url(href)
        if not normalised:
            continue

        parsed = urlparse(normalised)
        query = parse_qs(parsed.query)
        # Keep likely SERP listing links; avoid generic/internal anchors.
        if not (
            "source" in query and any("gig_cards" in value for value in query["source"])
            or "referrer_gig_slug" in query
            or "context_referrer" in query
            or "pckg_id" in query
        ):
            continue

        key = parsed.path.strip().lower()
        if not key or key in seen_paths:
            continue
        seen_paths.add(key)

        cards.append(
            {
                "href": normalised,
                "seller_username": _extract_seller_from_url(normalised),
                "sponsored": False,
            }
        )
        if len(cards) >= max_cards:
            break
    return cards


def _as_str(value: str | bool | None) -> str | None:
    return value if isinstance(value, str) else None


# ---------------------------------------------------------------------------
# perseus-initial-props JSON extraction
#
# Fiverr's search SPA embeds the full result set (gig objects, seller stats,
# pricing, pagination) as JSON in a `perseus-initial-props` script tag. It is
# the authoritative, complete data source — the rendered `data-testid`
# markup the _CardCollector below scans for has been removed from current
# Fiverr search pages, which is why that path degrades to the href-only
# fallback (no title/price/rating) in production today.
# ---------------------------------------------------------------------------

_PERSEUS_SCRIPT_RE = re.compile(
    r'<script[^>]*\bid=["\']perseus-initial-props["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)


def _extract_perseus_props(html: str) -> dict[str, Any] | None:
    """Locate and parse the perseus-initial-props JSON blob. Never raises."""
    match = _PERSEUS_SCRIPT_RE.search(html)
    if not match:
        return None
    try:
        props = json.loads(match.group(1).strip())
    except (ValueError, TypeError):
        return None
    return props if isinstance(props, dict) else None


def _perseus_total_result_count(props: dict[str, Any]) -> int | None:
    app_data = props.get("appData")
    pagination = app_data.get("pagination") if isinstance(app_data, dict) else None
    total = pagination.get("total") if isinstance(pagination, dict) else None
    return total if isinstance(total, int) else None


def _perseus_gig_price(gig: dict[str, Any]) -> float | None:
    # price_i / packages.recommended.price are already the displayed dollar amount
    # (e.g. price_i=495 renders as "From $495"), NOT cents — do not divide by 100.
    price = gig.get("price_i")
    if not isinstance(price, int | float):
        packages = gig.get("packages")
        recommended = packages.get("recommended") if isinstance(packages, dict) else None
        price = recommended.get("price") if isinstance(recommended, dict) else None
    return float(price) if isinstance(price, int | float) else None


def _perseus_review_count(gig: dict[str, Any]) -> int | None:
    # The gig card's visible review count is buying_review_rating_count, e.g. "(5)" —
    # seller_rating.count is the seller's aggregate across ALL their gigs and can be
    # far larger than what's shown on this specific card.
    count = gig.get("buying_review_rating_count")
    return int(count) if isinstance(count, int | float) else None


def _gig_cards_from_perseus(props: dict[str, Any], max_cards: int) -> list[SearchGigCard]:
    listings = props.get("listings")
    raw_gigs: list[Any] = []
    if isinstance(listings, list) and listings and isinstance(listings[0], dict):
        candidate = listings[0].get("gigs")
        if isinstance(candidate, list):
            raw_gigs = candidate

    cards: list[SearchGigCard] = []
    for index, gig in enumerate(raw_gigs[:max_cards]):
        if not isinstance(gig, dict):
            continue
        raw_pos = gig.get("pos")
        position = raw_pos + 1 if isinstance(raw_pos, int) else index + 1
        title = gig.get("title")
        cards.append(
            SearchGigCard(
                position=position,
                gig_url=_normalise_gig_url(_as_str(gig.get("gig_url"))),
                gig_title=title.strip() if isinstance(title, str) and title.strip() else None,
                seller_username=_as_str(gig.get("seller_name")),
                seller_level=_as_str(gig.get("seller_level")),
                review_count_visible=_perseus_review_count(gig),
                starting_price=_perseus_gig_price(gig),
                sponsored_flag=gig.get("type") == "promoted_gigs",
            )
        )
    return cards


# ---------------------------------------------------------------------------
# Lightweight HTML walker
# ---------------------------------------------------------------------------

class _CardCollector(HTMLParser):
    """
    Single-pass HTML walker that extracts gig card data.

    Fiverr uses data-testid attributes on key elements.  We scan for the
    same testids that fiverr_selectors.py targets so results stay aligned.

    Gracefully degrades — returns whatever it can find, never raises.
    """

    # testid values that identify card-level containers
    _CARD_TESTIDS = frozenset({"gig-card-layout", "gig_listing_item", "gig-card"})
    # testids for individual fields within a card
    _FIELD_TESTIDS = {
        "gig-title":           "title",
        "seller-name":         "seller_username",
        "seller-level":        "seller_level",
        "review-count":        "review_count",
        "starting-price":      "price",
        "price":               "price",
    }
    _SPONSORED_TESTIDS = frozenset({"sponsored-badge", "promoted-badge", "ad-badge"})
    _COUNT_TESTID = "total-result-count"

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._depth: int = 0                     # overall tag depth
        self._card_start_depth: int | None = None
        self._in_card: bool = False

        # per-card accumulators
        self._current: dict[str, str | None] = {}
        self._current_href: str | None = None
        self._sponsored: bool = False

        # active field collection
        self._collect_field: str | None = None
        self._collect_depth: int = 0
        self._chunks: list[str] = []

        # outputs
        self.cards: list[dict[str, str | bool | None]] = []
        self.total_result_count_text: str | None = None
        self._in_count: bool = False
        self._count_depth: int = 0
        self._count_chunks: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self._depth += 1
        attr_dict = {k: (v or "") for k, v in attrs}
        testid = attr_dict.get("data-testid", "")
        href = attr_dict.get("href", "")

        # ---- total result count ----
        if testid == self._COUNT_TESTID and not self._in_count:
            self._in_count = True
            self._count_depth = self._depth
            self._count_chunks = []
            return

        if self._in_count:
            if self._collect_field is None:
                self._count_chunks.append(href)  # just accumulate data
            return

        # ---- card boundary ----
        if not self._in_card and testid in self._CARD_TESTIDS:
            self._in_card = True
            self._card_start_depth = self._depth
            self._current = {}
            self._current_href = None
            self._sponsored = False
            return

        if not self._in_card:
            return

        # ---- sponsored badge ----
        if testid in self._SPONSORED_TESTIDS:
            self._sponsored = True

        # ---- link (gig URL + seller username) ----
        if tag == "a" and href and _is_gig_url(href) and self._current_href is None:
            self._current_href = href

        # ---- field collectors ----
        if self._collect_field is None and testid in self._FIELD_TESTIDS:
            self._collect_field = self._FIELD_TESTIDS[testid]
            self._collect_depth = self._depth
            self._chunks = []

    def handle_endtag(self, tag: str) -> None:
        # total count
        if self._in_count:
            if self._depth == self._count_depth:
                self.total_result_count_text = _clean("".join(self._count_chunks)) or None
                self._in_count = False
            self._depth -= 1
            return

        # field collection end
        if self._collect_field is not None and self._depth == self._collect_depth:
            text = _clean("".join(self._chunks))
            self._current[self._collect_field] = text or None
            self._collect_field = None
            self._chunks = []

        # card end
        if self._in_card and self._card_start_depth is not None:
            if self._depth == self._card_start_depth:
                self.cards.append({
                    **self._current,
                    "href": self._current_href,
                    "sponsored": self._sponsored,
                })
                self._in_card = False
                self._card_start_depth = None

        self._depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_count and not self._in_card:
            self._count_chunks.append(data)
            return
        if self._collect_field is not None:
            self._chunks.append(data)

    def close(self) -> None:
        # Flush any unclosed card (malformed HTML safety)
        if self._in_card and self._current:
            self.cards.append({
                **self._current,
                "href": self._current_href,
                "sponsored": self._sponsored,
            })
        # Flush count text
        if self._in_count and self._count_chunks:
            self.total_result_count_text = _clean("".join(self._count_chunks)) or None
        super().close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_search_results_from_html(
    html: str,
    *,
    max_cards: int = 20,
) -> SearchParseResult:
    """Parse a Fiverr search results page from raw HTML.

    Returns SearchParseResult with .gig_cards and .total_result_count.
    Never raises — warnings list captures any degraded-parse conditions.

    Args:
        html:      Full page HTML from ScrapFly or PlaywrightFetcher.
        max_cards: Cap returned card count (mirrors Playwright workflow default).
    """
    warnings: list[str] = []

    if not html or "<" not in html:
        return SearchParseResult(
            total_result_count=None,
            gig_cards=[],
            warnings=["Search HTML is empty or contains no tags."],
        )

    perseus_props = _extract_perseus_props(html)
    if perseus_props is not None:
        perseus_cards = _gig_cards_from_perseus(perseus_props, max_cards)
        if perseus_cards:
            return SearchParseResult(
                total_result_count=_perseus_total_result_count(perseus_props),
                gig_cards=perseus_cards,
                warnings=warnings,
            )
        warnings.append(
            "perseus-initial-props JSON found but contained zero gigs; falling back to HTML card scan."
        )

    collector = _CardCollector()
    try:
        collector.feed(html)
        collector.close()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"HTML parse error (partial results may be available): {exc}")

    raw_cards = collector.cards[:max_cards]
    if not raw_cards:
        raw_cards = _fallback_cards_from_hrefs(html, max_cards=max_cards)
        if raw_cards:
            warnings.append(
                "No gig cards found via data-testid; used href-based fallback extraction."
            )
        else:
            warnings.append(
                "No gig cards found via data-testid. "
                "Fiverr may have updated its markup — selectors need review."
            )

    gig_cards: list[SearchGigCard] = []
    for position, raw in enumerate(raw_cards, start=1):
        href = _normalise_gig_url(_as_str(raw.get("href")))
        seller = _as_str(raw.get("seller_username")) or _extract_seller_from_url(href or "")
        gig_cards.append(
            SearchGigCard(
                position=position,
                gig_url=href,
                gig_title=_as_str(raw.get("title")),
                seller_username=seller,
                seller_level=_as_str(raw.get("seller_level")),
                review_count_visible=_parse_count(_as_str(raw.get("review_count"))),
                starting_price=_parse_price(_as_str(raw.get("price"))),
                sponsored_flag=bool(raw.get("sponsored", False)),
            )
        )

    total = _parse_count(collector.total_result_count_text)

    return SearchParseResult(
        total_result_count=total,
        gig_cards=gig_cards,
        warnings=warnings,
    )
