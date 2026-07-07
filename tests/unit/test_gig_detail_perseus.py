"""Rank-5 (gap-audit-2 P0, SCRUM-1093): parse_gig_detail_from_html must extract from
Fiverr's embedded `perseus-initial-props` JSON, not just the JSON-LD/__NEXT_DATA__/
data-testid fallback chain.

Before this fix, real 2026 Fiverr gig-detail pages produced materially WRONG values via
the legacy chain: seller_name defaulted to the literal string "Fiverr" (not the actual
seller), description was generic schema.org boilerplate (not the real gig description),
image_count counted every <img> tag on the 1.9MB page (116, when the gig actually had 1
real portfolio image), and tags/faq_text/video_present were hardcoded to None entirely by
the calling workflow. This is validated against two real ScrapFly-fetched gig pages, not
hand-built mocks, per the project's real-data-over-mocks mandate.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from src.collection.gig_detail import parse_gig_detail_from_html

_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "live"


@pytest.fixture(scope="module")
def gig1_html() -> str:
    return (_FIXTURES_DIR / "fiverr_gig_detail_real.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def gig2_html() -> str:
    return (_FIXTURES_DIR / "fiverr_gig_detail_real_2.html").read_text(encoding="utf-8")


class TestPerseusRealFixtureGig1:
    """Gig with an empty FAQ and no video — validates the "nothing to report" paths are
    accurate (not false positives from regex/tag-count fallbacks)."""

    def test_core_identity_fields(self, gig1_html: str) -> None:
        result = parse_gig_detail_from_html(gig1_html)
        assert result.title == "build ai automation workflows using n8n, zapier, claude hermes"
        assert result.seller_name == "shahzadali08"  # was "Fiverr" via legacy JSON-LD fallback
        assert result.metadata["mode"] == "perseus"

    def test_description_is_real_content_not_boilerplate(self, gig1_html: str) -> None:
        result = parse_gig_detail_from_html(gig1_html)
        assert result.description is not None
        assert "Fiverr freelancer will provide" not in result.description  # old schema.org boilerplate
        assert "Automate Your Business" in result.description

    def test_empty_faq_is_reported_accurately(self, gig1_html: str) -> None:
        """The bug this fixes: legacy has_faq used a bare regex for the word "faq"
        anywhere in the page, which false-positived on this exact gig."""
        result = parse_gig_detail_from_html(gig1_html)
        assert result.has_faq is False
        assert result.faq_text is None

    def test_tags_extracted(self, gig1_html: str) -> None:
        result = parse_gig_detail_from_html(gig1_html)
        assert result.tags == [
            "business automation",
            "n8n automation",
            "workflow automation",
            "ai automation",
            "ai agent",
        ]

    def test_no_video_present(self, gig1_html: str) -> None:
        result = parse_gig_detail_from_html(gig1_html)
        assert result.video_present is False

    def test_gig_specific_rating_not_seller_aggregate(self, gig1_html: str) -> None:
        """This seller has 116 reviews in aggregate across all their gigs, but this
        specific gig has only 5 - rating/review_count must reflect the gig, not the
        seller (the same seller-vs-gig mix-up class of bug caught on PR #160)."""
        result = parse_gig_detail_from_html(gig1_html)
        assert result.rating == 5.0
        assert result.review_count == 5

    def test_image_count_matches_real_gallery_not_every_img_tag(self, gig1_html: str) -> None:
        """The bug this fixes: legacy image_count = count of every <img> tag anywhere on
        the 1.9MB page (116), not the gig's actual gallery (1 real image)."""
        result = parse_gig_detail_from_html(gig1_html)
        assert result.image_count == 1

    def test_all_three_packages_with_delivery_days(self, gig1_html: str) -> None:
        """The bug this fixes: legacy extraction found only 1 of 3 real packages and
        never populated delivery_days at all."""
        result = parse_gig_detail_from_html(gig1_html)
        assert len(result.packages) == 3
        basic, standard, premium = result.packages
        assert (basic.name, basic.price_cents, basic.delivery_days) == ("Basic", 49500, 3)
        assert (standard.name, standard.price_cents, standard.delivery_days) == ("Standard", 99500, 4)
        assert (premium.name, premium.price_cents, premium.delivery_days) == ("Premium", 199500, 5)


class TestPerseusRealFixtureGig2:
    """Gig with a real, non-empty FAQ — validates the Q&A extraction shape."""

    def test_core_identity_fields(self, gig2_html: str) -> None:
        result = parse_gig_detail_from_html(gig2_html)
        assert result.title == "do n8n ai agent automation workflow, custom ai agents n8n workflow"
        assert result.seller_name == "wp_monkey"

    def test_faq_extracted_with_real_qa_text(self, gig2_html: str) -> None:
        result = parse_gig_detail_from_html(gig2_html)
        assert result.has_faq is True
        assert result.faq_text is not None
        assert "Q: Do you provide any support once the project is done?" in result.faq_text
        assert "A: Yes, every project comes with basic support" in result.faq_text
        # 5 real Q&A pairs on this gig.
        assert result.faq_text.count("Q: ") == 5

    def test_review_count_is_larger_than_gig1(self, gig2_html: str) -> None:
        result = parse_gig_detail_from_html(gig2_html)
        assert result.rating == 5.0
        assert result.review_count == 466

    def test_three_packages_with_distinct_delivery_days(self, gig2_html: str) -> None:
        result = parse_gig_detail_from_html(gig2_html)
        assert len(result.packages) == 3
        delivery_days = [p.delivery_days for p in result.packages]
        assert delivery_days == [3, 7, 14]


class TestLegacyFallbackStillWorks:
    """Pages without perseus-initial-props (or a malformed blob) must still fall back to
    the pre-existing JSON-LD / __NEXT_DATA__ / data-testid scan — no regression."""

    def test_malformed_perseus_json_falls_back_without_raising(self) -> None:
        html = (
            '<script type="application/json" id="perseus-initial-props">{not valid json}</script>'
            '<html><body><h1>Some Gig Title</h1></body></html>'
        )
        result = parse_gig_detail_from_html(html)
        assert result.title == "Some Gig Title"
        assert result.metadata.get("mode") != "perseus"

    def test_perseus_present_but_no_title_falls_back(self) -> None:
        html = (
            '<script type="application/json" id="perseus-initial-props">{"general":{}}</script>'
            '<html><body><h1>Fallback Title</h1></body></html>'
        )
        result = parse_gig_detail_from_html(html)
        assert result.title == "Fallback Title"
        assert result.metadata.get("mode") != "perseus"
