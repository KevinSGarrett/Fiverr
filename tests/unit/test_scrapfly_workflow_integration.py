"""Integration-style unit tests for ScrapFly fetcher workflow paths."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.collection.http_fetcher import FetchResult
from src.collection.search_result_parser import SearchGigCard, SearchParseResult
from src.collection.workflows.fiverr_search import run_fiverr_search_collection
from src.collection.workflows.gig_detail import run_gig_detail_collection
from src.collection.workflows.seller_profile import run_seller_profile_collection
from src.models.base import Base
from src.models.gig import Gig

_SEARCH_HTML_TWO_CARDS = """
<html><body>
<div data-testid="total-result-count">234 results</div>
<div data-testid="gig-card-layout">
  <a href="/sellerone/i-will-design-a-logo">link</a>
  <div data-testid="gig-title">I will design a logo</div>
  <div data-testid="seller-name">sellerone</div>
  <div data-testid="starting-price">$25</div>
</div>
<div data-testid="gig-card-layout">
  <a href="/sellertwo/i-will-build-a-website">link</a>
  <div data-testid="gig-title">I will build a website</div>
  <div data-testid="seller-name">sellertwo</div>
  <div data-testid="starting-price">$40</div>
</div>
</body></html>
"""

_GIG_DETAIL_HTML = """
<html><body>
<h1>Pro logo package</h1>
<div data-testid="gig-description">High-converting logo design.</div>
<section data-testid="package-card">
  <div data-testid="package-name">Basic</div>
  <div data-testid="package-price">$55</div>
</section>
<img src="preview.jpg" />
</body></html>
"""

_SELLER_PROFILE_HTML = """
<html><body>
<div data-testid="seller-level">Level 2 Seller</div>
<div data-testid="member-since">Jan 2022</div>
<div data-testid="response-time">1 hour</div>
<div data-testid="seller-review-count">321 reviews</div>
<div data-testid="active-gig-count">12 active gigs</div>
<div data-testid="seller-language">English</div>
</body></html>
"""


def _fetch_result(html: str, *, url: str = "https://www.fiverr.com/test") -> FetchResult:
    return FetchResult(
        url=url,
        html=html,
        status_code=200,
        backend="scrapfly",
        credits_used=5,
        success=True,
    )


def _in_memory_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


@pytest.mark.asyncio
async def test_fiverr_search_with_scrapfly_fetcher_returns_correct_structure() -> None:
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_SEARCH_HTML_TWO_CARDS)))

    result = await run_fiverr_search_collection(
        keyword_id=101,
        keyword_text="logo design",
        niche_id="design",
        depth="standard",
        run_id="run-sf-1",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["gig_cards_collected"] == 2
    assert result["backend"] == "scrapfly"


@pytest.mark.asyncio
async def test_fiverr_search_with_scrapfly_fetcher_writes_search_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_write_search_result(**kwargs: object) -> None:
        captured.update(kwargs)
        return None

    monkeypatch.setattr(
        "src.collection.workflows.fiverr_search.write_search_result",
        _fake_write_search_result,
    )
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_SEARCH_HTML_TWO_CARDS)))

    await run_fiverr_search_collection(
        keyword_id=202,
        keyword_text="landing page",
        niche_id="web",
        depth="standard",
        run_id="run-sf-2",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        dry_run=False,
        fetcher=fetcher,
    )

    assert captured["keyword_id"] == 202


@pytest.mark.asyncio
async def test_fiverr_search_dry_run_ignores_fetcher() -> None:
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_SEARCH_HTML_TWO_CARDS)))

    result = await run_fiverr_search_collection(
        keyword_id=303,
        keyword_text="virtual assistant",
        niche_id="admin",
        depth="standard",
        run_id="run-sf-3",
        db=object(),
        session_manager=None,
        pacing_manager=None,
        dry_run=True,
        fetcher=fetcher,
    )

    assert result["dry_run"] is True
    fetcher.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_gig_detail_with_scrapfly_fetcher_parses_html() -> None:
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_GIG_DETAIL_HTML)))

    result = await run_gig_detail_collection(
        gig_url="https://www.fiverr.com/sellerone/i-will-design-a-logo",
        keyword_id=404,
        niche_id="design",
        depth="standard",
        run_id="run-sf-4",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["collected"] is True
    assert result["title"] is not None
    assert result["backend"] == "scrapfly"


@pytest.mark.asyncio
async def test_gig_detail_dry_run_ignores_fetcher() -> None:
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_GIG_DETAIL_HTML)))

    result = await run_gig_detail_collection(
        gig_url="https://www.fiverr.com/sellerone/i-will-design-a-logo",
        keyword_id=505,
        niche_id="design",
        depth="standard",
        run_id="run-sf-5",
        db=object(),
        session_manager=None,
        pacing_manager=None,
        checkpoint_manager=None,
        dry_run=True,
        fetcher=fetcher,
    )

    assert result["dry_run"] is True
    fetcher.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_seller_profile_with_scrapfly_fetcher_returns_collected() -> None:
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_SELLER_PROFILE_HTML)))

    result = await run_seller_profile_collection(
        seller_username="sellerone",
        niche_id="design",
        run_id="run-sf-6",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["collected"] is True
    assert result["backend"] == "scrapfly"
    assert result["seller_level"] == "LEVEL_2"
    assert result["member_since"] == "2022-01"
    assert result["total_reviews"] == 321
    assert result["total_gigs"] == 12


@pytest.mark.asyncio
async def test_seller_profile_fetcher_maps_parser_fields_for_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_write_seller_profile(**kwargs: object) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(
        "src.collection.workflows.seller_profile.write_seller_profile",
        _fake_write_seller_profile,
    )
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_SELLER_PROFILE_HTML)))
    db = _in_memory_session()

    result = await run_seller_profile_collection(
        seller_username="sellerpersist",
        niche_id="design",
        run_id="run-sf-6b",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert captured["seller_level"] == "LEVEL_2"
    assert captured["member_since"] == "2022-01"
    assert captured["total_reviews"] == 321
    assert captured["total_gigs"] == 12
    assert result["total_reviews"] == 321
    assert result["total_gigs"] == 12


@pytest.mark.asyncio
async def test_seller_profile_dry_run_ignores_fetcher() -> None:
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_SELLER_PROFILE_HTML)))

    result = await run_seller_profile_collection(
        seller_username="sellertwo",
        niche_id="design",
        run_id="run-sf-7",
        db=object(),
        session_manager=None,
        pacing_manager=None,
        checkpoint_manager=None,
        dry_run=True,
        fetcher=fetcher,
    )

    assert result["dry_run"] is True
    fetcher.fetch.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_parser_used_when_fetcher_provided(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def _fake_parse(html: str) -> SearchParseResult:
        calls.append(html)
        return SearchParseResult(
            total_result_count=1,
            gig_cards=[
                SearchGigCard(
                    position=1,
                    gig_url="https://www.fiverr.com/sellerx/i-will-do-work",
                    gig_title="I will do work",
                    seller_username="sellerx",
                    seller_level=None,
                    review_count_visible=12,
                    starting_price=20.0,
                    sponsored_flag=False,
                )
            ],
            warnings=[],
        )

    monkeypatch.setattr(
        "src.collection.search_result_parser.parse_search_results_from_html",
        _fake_parse,
    )
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result("<html>payload</html>")))

    result = await run_fiverr_search_collection(
        keyword_id=808,
        keyword_text="automation",
        niche_id="ops",
        depth="standard",
        run_id="run-sf-8",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        dry_run=False,
        fetcher=fetcher,
    )

    assert calls == ["<html>payload</html>"]
    assert result["gig_cards_collected"] == 1


@pytest.mark.asyncio
async def test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields() -> None:
    db = _in_memory_session()
    gig_url = "https://www.fiverr.com/sellerone/i-will-design-a-logo"
    db.add(
        Gig(
            gig_url=gig_url,
            seller_username="sellerone",
            tags=["legacy-tag"],
            faq_text="Existing FAQ",
            video_present=True,
        )
    )
    db.commit()

    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(_GIG_DETAIL_HTML)))

    result = await run_gig_detail_collection(
        gig_url=gig_url,
        keyword_id=111,
        niche_id="design",
        depth="keyword_only",
        run_id="run-sf-8b",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    refreshed = db.query(Gig).filter(Gig.gig_url == gig_url).one()
    assert refreshed.tags == ["legacy-tag"]
    assert refreshed.faq_text == "Existing FAQ"
    assert refreshed.video_present is True
    assert result["tags_count"] is None
    assert result["has_video"] is None


@pytest.mark.asyncio
async def test_fetcher_none_falls_through_to_playwright_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    page = AsyncMock()
    page.goto = AsyncMock()
    page.query_selector = AsyncMock(return_value=None)
    page.query_selector_all = AsyncMock(return_value=[])

    session_manager = AsyncMock()
    session_manager.new_page = AsyncMock(return_value=page)
    session_manager.close_page = AsyncMock()

    pacing_manager = AsyncMock()
    pacing_manager.wait = AsyncMock()

    monkeypatch.setattr(
        "src.collection.workflows.fiverr_search.write_search_result",
        lambda **_kwargs: None,
    )
    monkeypatch.setattr(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs",
        lambda **_kwargs: 0,
    )

    await run_fiverr_search_collection(
        keyword_id=909,
        keyword_text="seo",
        niche_id="marketing",
        depth="standard",
        run_id="run-sf-9",
        db=object(),
        session_manager=session_manager,
        pacing_manager=pacing_manager,
        dry_run=False,
        fetcher=None,
    )

    session_manager.new_page.assert_awaited_once()
