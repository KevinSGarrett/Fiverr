"""Integration-style wiring tests for R1 search strictness workflow behavior."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any
from unittest.mock import AsyncMock

import pytest
from src.collection.search_url_builder import SearchStrictness
from src.collection.workflows import fiverr_search as workflow


def _run(coro: Coroutine[Any, Any, dict[str, Any]]) -> dict[str, Any]:
    return asyncio.run(coro)


def test_fiverr_search_fetcher_calls_builder_and_fallback_with_niche(monkeypatch: pytest.MonkeyPatch) -> None:
    build_calls: list[tuple[str, str, SearchStrictness]] = []
    freshness_calls = {"count": 0}
    fallback_calls: list[tuple[str, str, dict[str, int]]] = []

    cards_by_strictness = {
        SearchStrictness.SUBCATEGORY: [
            {
                "position": 1,
                "gig_url": "https://www.fiverr.com/gig/subcategory",
                "gig_title": "Subcategory Result",
                "seller_username": "seller_sub",
                "seller_level": "Level 2",
                "review_count_visible": 12,
                "starting_price": 45.0,
                "sponsored_flag": False,
            }
        ],
        SearchStrictness.CATEGORY: [
            {
                "position": 1,
                "gig_url": "https://www.fiverr.com/gig/category",
                "gig_title": "Category Result",
                "seller_username": "seller_cat",
                "seller_level": "Top Rated",
                "review_count_visible": 55,
                "starting_price": 60.0,
                "sponsored_flag": False,
            }
        ],
        SearchStrictness.NONE: [],
    }
    strictness_for_url: dict[str, SearchStrictness] = {}
    written_rows: list[dict[str, object]] = []

    def fake_freshness() -> bool:
        freshness_calls["count"] += 1
        return False

    def fake_build_search_url(keyword: str, niche_id: str | None, strictness: SearchStrictness, page: int = 1) -> str:
        assert keyword == "python automation"
        assert page == 1
        build_calls.append((keyword, niche_id or "", strictness))
        url = f"https://example.test/search/{strictness.value.lower()}"
        strictness_for_url[url] = strictness
        return url

    async def fake_collect(_url: str, _fetcher: object) -> tuple[list[dict[str, Any]], int, str, list[str], bool]:
        strictness = strictness_for_url[_url]
        cards = cards_by_strictness[strictness]
        return cards, len(cards), "mock-fetcher", [], True

    def fake_search_with_fallback(
        keyword: str,
        niche_id: str | None,
        config: dict[str, int] | None,
        _collect_fn: Any,
    ) -> tuple[list[dict[str, object]], SearchStrictness]:
        fallback_calls.append((keyword, niche_id or "", config or {}))
        return cards_by_strictness[SearchStrictness.CATEGORY], SearchStrictness.CATEGORY

    def fake_write_search_result(**kwargs: object) -> None:
        written_rows.append(kwargs)

    monkeypatch.setattr(workflow, "check_category_mapping_freshness", fake_freshness)
    monkeypatch.setattr(workflow, "build_search_url", fake_build_search_url)
    monkeypatch.setattr(workflow, "_collect_search_page_via_fetcher", fake_collect)
    monkeypatch.setattr(workflow, "search_with_fallback", fake_search_with_fallback)
    monkeypatch.setattr(workflow, "write_search_result", fake_write_search_result)
    monkeypatch.setattr(workflow, "_queue_gig_detail_jobs", lambda **_kwargs: 0)

    fake_fetcher = AsyncMock()
    result = _run(
        workflow.run_fiverr_search_collection(
            keyword_id=11,
            keyword_text="python automation",
            niche_id="python_automation",
            depth="standard",
            run_id="run-r1-fetcher",
            db=object(),
            session_manager=None,
            pacing_manager=None,
            dry_run=False,
            fetcher=fake_fetcher,
        )
    )

    assert freshness_calls["count"] == 1
    assert fallback_calls == [("python automation", "python_automation", {"min_result_threshold": 5})]
    assert build_calls
    assert all(call[1] == "python_automation" for call in build_calls)
    assert result["search_strictness_used"] == SearchStrictness.CATEGORY.value
    assert written_rows[0]["search_strictness_used"] == SearchStrictness.CATEGORY.value


def test_fiverr_search_fetcher_preserves_gig_card_shape_for_constrained_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_cards = [
        {
            "position": 1,
            "gig_url": "https://www.fiverr.com/gig/r1-constrained",
            "gig_title": "Constrained Gig",
            "seller_username": "seller_r1",
            "seller_level": "Level 1",
            "review_count_visible": 8,
            "starting_price": 35.0,
            "sponsored_flag": False,
        }
    ]
    strictness_for_url: dict[str, SearchStrictness] = {}
    written_rows: list[dict[str, object]] = []

    monkeypatch.setattr(workflow, "check_category_mapping_freshness", lambda: False)

    def fake_build_search_url(keyword: str, niche_id: str | None, strictness: SearchStrictness, page: int = 1) -> str:
        assert keyword == "mcp automation"
        assert niche_id == "mcp_ai_agent"
        assert page == 1
        url = f"https://example.test/{strictness.value.lower()}"
        strictness_for_url[url] = strictness
        return url

    async def fake_collect(_url: str, _fetcher: object) -> tuple[list[dict[str, Any]], int, str, list[str], bool]:
        strictness = strictness_for_url[_url]
        if strictness == SearchStrictness.SUBCATEGORY:
            return expected_cards, 24, "mock-fetcher", [], True
        return [], 0, "mock-fetcher", [], True

    monkeypatch.setattr(workflow, "build_search_url", fake_build_search_url)
    monkeypatch.setattr(workflow, "_collect_search_page_via_fetcher", fake_collect)
    monkeypatch.setattr(
        workflow,
        "search_with_fallback",
        lambda _k, _n, _c, _fn: (expected_cards, SearchStrictness.SUBCATEGORY),
    )
    monkeypatch.setattr(workflow, "_queue_gig_detail_jobs", lambda **_kwargs: 0)
    monkeypatch.setattr(workflow, "write_search_result", lambda **kwargs: written_rows.append(kwargs))

    result = _run(
        workflow.run_fiverr_search_collection(
            keyword_id=22,
            keyword_text="mcp automation",
            niche_id="mcp_ai_agent",
            depth="standard",
            run_id="run-r1-preserve",
            db=object(),
            session_manager=None,
            pacing_manager=None,
            dry_run=False,
            fetcher=AsyncMock(),
        )
    )

    assert result["gig_cards_collected"] == 1
    assert result["search_strictness_used"] == SearchStrictness.SUBCATEGORY.value
    assert written_rows[0]["gig_cards"] == expected_cards
    assert written_rows[0]["search_strictness_used"] == SearchStrictness.SUBCATEGORY.value

