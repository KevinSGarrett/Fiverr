"""ScrapFly HTTP client for PerimeterX bypass on Fiverr pages.

Wraps the scrapfly-sdk with project conventions:
- Reads API key from environment (never hard-coded)
- Integrates with PacingManager for rate control
- Tracks credit usage per session
- Retries transient errors with backoff

Install: pip install scrapfly-sdk
Env var: SCRAPFLY_API_KEY=scp-live-...
"""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ScrapFlyError(RuntimeError):
    """Raised for unrecoverable ScrapFly API errors."""


class ScrapFlyRateLimitError(ScrapFlyError):
    """Credits exhausted or rate-limited (HTTP 429)."""


class ScrapFlyBlockedError(ScrapFlyError):
    """Bot protection was not bypassed despite asp=True."""


class ScrapFlyMissingKeyError(ScrapFlyError):
    """API key env var is set but empty, or not set at all."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ScrapFlyConfig:
    """Immutable ScrapFly request configuration.

    Defaults are tuned for Fiverr (React SPA, PerimeterX protected):
    - asp=True     : Anti Scraping Protection bypass — handles PerimeterX
    - render_js=True: Full headless JS render — Fiverr is React
    - country="US" : US residential exit nodes look natural for Fiverr
    - auto_scroll  : Triggers lazy-loaded gig card images + infinite scroll
    """

    api_key_env_var: str = "SCRAPFLY_API_KEY"
    asp: bool = True
    render_js: bool = True
    country: str = "US"
    auto_scroll: bool = True
    max_retries: int = 3
    retry_wait_seconds: float = 5.0
    timeout_seconds: int = 60
    cost_budget_credits: int | None = None  # Raise ScrapFlyRateLimitError if exceeded

    def redact(self) -> dict[str, Any]:
        """Safe repr — never exposes the key value."""
        return {
            "api_key_env_var": self.api_key_env_var,
            "asp": self.asp,
            "render_js": self.render_js,
            "country": self.country,
            "auto_scroll": self.auto_scroll,
            "max_retries": self.max_retries,
            "cost_budget_credits": self.cost_budget_credits,
        }


# ---------------------------------------------------------------------------
# Session stats
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ScrapFlyStats:
    """Running credit and request tally for the current session."""

    total_requests: int = 0
    total_credits_used: int = 0
    errors: int = 0
    asp_bypasses: int = 0
    blocked: int = 0

    def log_summary(self) -> None:
        log.info(
            "ScrapFly session summary: requests=%d credits=%d errors=%d asp_bypasses=%d",
            self.total_requests,
            self.total_credits_used,
            self.errors,
            self.asp_bypasses,
        )


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class ScrapFlyResult:
    """Normalised result from a single ScrapFly API call."""

    url: str
    html: str
    status_code: int
    credits_used: int
    asp_triggered: bool
    success: bool


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ScrapFlyClient:
    """
    Async wrapper around scrapfly-sdk that integrates with PacingManager.

    Typical usage (preferred — async context manager):

        async with ScrapFlyClient(ScrapFlyConfig()) as client:
            result = await client.fetch("https://www.fiverr.com/search/gigs?query=logo")
            html = result.html

    Manual usage (fine when lifecycle is managed externally):

        client = ScrapFlyClient(config, pacing_manager=pacing)
        await client.open()
        result = await client.fetch(url)
        await client.close()
    """

    def __init__(
        self,
        config: ScrapFlyConfig | None = None,
        *,
        pacing_manager: Any | None = None,
        env_provider: Any | None = None,
    ) -> None:
        self._config = config or ScrapFlyConfig()
        self._pacing = pacing_manager
        self._env = env_provider or os.getenv
        self._stats: ScrapFlyStats = ScrapFlyStats()
        self._sdk_client: Any | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def open(self) -> None:
        """Initialise the underlying SDK client (idempotent)."""
        if self._sdk_client is not None:
            return

        api_key = self._env(self._config.api_key_env_var)
        if not api_key:
            raise ScrapFlyMissingKeyError(
                f"ScrapFly API key not found. "
                f"Set env var '{self._config.api_key_env_var}' before running live collection.\n"
                f"Get a key at https://scrapfly.io/"
            )

        try:
            scrapfly_module = importlib.import_module("scrapfly")
            _SDK = scrapfly_module.ScrapflyClient
        except ImportError as exc:
            raise ImportError(
                "scrapfly-sdk is not installed.\n"
                "Run:  pip install scrapfly-sdk\n"
                "Docs: https://scrapfly.io/docs/sdk/python"
            ) from exc

        self._sdk_client = _SDK(key=str(api_key))
        log.info(
            "ScrapFlyClient ready — %s",
            self._config.redact(),
        )

    async def close(self) -> None:
        """Gracefully close the SDK client."""
        if self._sdk_client is not None:
            closer = getattr(self._sdk_client, "close", None)
            if closer is not None:
                try:
                    await closer()
                except Exception as exc:
                    log.warning("ScrapFly close error (ignored): %s", exc)
            self._sdk_client = None

    async def __aenter__(self) -> ScrapFlyClient:
        await self.open()
        return self

    async def __aexit__(self, *_: Any) -> None:
        self._stats.log_summary()
        await self.close()

    # ------------------------------------------------------------------
    # Public fetch
    # ------------------------------------------------------------------

    async def fetch(
        self,
        url: str,
        *,
        asp: bool | None = None,
        render_js: bool | None = None,
        pacing_key: str = "scrapfly",
    ) -> ScrapFlyResult:
        """Fetch a URL via ScrapFly and return normalised HTML content.

        Args:
            url:        Full URL to fetch.
            asp:        Override config.asp for this single request.
            render_js:  Override config.render_js for this single request.
            pacing_key: Key forwarded to PacingManager.wait() if one is set.

        Returns:
            ScrapFlyResult — always contains .html and .credits_used.

        Raises:
            ScrapFlyMissingKeyError: API key not configured.
            ScrapFlyRateLimitError:  Credits exhausted (HTTP 429).
            ScrapFlyBlockedError:    Protection not bypassed (403/503 + no HTML).
            ScrapFlyError:           Other unrecoverable failure after retries.
        """
        await self.open()

        if self._pacing is not None:
            try:
                await self._pacing.wait(pacing_key, dry_run=False)
            except TypeError:
                await self._pacing.wait(pacing_key)

        use_asp = asp if asp is not None else self._config.asp
        use_js = render_js if render_js is not None else self._config.render_js

        last_exc: Exception | None = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                result = await self._single_fetch(url, asp=use_asp, render_js=use_js)

                self._stats.total_requests += 1
                self._stats.total_credits_used += result.credits_used
                if result.asp_triggered:
                    self._stats.asp_bypasses += 1

                if (
                    self._config.cost_budget_credits is not None
                    and self._stats.total_credits_used > self._config.cost_budget_credits
                ):
                    raise ScrapFlyRateLimitError(
                        f"ScrapFly credit budget exceeded: "
                        f"used={self._stats.total_credits_used} "
                        f"budget={self._config.cost_budget_credits}"
                    )

                log.debug(
                    "ScrapFly OK  url=%s  credits=%d  session_total=%d",
                    url,
                    result.credits_used,
                    self._stats.total_credits_used,
                )
                return result

            except (ScrapFlyRateLimitError, ScrapFlyBlockedError, ScrapFlyMissingKeyError):
                self._stats.errors += 1
                raise

            except Exception as exc:
                last_exc = exc
                self._stats.errors += 1
                log.warning(
                    "ScrapFly attempt %d/%d failed — url=%s  error=%s",
                    attempt,
                    self._config.max_retries,
                    url,
                    exc,
                )
                if attempt < self._config.max_retries:
                    import asyncio
                    await asyncio.sleep(self._config.retry_wait_seconds * attempt)

        raise ScrapFlyError(
            f"ScrapFly gave up after {self._config.max_retries} attempts for {url}"
        ) from last_exc

    # ------------------------------------------------------------------
    # Internal single request
    # ------------------------------------------------------------------

    async def _single_fetch(
        self, url: str, *, asp: bool, render_js: bool
    ) -> ScrapFlyResult:
        """Execute one ScrapFly API call and normalise the response."""
        try:
            scrapfly_module = importlib.import_module("scrapfly")
            ScrapeConfig = scrapfly_module.ScrapeConfig
        except ImportError as exc:
            if self._sdk_client is None:
                raise ImportError("scrapfly-sdk not installed") from exc

            # Test and fallback path: allow injected SDK doubles without the
            # real scrapfly package installed.
            class ScrapeConfig:  # type: ignore[no-redef]
                def __init__(self, **kwargs: Any) -> None:
                    for key, value in kwargs.items():
                        setattr(self, key, value)

        cfg = ScrapeConfig(
            url=url,
            asp=asp,
            render_js=render_js,
            country=self._config.country,
            auto_scroll=self._config.auto_scroll,
            timeout=self._config.timeout_seconds * 1000,
        )

        if self._sdk_client is None:
            raise ScrapFlyError("ScrapFly SDK client is not initialized.")
        response = await self._sdk_client.async_scrape(cfg)
        scrape = response.scrape_result

        html: str = scrape.get("content", "") or ""
        status: int = int(scrape.get("status_code") or 200)

        # Credit extraction — SDK wraps this in response.context
        credits_used: int = 0
        ctx = getattr(response, "context", None)
        if isinstance(ctx, dict):
            credits_used = int(ctx.get("cost", {}).get("total", 0) or 0)

        asp_triggered: bool = bool(scrape.get("asp_trial", False))

        if status == 429:
            raise ScrapFlyRateLimitError(f"Rate limited (429) on {url}")
        if status in (403, 503) and not html.strip():
            self._stats.blocked += 1
            raise ScrapFlyBlockedError(
                f"PerimeterX block not bypassed (status={status}) on {url}. "
                "Ensure asp=True is set and your plan supports ASP."
            )

        return ScrapFlyResult(
            url=url,
            html=html,
            status_code=status,
            credits_used=credits_used,
            asp_triggered=asp_triggered,
            success=bool(html.strip() and status < 400),
        )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def stats(self) -> ScrapFlyStats:
        """Snapshot of credit / request counters for this session."""
        return ScrapFlyStats(
            total_requests=self._stats.total_requests,
            total_credits_used=self._stats.total_credits_used,
            errors=self._stats.errors,
            asp_bypasses=self._stats.asp_bypasses,
            blocked=self._stats.blocked,
        )
