# EPIC 02 — Collection Engine
# Fiverr Research System — Implementation To-Do

**Epic Owner:** Backend Engineer
**Source Specs:** Wave 4 (04_collection) + Wave 2 (02_architecture)
**Depends On:** Epic 01 (Foundation)
**Priority:** P0 — No data = no analysis
**Estimated Stories:** 18 | **Estimated Tasks:** 82

---

## Story 2.1 — Playwright Session Manager

| ID | Task | Type | Description |
|---|---|---|---|
| 2.1.1 | Create SessionManager class | TASK | `src/collection/session_manager.py` — Manages Playwright persistent browser context. Methods: `start()`, `stop()`, `get_page()`, `is_authenticated()` |
| 2.1.2 | Implement persistent context | TASK | Reuse browser profile with cookie persistence at `data/browser_profile/` |
| 2.1.3 | Implement auth detection | TASK | Check for logged-in indicators (avatar element, dashboard link) |
| 2.1.4 | Implement login flow | TASK | Navigate to login page, fill credentials, handle 2FA prompt, verify success |
| 2.1.5 | Implement unauth mode | TASK | Public-only collection mode — search results, gig cards, basic gig pages without login |
| 2.1.6 | Implement human-event simulation | TASK | Random mouse movements, scroll patterns, click delays, viewport jitter per PLAYWRIGHT_SESSION_DESIGN.md |
| 2.1.7 | Implement request interception | TASK | Block unnecessary resources (images, fonts, analytics) for speed. Configurable per workflow |
| 2.1.8 | Create session manager tests | TASK | Test startup, cookie persistence, auth detection, graceful shutdown |

---

## Story 2.2 — Fiverr Selectors

| ID | Task | Type | Description |
|---|---|---|---|
| 2.2.1 | Create fiverr_selectors.py | TASK | `src/collection/selectors.py` — All 30+ CSS selectors from PLAYWRIGHT_SESSION_DESIGN.md organized by page type |
| 2.2.2 | Implement search page selectors | TASK | GIG_CARD, GIG_TITLE, GIG_PRICE, SELLER_NAME, SELLER_LEVEL, REVIEW_COUNT, TOTAL_RESULTS, PAGINATION_NEXT |
| 2.2.3 | Implement gig detail selectors | TASK | PACKAGES, DESCRIPTION, FAQ, SELLER_BIO_LINK, GIG_EXTRAS, GALLERY, TAGS |
| 2.2.4 | Implement seller profile selectors | TASK | BIO_TEXT, MEMBER_SINCE, RESPONSE_TIME, LANGUAGES, PORTFOLIO, SKILLS, AVATAR |
| 2.2.5 | Implement visual selectors | TASK | THUMBNAIL, GALLERY_ITEM, VIDEO_INDICATOR, SELLER_AVATAR (Wave 11) |
| 2.2.6 | Create selector validation script | TASK | Utility that loads a Fiverr page and tests each selector, reporting which ones match |

---

## Story 2.3 — Pacing Manager

| ID | Task | Type | Description |
|---|---|---|---|
| 2.3.1 | Create PacingManager class | TASK | `src/collection/pacing.py` — Adaptive delay system per source. Source: PACING_MODEL.md |
| 2.3.2 | Implement base delays | TASK | Fiverr search: 3-5s, Gig detail: 2-4s, Seller profile: 2-4s, Google Trends: 10-15s, Reddit: 1-2s |
| 2.3.3 | Implement adaptive escalation | TASK | On 429/timeout: multiply delay by 1.5 (3-strike pattern for Google Trends) |
| 2.3.4 | Implement jitter | TASK | ±20% random jitter on all delays |
| 2.3.5 | Implement cooldown periods | TASK | After every 50 requests to same source, pause 30-60 seconds |
| 2.3.6 | Create pacing tests | TASK | Test delay ranges, escalation behavior, jitter distribution |

---

## Story 2.4 — Queue Processor

| ID | Task | Type | Description |
|---|---|---|---|
| 2.4.1 | Create QueueProcessor class | TASK | `src/collection/queue.py` — Sequential job processor. Methods: `enqueue(job)`, `process_next()`, `get_pending()`, `get_dead_letter()` |
| 2.4.2 | Implement job status management | TASK | States: PENDING → RUNNING → COMPLETED / FAILED / DEAD_LETTER |
| 2.4.3 | Implement retry logic | TASK | Max 3 retries per job. On 3rd failure → DEAD_LETTER. Exponential backoff between retries |
| 2.4.4 | Implement priority ordering | TASK | HIGH > STANDARD > LOW priority. Within same priority: FIFO |
| 2.4.5 | Implement dead letter queue | TASK | Failed jobs stored with error message + traceback for manual review |
| 2.4.6 | Implement job cancellation | TASK | Cancel pending jobs when a new run starts or mode changes |
| 2.4.7 | Create queue tests | TASK | Test ordering, retry, dead letter, cancellation |

---

## Story 2.5 — Checkpoint System

| ID | Task | Type | Description |
|---|---|---|---|
| 2.5.1 | Create CheckpointManager class | TASK | `src/collection/checkpoint.py` — Atomic checkpoint writes. Source: RETRY_AND_CHECKPOINT.md |
| 2.5.2 | Implement checkpoint write | TASK | JSON file at `data/checkpoints/{run_id}.json` containing: stage, job_index, timestamp, partial_results_count |
| 2.5.3 | Implement atomic write | TASK | Write to temp file then rename (prevents corruption on crash) |
| 2.5.4 | Implement checkpoint every N records | TASK | Configurable interval (default 50 records). DB commit + checkpoint write |
| 2.5.5 | Implement checkpoint read for resume | TASK | `load_checkpoint(run_id)` returns last stage + job index |
| 2.5.6 | Implement checkpoint cleanup | TASK | Delete checkpoint file after successful run completion |
| 2.5.7 | Create checkpoint tests | TASK | Test write/read roundtrip, atomic write on simulated crash, resume from checkpoint |

---

## Story 2.6 — Proxy Layer (Pluggable)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.6.1 | Create ProxyLayer interface | TASK | `src/collection/proxy.py` — Abstract base class with `get_proxy()`, `mark_failed(proxy)`, `mark_success(proxy)` |
| 2.6.2 | Create NoProxy implementation | TASK | Default implementation that returns None (direct connection). v1 default |
| 2.6.3 | Create RotatingProxy stub | TASK | Stub for future implementation — reads proxy list from config, rotates on failure |
| 2.6.4 | Wire proxy into SessionManager | TASK | SessionManager accepts optional proxy from ProxyLayer at context creation |

---

## Story 2.7 — Workflow: Keyword Expansion (Stage 2)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.7.1 | Create KeywordExpansionWorkflow | TASK | `src/collection/workflows/keyword_expansion.py` — Stage 2: expand seed keywords via Fiverr autocomplete |
| 2.7.2 | Implement autocomplete scraping | TASK | Type keyword prefix → capture autocomplete dropdown suggestions |
| 2.7.3 | Implement deduplication | TASK | Jaccard similarity 0.65 threshold against existing keywords |
| 2.7.4 | Implement intent classification stub | TASK | Mark intent_class=None for new keywords (classified in Stage 7) |
| 2.7.5 | Create expansion tests | TASK | Test dedup, autocomplete parsing, keyword insertion |

---

## Story 2.8 — Workflow: Fiverr Search (Stage 3)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.8.1 | Create FiverrSearchWorkflow | TASK | `src/collection/workflows/fiverr_search.py` — Stage 3: search each keyword, extract gig cards |
| 2.8.2 | Implement search URL construction | TASK | Build Fiverr search URL with keyword + category filter |
| 2.8.3 | Implement search result parsing | TASK | Extract: gig_id, title, seller, price, reviews, level from each gig card |
| 2.8.4 | Implement pagination | TASK | Follow pagination links up to configurable max pages (default 3 = 48 gigs) |
| 2.8.5 | Implement total_result_count extraction | TASK | Parse "X services available" header text |
| 2.8.6 | Store search_results table entries | TASK | Write SearchResult row per keyword-search |
| 2.8.7 | Store keyword_gig_associations | TASK | Create association rows for each gig found per keyword |
| 2.8.8 | Create search workflow tests | TASK | Test URL construction, result parsing, pagination |

---

## Story 2.9 — Workflow: Gig Detail Scrape (Stage 4)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.9.1 | Create GigDetailWorkflow | TASK | `src/collection/workflows/gig_detail.py` — Stage 4: visit each gig, extract full details |
| 2.9.2 | Implement package extraction | TASK | Parse 3-tier packages: name, price, deliverables, delivery_days, revisions |
| 2.9.3 | Implement description extraction | TASK | Full gig description text |
| 2.9.4 | Implement FAQ extraction | TASK | Extract all FAQ question/answer pairs |
| 2.9.5 | Implement gig extras extraction | TASK | Parse all extras: name, price, description |
| 2.9.6 | Implement tag extraction | TASK | Extract gig tags/keywords |
| 2.9.7 | Implement visual capture | TASK | Screenshot thumbnail, count gallery items, detect video (Wave 11) |
| 2.9.8 | Implement depth-based gig limits | TASK | full=20 gigs/keyword, standard=10, feasibility=5 |
| 2.9.9 | Store Gig table entries | TASK | UPSERT gig data (update if gig_id exists) |
| 2.9.10 | Create gig detail tests | TASK | Test package parsing, FAQ parsing, extra parsing |

---

## Story 2.10 — Workflow: Seller Profile Scrape (Stage 5)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.10.1 | Create SellerProfileWorkflow | TASK | `src/collection/workflows/seller_profile.py` — Stage 5: visit seller profiles |
| 2.10.2 | Implement bio extraction | TASK | Bio text, word count, credential detection, specialization detection |
| 2.10.3 | Implement stats extraction | TASK | Member since, response time, response rate, languages, country |
| 2.10.4 | Implement portfolio extraction | TASK | Portfolio count, portfolio item types |
| 2.10.5 | Implement skills extraction | TASK | Skills listed, skill tests passed (Wave 11) |
| 2.10.6 | Implement avatar classification | TASK | Detect avatar type: headshot/logo/illustration/none |
| 2.10.7 | Store Seller table entries | TASK | UPSERT seller data |
| 2.10.8 | Deduplicate sellers across keywords | TASK | Same seller_username → update, don't create duplicate |
| 2.10.9 | Create seller profile tests | TASK | Test bio parsing, stats extraction, deduplication |

---

## Story 2.11 — Workflow: Google Trends Fetch (Stage 6a)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.11.1 | Create GoogleTrendsWorkflow | TASK | `src/collection/workflows/google_trends.py` — Uses pytrends to fetch interest over time |
| 2.11.2 | Implement 12-month data fetch | TASK | Last 12 months interest data for each keyword |
| 2.11.3 | Implement slope calculation | TASK | Linear regression on interest values → RISING/STABLE/DECLINING |
| 2.11.4 | Implement 3-strike escalation | TASK | On 429: 10s → 15s → 22.5s → DEAD_LETTER |
| 2.11.5 | Store ExternalSignal entries | TASK | source_type="google_trends", store slope, raw data as JSON |
| 2.11.6 | Create trends tests | TASK | Test slope calculation, escalation behavior |

---

## Story 2.12 — Workflow: Reddit Signal Collection (Stage 6b)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.12.1 | Create RedditSignalWorkflow | TASK | `src/collection/workflows/reddit_signals.py` — Search Reddit for niche-level demand signals |
| 2.12.2 | Implement subreddit search | TASK | Search relevant subreddits for niche keywords, count posts/comments |
| 2.12.3 | Implement intent phrase detection | TASK | Scan for buying-intent phrases: "looking for", "need someone to", "can anyone build" |
| 2.12.4 | Store ExternalSignal entries | TASK | source_type="reddit_demand", store intent score and sample phrases |
| 2.12.5 | Create Reddit tests | TASK | Test intent phrase detection, signal storage |

---

## Story 2.13 — Workflow: Autocomplete Collection (Stage 2b)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.13.1 | Create AutocompleteWorkflow | TASK | `src/collection/workflows/autocomplete.py` — Capture Fiverr autocomplete position for each keyword |
| 2.13.2 | Implement position extraction | TASK | Type keyword → record position in dropdown (1-10) or null if not present |
| 2.13.3 | Store autocomplete_position on Keyword | TASK | Update keyword.autocomplete_position field |

---

## Story 2.14 — Stage Orchestration Wiring

| ID | Task | Type | Description |
|---|---|---|---|
| 2.14.1 | Wire Stage 2 into orchestrator | TASK | RunOrchestrator calls KeywordExpansionWorkflow + AutocompleteWorkflow |
| 2.14.2 | Wire Stage 3 into orchestrator | TASK | RunOrchestrator calls FiverrSearchWorkflow |
| 2.14.3 | Wire Stage 4 into orchestrator | TASK | RunOrchestrator calls GigDetailWorkflow |
| 2.14.4 | Wire Stage 5 into orchestrator | TASK | RunOrchestrator calls SellerProfileWorkflow |
| 2.14.5 | Wire Stage 6 into orchestrator | TASK | RunOrchestrator calls GoogleTrendsWorkflow + RedditSignalWorkflow |
| 2.14.6 | Implement stage timing | TASK | Record start/end time per stage in RunLog |
| 2.14.7 | Implement stage error handling | TASK | Stage failure logs error, sets run status to COMPLETED_WITH_ERRORS, continues to next stage if non-critical |

---

## Story 2.15 — Collection Workflow: Auto-Promotion (Workflow 14)

| ID | Task | Type | Description |
|---|---|---|---|
| 2.15.1 | Create AutoPromotionEvaluator | TASK | `src/collection/workflows/auto_promotion.py` — Evaluates Tier 2 niches for depth promotion |
| 2.15.2 | Implement 3-run consecutive check | TASK | After 3 consecutive runs with scores, evaluate promotion criteria |
| 2.15.3 | Implement promotion criteria | TASK | Promote if avg_score > 50 AND strong_go_count >= 1 across 3 runs |
| 2.15.4 | Implement depth change | TASK | Update niche depth in config (standard → full) and log to AutoPromotionLog |
| 2.15.5 | Create auto-promotion tests | TASK | Test 3-run check, promotion criteria, depth change |

---

## Story 2.16 — End-to-End Collection Smoke Test

| ID | Task | Type | Description |
|---|---|---|---|
| 2.16.1 | Create collection integration test | TASK | Run Stages 2-6 against one niche with 2 seed keywords, verify data in all tables |
| 2.16.2 | Verify checkpoint and resume | TASK | Start collection, kill mid-way, resume, verify no data loss |
| 2.16.3 | Verify pacing compliance | TASK | Log all request timestamps, verify minimum delays respected |

---

## Epic 02 Summary

| Metric | Count |
|---|---|
| Stories | 16 |
| Tasks | 82 |
| Source Spec Files | COLLECTION_WORKFLOWS.md, PLAYWRIGHT_SESSION_DESIGN.md, PACING_MODEL.md, RETRY_AND_CHECKPOINT.md, QUEUE_DESIGN.md, PROXY_LAYER.md |
| New Python Files | ~20 |
| New Test Files | ~16 |
