# Source Connectors
# Fiverr Research System — Wave 3

**Document Status:** Complete
**Wave:** 3 — Data Schema and Source Design
**Purpose:** All 6 source connectors — method, authentication, rate limits, fields returned, TTL, retry behavior, known failure modes, and fallback impact.

---

## Connector 1 — Fiverr Search (Playwright, Authenticated)

**Method:** Playwright browser automation (async)
**Authentication:** User's own Fiverr account via saved Playwright storage_state session
**Stage:** 3

### Connection Details
```python
# Session loaded by Session Manager before collection begins
context = await session_manager.get_context()
page = await context.new_page()
# Human events attached automatically
url = f"https://www.fiverr.com/search/gigs?query={urllib.parse.quote(keyword_text)}"
await page.goto(url, wait_until="networkidle")
```

### Rate Limits
| Limit Type | Value | Source |
|---|---|---|
| Configured max | 60 requests/hour | config.yaml pacing.fiverr_search.max_requests_per_hour |
| Base delay | 4 seconds | config.yaml pacing.fiverr_search.base_delay_seconds |
| Jitter | 0–3 seconds | config.yaml pacing.fiverr_search.jitter_seconds |
| Effective rate | ~10–12 keywords/hour | Based on 4–7s average delay |

### Fields Returned (from search result cards)
```
total_result_count        Integer  Total gig count shown at top of results page
pagination_depth          Integer  Number of result pages available

Per gig card (stored in gig_cards JSON array):
  gig_url                 String   Full URL to gig detail page
  gig_title               String   Gig title as shown in card
  seller_username         String   Seller's Fiverr username
  seller_level            String   "No Level" | "Level 1" | "Level 2" | "Top Rated" | "Pro"
  rating_visible          Float    Star rating shown in card (e.g., 4.9)
  review_count_visible    Integer  Review count if shown as exact number
  review_count_abbreviated Boolean True when Fiverr shows "1k+" instead of exact count
  starting_price          Float    "Starting at $XX" price
  delivery_time           String   "3 days" | "1 day" etc.
  tags_visible            Array    Tags shown in card (up to 3 usually)
  sponsored_flag          Boolean  Whether this is a promoted/sponsored result
  orders_in_queue_visible Integer  If visible in card (often null — see OQ-003 note)
  position                Integer  1-based position in search results
```

### OQ-002 Resolution — Review Count Visibility
Manual inspection finding: Fiverr shows review count in search result cards as an exact integer for gigs with fewer than ~1,000 reviews. For gigs above ~1,000 reviews, Fiverr shows abbreviated text ("1k+", "2k+"). The `review_count_abbreviated` flag captures this. When abbreviated, the exact count is collected from the gig detail page (Stage 4) and stored in `gigs.review_count_exact`. The schema handles both cases — search card value in `gig_cards[].review_count_visible`, exact value in `gigs.review_count_exact`.

### OQ-003 Resolution — Orders in Queue
Manual inspection finding: The "orders in queue" badge appears inconsistently across Fiverr UI tests. It is present for some sellers at some times and absent for others. The field `orders_in_queue_visible` in gig_cards is collected when visible and stored as null when not shown. When null, the system uses `review_velocity_30d` as a proxy demand signal (estimated reviews received in the last 30 days, calculated from the distribution of review dates visible in review snippets). This proxy is calculated in Stage 7 and stored in `gig_quality_scores.review_velocity_30d`.

### TTL
- Search results: 72 hours (3 days)
- Re-collection triggered when `search_results.collected_at + ttl_hours < now()`

### Retry Behavior
| Error | Action |
|---|---|
| Playwright timeout (page load > 30s) | Retry 3× with 10s backoff |
| Playwright crash | Re-launch browser, restore session, retry |
| Fiverr session expired (no login indicator) | Trigger re-login flow, retry |
| Empty results page (0 gigs) | Log warning, mark keyword as low-demand, do not retry |
| CAPTCHA / bot challenge | Pause 30 minutes, retry; if persistent log as DEAD_LETTER |
| HTTP 5xx from Fiverr | Retry 3× with 30s backoff |

### Known Failure Modes
- **Session expiry:** Fiverr sessions typically last 30–90 days. Auto-detected and resolved by Session Manager.
- **UI experiments:** Fiverr regularly A/B tests their search results UI. CSS selectors for gig card elements may need updating if Fiverr changes their DOM structure. Selectors are stored in `config.yaml` (not hardcoded) to allow updates without code changes.
- **Geo-blocking:** Some Fiverr results vary by user location. The system uses the user's own residential IP, which provides consistent geo context.
- **Sponsored result inflation:** Some results are paid promotions. The `sponsored_flag` allows filtering these in analysis.

### Impact if Connector Fails
- **HIGH** — This is the core data source. If Fiverr search fails for a keyword, no downstream collection runs for that keyword. Confidence score reduced by 0.20 for affected keywords.

---

## Connector 2 — Fiverr Gig Detail (Playwright, Authenticated)

**Method:** Playwright browser automation (async)
**Authentication:** Same session as Connector 1
**Stage:** 4

### Connection Details
```python
page = await session_manager.new_page()
await page.goto(gig_url, wait_until="networkidle")
# Human events applied: read_delay, scroll, hover simulation
```

### Rate Limits
| Limit Type | Value |
|---|---|
| Configured max | 40 requests/hour |
| Base delay | 6 seconds |
| Jitter | 0–4 seconds |
| Effective rate | ~7–8 gigs/hour |

### Fields Returned
```
gig_title_full            String   Complete gig title from detail page
description_text          String   Full gig description (may be long-form)
packages                  Array    All package tiers: name, price, deliverables, delivery_days, revisions
gig_extras                Array    Add-on extras: name, price
tags                      Array    All 5 gig tags
faq_text                  String   Complete FAQ text
faq_entries               Array    Parsed Q&A pairs
video_present             Boolean  Whether a gig video is present
portfolio_count           Integer  Number of portfolio items
review_count_exact        Integer  Exact review count (bypasses abbreviated display)
rating_exact              Float    Exact star rating
review_snippets           Array    Visible review excerpts: reviewer, rating, snippet, date
orders_in_queue           Integer  If visible on detail page (often null)
thumbnail_url             String   URL of the gig thumbnail image
```

### Authenticated vs. Unauthenticated Differences (OQ-001 Direction)
Based on known Fiverr behavior, authenticated sessions may expose:
- Full description text (some descriptions may be truncated for guests)
- Complete FAQ (some FAQ entries may be hidden for guests)
- Seller response rate and response time (visible in sidebar when logged in)
- "Orders in queue" badge (more likely to appear for logged-in users, per Fiverr's own display logic)

The system collects all available fields in authenticated mode. Fields that differ between authenticated and unauthenticated views are flagged in `gigs.detail_collected` and tracked in the confidence score.

### TTL
- Top-ranked gigs (position 1–5): 72 hours (3 days)
- Other gigs: 120 hours (5 days)
- Configurable per depth tier in config.yaml

### Retry Behavior
Same as Connector 1, plus:
| Error | Action |
|---|---|
| Gig not found (404) | Mark as DEAD_LETTER, flag in search_results as deleted |
| Gig removed (410) | Same as 404 |
| Private/restricted gig | Log, skip, do not retry |

### Impact if Connector Fails
- **MEDIUM** — Without gig detail, scores 4–9 are degraded. Confidence reduced by 0.20. Scores 1–3 still available from search result data.

---

## Connector 3 — Fiverr Seller Profile (Playwright, Authenticated)

**Method:** Playwright browser automation (async)
**Authentication:** Same session as Connectors 1 and 2
**Stage:** 5

### Connection Details
```python
profile_url = f"https://www.fiverr.com/{seller_username}"
page = await session_manager.new_page()
await page.goto(profile_url, wait_until="networkidle")
```

### Rate Limits
| Limit Type | Value |
|---|---|
| Configured max | 40 requests/hour |
| Base delay | 5 seconds |
| Jitter | 0–3 seconds |

### Fields Returned
```
seller_username           String   Fiverr username
seller_level              String   No Level | Level 1 | Level 2 | Top Rated | Pro
member_since              String   "Jan 2022" (not exact date — Fiverr displays month/year)
response_time             String   "1 hour" | "a few hours" | "1 day"
response_rate             Integer  Percentage (e.g., 97)
languages                 Array    [{language, level}]
bio_text                  String   Full seller bio
total_reviews             Integer  Total reviews across all gigs
total_gigs                Integer  Total gigs listed
active_gig_titles         Array    All gig titles on seller's profile page
portfolio_count           Integer  Portfolio samples count
badges                    Array    [{badge_name, earned_date}]
```

### TTL
- 168 hours (7 days) — seller profiles change slowly

### Deduplication Logic
- If `sellers.collected_at + ttl_hours > now()`: skip, reuse existing record
- Deduplication across niches: a seller appearing in both PRD and AI Tool searches is visited once per TTL window

### Retry Behavior
Same as Connector 1.

### Impact if Connector Fails
- **LOW** — Seller-level authority scores and competitor synthesis are degraded. Confidence reduced by 0.10. Keyword scores still available.

---

## Connector 4 — Google Trends (pytrends / httpx)

**Method:** pytrends library (unofficial Google Trends API wrapper)
**Authentication:** None (public endpoint) — uses residential IP from user's machine
**Stage:** 6

### Connection Details
```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))
# Batch up to 5 keywords per request
pytrends.build_payload(
    kw_list=keyword_batch,   # max 5 keywords
    cat=0,                   # all categories
    timeframe="today 12-m",  # 12 months
    geo="",                  # worldwide
    gprop=""                 # web search
)
df = pytrends.interest_over_time()
```

### Rate Limits
| Limit Type | Value |
|---|---|
| Configured max | 20 requests/hour |
| Base delay | 10 seconds |
| Jitter | 0–5 seconds |
| Batch size | 5 keywords per request |
| Effective throughput | ~100 keywords/hour |
| 429 backoff | 10 minutes (then exponential: 20, 40, 60 min) |

### Fields Returned
```
Per keyword (from interest_over_time() DataFrame):
  trends_12mo_score         Float    0–100, normalized Google search interest over 12 months
  trends_3mo_score          Float    0–100, average for last 3 months
  trends_slope              String   Derived: RISING|FLAT|DECLINING|STRONGLY_RISING|STRONGLY_DECLINING
                                     (calculated from regression of weekly data points)
  trends_related_queries    Array    Top 10 rising and top 10 related queries from related_queries()
  trends_related_topics     Array    Top 5 rising and top 5 related topics from related_topics()
```

### Slope Calculation
```python
def calculate_slope(weekly_scores: list[float]) -> str:
    import numpy as np
    x = np.arange(len(weekly_scores))
    slope = np.polyfit(x, weekly_scores, 1)[0]
    if slope > 2.0:   return "STRONGLY_RISING"
    if slope > 0.5:   return "RISING"
    if slope > -0.5:  return "FLAT"
    if slope > -2.0:  return "DECLINING"
    return "STRONGLY_DECLINING"
```

### TTL
- 24 hours — Google Trends updates daily

### Retry Behavior
| Error | Action |
|---|---|
| HTTP 429 | Pause 10 minutes, retry; exponential backoff up to 60 minutes |
| HTTP 500 | Retry 3× with 30s backoff |
| Empty response (keyword has no data) | Store score = 0, confidence deduction 0.10 |
| pytrends TooManyRequestsError | Same as 429 |
| Connection timeout | Retry 3× with 15s backoff |

### Known Failure Modes
- **Aggressive rate limiting:** pytrends is an unofficial wrapper and Google rate-limits heavily. The 10-second base delay handles most cases. Extended 429s require longer pauses.
- **New keywords with no data:** Very new or very obscure keywords return empty DataFrames. Treated as score = 0 with a confidence deduction rather than an error.
- **Geo-specific results:** Worldwide results (geo="") are used by default. If US-specific results are preferred, set geo="US" in config — but this reduces comparability for Fiverr's global marketplace.
- **VPN/proxy interference:** Google may return CAPTCHAs if requests come from known VPN ranges. No-proxy mode (home residential IP) is the safest option.

### Impact if Connector Fails
- **MEDIUM** — Google Trends is a key Demand Score input (25% weight within demand) and a primary Trend Score input (40% weight). Confidence reduced by 0.15 per keyword when unavailable.

---

## Connector 5 — Reddit (praw / Reddit API)

**Method:** praw (Python Reddit API Wrapper) using official Reddit API
**Authentication:** Reddit API credentials (client_id, client_secret) stored in .env
**Stage:** 6

### Connection Details
```python
import praw

reddit = praw.Reddit(
    client_id=config.reddit.client_id,       # from .env
    client_secret=config.reddit.client_secret,
    user_agent="FiverrResearchBot/1.0",
    check_for_async=False
)

# Search relevant subreddits
for subreddit_name in niche_subreddits:
    results = reddit.subreddit(subreddit_name).search(
        query=keyword_text,
        sort="relevance",
        time_filter="year",
        limit=25
    )
```

### Subreddit Targets Per Niche
```yaml
# config.yaml niche-level reddit config
prd_ai_saas:
  reddit_subreddits: ["SaaS", "startups", "ProductManagement", "entrepreneur", "learnprogramming"]
python_automation:
  reddit_subreddits: ["Python", "learnpython", "automation", "programming", "webdev"]
ai_tool_llm:
  reddit_subreddits: ["LocalLLaMA", "OpenAI", "MachineLearning", "SideProject", "startups"]
ai_agent_development:
  reddit_subreddits: ["AIAssistants", "MachineLearning", "LocalLLaMA", "SideProject", "Python"]
workflow_automation:
  reddit_subreddits: ["n8n", "nocode", "Zapier", "automation", "selfhosted"]
python_web_scraping:
  reddit_subreddits: ["Python", "learnpython", "datasets", "webdev", "datascience"]
```

### Rate Limits
| Limit Type | Value |
|---|---|
| Reddit API official limit | 100 requests/minute (OAuth) |
| Configured max | 60 requests/hour (conservative) |
| Base delay | 2 seconds |
| Jitter | 0–1 seconds |

### Fields Returned (raw — before LLM processing)
```
reddit_post_count_90d     Integer  Posts found matching keyword in last 90 days across target subreddits
reddit_top_snippets       Array    [{subreddit, title, body_snippet, upvotes, created_utc}]
                                   Top 10 posts by relevance/upvotes
```

### LLM Processing (Stage 6, gpt-4o-mini)
After collection, gpt-4o-mini processes the `reddit_top_snippets` to extract:
```
reddit_demand_intent_score   Float  0–10: How frequently buyers express need for this service
reddit_intent_phrases        Array  Extracted phrases like "I need someone to...", "looking for..."
```

### TTL
- 72 hours (3 days) — Reddit post volume is relatively stable

### Retry Behavior
| Error | Action |
|---|---|
| praw.exceptions.APIException | Retry 2× with 5s backoff |
| prawcore.exceptions.TooManyRequests | Pause 60 seconds, retry |
| Subreddit not found | Skip that subreddit, continue with others |
| Private subreddit | Skip, log warning |
| No posts found | Store count = 0, intent score = 0 — not an error |

### Reddit API Setup (one-time)
User creates a Reddit app at reddit.com/prefs/apps:
- App type: "script"
- No redirect URI needed for script apps
- Store client_id and client_secret in .env as REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET

### Impact if Connector Fails
- **LOW** — Reddit signals contribute 10–15% of the Demand Score and provide LLM intent context. Confidence reduced by 0.05. Run continues normally.

---

## Connector 6 — YouTube (httpx, Search Result Count)

**Method:** httpx (lightweight HTTP) — Google/YouTube search result count only
**Authentication:** None (public endpoint)
**Stage:** 6

### Connection Details
```python
import httpx

# Collect YouTube search result count for keyword
response = await httpx_client.get(
    "https://www.youtube.com/results",
    params={"search_query": keyword_text},
    headers={"User-Agent": random_user_agent()},
    follow_redirects=True,
    timeout=15
)
# Parse result count from response HTML
# YouTube shows "About X,XXX results" near the top of results page
```

### Rate Limits
| Limit Type | Value |
|---|---|
| Configured max | 60 requests/hour |
| Base delay | 3 seconds |
| Jitter | 0–2 seconds |

### Fields Returned
```
youtube_result_count    Integer  Approximate number of YouTube videos matching the keyword
                                 (used as a secondary demand proxy signal only)
```

### TTL
- 72 hours (3 days)

### Retry Behavior
| Error | Action |
|---|---|
| HTTP 429 | Pause 5 minutes, retry 2× |
| Parse failure (count not found in HTML) | Store null, log warning, do not retry |
| Connection timeout | Retry 2× with 10s backoff |

### Known Failure Modes
- **HTML structure changes:** YouTube occasionally changes the way result counts are displayed. If parsing fails, the field stores null and confidence is not reduced (YouTube is a minor signal).
- **Result count is approximate:** YouTube's result count is not precise and varies between requests. Used as a directional signal only.

### Impact if Connector Fails
- **LOW** — YouTube contributes 5% of the Demand Score. Null value reduces confidence by 0.03. No other downstream effects.

---

## Connector Summary Table

| Connector | Stage | Method | Auth | TTL | Impact if Fails | Retry Strategy |
|---|---|---|---|---|---|---|
| Fiverr Search | 3 | Playwright | Fiverr session | 72h | HIGH — blocks downstream | 3× exp backoff + session refresh |
| Fiverr Gig Detail | 4 | Playwright | Fiverr session | 72–120h | MEDIUM — degrades scores 4–9 | 3× exp backoff + session refresh |
| Fiverr Seller Profile | 5 | Playwright | Fiverr session | 168h | LOW — degrades competitor analysis | 3× exp backoff |
| Google Trends | 6 | pytrends/httpx | None | 24h | MEDIUM — 0.15 confidence deduction | 3× exp backoff + 10-min 429 pause |
| Reddit | 6 | praw | Reddit API key | 72h | LOW — 0.05 confidence deduction | 2× backoff, skip private subreddits |
| YouTube | 6 | httpx | None | 72h | LOW — 0.03 confidence deduction | 2× backoff, null on parse failure |
