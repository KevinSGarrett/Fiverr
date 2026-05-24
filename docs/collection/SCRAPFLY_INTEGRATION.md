# ScrapFly Integration

## Overview

Fiverr uses PerimeterX (HUMAN Security) bot protection that can block headless browser traffic in
Playwright-only collection runs. ScrapFly is a managed scraping API that handles those anti-bot
challenges and returns fully rendered HTML, which allows Stage 3/4/5 collection parsing to proceed.

## Architecture

The integration uses a three-layer transport design:

1. `src/collection/scrapfly_client.py`
   - `ScrapFlyClient` wraps the ScrapFly SDK.
   - Handles retries, pacing integration, and credit accounting.
2. `src/collection/http_fetcher.py`
   - Defines `PageFetcher` protocol plus Playwright/ScrapFly adapters.
   - Exposes `build_fetcher(...)` to choose the transport at runtime.
3. `src/collection/search_result_parser.py`
   - Parses Fiverr HTML into workflow-ready structured records.
   - Keeps extraction logic transport-agnostic.

## How to Enable

1. Create a ScrapFly account and generate an API key: [https://scrapfly.io/](https://scrapfly.io/)
2. Add the key to `.env`:
   - `SCRAPFLY_API_KEY=scp-live-your-key-here`
3. Enable ScrapFly in `config.yaml`:
   - `collection.scrapfly.enabled: true`
4. Run collection:
   - `python run.py collect-only`

## Cost Estimation

| Request profile | Typical credits |
| --- | ---: |
| `asp=true` + `render_js=true` (Fiverr default) | ~25 credits/request |
| 100,000 credit monthly plan | ~4,000 Fiverr page fetches/month |

## Fallback Behavior

When `collection.scrapfly.enabled: false`, the fetcher factory falls back to the existing Playwright
path. ScrapFly is optional; disabling it preserves prior behavior.

## Config Reference

Example `config.yaml` block:

```yaml
collection:
  scrapfly:
    # ScrapFly API settings for PerimeterX bypass on Fiverr collection pages.
    # Set enabled: true and add SCRAPFLY_API_KEY to .env to activate.
    # When enabled, ScrapFly replaces Playwright for page fetching (Stages 3/4/5/8).
    # All existing HTML parsers remain unchanged - only the HTTP transport changes.
    enabled: false
    asp: true
    render_js: true
    country: "US"
    auto_scroll: true
    max_retries: 3
    timeout_seconds: 60
    cost_budget_credits: null
```

Field notes:

- `enabled`: switches transport preference to ScrapFly.
- `asp`: enables anti-bot bypass mode (required for many Fiverr pages).
- `render_js`: executes page JavaScript for React-driven content.
- `country`: exit-country hint for geolocated fetching.
- `auto_scroll`: helps trigger lazy-loaded card content.
- `max_retries`: retry budget for transient API/network failures.
- `timeout_seconds`: per-request timeout.
- `cost_budget_credits`: optional hard stop budget for a run.

## Environment Variable Reference

- Variable: `SCRAPFLY_API_KEY`
- Expected format: `scp-live-...`
- Source: ScrapFly dashboard/API key page at [https://scrapfly.io/](https://scrapfly.io/)
- Storage: `.env` only (never commit real keys)

## Credit Monitoring

At runtime, inspect usage counters from the client:

```python
stats = client.stats
print(stats.total_requests, stats.total_credits_used)
```

The collection orchestrator also logs a session summary:

- `ScrapFly session: requests=N credits=N`
