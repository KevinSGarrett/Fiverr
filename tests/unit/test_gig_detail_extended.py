"""Extended gig detail parser tests for uncovered edge branches."""

from __future__ import annotations

import pytest
from src.collection.gig_detail import (
    _extract_delivery_days,
    _extract_json_ld_objects,
    _extract_next_data_payload,
    _extract_packages_from_json,
    _extract_price_text_from_payload,
    _extract_text,
    _normalize_price_to_cents,
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


def test_gig_detail_invalid_price_and_delivery_payload_edges() -> None:
    assert _extract_delivery_days("soon") is None


def test_gig_detail_normalize_price_handles_invalid_decimal(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.collection import gig_detail as gig_detail_module

    def _raise_invalid_operation(_: str):
        raise gig_detail_module.InvalidOperation()

    monkeypatch.setattr(gig_detail_module, "Decimal", _raise_invalid_operation)
    assert _normalize_price_to_cents("$12") is None


def test_gig_detail_json_ld_and_next_data_malformed_payloads() -> None:
    html = """
    <script type="application/ld+json"></script>
    <script type="application/ld+json">{"@graph":[{"name":"ok"}, 2, "bad"]}</script>
    <script id="__NEXT_DATA__">{"not":"json"</script>
    """
    objs = _extract_json_ld_objects(html)
    assert any(obj.get("name") == "ok" for obj in objs)
    assert _extract_next_data_payload(html) is None


def test_gig_detail_nested_price_payload_filters_invalid_candidates() -> None:
    payload = {
        "price": [{"value": None}, {"price": object()}, {"amount": "88"}],
        "currency": "USD",
    }
    assert _extract_price_text_from_payload(payload) == "$88"


def test_gig_detail_parse_from_next_data_uses_username_and_rating_keys() -> None:
    html = """
    <html><body>
      <script id="__NEXT_DATA__">
      {
        "props": {
          "pageProps": {
            "gigTitle": "From next data",
            "username": "next-seller",
            "gigRating": "4.8",
            "reviewCount": "23",
            "packages": [{"name":"Basic","price":{"amount":15,"currency":"USD"}}]
          }
        }
      }
      </script>
    </body></html>
    """
    result = parse_gig_detail_from_html(html)
    assert result.seller_name == "next-seller"
    assert result.rating == 4.8
