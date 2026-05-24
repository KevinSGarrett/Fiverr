"""Abstract PageFetcher protocol with Playwright and ScrapFly adapters.

Workflows accept an optional `fetcher: PageFetcher | None = None` parameter.
When None  → existing Playwright session_manager path is used (zero change).
When set   → fetcher.fetch(url) returns HTML; no browser page needed.

This lets the same workflow code run against either backend transparently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Shared result type
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class FetchResult:
    """Normalised page result from any backend."""

    url: str
    html: str
    status_code: int
    backend: str        # "playwright" | "scrapfly"
    credits_used: int = 0
    success: bool = True


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class PageFetcher(Protocol):
    """
    Protocol satisfied by both PlaywrightFetcher and ScrapFlyFetcher.

    Workflows check `if fetcher is not None` then call `fetcher.fetch(url)`.
    """

    async def fetch(self, url: str, *, pacing_key: str = "fiverr") -> FetchResult:
        ...


# ---------------------------------------------------------------------------
# Playwright adapter
# ---------------------------------------------------------------------------

class PlaywrightFetcher:
    """
    Adapts an existing SessionManager to the PageFetcher protocol.

    Use this when you want HTML from a page without writing
    Playwright selector code inside the workflow.

        fetcher = PlaywrightFetcher(session_manager, pacing_manager)
        result  = await fetcher.fetch("https://www.fiverr.com/...")
        html    = result.html
    """

    def __init__(
        self,
        session_manager: Any,
        pacing_manager: Any | None = None,
    ) -> None:
        self._session = session_manager
        self._pacing = pacing_manager

    async def fetch(self, url: str, *, pacing_key: str = "fiverr") -> FetchResult:
        page = await self._session.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            if self._pacing is not None:
                try:
                    await self._pacing.wait(pacing_key, dry_run=False)
                except TypeError:
                    await self._pacing.wait(pacing_key)
            html: str = await page.content()
            return FetchResult(
                url=url,
                html=html,
                status_code=200,
                backend="playwright",
            )
        finally:
            await self._session.close_page(page)


# ---------------------------------------------------------------------------
# ScrapFly adapter
# ---------------------------------------------------------------------------

class ScrapFlyFetcher:
    """
    Adapts ScrapFlyClient to the PageFetcher protocol.

    Drop-in replacement for PlaywrightFetcher — same interface, zero
    workflow changes required.

        async with ScrapFlyClient(config) as sf_client:
            fetcher = ScrapFlyFetcher(sf_client)
            result  = await fetcher.fetch("https://www.fiverr.com/...")
    """

    def __init__(self, client: Any) -> None:
        self._client = client

    async def fetch(self, url: str, *, pacing_key: str = "scrapfly") -> FetchResult:
        from src.collection.scrapfly_client import ScrapFlyResult

        raw: ScrapFlyResult = await self._client.fetch(url, pacing_key=pacing_key)
        return FetchResult(
            url=raw.url,
            html=raw.html,
            status_code=raw.status_code,
            backend="scrapfly",
            credits_used=raw.credits_used,
            success=raw.success,
        )


# ---------------------------------------------------------------------------
# Factory helper
# ---------------------------------------------------------------------------

def build_fetcher(
    *,
    session_manager: Any | None = None,
    scrapfly_client: Any | None = None,
    pacing_manager: Any | None = None,
    prefer_scrapfly: bool = False,
) -> PageFetcher | None:
    """
    Convenience factory — returns the right fetcher given what's available.

    Priority:
    1. scrapfly_client if provided and prefer_scrapfly is True
    2. scrapfly_client if session_manager is None
    3. PlaywrightFetcher if session_manager is available
    4. None if nothing is available (caller uses legacy path)

    Example from orchestrator:

        fetcher = build_fetcher(
            session_manager=session_manager,
            scrapfly_client=sf_client,
            pacing_manager=pacing,
            prefer_scrapfly=config.get("collection", {}).get("scrapfly", {}).get("enabled", False),
        )
    """
    if scrapfly_client is not None and (prefer_scrapfly or session_manager is None):
        return ScrapFlyFetcher(scrapfly_client)
    if session_manager is not None:
        return PlaywrightFetcher(session_manager, pacing_manager)
    if scrapfly_client is not None:
        return ScrapFlyFetcher(scrapfly_client)
    return None
