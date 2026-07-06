"""Rank-3 (real-data fix): parse_search_results_from_html must extract gig data from
Fiverr's embedded `perseus-initial-props` JSON, not just the removed `data-testid`
markup.

Before this fix, every field on a real 2026 Fiverr search page (title, price, rating,
review count) came back None — the parser fell all the way through to the href-only
fallback because Fiverr no longer renders the data-testid hooks _CardCollector scans
for. This is validated against a real ScrapFly-fetched search page fixture, not a
hand-built mock, per the project's real-data-over-mocks mandate.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from src.collection.search_result_parser import (
    SearchGigCard,
    parse_search_results_from_html,
)

_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "live" / "fiverr_search_ai_automation.html"


@pytest.fixture(scope="module")
def real_search_html() -> str:
    return _FIXTURE_PATH.read_text(encoding="utf-8")


class TestPerseusRealFixture:
    """End-to-end validation against a real, ScrapFly-fetched Fiverr search page."""

    def test_extracts_all_gigs_with_no_warnings(self, real_search_html: str) -> None:
        result = parse_search_results_from_html(real_search_html, max_cards=48)
        assert result.warnings == []
        assert len(result.gig_cards) == 48

    def test_total_result_count_from_pagination(self, real_search_html: str) -> None:
        result = parse_search_results_from_html(real_search_html, max_cards=48)
        assert result.total_result_count == 23397

    def test_first_card_fields_are_fully_populated(self, real_search_html: str) -> None:
        card = parse_search_results_from_html(real_search_html, max_cards=48).gig_cards[0]
        assert card == SearchGigCard(
            position=1,
            gig_url=(
                "https://www.fiverr.com/shahzadali08/"
                "provide-office-365-solution-custom-power-apps-automate-bi-and-azure-functions"
            ),
            gig_title="build ai automation workflows using n8n, zapier, claude hermes",
            seller_username="shahzadali08",
            seller_level="top_rated_seller",
            review_count_visible=116,
            starting_price=4.95,
            sponsored_flag=True,
        )

    def test_no_field_is_none_across_any_real_card(self, real_search_html: str) -> None:
        """The bug this fixes: every field degraded to None on real Fiverr HTML."""
        cards = parse_search_results_from_html(real_search_html, max_cards=48).gig_cards
        assert cards
        for card in cards:
            assert card.gig_url is not None
            assert card.gig_title is not None
            assert card.seller_username is not None
            assert card.starting_price is not None

    def test_sponsored_flag_matches_promoted_gigs_count(self, real_search_html: str) -> None:
        cards = parse_search_results_from_html(real_search_html, max_cards=48).gig_cards
        assert sum(1 for c in cards if c.sponsored_flag) == 17

    def test_default_max_cards_caps_at_20(self, real_search_html: str) -> None:
        result = parse_search_results_from_html(real_search_html)
        assert len(result.gig_cards) == 20


class TestLegacyHtmlFallbackStillWorks:
    """Pages without perseus-initial-props (or with a malformed/empty blob) must still
    fall back to the pre-existing data-testid / href scan — no regression for whatever
    page shapes that path already handled."""

    _LEGACY_HTML = """
    <html><body>
    <div data-testid="total-result-count">1,234 results</div>
    <div data-testid="gig-card-layout">
      <a href="/someuser/some-gig-slug?source=gig_cards&amp;pckg_id=1">
        <div data-testid="gig-title">Sample Gig Title</div>
        <div data-testid="seller-name">someuser</div>
        <div data-testid="seller-level">Level 2</div>
        <div data-testid="review-count">42 reviews</div>
        <div data-testid="starting-price">$25</div>
      </a>
    </div>
    </body></html>
    """

    def test_no_perseus_tag_uses_legacy_card_collector(self) -> None:
        result = parse_search_results_from_html(self._LEGACY_HTML)
        assert result.total_result_count == 1234
        assert len(result.gig_cards) == 1
        card = result.gig_cards[0]
        assert card.gig_title == "Sample Gig Title"
        assert card.starting_price == 25.0

    def test_malformed_perseus_json_falls_back_without_raising(self) -> None:
        html = (
            '<script type="application/json" id="perseus-initial-props">{not valid json}</script>'
            + self._LEGACY_HTML
        )
        result = parse_search_results_from_html(html)
        assert len(result.gig_cards) == 1
        assert result.gig_cards[0].gig_title == "Sample Gig Title"

    def test_perseus_present_but_empty_gigs_falls_back_with_warning(self) -> None:
        html = (
            '<script type="application/json" id="perseus-initial-props">'
            '{"listings":[{"gigs":[]}],"appData":{"pagination":{"total":0}}}'
            "</script>" + self._LEGACY_HTML
        )
        result = parse_search_results_from_html(html)
        assert len(result.gig_cards) == 1
        assert any("zero gigs" in w for w in result.warnings)
