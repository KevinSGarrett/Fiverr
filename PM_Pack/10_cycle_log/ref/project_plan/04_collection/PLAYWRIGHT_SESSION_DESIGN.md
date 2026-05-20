# Playwright Session Design
# Fiverr Research System — Wave 4

**Document Status:** Complete
**Wave:** 4 — Collection Engine Design
**Purpose:** Complete implementation specification for session_manager.py — all class methods, selector strategy, browser launch config, storage state handling, headed login flow, context reuse, page lifecycle, and error boundaries.

---

## Design Goals

1. Single entry point for all Playwright operations — no collection module creates its own browser context
2. Session state is always verified before returning to callers — callers never handle session expiry
3. Selectors are named constants, never hardcoded in logic — DOM changes require only a constants update
4. Headed login is as smooth as possible — clear terminal instructions, minimal user friction
5. Headless operation is the default after first login — no headed browser in normal runs
6. Context is shared across all collection modules in a run — one browser process, many pages

---

## Fiverr DOM Selectors (Named Constants)

All CSS selectors used by the Session Manager and collection modules are stored as named constants. When Fiverr updates their frontend, only these constants need updating — no business logic changes required.

```python
# src/collection/fiverr_selectors.py

# ─── Session verification ─────────────────────────────────────────────────────
LOGGED_IN_INDICATOR       = "[data-testid='user-menu-button']"
# The user avatar / menu button visible when logged in
LOGGED_IN_FALLBACK        = ".nav-link.user-actions"
# Fallback selector if primary is not found

# ─── Search results page ──────────────────────────────────────────────────────
SEARCH_RESULT_COUNT       = "[data-testid='results-count'], .results-count, h1.listings-perseus"
# Text element showing "X results for Y"
GIG_CARD_CONTAINER        = "[data-testid='gig-card-layout'], .gig-card-layout"
GIG_CARD_TITLE            = "[data-testid='gig-title'], .gig-title"
GIG_CARD_SELLER_NAME      = "[data-testid='seller-name'], .seller-name"
GIG_CARD_SELLER_LEVEL     = "[data-testid='seller-level-badge'], .seller-level-badge"
GIG_CARD_RATING           = "[data-testid='rating-count'], .rating-count-number"
GIG_CARD_REVIEW_COUNT     = "[data-testid='rating-count-number'], .reviews-count"
GIG_CARD_PRICE            = "[data-testid='starting-price'], .gig-price"
GIG_CARD_DELIVERY         = "[data-testid='delivery-time'], .delivery-time"
GIG_CARD_LINK             = "a[data-testid='gig-link'], a.gig-link"
GIG_CARD_SPONSORED        = "[data-testid='promoted-badge'], .promoted-badge"
GIG_CARD_QUEUE            = "[data-testid='orders-queue'], .orders-queue"
PAGINATION_NEXT           = "[data-testid='pagination-next'], .pagination-next"

# ─── Gig detail page ─────────────────────────────────────────────────────────
GIG_DETAIL_TITLE          = "h1.title"
GIG_DETAIL_DESCRIPTION    = "[data-testid='description'], .description, .gig-description"
GIG_DETAIL_PACKAGES       = "[data-testid='package-header'], .package-content"
GIG_DETAIL_PACKAGE_PRICE  = "[data-testid='package-price'], .price"
GIG_DETAIL_PACKAGE_ITEMS  = "[data-testid='package-includes'] li, .package-items li"
GIG_DETAIL_DELIVERY       = "[data-testid='delivery-time-value'], .delivery-days"
GIG_DETAIL_REVISIONS      = "[data-testid='revisions-value'], .revisions"
GIG_DETAIL_EXTRAS         = "[data-testid='gig-extra'], .gig-extra-service"
GIG_DETAIL_TAGS           = "[data-testid='tag'], .gig-tags a, .tags-wrapper a"
GIG_DETAIL_FAQ_ITEMS      = "[data-testid='faq-item'], .faq-item"
GIG_DETAIL_FAQ_QUESTION   = "[data-testid='faq-question'], .question"
GIG_DETAIL_FAQ_ANSWER     = "[data-testid='faq-answer'], .answer"
GIG_DETAIL_VIDEO          = "[data-testid='gig-video'], video, .gig-video-player"
GIG_DETAIL_PORTFOLIO      = "[data-testid='portfolio-item'], .portfolio-gallery-item"
GIG_DETAIL_REVIEW_COUNT   = "[data-testid='review-count'], .reviews-header .count"
GIG_DETAIL_RATING         = "[data-testid='rating-value'], .main-ratings-score"
GIG_DETAIL_REVIEW_ITEMS   = "[data-testid='review-item'], .review-item"
GIG_DETAIL_THUMBNAIL      = "img[data-testid='gig-thumbnail'], img.gallery-image-container"
GIG_DETAIL_ORDERS_QUEUE   = "[data-testid='orders-in-queue'], .orders-in-queue"
GIG_DETAIL_READ_MORE      = "[data-testid='read-more'], .read-more-btn, button.read-more"

# ─── Seller profile page ─────────────────────────────────────────────────────
SELLER_LEVEL_BADGE        = "[data-testid='seller-level'], .seller-level"
SELLER_MEMBER_SINCE       = "[data-testid='member-since'], .member-since"
SELLER_RESPONSE_TIME      = "[data-testid='response-time'], .response-time"
SELLER_RESPONSE_RATE      = "[data-testid='response-rate'], .response-rate"
SELLER_LANGUAGES          = "[data-testid='language-item'], .language-list li"
SELLER_BIO                = "[data-testid='seller-description'], .seller-overview p"
SELLER_REVIEW_COUNT       = "[data-testid='seller-review-count'], .total-reviews"
SELLER_GIG_COUNT          = "[data-testid='gig-count'], .gigs-count"
SELLER_GIG_TITLES         = "[data-testid='seller-gig-title'], .gig-list .title"
SELLER_PORTFOLIO_ITEMS    = "[data-testid='portfolio-item'], .portfolio-item"
SELLER_BADGES             = "[data-testid='badge-item'], .badge-card"
```

### Selector Update Procedure

When Fiverr updates their frontend and selectors break:
1. Open Fiverr in browser with DevTools
2. Inspect the element to find the new selector (prefer `data-testid` attributes — they are more stable than class names)
3. Update the constant in `fiverr_selectors.py`
4. Run: `python -m pytest tests/unit/test_selectors.py` — selector smoke tests verify key elements are found
5. No other code changes required

---

## Full SessionManager Class Specification

```python
# src/collection/session_manager.py

import asyncio
import os
import random
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page,
    PlaywrightTimeoutError, Error as PlaywrightError
)

from src.core.config import SystemConfig
from src.collection.human_events import attach_human_events, random_viewport, random_user_agent
from src.core.logging import get_logger

log = get_logger(__name__)

FIVERR_BASE_URL = "https://www.fiverr.com"
VERIFICATION_TIMEOUT_MS = 10_000   # 10 seconds to check for login indicator
LOGIN_TIMEOUT_MS        = 300_000  # 5 minutes — generous time for user to log in
MAX_LOGIN_ATTEMPTS      = 3


class SessionLoginError(Exception):
    """Raised when Fiverr login cannot be verified after maximum attempts."""
    pass


class SessionManager:
    """
    Single entry point for all Playwright browser operations.

    Usage pattern:
        async with SessionManager(config) as sm:
            page = await sm.new_page()
            await page.goto("https://www.fiverr.com/search/...")

    Or:
        sm = SessionManager(config)
        page = await sm.new_page()
        # ... collection work ...
        await sm.close()
    """

    def __init__(self, config: SystemConfig):
        self.config = config
        self.session_file = Path(config.fiverr.session_file)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._verified: bool = False
        self._pages_open: int = 0

    # ─── Context manager support ─────────────────────────────────────────────

    async def __aenter__(self) -> "SessionManager":
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # ─── Public API ──────────────────────────────────────────────────────────

    async def new_page(self) -> Page:
        """
        Creates a new Playwright page with human events attached.
        The returned page shares the authenticated session context.
        Caller is responsible for closing the page when done.
        """
        context = await self._get_context()
        page = await context.new_page()
        attach_human_events(page, self.config.pacing)
        self._pages_open += 1
        log.debug(f"New page created. Open pages: {self._pages_open}")
        return page

    async def close_page(self, page: Page):
        """Closes a page and decrements the open page counter."""
        await page.close()
        self._pages_open = max(0, self._pages_open - 1)

    async def close(self):
        """Gracefully closes all browser resources."""
        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                log.warning(f"Error closing browser context: {e}")
        if self._browser:
            try:
                await self._browser.close()
            except Exception as e:
                log.warning(f"Error closing browser: {e}")
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                log.warning(f"Error stopping playwright: {e}")
        self._context = None
        self._browser = None
        self._playwright = None
        self._verified = False

    async def force_relogin(self):
        """Forces a complete re-login flow, overwrites the session file."""
        log.info("Forcing re-login flow.")
        await self.close()
        await self._headed_login_flow()

    async def is_session_valid(self) -> bool:
        """Public method to check session validity without side effects."""
        try:
            context = await self._get_context()
            return await self._verify_session(context)
        except Exception:
            return False

    # ─── Internal initialization ─────────────────────────────────────────────

    async def _initialize(self):
        """Called once at context manager entry or first new_page() call."""
        if self._context is not None:
            return
        self._context = await self._load_or_login()

    async def _get_context(self) -> BrowserContext:
        """Returns initialized context, initializing if needed."""
        if self._context is None:
            await self._initialize()
        return self._context

    async def _load_or_login(self) -> BrowserContext:
        """Core logic: load saved session or trigger login flow."""
        if self.session_file.exists():
            log.info(f"Session file found: {self.session_file}")
            context = await self._load_session_headless()
            if await self._verify_session(context):
                log.info("Session verified successfully. Running headless.")
                self._verified = True
                return context
            else:
                log.info("Session expired. Triggering re-login.")
                await context.close()
                await self._browser.close()
        else:
            log.info("No session file found. First-run login required.")

        return await self._headed_login_flow()

    async def _load_session_headless(self) -> BrowserContext:
        """Loads saved session file into a headless browser context."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=self._browser_args(),
        )
        context = await self._browser.new_context(
            storage_state=str(self.session_file),
            **self._context_options(),
        )
        log.debug("Headless browser context created with saved session.")
        return context

    async def _verify_session(self, context: BrowserContext) -> bool:
        """
        Navigates to Fiverr and checks for the logged-in UI indicator.
        Returns True if session is valid, False if expired/invalid.
        """
        from src.collection.fiverr_selectors import LOGGED_IN_INDICATOR, LOGGED_IN_FALLBACK

        page = await context.new_page()
        try:
            await page.goto(FIVERR_BASE_URL, wait_until="domcontentloaded", timeout=30_000)
            # Try primary selector first, then fallback
            element = await page.query_selector(LOGGED_IN_INDICATOR)
            if element is None:
                element = await page.query_selector(LOGGED_IN_FALLBACK)
            return element is not None
        except PlaywrightTimeoutError:
            log.warning("Timeout during session verification.")
            return False
        except PlaywrightError as e:
            log.warning(f"Playwright error during session verification: {e}")
            return False
        finally:
            await page.close()

    async def _headed_login_flow(self) -> BrowserContext:
        """
        Opens a headed browser, guides user through manual login, saves session.
        Returns a headless context loaded from the saved session.
        """
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            log.info(f"Login attempt {attempt}/{MAX_LOGIN_ATTEMPTS}")
            browser = await self._playwright.chromium.launch(headless=False)
            context = await browser.new_context(**self._context_options())
            page = await context.new_page()

            await page.goto(self.config.fiverr.login_url, wait_until="domcontentloaded")

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
                except OSError as e:
                    log.warning(f"Could not set session file permissions: {e}")
                await context.close()
                await browser.close()
                return await self._load_session_headless()
            else:
                print(f"\n  Login could not be verified. Please try again.")
                await context.close()
                await browser.close()

        raise SessionLoginError(
            f"Failed to verify Fiverr login after {MAX_LOGIN_ATTEMPTS} attempts. "
            "Run 'python run.py --mode relogin' to try again."
        )

    async def _verify_session_on_page(self, page: Page) -> bool:
        """Verifies login state on an already-open page."""
        from src.collection.fiverr_selectors import LOGGED_IN_INDICATOR, LOGGED_IN_FALLBACK
        try:
            element = await page.query_selector(LOGGED_IN_INDICATOR)
            if element is None:
                element = await page.query_selector(LOGGED_IN_FALLBACK)
            return element is not None
        except Exception:
            return False

    # ─── Browser configuration ───────────────────────────────────────────────

    def _browser_args(self) -> list[str]:
        """
        Playwright Chromium launch arguments.
        Reduces automation fingerprints that modern detection tools look for.
        """
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

    def _context_options(self) -> dict:
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
```

---

## Context Reuse Pattern

All collection modules receive a `SessionManager` instance and call `new_page()` / `close_page()` on it. They do NOT store or reuse pages between calls — each navigation gets a fresh page.

```python
# Pattern used by all collection modules:

async def collect_gig_detail(gig_url: str, session_manager: SessionManager) -> dict:
    page = await session_manager.new_page()
    try:
        await page.goto(gig_url, wait_until="domcontentloaded", timeout=30_000)
        # ... collection logic ...
        return collected_data
    except Exception as e:
        log.error(f"Error collecting {gig_url}: {e}")
        raise
    finally:
        await session_manager.close_page(page)  # Always close, even on error
```

---

## Page Lifecycle Rules

1. Pages are created via `session_manager.new_page()` — never `browser.new_page()` directly
2. Pages are always closed in a `finally` block — no page is left open on error
3. At most N pages are open simultaneously (N = max concurrent jobs for the current stage)
4. In v1 (sequential execution): max 1 page open at a time
5. Pages are not reused across different gig URLs — each URL gets a new page
6. The browser context is shared across all pages in a run — cookies/session persist

---

## Error Boundaries

The Session Manager catches session-level errors. Individual collection module errors bubble up to the job queue.

| Error Type | Caught By | Behavior |
|---|---|---|
| Session expired (no login indicator) | Session Manager | Trigger `_headed_login_flow()`, retry |
| Playwright crash (browser process dies) | Session Manager | Re-launch browser, restore session, return new context |
| Login verification failure (max attempts) | Session Manager | Raise `SessionLoginError` — job fails, run paused |
| Page navigation timeout | Collection module | Retry job (handled by retry policy) |
| Gig page 404 | Collection module | Mark DEAD_LETTER, do not retry |
| Selector not found | Collection module | Store null for that field, continue |
| Session file permission error | Session Manager | Log warning, continue (best-effort security) |
