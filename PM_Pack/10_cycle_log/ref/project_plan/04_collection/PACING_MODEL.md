# Pacing Model
# Fiverr Research System — Wave 4

**Document Status:** Complete
**Wave:** 4 — Collection Engine Design
**Purpose:** Complete pacing delay tables, jitter formula, PacingManager class spec, adaptive pacing on 429 errors, human event timing, run-time pacing log, and per-niche pacing overrides.

---

## Pacing Design Principles

1. Every outbound request waits a minimum of `base_delay_seconds` before execution
2. Jitter adds randomness: actual delay = base + uniform_random(0, jitter_seconds)
3. Hourly rate limits cap requests regardless of delay timing
4. 429 responses trigger adaptive pacing — delay increases for remainder of run
5. Human event timing (scroll, hover, dwell) is separate from inter-request pacing
6. All pacing parameters are in config.yaml — no hardcoded values in code
7. Per-niche pacing overrides are supported for special cases

---

## Pacing Delay Table (Default Configuration)

| Source | Base Delay (s) | Jitter (s) | Max/Hour | Human Events | Effective Rate |
|---|---|---|---|---|---|
| fiverr_search | 4.0 | 3.0 | 60 | Yes | ~10–12 requests/hr |
| fiverr_gig_detail | 6.0 | 4.0 | 40 | Yes | ~7–8 requests/hr |
| fiverr_seller_profile | 5.0 | 3.0 | 40 | Yes | ~9–10 requests/hr |
| google_trends | 10.0 | 5.0 | 20 | No | ~4–5 requests/hr |
| reddit_api | 2.0 | 1.0 | 60 | No | ~25–30 requests/hr |
| youtube | 3.0 | 2.0 | 60 | No | ~17–20 requests/hr |
| external_default | 3.0 | 2.0 | 100 | No | ~22–25 requests/hr |

### Effective Rate Calculation
```
effective_requests_per_hour = min(
    3600 / (base_delay + jitter/2),  # based on average delay
    max_requests_per_hour            # hard cap
)
```

---

## Jitter Formula Implementation

```python
# src/collection/pacing_manager.py

import random
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict

class PacingManager:
    """
    Manages request rate limiting and delay enforcement for all collection sources.
    Thread-safe for async use within a single event loop.
    """

    def __init__(self, config):
        self.config = config
        # Tracks timestamps of recent requests per source
        self._request_log: dict[str, list[datetime]] = defaultdict(list)
        # Adaptive delay multipliers (increased when 429s are encountered)
        self._adaptive_multipliers: dict[str, float] = defaultdict(lambda: 1.0)
        # Per-run delay increase log
        self._adaptive_events: list[dict] = []

    async def wait(self, source: str, niche_id: str | None = None) -> float:
        """
        Enforces pacing delay for the given source.
        Returns the actual delay applied (for logging).

        Args:
            source: pacing config key (e.g., "fiverr_search")
            niche_id: optional niche override (checks niche-specific pacing first)
        """
        pacing = self._get_pacing_config(source, niche_id)
        adaptive_mult = self._adaptive_multipliers[source]

        # Step 1: Enforce hourly rate limit
        await self._enforce_rate_limit(source, pacing.max_requests_per_hour)

        # Step 2: Calculate base delay with jitter and adaptive multiplier
        base = pacing.base_delay_seconds * adaptive_mult
        jitter = random.uniform(0, pacing.jitter_seconds * adaptive_mult)
        total_delay = base + jitter

        # Step 3: Sleep
        await asyncio.sleep(total_delay)

        # Step 4: Log this request
        self._request_log[source].append(datetime.utcnow())
        self._clean_old_requests(source)

        return total_delay

    async def _enforce_rate_limit(self, source: str, max_per_hour: int):
        """Waits if hourly request limit has been reached."""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=1)

        # Remove requests older than 1 hour
        self._request_log[source] = [
            t for t in self._request_log[source] if t > cutoff
        ]

        if len(self._request_log[source]) >= max_per_hour:
            # Calculate how long to wait for the oldest request to age out
            oldest = self._request_log[source][0]
            wait_until = oldest + timedelta(hours=1)
            wait_seconds = max(0, (wait_until - now).total_seconds()) + 1
            print(f"\n[PACING] Rate limit reached for {source}. Waiting {wait_seconds:.0f}s.")
            await asyncio.sleep(wait_seconds)

    def _clean_old_requests(self, source: str):
        """Removes request timestamps older than 1 hour from log."""
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self._request_log[source] = [
            t for t in self._request_log[source] if t > cutoff
        ]

    def _get_pacing_config(self, source: str, niche_id: str | None):
        """Returns pacing config, checking niche override first."""
        # Check niche-level override
        if niche_id and hasattr(self.config, "niches"):
            niche = next((n for n in self.config.niches if n.id == niche_id), None)
            if niche and hasattr(niche, "pacing_overrides") and source in niche.pacing_overrides:
                return niche.pacing_overrides[source]
        # Fall back to global config
        return getattr(self.config.pacing, source, self.config.pacing.external_default)

    def on_rate_limit_error(self, source: str):
        """
        Called when a 429 response is received for a source.
        Implements adaptive pacing: increases delay by 50% for remainder of run.
        """
        current_mult = self._adaptive_multipliers[source]
        new_mult = min(current_mult * 1.5, 5.0)  # Cap at 5× original delay
        self._adaptive_multipliers[source] = new_mult

        event = {
            "source": source,
            "old_multiplier": current_mult,
            "new_multiplier": new_mult,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"429 encountered for {source}. Delay increased to {new_mult:.1f}× original."
        }
        self._adaptive_events.append(event)
        print(f"\n[ADAPTIVE PACING] {event['message']}")

    def get_adaptive_events(self) -> list[dict]:
        """Returns all adaptive pacing events for run summary logging."""
        return self._adaptive_events

    def get_request_stats(self) -> dict:
        """Returns per-source request counts for run summary."""
        return {source: len(times) for source, times in self._request_log.items()}
```

---

## Adaptive Pacing Rules (OQ-004 Resolution — Google Trends Rate Limits)

Based on known pytrends community experience, Google Trends rate limits work as follows:

| Situation | Observed Behavior | Recommended Response |
|---|---|---|
| Normal use (10s delay) | Rarely 429 for small keyword sets (<100) | Default config is safe |
| Medium volume (50–200 keywords) | Occasional 429s, especially in first hour | 10s base delay prevents most |
| High volume (200+ keywords) | Frequent 429s without adequate delay | Increase to 15–20s base |
| After a 429 | Next request same speed → likely another 429 | Pause 10 min minimum |
| Residential IP | Lower rate limiting than datacenter | No-proxy approach is correct |

**Recommended safe defaults (already in config.yaml):**
```yaml
pacing:
  google_trends:
    base_delay_seconds: 10    # Safe for up to ~150 keywords/session
    jitter_seconds: 5         # Critical — prevents pattern detection
    max_requests_per_hour: 20 # Hard cap well below observed limits
    rate_limit_pause_minutes: 10  # Pause when 429 received
```

**Adaptive pacing trigger sequence for Google Trends:**
```
1st 429: pause 10 min → increase delay by 50% (10s → 15s base)
2nd 429: pause 10 min → increase delay by 50% (15s → 22.5s base)
3rd 429: mark remaining Trends jobs as DEAD_LETTER → apply confidence deductions
         log: "Google Trends rate limiting too aggressive. Reducing collection scope."
```

---

## Human Event Timing Tables

Human events are applied on all Fiverr browser sessions (not on API sources). Timing is randomized within these ranges:

### read_delay — After Page Load
Applied after every page navigation on Fiverr.

| Config Key | Min (s) | Max (s) | Notes |
|---|---|---|---|
| fiverr_search | 2.0 | 5.0 | Quick browsing pace |
| fiverr_gig_detail | 4.0 | 10.0 | Longer — simulates reading description |
| fiverr_seller_profile | 3.0 | 8.0 | Medium — browsing profile |

```python
async def read_delay(page: Page, source: str, config):
    pacing = getattr(config.pacing, source, config.pacing.external_default)
    delay = random.uniform(
        pacing.get("human_read_min", 2.0),
        pacing.get("human_read_max", 6.0)
    )
    await asyncio.sleep(delay)
```

### random_scroll — After Read Delay
Simulates reading content by scrolling.

| Behavior | Probability | Distance | Speed |
|---|---|---|---|
| Short scroll (200–400px) | 40% | 200–400px | 0.3–0.8s total |
| Medium scroll (400–700px) | 35% | 400–700px | 0.5–1.2s total |
| Long scroll (700–1200px) | 20% | 700–1200px | 0.8–2.0s total |
| No scroll | 5% | 0 | 0s |

```python
async def random_scroll(page: Page):
    scroll_type = random.choices(
        ["short", "medium", "long", "none"],
        weights=[40, 35, 20, 5]
    )[0]

    if scroll_type == "none":
        return

    distances = {"short": (200, 400), "medium": (400, 700), "long": (700, 1200)}
    min_d, max_d = distances[scroll_type]
    total_distance = random.randint(min_d, max_d)
    steps = random.randint(3, 8)
    step_size = total_distance // steps

    for _ in range(steps):
        await page.mouse.wheel(0, step_size)
        await asyncio.sleep(random.uniform(0.08, 0.35))
```

### hover_before_click — Before Every Click
Simulates natural mouse movement.

| Pause Before Click | Range |
|---|---|
| Hover pause | 100–400ms |
| Post-hover pause before click | 50–150ms |

```python
async def hover_before_click(page: Page, selector: str):
    element = await page.wait_for_selector(selector, timeout=10_000)
    await element.hover()
    await asyncio.sleep(random.uniform(0.1, 0.4))  # hover pause
    await asyncio.sleep(random.uniform(0.05, 0.15))  # pre-click pause
    await element.click()
```

### maybe_dead_navigate — Occasional Detour
Loads an adjacent Fiverr page before the target to vary navigation patterns.

| Probability | Detour URLs |
|---|---|
| 15% on gig detail pages | fiverr.com/categories, fiverr.com/explore/gigs |
| 10% on seller profiles | fiverr.com/categories, fiverr.com |
| 5% on search pages | fiverr.com (homepage) |

```python
DETOUR_URLS = [
    "https://www.fiverr.com/categories",
    "https://www.fiverr.com/explore/gigs",
    "https://www.fiverr.com",
]

async def maybe_dead_navigate(page: Page, probability: float = 0.15):
    if random.random() < probability:
        url = random.choice(DETOUR_URLS)
        await page.goto(url, wait_until="domcontentloaded", timeout=15_000)
        await asyncio.sleep(random.uniform(1.5, 4.0))
```

### random_viewport — Per Session
Called once per browser context creation.

```python
def random_viewport() -> dict:
    widths  = [1280, 1366, 1440, 1536, 1600, 1920]
    heights = [720,  768,  800,  900,  1050, 1080]
    return {
        "width":  random.choice(widths),
        "height": random.choice(heights),
    }
```

---

## Per-Niche Pacing Overrides

PRD (the primary niche) may warrant slightly more conservative pacing than Tier 2 niches to reduce any risk of pattern detection on the most-collected niche:

```yaml
# config.yaml — per-niche pacing override example
niches:
  - id: prd_ai_saas
    # ... other fields ...
    pacing_overrides:
      fiverr_gig_detail:
        base_delay_seconds: 8     # 2s more conservative than default (6s)
        jitter_seconds: 5
        max_requests_per_hour: 35

  - id: python_automation
    # No pacing_overrides — uses global defaults
```

---

## Run-Time Pacing Log

Every request is logged for audit trail and performance analysis:

```python
# Added to PacingManager.wait() after sleeping:
await pacing_log.write({
    "timestamp": datetime.utcnow().isoformat(),
    "source": source,
    "niche_id": niche_id,
    "delay_applied": total_delay,
    "adaptive_multiplier": adaptive_mult,
    "hourly_request_count": len(self._request_log[source]),
})
```

Pacing logs are written to `data/logs/pacing_{run_id}.jsonl` (one JSON object per line). This file is used by:
- Run summary: reports average delay per source, total requests per source
- Dashboard LLM costs view: correlates collection volume with API spend
- Developer debugging: shows exactly when and how long each request waited
