# Collection Architecture
# Fiverr Research System — Wave 2

**Document Status:** Complete
**Wave:** 2 — Technical Architecture
**Purpose:** Playwright session manager design, human-event simulation module, niche depth dispatcher, proxy layer as pluggable interface, and session security.

---

## Session Manager Design (src/collection/session_manager.py)

The Session Manager is the single entry point for all Playwright browser operations. No collection module creates its own browser context — all receive a verified context from the Session Manager.

### Session Manager Responsibilities

1. On every run: check for saved session file at `data/sessions/fiverr_session.json`
2. If found: load into a new browser context, navigate to Fiverr, verify session validity
3. If expired or invalid: trigger headed re-login flow, save new session, return verified context
4. If not found: trigger headed first-run login flow, save session, return verified context
5. Attach Human Events module to every new page created from the context
6. On run completion: call `context.close()` and release browser resources

### Session Lifecycle State Machine

```
START
  │
  ▼
Check data/sessions/fiverr_session.json exists?
  │
  ├── NO ──────────────────────────────────────────────────────┐
  │                                                            │
  ▼                                                            ▼
Load storage_state from file                          Launch headed Playwright
  │                                                   Navigate to fiverr.com/login
  ▼                                                   Print terminal prompt:
Create browser_context(storage_state=file)            "Log in to Fiverr. Press Enter."
  │                                                   Wait for Enter
  ▼                                                   Verify login state
Navigate to fiverr.com                                  │
Check for logged-in indicator                       ┌──┴──────────────┐
  │                                             VERIFIED          NOT VERIFIED
  ├── VALID ──────────────────────┐                 │                 │
  │                               │                 ▼                 ▼
  ├── EXPIRED/INVALID ────────┐   │     Save storage_state()    Print error,
                              │   │     to session file         retry prompt
                              ▼   │     chmod 600               │
                     Launch headed│           │                  │
                     re-login     │           └──────────────────┘
                     Save new     │                   │
                     session      │                   ▼
                              │   │        Close headed browser
                              │   │        Launch headless context
                              │   │        Load saved session
                              └───┘               │
                                                  ▼
                                        VALID HEADLESS CONTEXT
                                        Attach human_events to all pages
                                              │
                                              ▼
                                        Return context to caller
```

### Session Manager API

```python
class SessionManager:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.session_file = Path(config.fiverr.session_file)
        self._context: BrowserContext | None = None
        self._browser: Browser | None = None
        self._playwright: Playwright | None = None

    async def get_context(self) -> BrowserContext:
        """Returns a verified, authenticated Playwright browser context."""
        if self._context is not None:
            return self._context
        self._context = await self._load_or_login()
        return self._context

    async def new_page(self) -> Page:
        """Creates a new page with human events attached."""
        context = await self.get_context()
        page = await context.new_page()
        attach_human_events(page, self.config.pacing)
        return page

    async def close(self):
        """Gracefully closes browser resources."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def force_relogin(self):
        """Forces a headed re-login, overwrites session file."""
        await self.close()
        self._context = await self._headed_login_flow()

    async def _load_or_login(self) -> BrowserContext:
        if self.session_file.exists():
            context = await self._load_session()
            if await self._verify_session(context):
                return context
            await context.close()
        return await self._headed_login_flow()

    async def _load_session(self) -> BrowserContext:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        return await self._browser.new_context(
            storage_state=str(self.session_file),
            viewport=random_viewport(),
            user_agent=random_user_agent(),
            locale="en-US",
            timezone_id="America/Chicago",
        )

    async def _verify_session(self, context: BrowserContext) -> bool:
        page = await context.new_page()
        await page.goto("https://www.fiverr.com", wait_until="domcontentloaded")
        # Check for logged-in indicator (seller dashboard link or nav avatar)
        logged_in = await page.query_selector("[data-testid='user-menu-button']")
        await page.close()
        return logged_in is not None

    async def _headed_login_flow(self) -> BrowserContext:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=False)
        context = await self._browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.fiverr.com/login")
        print("\n" + "="*60)
        print("ACTION REQUIRED: Please log in to Fiverr in the browser window.")
        print("Complete any 2FA or CAPTCHA, then press Enter here to continue.")
        print("="*60)
        input()
        verified = await self._verify_session(context)
        if not verified:
            raise SessionLoginError("Login verification failed. Please try again.")
        await context.storage_state(path=str(self.session_file))
        self.session_file.chmod(0o600)
        await page.close()
        # Switch to headless for remainder of run
        await context.close()
        await self._browser.close()
        return await self._load_session()
```

---

## Human Events Module (src/collection/human_events.py)

The Human Events module attaches behavioral simulation to Playwright pages to mimic natural human browsing on Fiverr.

### The 5 Human Behaviors

**1. random_scroll — Simulates reading after page load**
```python
async def random_scroll(page: Page, config: PacingConfig):
    """Scroll down 200–600px at random speed after page load."""
    scroll_distance = random.randint(200, 600)
    scroll_steps = random.randint(3, 8)
    for _ in range(scroll_steps):
        await page.mouse.wheel(0, scroll_distance // scroll_steps)
        await asyncio.sleep(random.uniform(0.1, 0.4))
```

**2. hover_before_click — Simulates mouse movement before interaction**
```python
async def hover_before_click(page: Page, selector: str):
    """Move mouse to element, pause, then click."""
    element = await page.wait_for_selector(selector)
    await element.hover()
    await asyncio.sleep(random.uniform(0.1, 0.4))  # 100–400ms hover pause
    await element.click()
```

**3. read_delay — Simulates reading time on page**
```python
async def read_delay(page: Page, config: PacingConfig):
    """Pause 2–8 seconds (configurable) after page load."""
    base = config.pacing.fiverr_gig_detail.base_delay_seconds
    jitter = config.pacing.fiverr_gig_detail.jitter_seconds
    delay = base + random.uniform(0, jitter)
    await asyncio.sleep(delay)
```

**4. dead_navigation — Occasionally loads adjacent page before target**
```python
async def maybe_dead_navigate(page: Page, probability: float = 0.15):
    """With 15% probability, load an adjacent Fiverr page first."""
    if random.random() < probability:
        dead_urls = [
            "https://www.fiverr.com/categories",
            "https://www.fiverr.com/explore/gigs",
        ]
        await page.goto(random.choice(dead_urls), wait_until="domcontentloaded")
        await asyncio.sleep(random.uniform(1.5, 4.0))
```

**5. random_viewport — Randomizes browser window size**
```python
def random_viewport() -> dict:
    """Returns a random but realistic viewport size."""
    widths = [1280, 1366, 1440, 1536, 1920]
    heights = [720, 768, 800, 900, 1080]
    return {
        "width": random.choice(widths),
        "height": random.choice(heights)
    }
```

### attach_human_events — The main attachment function

```python
def attach_human_events(page: Page, config: PacingConfig):
    """Attaches human event simulation to a Playwright page."""
    page._human_config = config  # Store config on page for use in event handlers

    async def on_load(response):
        if "fiverr.com" in response.url:
            await maybe_dead_navigate(page)
            await read_delay(page, config)
            await random_scroll(page, config)

    page.on("response", on_load)
```

### User Agent Rotation

```python
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

def random_user_agent() -> str:
    return random.choice(USER_AGENTS)
```

---

## Niche Depth Dispatcher (src/core/niche_depth_dispatcher.py)

The Niche Depth Dispatcher reads the current depth for each niche and produces NicheJobSpec objects that determine exactly what every downstream module should do for that niche.

### Dispatcher Logic

```python
class NicheDepthDispatcher:
    def __init__(self, config: SystemConfig, db_session):
        self.config = config
        self.db = db_session

    def dispatch(self) -> list[NicheJobSpec]:
        """
        Reads current depth from niche_configs table.
        Config.yaml depth is the initial value; niche_configs table overrides it at runtime.
        Returns a list of NicheJobSpec objects, one per active niche.
        """
        specs = []
        for niche in self.config.niches:
            # Runtime depth from database (auto-promotion may have changed it)
            runtime_depth = self._get_runtime_depth(niche.id)
            # Gate check: if gate is enabled and not passed, cap depth
            effective_depth = self._apply_gate(niche, runtime_depth)

            specs.append(NicheJobSpec(
                niche_id=niche.id,
                slot=niche.slot,
                tier=niche.tier,
                depth=effective_depth,
                top_n_gigs=DEPTH_TO_TOP_N_GIGS[effective_depth],
                top_n_sellers=DEPTH_TO_TOP_N_SELLERS[effective_depth],
                priority=self._assign_priority(niche.slot),
                run_gig_quality_llm=(effective_depth in ("standard", "full")),
                run_competitor_synthesis=(effective_depth in ("standard", "full")),
                run_recommendations=(
                    effective_depth == "full" or
                    (effective_depth == "standard" and niche.llm.recommendation_generation)
                ),
                score_depth=DEPTH_TO_SCORE_DEPTH[effective_depth],
            ))

        return sorted(specs, key=lambda s: PRIORITY_ORDER[s.priority])

    def _apply_gate(self, niche, runtime_depth: str) -> str:
        """If niche has a gate and gate is not passed, cap depth."""
        if niche.gating.enabled and not niche.gating.gate_passed:
            if niche.slot == 4:     # MCP stays at feasibility even when gated
                return "feasibility"
            return "keyword_only"
        return runtime_depth

DEPTH_TO_TOP_N_GIGS    = {"full": 20, "standard": 10, "feasibility": 5, "keyword_only": 0}
DEPTH_TO_TOP_N_SELLERS = {"full": 20, "standard": 10, "feasibility": 5, "keyword_only": 0}
DEPTH_TO_SCORE_DEPTH   = {"full": "all_11", "standard": "all_11",
                           "feasibility": "scores_1_to_5", "keyword_only": "scores_1_to_3"}
PRIORITY_ORDER         = {"CRITICAL": 0, "HIGH": 1, "STANDARD": 2, "LOW": 3, "BACKGROUND": 4}
```

---

## Proxy Layer (src/collection/proxy_layer.py)

The proxy layer is designed as a pluggable interface for v1 (no-proxy, direct residential IP) with a clear extension point for v2 (residential or datacenter proxy rotation).

### v1 — No Proxy (Default)

For v1, the proxy layer is a pass-through. All collection uses the user's direct internet connection (home or office residential IP) combined with the authenticated Fiverr session and natural-rate pacing. This is the safest and simplest approach for a solo developer running weekly research runs.

```python
class ProxyLayer:
    """
    v1: No-proxy pass-through.
    v2: Override get_proxy() to return rotating proxy configs.
    """
    def __init__(self, config: SystemConfig):
        self.config = config
        self.proxy_enabled = getattr(config, "proxy", {}).get("enabled", False)

    def get_proxy(self) -> dict | None:
        """Returns proxy config dict for Playwright, or None for no proxy."""
        if not self.proxy_enabled:
            return None
        # v2: return {"server": "http://proxy:port", "username": "...", "password": "..."}
        return None

    def get_httpx_proxy(self) -> str | None:
        """Returns proxy URL for httpx, or None for no proxy."""
        if not self.proxy_enabled:
            return None
        return None

    def report_failure(self, proxy: dict):
        """v2: Report a failed proxy for rotation logic."""
        pass  # No-op in v1
```

### v2 Proxy Extension (Interface Design)

When ready to add proxy rotation in v2, override ProxyLayer with a concrete implementation:

```python
class RotatingResidentialProxyLayer(ProxyLayer):
    """
    v2 implementation using a residential proxy provider
    (e.g., Bright Data, Oxylabs, Smartproxy).
    """
    def __init__(self, config: SystemConfig):
        super().__init__(config)
        self.proxy_list = self._load_proxy_list()
        self.current_index = 0
        self.failure_counts: dict[str, int] = {}

    def get_proxy(self) -> dict:
        proxy = self.proxy_list[self.current_index % len(self.proxy_list)]
        self.current_index += 1
        return {
            "server": proxy["server"],
            "username": proxy["username"],
            "password": proxy["password"],
        }

    def report_failure(self, proxy: dict):
        key = proxy["server"]
        self.failure_counts[key] = self.failure_counts.get(key, 0) + 1
        if self.failure_counts[key] >= 3:
            self.proxy_list = [p for p in self.proxy_list if p["server"] != key]
            log.warning(f"Proxy {key} removed after 3 failures")
```

### Proxy Configuration in config.yaml (v2 Ready)

```yaml
# config.yaml — proxy section (v1: disabled)
proxy:
  enabled: false                    # Set to true in v2 when proxies are added
  provider: none                    # none | brightdata | oxylabs | smartproxy | custom
  rotation_mode: round_robin        # round_robin | random | sticky_session
  proxy_list_file: data/proxies.txt # Optional: file with proxy list
  sticky_session_duration: 300      # Seconds to keep same proxy per niche (for sticky mode)
```

---

## Session Security

All session-related security practices are enforced by the Session Manager and documented here for implementation reference.

### File System Security

```bash
# Session file location (within .gitignore)
data/sessions/fiverr_session.json

# Permissions set after every save
chmod 600 data/sessions/fiverr_session.json
# Owner read/write only — no group or world access

# .gitignore entries (required)
data/sessions/
.env
*.env
data/db/
data/checkpoints/
data/raw/
```

### .env File Contents

```bash
# .env — secrets only, never in config.yaml
OPENAI_API_KEY=sk-...
# Fiverr credentials stored here ONLY for reference during manual login
# The system does NOT use these programmatically to auto-login
# They exist only as a reminder for the user during the headed login flow
FIVERR_EMAIL=user@example.com
```

### Session Data Contents

The Playwright `storage_state()` file contains:
- Browser cookies (session tokens, auth tokens)
- localStorage data (Fiverr client-side session state)
- Origin-scoped storage

This file grants the same access as a logged-in browser session and must be treated as a credential. It is never logged, never transmitted, and never included in exports or reports.

### Session Expiry Handling

Fiverr sessions typically expire after 30–90 days of inactivity. The Session Manager detects expiry on every run by checking for the logged-in UI indicator after loading the session. When expiry is detected:
1. A clear terminal message is printed: "Fiverr session expired. Launching re-login flow."
2. Headed browser opens for manual re-login
3. New session is saved, overwriting the old file
4. Run continues headlessly

---

## Pacing Implementation Detail

Every collection module applies pacing through a shared `PacingManager` utility:

```python
class PacingManager:
    def __init__(self, config: PacingConfig):
        self.config = config
        self._request_counts: dict[str, list[datetime]] = {}

    async def wait(self, source: str):
        """
        Apply pacing delay for the given source.
        Enforces: base delay + random jitter + hourly rate limit.
        """
        pacing = getattr(self.config, source, self.config.external_default)

        # Enforce hourly rate limit
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=1)
        self._request_counts.setdefault(source, [])
        self._request_counts[source] = [
            t for t in self._request_counts[source] if t > cutoff
        ]
        if len(self._request_counts[source]) >= pacing.max_requests_per_hour:
            wait_seconds = (self._request_counts[source][0] - cutoff).seconds + 1
            log.info(f"Rate limit reached for {source}. Waiting {wait_seconds}s.")
            await asyncio.sleep(wait_seconds)

        # Apply base delay + jitter
        delay = pacing.base_delay_seconds + random.uniform(0, pacing.jitter_seconds)
        await asyncio.sleep(delay)

        self._request_counts[source].append(datetime.utcnow())
```

Usage in every collection module:

```python
# Before every Fiverr page request
await pacing_manager.wait("fiverr_gig_detail")
await page.goto(gig_url)

# Before every Google Trends request
await pacing_manager.wait("google_trends")
trends_data = pytrends.interest_over_time()
```
