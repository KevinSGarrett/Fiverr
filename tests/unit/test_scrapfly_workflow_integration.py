"""Integration-style unit tests for ScrapFly fetcher workflow paths."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
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
async def test_seller_profile_live_markup_drift_regression_spec() -> None:
    # Regression spec for the observed live failure mode where seller rows are created
    # but key profile fields remain null. This test documents expected behavior once
    # parser support for alternate live testids is implemented.
    live_drift_html = """
    <html><body>
    <div data-testid="seller-overview-level">Level 2 Seller</div>
    <div data-testid="seller-member-since">Jan 2022</div>
    <div data-testid="seller-reviews-count">321 reviews</div>
    <div data-testid="seller-active-gigs">12 active gigs</div>
    </body></html>
    """
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(live_drift_html)))

    result = await run_seller_profile_collection(
        seller_username="sellerdrift",
        niche_id="design",
        run_id="run-sf-6c",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["seller_level"] == "LEVEL_2"
    assert result["member_since"] == "2022-01"
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
async def test_gig_detail_perseus_recrawl_clears_stale_faq_and_video() -> None:
    """Codex finding on PR #162: unlike the legacy fallback (above), a perseus-JSON
    recrawl is AUTHORITATIVE - if the real page now reports no FAQ/video, that must
    overwrite stale faq_text/video_present left over from a previous crawl, not be
    silently skipped by the "don't clobber unknowns" guard."""
    real_html = (Path(__file__).resolve().parents[1] / "fixtures" / "live" / "fiverr_gig_detail_real.html").read_text(
        encoding="utf-8"
    )
    db = _in_memory_session()
    gig_url = "https://www.fiverr.com/shahzadali08/provide-office-365-solution-custom-power-apps-automate-bi-and-azure-functions"
    db.add(
        Gig(
            gig_url=gig_url,
            seller_username="shahzadali08",
            faq_text="Stale FAQ from a previous crawl",
            video_present=True,
        )
    )
    db.commit()

    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(real_html, url=gig_url)))

    await run_gig_detail_collection(
        gig_url=gig_url,
        keyword_id=333,
        niche_id="automation",
        depth="keyword_only",
        run_id="run-sf-real-clear",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    refreshed = db.query(Gig).filter(Gig.gig_url == gig_url).one()
    assert refreshed.faq_text is None  # real page has no FAQ - stale text must be cleared
    assert refreshed.video_present is False  # real page has no video - stale True must be cleared


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


@pytest.mark.asyncio
async def test_scrapfly_path_persists_real_tags_faq_and_video_from_perseus_json() -> None:
    """Rank-5 (gap-audit-2 P0, SCRUM-1093): the ScrapFly path used to hardcode
    tags/faq_text/video_present to None regardless of what the fetched page contained.
    With a real ScrapFly-fetched gig page (perseus-initial-props present), these must
    now flow through to the persisted Gig row."""
    real_html = (
        Path(__file__).resolve().parents[1] / "fixtures" / "live" / "fiverr_gig_detail_real_2.html"
    ).read_text(encoding="utf-8")
    db = _in_memory_session()
    gig_url = "https://www.fiverr.com/wp_monkey/flutter-app-development-for-android-and-ios-mobile-app-figma-to-flutter"
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_fetch_result(real_html, url=gig_url)))

    await run_gig_detail_collection(
        gig_url=gig_url,
        keyword_id=222,
        niche_id="automation",
        depth="keyword_only",
        run_id="run-sf-real-detail",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    gig = db.query(Gig).filter(Gig.gig_url == gig_url).one()
    assert gig.tags == ["n8n workflow", "n8n automation", "workflow automation", "n8n ai agent", "ai agent"]
    assert gig.faq_text is not None
    assert "Q: Do you provide any support once the project is done?" in gig.faq_text
    assert gig.video_present is False
    assert gig.portfolio_count == 1  # not the old wildly-inflated <img>-tag count
    # Codex finding: delivery_days must survive persistence, not just parsing.
    assert [p["delivery_days"] for p in gig.packages] == [3, 7, 14]
    assert [p["price_cents"] for p in gig.packages] == [8000, 45000, 95000]


# ---------------------------------------------------------------------------
# Rank-13 (gap-audit-2 P1, SCRUM-1096): a blocked/failed fetch (success=False or
# empty HTML) must never be parsed and persisted as real data. Previously all
# three fetcher workflows treated a failed fetch identically to a good one.
# ---------------------------------------------------------------------------


def _failed_fetch_result(url: str = "https://www.fiverr.com/test") -> FetchResult:
    return FetchResult(
        url=url,
        html="<html><body>Access Denied</body></html>",
        status_code=403,
        backend="scrapfly",
        credits_used=1,
        success=False,
    )


@pytest.mark.asyncio
async def test_gig_detail_failed_fetch_persists_nothing() -> None:
    db = _in_memory_session()
    gig_url = "https://www.fiverr.com/sellerone/i-will-design-a-logo"
    db.add(
        Gig(
            gig_url=gig_url,
            seller_username="sellerone",
            title="Existing real title",
            faq_text="Existing FAQ",
        )
    )
    db.commit()

    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_failed_fetch_result(gig_url)))
    result = await run_gig_detail_collection(
        gig_url=gig_url,
        keyword_id=444,
        niche_id="design",
        depth="standard",
        run_id="run-sf-blocked",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["collected"] is False
    assert result["seller_queued"] is False
    assert "Fetch failed" in result["error"]
    # Existing real data untouched - the blocked page was never parsed or persisted.
    refreshed = db.query(Gig).filter(Gig.gig_url == gig_url).one()
    assert refreshed.title == "Existing real title"
    assert refreshed.faq_text == "Existing FAQ"
    assert refreshed.detail_collected is not True


@pytest.mark.asyncio
async def test_seller_profile_failed_fetch_persists_nothing() -> None:
    from src.models.seller import Seller

    db = _in_memory_session()
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_failed_fetch_result()))
    result = await run_seller_profile_collection(
        seller_username="blocked_seller",
        niche_id="design",
        run_id="run-sf-blocked-seller",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["collected"] is False
    assert "Fetch failed" in result["error"]
    assert db.query(Seller).count() == 0


@pytest.mark.asyncio
async def test_fiverr_search_failed_fetch_returns_no_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def _capture_write(**kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr("src.collection.workflows.fiverr_search.write_search_result", _capture_write)
    monkeypatch.setattr(
        "src.collection.workflows.fiverr_search._queue_gig_detail_jobs", lambda **_kwargs: 0
    )
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=_failed_fetch_result()))

    result = await run_fiverr_search_collection(
        keyword_id=555,
        keyword_text="blocked query",
        niche_id="design",
        depth="standard",
        run_id="run-sf-blocked-search",
        db=object(),
        session_manager=object(),
        pacing_manager=object(),
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["gig_cards_collected"] == 0
    assert result["fetch_failed"] is True
    assert result["pages_collected"] == 0
    assert any("Fetch failed" in warning for warning in result["parse_warnings"])
    # Nothing persisted: an all-fetches-failed keyword must NOT be written as an
    # empty (ghost-market-looking) search result (Codex review, PR #170).
    assert captured == {}


@pytest.mark.asyncio
async def test_gig_detail_http200_block_page_persists_nothing() -> None:
    """Codex finding on PR #170: block pages can return HTTP 200 with real HTML
    ("Access Denied"), passing the transport-level success check but parsing to an
    empty shell - the content check must reject them before persisting."""
    db = _in_memory_session()
    gig_url = "https://www.fiverr.com/sellerone/i-will-design-a-logo"
    db.add(Gig(gig_url=gig_url, seller_username="sellerone", title="Existing real title"))
    db.commit()

    block_page = FetchResult(
        url=gig_url,
        html="<html><body><h1>Access Denied</h1><p>You do not have permission.</p></body></html>",
        status_code=200,
        backend="scrapfly",
        credits_used=1,
        success=True,  # transport-level success - the trap this guard closes
    )
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=block_page))
    result = await run_gig_detail_collection(
        gig_url=gig_url,
        keyword_id=666,
        niche_id="design",
        depth="standard",
        run_id="run-sf-block200",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["collected"] is False
    assert "does not look like a gig detail page" in result["error"]
    refreshed = db.query(Gig).filter(Gig.gig_url == gig_url).one()
    assert refreshed.title == "Existing real title"
    assert refreshed.detail_collected is not True


@pytest.mark.asyncio
async def test_seller_profile_http200_block_page_persists_nothing() -> None:
    from src.models.seller import Seller

    db = _in_memory_session()
    block_page = FetchResult(
        url="https://www.fiverr.com/blocked",
        html="<html><body><h1>Access Denied</h1></body></html>",
        status_code=200,
        backend="scrapfly",
        credits_used=1,
        success=True,
    )
    fetcher = SimpleNamespace(fetch=AsyncMock(return_value=block_page))
    result = await run_seller_profile_collection(
        seller_username="blocked_seller_200",
        niche_id="design",
        run_id="run-sf-block200-seller",
        db=db,
        session_manager=object(),
        pacing_manager=object(),
        checkpoint_manager=None,
        dry_run=False,
        fetcher=fetcher,
    )

    assert result["collected"] is False
    assert "does not look like a seller profile" in result["error"]
    assert db.query(Seller).count() == 0
