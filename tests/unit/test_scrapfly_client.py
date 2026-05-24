"""Tests for ScrapFly client, PageFetcher adapters, and search result parser."""
from __future__ import annotations

import builtins

import pytest
from src.collection.http_fetcher import (
    FetchResult,
    PageFetcher,
    PlaywrightFetcher,
    ScrapFlyFetcher,
    build_fetcher,
)
from src.collection.scrapfly_client import (
    ScrapFlyBlockedError,
    ScrapFlyClient,
    ScrapFlyConfig,
    ScrapFlyMissingKeyError,
    ScrapFlyRateLimitError,
    ScrapFlyResult,
)
from src.collection.search_result_parser import (
    SearchParseResult,
    parse_search_results_from_html,
)

# ─────────────────────────────────────────────
# ScrapFlyConfig
# ─────────────────────────────────────────────

class TestScrapFlyConfig:
    def test_defaults(self):
        cfg = ScrapFlyConfig()
        assert cfg.asp is True
        assert cfg.render_js is True
        assert cfg.country == "US"
        assert cfg.max_retries == 3
        assert cfg.cost_budget_credits is None

    def test_redact_never_exposes_key_value(self):
        cfg = ScrapFlyConfig(api_key_env_var="MY_SECRET_KEY")
        redacted = cfg.redact()
        assert redacted["api_key_env_var"] == "MY_SECRET_KEY"
        # The actual value is never in the dict
        assert "scp-live" not in str(redacted)

    def test_custom_values(self):
        cfg = ScrapFlyConfig(
            asp=False,
            render_js=False,
            country="GB",
            max_retries=5,
            cost_budget_credits=1000,
        )
        assert cfg.asp is False
        assert cfg.country == "GB"
        assert cfg.cost_budget_credits == 1000


# ─────────────────────────────────────────────
# ScrapFlyClient — key / import errors
# ─────────────────────────────────────────────

class TestScrapFlyClientMissingKey:
    @pytest.mark.asyncio
    async def test_raises_missing_key_when_env_empty(self):
        client = ScrapFlyClient(
            ScrapFlyConfig(api_key_env_var="NO_SUCH_VAR_XYZ"),
            env_provider=lambda k: None,
        )
        with pytest.raises(ScrapFlyMissingKeyError, match="NO_SUCH_VAR_XYZ"):
            await client.open()

    @pytest.mark.asyncio
    async def test_raises_missing_key_when_env_blank(self):
        client = ScrapFlyClient(
            ScrapFlyConfig(api_key_env_var="BLANK_KEY"),
            env_provider=lambda k: "",
        )
        with pytest.raises(ScrapFlyMissingKeyError):
            await client.open()

    @pytest.mark.asyncio
    async def test_raises_import_error_when_sdk_missing(self, monkeypatch):
        real_import = builtins.__import__

        def block_scrapfly(name, *args, **kwargs):
            if "scrapfly" in name:
                raise ImportError("No module named 'scrapfly'")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", block_scrapfly)
        client = ScrapFlyClient(
            ScrapFlyConfig(),
            env_provider=lambda k: "fake-key",
        )
        with pytest.raises(ImportError, match="scrapfly-sdk"):
            await client.open()


# ─────────────────────────────────────────────
# Shared mock SDK helpers
# ─────────────────────────────────────────────

class _MockScrapeResult:
    def __init__(self, html: str = "<html>ok</html>", status: int = 200, credits: int = 25):
        self.scrape_result = {
            "content": html,
            "status_code": status,
            "asp_trial": True,
        }
        self.context = {"cost": {"total": credits}}


class _MockSDKClient:
    def __init__(self, result: _MockScrapeResult):
        self._result = result
        self.calls: list[str] = []

    async def async_scrape(self, config: object) -> _MockScrapeResult:
        self.calls.append(getattr(config, "url", "unknown"))
        return self._result


def _client_with(html: str = "<html>ok</html>", status: int = 200, credits: int = 25) -> ScrapFlyClient:
    c = ScrapFlyClient(ScrapFlyConfig(api_key_env_var="KEY"), env_provider=lambda k: "fake")
    c._sdk_client = _MockSDKClient(_MockScrapeResult(html, status, credits))
    return c


# ─────────────────────────────────────────────
# ScrapFlyClient — successful fetch
# ─────────────────────────────────────────────

class TestScrapFlyClientFetch:
    @pytest.mark.asyncio
    async def test_returns_correct_html(self):
        c = _client_with("<html>logo gigs</html>")
        result = await c.fetch("https://www.fiverr.com/search/gigs?query=logo")
        assert result.html == "<html>logo gigs</html>"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_returns_correct_credits(self):
        c = _client_with(credits=42)
        result = await c.fetch("https://www.fiverr.com/x")
        assert result.credits_used == 42

    @pytest.mark.asyncio
    async def test_tracks_total_requests(self):
        c = _client_with()
        await c.fetch("https://www.fiverr.com/a")
        await c.fetch("https://www.fiverr.com/b")
        assert c.stats.total_requests == 2

    @pytest.mark.asyncio
    async def test_accumulates_credits(self):
        c = _client_with(credits=25)
        await c.fetch("https://www.fiverr.com/a")
        await c.fetch("https://www.fiverr.com/b")
        assert c.stats.total_credits_used == 50

    @pytest.mark.asyncio
    async def test_counts_asp_bypasses(self):
        c = _client_with()
        await c.fetch("https://www.fiverr.com/x")
        assert c.stats.asp_bypasses == 1

    @pytest.mark.asyncio
    async def test_result_url_matches_requested(self):
        c = _client_with()
        result = await c.fetch("https://www.fiverr.com/search/gigs?query=logo")
        assert result.url == "https://www.fiverr.com/search/gigs?query=logo"

    @pytest.mark.asyncio
    async def test_backend_is_scrapfly(self):
        # ScrapFlyResult itself — not FetchResult — has no backend field
        # but ScrapFlyFetcher wraps it into FetchResult with backend="scrapfly"
        sf_result = ScrapFlyResult(
            url="https://www.fiverr.com/x",
            html="<html/>",
            status_code=200,
            credits_used=10,
            asp_triggered=True,
            success=True,
        )

        class _FakeClient:
            async def fetch(self, url, **_kw):
                return sf_result

        fetcher = ScrapFlyFetcher(_FakeClient())
        result = await fetcher.fetch("https://www.fiverr.com/x")
        assert result.backend == "scrapfly"


# ─────────────────────────────────────────────
# ScrapFlyClient — error paths
# ─────────────────────────────────────────────

class TestScrapFlyClientErrors:
    @pytest.mark.asyncio
    async def test_raises_rate_limit_on_429(self):
        c = _client_with(status=429)
        with pytest.raises(ScrapFlyRateLimitError):
            await c.fetch("https://www.fiverr.com/x")

    @pytest.mark.asyncio
    async def test_raises_blocked_on_403_no_html(self):
        c = _client_with(html="", status=403)
        with pytest.raises(ScrapFlyBlockedError):
            await c.fetch("https://www.fiverr.com/x")

    @pytest.mark.asyncio
    async def test_raises_blocked_on_503_no_html(self):
        c = _client_with(html="", status=503)
        with pytest.raises(ScrapFlyBlockedError):
            await c.fetch("https://www.fiverr.com/x")

    @pytest.mark.asyncio
    async def test_does_not_raise_blocked_when_html_present_on_403(self):
        # Some 403s still return useful HTML — should not raise
        c = _client_with(html="<html>partial content</html>", status=403)
        result = await c.fetch("https://www.fiverr.com/x")
        assert result.html == "<html>partial content</html>"

    @pytest.mark.asyncio
    async def test_budget_exceeded_raises_rate_limit(self):
        c = ScrapFlyClient(
            ScrapFlyConfig(api_key_env_var="KEY", cost_budget_credits=10),
            env_provider=lambda k: "fake",
        )
        c._sdk_client = _MockSDKClient(_MockScrapeResult(credits=25))
        with pytest.raises(ScrapFlyRateLimitError, match="budget exceeded"):
            await c.fetch("https://www.fiverr.com/x")

    @pytest.mark.asyncio
    async def test_increments_error_count_on_429(self):
        c = _client_with(status=429)
        try:
            await c.fetch("https://www.fiverr.com/x")
        except ScrapFlyRateLimitError:
            pass
        assert c.stats.errors == 1

    @pytest.mark.asyncio
    async def test_retries_transient_errors(self):
        """SDK raises generic Exception twice, succeeds on third attempt."""
        call_count = 0

        class _FlakySDK:
            async def async_scrape(self, config):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise RuntimeError("transient failure")
                return _MockScrapeResult()

        c = ScrapFlyClient(
            ScrapFlyConfig(api_key_env_var="KEY", max_retries=3, retry_wait_seconds=0.0),
            env_provider=lambda k: "fake",
        )
        c._sdk_client = _FlakySDK()
        result = await c.fetch("https://www.fiverr.com/x")
        assert result.success is True
        assert call_count == 3


# ─────────────────────────────────────────────
# ScrapFlyClient — context manager
# ─────────────────────────────────────────────

class TestScrapFlyClientLifecycle:
    @pytest.mark.asyncio
    async def test_context_manager_calls_close(self):
        closed = []

        class _ClosingSDK(_MockSDKClient):
            async def close(self):
                closed.append(True)

        c = ScrapFlyClient(ScrapFlyConfig(api_key_env_var="K"), env_provider=lambda k: "fake")
        c._sdk_client = _ClosingSDK(_MockScrapeResult())
        async with c:
            await c.fetch("https://www.fiverr.com/x")
        assert closed == [True]

    @pytest.mark.asyncio
    async def test_open_is_idempotent(self):
        c = _client_with()
        sdk_ref = c._sdk_client
        await c.open()   # should not create a new client
        assert c._sdk_client is sdk_ref

    @pytest.mark.asyncio
    async def test_close_sets_sdk_to_none(self):
        c = _client_with()
        await c.close()
        assert c._sdk_client is None


# ─────────────────────────────────────────────
# ScrapFlyFetcher — PageFetcher protocol
# ─────────────────────────────────────────────

class TestScrapFlyFetcher:
    def _make_fetcher(self, html: str = "<html/>") -> ScrapFlyFetcher:
        sf_result = ScrapFlyResult(
            url="https://www.fiverr.com/x",
            html=html,
            status_code=200,
            credits_used=25,
            asp_triggered=True,
            success=True,
        )

        class _FakeClient:
            async def fetch(self, url, **_kw):
                return sf_result

        return ScrapFlyFetcher(_FakeClient())

    def test_satisfies_page_fetcher_protocol(self):
        assert isinstance(self._make_fetcher(), PageFetcher)

    @pytest.mark.asyncio
    async def test_returns_fetch_result(self):
        fetcher = self._make_fetcher("<html>gig content</html>")
        result = await fetcher.fetch("https://www.fiverr.com/x")
        assert isinstance(result, FetchResult)
        assert result.html == "<html>gig content</html>"
        assert result.backend == "scrapfly"
        assert result.credits_used == 25

    @pytest.mark.asyncio
    async def test_passes_pacing_key(self):
        received_key: list[str] = []

        class _TrackingClient:
            async def fetch(self, url, **kw):
                received_key.append(kw.get("pacing_key", ""))
                return ScrapFlyResult("", "<html/>", 200, 0, False, True)

        fetcher = ScrapFlyFetcher(_TrackingClient())
        await fetcher.fetch("https://www.fiverr.com/x", pacing_key="fiverr_gig_detail")
        assert received_key == ["fiverr_gig_detail"]


# ─────────────────────────────────────────────
# PlaywrightFetcher — PageFetcher protocol
# ─────────────────────────────────────────────

class TestPlaywrightFetcher:
    def _make_fetcher(self) -> PlaywrightFetcher:
        class _FakePage:
            url = "https://www.fiverr.com/x"
            async def goto(self, *a, **kw): pass
            async def content(self): return "<html>playwright content</html>"
            async def close(self): pass

        class _FakeSM:
            async def new_page(self): return _FakePage()
            async def close_page(self, p): pass

        return PlaywrightFetcher(_FakeSM())

    def test_satisfies_page_fetcher_protocol(self):
        assert isinstance(self._make_fetcher(), PageFetcher)

    @pytest.mark.asyncio
    async def test_returns_fetch_result(self):
        result = await self._make_fetcher().fetch("https://www.fiverr.com/x")
        assert isinstance(result, FetchResult)
        assert result.html == "<html>playwright content</html>"
        assert result.backend == "playwright"
        assert result.credits_used == 0


# ─────────────────────────────────────────────
# build_fetcher factory
# ─────────────────────────────────────────────

class TestBuildFetcher:
    def test_returns_none_when_nothing_provided(self):
        assert build_fetcher() is None

    def test_returns_playwright_with_session_manager_only(self):
        class _SM:
            async def new_page(self): pass
            async def close_page(self, p): pass

        result = build_fetcher(session_manager=_SM())
        assert isinstance(result, PlaywrightFetcher)

    def test_returns_scrapfly_with_client_only(self):
        class _SF:
            async def fetch(self, url, **kw): pass

        result = build_fetcher(scrapfly_client=_SF())
        assert isinstance(result, ScrapFlyFetcher)

    def test_prefer_scrapfly_overrides_session_manager(self):
        class _SM:
            async def new_page(self): pass
            async def close_page(self, p): pass

        class _SF:
            async def fetch(self, url, **kw): pass

        result = build_fetcher(session_manager=_SM(), scrapfly_client=_SF(), prefer_scrapfly=True)
        assert isinstance(result, ScrapFlyFetcher)

    def test_falls_back_to_playwright_when_prefer_false(self):
        class _SM:
            async def new_page(self): pass
            async def close_page(self, p): pass

        class _SF:
            async def fetch(self, url, **kw): pass

        result = build_fetcher(session_manager=_SM(), scrapfly_client=_SF(), prefer_scrapfly=False)
        assert isinstance(result, PlaywrightFetcher)

    def test_scrapfly_wins_when_no_session_manager(self):
        class _SF:
            async def fetch(self, url, **kw): pass

        result = build_fetcher(scrapfly_client=_SF(), prefer_scrapfly=False)
        assert isinstance(result, ScrapFlyFetcher)


# ─────────────────────────────────────────────
# Config model — ScrapFlyCollectionConfig
# ─────────────────────────────────────────────

class TestScrapFlyCollectionConfig:
    def test_defaults_disabled(self):
        from src.config.models import ScrapFlyCollectionConfig
        cfg = ScrapFlyCollectionConfig()
        assert cfg.enabled is False
        assert cfg.asp is True
        assert cfg.render_js is True
        assert cfg.country == "US"

    def test_collection_config_has_scrapfly_field(self):
        from src.config.models import CollectionConfig, PacingConfig
        cfg = CollectionConfig(pacing={"default": PacingConfig()})
        assert hasattr(cfg, "scrapfly")
        assert cfg.scrapfly.enabled is False

    def test_collection_config_scrapfly_can_be_enabled(self):
        from src.config.models import CollectionConfig, PacingConfig, ScrapFlyCollectionConfig
        cfg = CollectionConfig(
            pacing={"default": PacingConfig()},
            scrapfly=ScrapFlyCollectionConfig(enabled=True, country="GB"),
        )
        assert cfg.scrapfly.enabled is True
        assert cfg.scrapfly.country == "GB"


# ─────────────────────────────────────────────
# Search result parser
# ─────────────────────────────────────────────

_SEARCH_HTML = """
<html><body>
<div data-testid="total-result-count">1,234 results for logo design</div>
<div data-testid="gig-card-layout">
  <a href="/alexcreative/i-will-design-your-logo">link</a>
  <div data-testid="gig-title">I will design a professional logo</div>
  <div data-testid="seller-name">alexcreative</div>
  <div data-testid="seller-level">Level 2</div>
  <div data-testid="review-count">842</div>
  <div data-testid="starting-price">$25</div>
</div>
<div data-testid="gig-card-layout">
  <a href="/bestlogos/i-will-create-unique-logo">link</a>
  <div data-testid="gig-title">I will create a unique minimalist logo</div>
  <div data-testid="seller-name">bestlogos</div>
  <div data-testid="starting-price">$50</div>
  <div data-testid="sponsored-badge">Ad</div>
</div>
</body></html>
"""


class TestSearchResultParser:
    def test_returns_search_parse_result_type(self):
        assert isinstance(parse_search_results_from_html(_SEARCH_HTML), SearchParseResult)

    def test_parses_total_result_count(self):
        result = parse_search_results_from_html(_SEARCH_HTML)
        assert result.total_result_count == 1234

    def test_parses_two_cards(self):
        result = parse_search_results_from_html(_SEARCH_HTML)
        assert len(result.gig_cards) == 2

    def test_first_card_position(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.position == 1

    def test_first_card_title(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.gig_title == "I will design a professional logo"

    def test_first_card_seller(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.seller_username == "alexcreative"

    def test_first_card_level(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.seller_level == "Level 2"

    def test_first_card_review_count(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.review_count_visible == 842

    def test_first_card_price(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.starting_price == 25.0

    def test_first_card_not_sponsored(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.sponsored_flag is False

    def test_second_card_sponsored(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[1]
        assert card.sponsored_flag is True

    def test_second_card_price(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[1]
        assert card.starting_price == 50.0

    def test_second_card_position(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[1]
        assert card.position == 2

    def test_empty_string_returns_warning(self):
        result = parse_search_results_from_html("")
        assert result.gig_cards == []
        assert result.total_result_count is None
        assert len(result.warnings) > 0

    def test_no_tags_returns_warning(self):
        result = parse_search_results_from_html("just plain text, no html")
        assert len(result.warnings) > 0

    def test_max_cards_cap_respected(self):
        cards = "\n".join(
            f'<div data-testid="gig-card-layout">'
            f'<div data-testid="gig-title">Gig {i}</div></div>'
            for i in range(30)
        )
        result = parse_search_results_from_html(
            f"<html><body>{cards}</body></html>", max_cards=10
        )
        assert len(result.gig_cards) == 10

    def test_no_cards_returns_warning(self):
        result = parse_search_results_from_html("<html><body><p>nothing here</p></body></html>")
        assert result.gig_cards == []
        assert any("gig card" in w.lower() or "testid" in w.lower() for w in result.warnings)

    def test_gig_url_extracted_from_href(self):
        card = parse_search_results_from_html(_SEARCH_HTML).gig_cards[0]
        assert card.gig_url is not None
        assert "alexcreative" in card.gig_url

    def test_relative_gig_href_is_normalized_to_absolute(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <a href="/reluser/i-will-build-your-app">link</a>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.gig_url == "https://www.fiverr.com/reluser/i-will-build-your-app"

    def test_absolute_gig_href_is_preserved(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <a href="https://www.fiverr.com/absuser/i-will-build-your-app">link</a>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.gig_url == "https://www.fiverr.com/absuser/i-will-build-your-app"

    def test_non_gig_search_href_is_not_used_as_gig_url(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <a href="/search/gigs?query=logo">not a gig</a>
          <div data-testid="gig-title">Card with search link</div>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.gig_url is None

    def test_seller_username_falls_back_to_href_when_name_missing(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <a href="https://www.fiverr.com/fallbackseller/i-will-code">link</a>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.seller_username == "fallbackseller"

    def test_total_result_count_parses_without_comma(self):
        html = """<html><body>
        <div data-testid="total-result-count">432 results for keyword</div>
        <div data-testid="gig-card-layout"><div data-testid="gig-title">Any</div></div>
        </body></html>"""
        result = parse_search_results_from_html(html)
        assert result.total_result_count == 432

    def test_missing_price_returns_none(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <div data-testid="gig-title">Title only card</div>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.starting_price is None

    def test_missing_review_count_returns_none(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <div data-testid="gig-title">No reviews card</div>
          <div data-testid="starting-price">$10</div>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.review_count_visible is None

    def test_price_with_comma_parsed_correctly(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <div data-testid="starting-price">$1,500</div>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.starting_price == 1500.0

    def test_euro_price_parsed(self):
        html = """<html><body>
        <div data-testid="gig-card-layout">
          <div data-testid="starting-price">€75</div>
        </div></body></html>"""
        card = parse_search_results_from_html(html).gig_cards[0]
        assert card.starting_price == 75.0
