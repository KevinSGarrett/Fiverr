"""Extended gig detail parser tests for uncovered edge branches."""

from __future__ import annotations

from src.collection.gig_detail import (
    _extract_packages_from_json,
    _extract_text,
    parse_gig_detail_from_html,
)


def test_gig_detail_extract_text_recovers_on_unclosed_target_tag() -> None:
    html = "<div data-testid='gig-title'>Unclosed title"
    assert _extract_text(html, "gig-title") == "Unclosed title"


def test_gig_detail_extract_packages_ignores_non_dict_entries() -> None:
    packages = _extract_packages_from_json([None, "invalid", {"name": "Basic", "price": {"amount": 55, "currency": "USD"}}])
    assert len(packages) == 1
    assert packages[0].price_cents == 5500


def test_gig_detail_parse_uses_jsonld_image_count_when_no_img_tags() -> None:
    html = """
    <html><body>
      <script type="application/ld+json">
        {"@type":"Product","name":"Image Count Gig","image":["a.png","b.png","c.png"]}
      </script>
    </body></html>
    """
    result = parse_gig_detail_from_html(html)
    assert result.image_count == 3


def test_gig_detail_parse_warns_when_images_missing_everywhere() -> None:
    html = "<html><body><h1>No image gig</h1><div data-testid='seller-name'>seller</div></body></html>"
    result = parse_gig_detail_from_html(html)
    assert any("No images were detected" in warning for warning in result.warnings)
