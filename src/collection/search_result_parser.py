"""HTML-based parser for Fiverr search result pages.

Used when ScrapFly (or PlaywrightFetcher) returns raw HTML and we need to
extract gig cards without Playwright selector calls.

Mirrors the field set extracted by _extract_gig_card() in workflows/fiverr_search.py
so downstream DB writes are identical regardless of which backend fetched the page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

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


def _as_str(value: str | bool | None) -> str | None:
    return value if isinstance(value, str) else None


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

    collector = _CardCollector()
    try:
        collector.feed(html)
        collector.close()
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"HTML parse error (partial results may be available): {exc}")

    raw_cards = collector.cards[:max_cards]
    if not raw_cards:
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
