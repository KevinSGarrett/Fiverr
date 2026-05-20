"""Playwright session manager for authenticated Fiverr collection."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)
from playwright.async_api import (
    Error as PlaywrightError,
)
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)

from src.collection.fiverr_selectors import LOGGED_IN_FALLBACK, LOGGED_IN_INDICATOR
from src.collection.human_events import attach_human_events, random_user_agent, random_viewport

log = logging.getLogger(__name__)

FIVERR_BASE_URL = "https://www.fiverr.com"
VERIFICATION_TIMEOUT_MS = 10_000
LOGIN_TIMEOUT_MS = 300_000
MAX_LOGIN_ATTEMPTS = 3


class SessionLoginError(Exception):
    """Raised when Fiverr login cannot be verified after maximum attempts."""


def validate_session_file(session_file_path: Path) -> dict[str, bool | str]:
    """
    Validate session file structure without launching a browser.

    Returns:
        Dict with keys: exists, valid_json, has_cookies, has_origins, path
    """
    result: dict[str, bool | str] = {
        "exists": False,
        "valid_json": False,
        "has_cookies": False,
        "has_origins": False,
        "path": str(session_file_path),
    }
    if not session_file_path.exists():
        return result

    result["exists"] = True
    try:
        data = json.loads(session_file_path.read_text(encoding="utf-8"))
        result["valid_json"] = True
        if isinstance(data, dict):
            result["has_cookies"] = bool(data.get("cookies", []))
            result["has_origins"] = bool(data.get("origins", []))
    except (json.JSONDecodeError, OSError):
        pass
    return result


class SessionManager:
    """Single entry point for Playwright browser operations."""

    FIVERR_BASE_URL = FIVERR_BASE_URL

    def __init__(self, config: Any):
        self.config = config
        self.session_file = Path(str(self._cfg("fiverr.session_file", "data/sessions/fiverr_session.json")))
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._verified = False
        self._pages_open = 0

    async def __aenter__(self) -> SessionManager:
        await self._initialize()
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        await self.close()

    async def new_page(self) -> Page:
        """Create an authenticated page and attach human event hooks."""
        context = await self._get_context()
        page = await context.new_page()
        pacing = self._cfg("collection.pacing", {})
        attach_human_events(page, pacing if isinstance(pacing, dict) else {})
        self._pages_open += 1
        return page

    async def close_page(self, page: Page) -> None:
        """Close a page and decrement open page count."""
        await page.close()
        self._pages_open = max(0, self._pages_open - 1)

    async def close(self) -> None:
        """Gracefully close context, browser, and playwright in order."""
        if self._context is not None:
            try:
                await self._context.close()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                log.warning("Error closing browser context: %s", exc)
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                log.warning("Error closing browser: %s", exc)
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                log.warning("Error stopping playwright: %s", exc)
        self._context = None
        self._browser = None
        self._playwright = None
        self._verified = False
        self._pages_open = 0

    async def force_relogin(self) -> None:
        """Force a full relogin flow and overwrite session state."""
        await self.close()
        self._context = await self._headed_login_flow()

    async def is_session_valid(self) -> bool:
        """Check whether current session is valid without side effects."""
        try:
            context = await self._get_context()
            return await self._verify_session(context)
        except Exception:
            return False

    async def _initialize(self) -> None:
        """Initialize shared browser context once (idempotent)."""
        if self._context is not None:
            return
        self._context = await self._load_or_login()

    async def _get_context(self) -> BrowserContext:
        """Get initialized browser context, initializing on first use."""
        if self._context is None:
            await self._initialize()
        if self._context is None:  # pragma: no cover - safety net
            raise RuntimeError("Session context initialization failed.")
        return self._context

    async def _load_or_login(self) -> BrowserContext:
        """Load saved session if valid; otherwise trigger headed login flow."""
        if self.session_file.exists():
            context = await self._load_session_headless()
            if await self._verify_session(context):
                self._verified = True
                return context
            await context.close()
            if self._browser is not None:
                await self._browser.close()
                self._browser = None
        return await self._headed_login_flow()

    async def _load_session_headless(self) -> BrowserContext:
        """Open headless Chromium and load storage_state from disk."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=self._browser_args(),
        )
        context = await self._browser.new_context(
            storage_state=str(self.session_file),
            **self._context_options(),
        )
        return context

    async def _verify_session(self, context: BrowserContext) -> bool:
        """Verify whether Fiverr home reflects a logged-in account."""
        page = await context.new_page()
        try:
            await page.goto(
                self.FIVERR_BASE_URL,
                wait_until="domcontentloaded",
                timeout=VERIFICATION_TIMEOUT_MS,
            )
            element = await page.query_selector(LOGGED_IN_INDICATOR)
            if element is None:
                element = await page.query_selector(LOGGED_IN_FALLBACK)
            return element is not None
        except PlaywrightTimeoutError:
            return False
        except PlaywrightError:
            return False
        finally:
            await page.close()

    async def _headed_login_flow(self) -> BrowserContext:
        """Open headed browser, wait for user login, persist, then return headless context."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            log.info("Login attempt %s/%s", attempt, MAX_LOGIN_ATTEMPTS)
            browser = await self._playwright.chromium.launch(headless=False, args=self._browser_args())
            context = await browser.new_context(**self._context_options())
            page = await context.new_page()
            await page.goto(
                str(self._cfg("fiverr.login_url", "https://www.fiverr.com/login")),
                wait_until="domcontentloaded",
                timeout=LOGIN_TIMEOUT_MS,
            )
            print("\n" + "=" * 62)
            print("  ACTION REQUIRED — Fiverr Login")
            print("=" * 62)
            print("  A browser window has opened. Please:")
            print("  1. Log in to your Fiverr account")
            print("  2. Complete any 2FA or CAPTCHA steps")
            print("  3. Wait until you see your Fiverr dashboard/homepage")
            print("  4. Return here and press Enter to continue")
            print("=" * 62)
            input("  Press Enter when logged in: ")
            verified = await self._verify_session_on_page(page)
            await page.close()
            if verified:
                log.info("Login verified. Saving session.")
                self.session_file.parent.mkdir(parents=True, exist_ok=True)
                await context.storage_state(path=str(self.session_file))
                try:
                    os.chmod(self.session_file, 0o600)
                except OSError as exc:
                    log.warning("Could not set session file permissions: %s", exc)
                await context.close()
                await browser.close()
                return await self._load_session_headless()

            print("\n  Login could not be verified. Please try again.")
            await context.close()
            await browser.close()

        raise SessionLoginError(
            f"Failed to verify Fiverr login after {MAX_LOGIN_ATTEMPTS} attempts. "
            "Run 'python run.py relogin' to try again."
        )

    async def _verify_session_on_page(self, page: Page) -> bool:
        """Verify login indicators on an already open page."""
        try:
            element = await page.query_selector(LOGGED_IN_INDICATOR)
            if element is None:
                element = await page.query_selector(LOGGED_IN_FALLBACK)
            return element is not None
        except Exception:
            return False

    def _browser_args(self) -> list[str]:
        """Chromium launch flags to reduce automation fingerprints."""
        return [
            "--disable-blink-features=AutomationControlled",
            "--disable-automation",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-infobars",
            "--disable-notifications",
            "--disable-popup-blocking",
            "--ignore-certificate-errors",
            "--no-sandbox",
        ]

    def _context_options(self) -> dict[str, Any]:
        """Options applied to every browser context."""
        return {
            "viewport": random_viewport(),
            "user_agent": random_user_agent(),
            "locale": "en-US",
            "timezone_id": "America/Chicago",
            "java_script_enabled": True,
            "accept_downloads": False,
            "extra_http_headers": {
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
            },
        }

    def _cfg(self, key_path: str, default: Any = None) -> Any:
        """Read nested config values from dict-like or attribute-based config."""
        current: Any = self.config
        for key in key_path.split("."):
            if isinstance(current, dict):
                if key not in current:
                    return default
                current = current[key]
                continue
            if hasattr(current, key):
                current = getattr(current, key)
                continue
            if hasattr(current, "model_dump"):
                dumped = current.model_dump()  # pydantic v2
                if key not in dumped:
                    return default
                current = dumped[key]
                continue
            return default
        return current
