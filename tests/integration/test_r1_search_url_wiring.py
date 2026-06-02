"""Integration tests for R1 search URL and category filter wiring."""
from __future__ import annotations

from src.collection.search_url_builder import NICHE_CATEGORY_MAP, SearchStrictness, build_search_url

PRODUCTION_NICHES = list(NICHE_CATEGORY_MAP.keys())


def test_all_production_niches_get_category_filter() -> None:
    for niche_id in PRODUCTION_NICHES:
        mapping = NICHE_CATEGORY_MAP[niche_id]
        url = build_search_url(keyword="test service", niche_id=niche_id, strictness=SearchStrictness.SUBCATEGORY)
        assert url.startswith("https://www.fiverr.com/search/gigs")
        assert f"category_id={mapping.fiverr_category_id}" in url
        assert "sub_category=" in url
        assert "query=test%20service" in url


def test_subcategory_strictness_produces_subcategory_param() -> None:
    url = build_search_url(
        keyword="python automation",
        niche_id="python_automation",
        strictness=SearchStrictness.SUBCATEGORY,
    )
    assert "query=python%20automation" in url
    assert "category_id=6" in url
    assert "sub_category=desktop_applications" in url
    assert "offset=0" in url


def test_none_strictness_url_does_not_include_category_constraint() -> None:
    url = build_search_url(
        keyword="generic search",
        niche_id="python_automation",
        strictness=SearchStrictness.NONE,
    )
    assert url.startswith("https://www.fiverr.com/search/gigs")
    assert "query=generic%20search" in url
    assert "category_id=" not in url
    assert "sub_category=" not in url
