# Collection Workflows
# Fiverr Research System — Wave 4

**Document Status:** Complete
**Wave:** 4 — Collection Engine Design
**Purpose:** All 15 collection workflow specs with depth variants, error handling, checkpoint locations, pacing, and LLM integration points.

---

## Workflow Design Standards

Every workflow document follows this structure:
- **Trigger:** What initiates this workflow
- **Input:** Data/state required before starting
- **Steps:** Numbered, precise, with decision branches
- **Output:** What is written to which table/file
- **Depth Variants:** How the workflow differs by collection depth
- **Error Handling:** Which errors are caught and how
- **Checkpoint:** Where checkpoint files are written
- **Pacing:** Which pacing config applies

---

## Workflow 1 — Niche Initialization (Stage 1)

**Trigger:** Run start, for every active niche.

**Input:**
- config.yaml niches list
- niche_configs table (runtime depth overrides)

**Steps:**
1. Load all niches from config.yaml
2. For each niche, query niche_configs table for runtime depth
   - If runtime depth exists in niche_configs: use it (auto-promotion may have changed it)
   - If not exists: use config.yaml depth as initial value, insert niche_configs row
3. Apply gate check per niche:
   - If `gating.enabled = true` AND `gate_passed = false`:
     - Force depth to `keyword_only` (or `feasibility` for Slot 4)
     - Log: "[NICHE] running in keyword_only mode — gate condition not yet passed"
4. Call Niche Depth Dispatcher → generate NicheJobSpec for each niche
5. For each niche, load seed keywords from config.yaml
6. Validate seeds: strip whitespace, deduplicate, check for empty strings
7. Optional LLM brainstorm (if `config.llm.niche_brainstorm = true`):
   - Call gpt-4o-mini with niche name and current seeds
   - Display suggestions in run summary only (user decides whether to add to config)
8. Write validated seed lists to in-memory queue → pass to Workflow 2

**Output:**
- NicheJobSpec objects (in-memory, not stored)
- niche_configs table rows created/updated
- run_niches association rows created for this run

**Depth Variants:** No depth differentiation at this stage — all niches run through initialization.

**Error Handling:**
- Invalid niche_id in config.yaml → raise ValueError at startup, halt run
- Gate check failure → log warning, cap depth, continue
- LLM brainstorm failure → log warning, skip brainstorm, continue

**Checkpoint:** None (fast, < 5 seconds total)

**Pacing:** None

---

## Workflow 2 — Keyword Expansion Per Niche (Stage 2)

**Trigger:** Workflow 1 complete for a niche. One execution per niche.

**Input:**
- Validated seed list from Workflow 1
- NicheJobSpec (depth setting, niche_id)
- Existing keywords table rows (for deduplication)

**Steps:**
1. Check existing keywords in DB: select all non-stale keywords for this niche
   - If keyword_text exists and collected_at + ttl_hours > now(): skip re-expansion
   - If stale or not exists: add to expansion queue
2. **Step 2a — Fiverr Autocomplete** (Playwright, authenticated):
   - For each seed keyword:
     - Navigate to `fiverr.com/search/gigs?query={seed}` (don't submit — collect suggestions)
     - Intercept network request to Fiverr's autocomplete API endpoint
     - Alternatively: simulate keypress into search box, collect dropdown suggestions
     - Record each suggestion with its position (1–10)
     - Apply pacing: `pacing_manager.wait("fiverr_search")`
3. **Step 2b — Google Suggest** (httpx):
   - GET `https://suggestqueries.google.com/complete/search?q={seed}&client=firefox`
   - Parse JSON suggestions array
   - Apply pacing: `pacing_manager.wait("external_default")`
4. **Step 2c — LLM Keyword Generation** (gpt-4o-mini):
   - Batch all seeds for this niche into a single prompt
   - Prompt: generate 10–20 related keywords, long-tail variants, buyer-intent modifier combos per seed
   - Parse JSON response into flat keyword list
   - Check LLM cache before calling API
5. **Step 2d — LLM Relevance Filter** (gpt-4o-mini):
   - Batch all generated keywords (autocomplete + Google suggest + LLM-generated)
   - Prompt: classify each as RELEVANT or IRRELEVANT to this niche
   - Remove IRRELEVANT keywords from list
   - Check LLM cache before calling API
6. **Step 2e — Deduplication**: deduplicate final keyword list (case-insensitive)
7. **Step 2f — LLM Intent Classification** (gpt-4o-mini):
   - Batch all keywords per niche (max 50 per call to avoid token limits)
   - Classify each: INFORMATIONAL / CONSIDERATION / HIGH_INTENT / TRANSACTIONAL
   - Check LLM cache before calling API
8. **Step 2g — Embedding Generation** (text-embedding-3-small):
   - Batch keywords in groups of 100 (API batch limit)
   - Generate 1536-dimension vector per keyword
   - Check LLM cache before calling API
9. Write all keywords to DB: insert new rows, skip existing non-stale rows
10. Update `keywords.cluster_id = null` for all expanded keywords (clustering runs in Stage 9)
11. Checkpoint after every 50 keywords written

**Output:**
- keywords table rows with keyword_text, source, autocomplete_position, intent_class, embedding_vector

**Depth Variants:**
- `full` / `standard`: all steps (2a–2g)
- `keyword_only`: all steps (2a–2g) — keyword expansion runs at all depths
- `feasibility`: steps 2a–2e only (no embeddings — clustering skipped at feasibility depth)

**Error Handling:**
- Fiverr autocomplete timeout → skip autocomplete for this seed, continue with Google suggest
- Google suggest connection error → retry 2×, skip on failure, continue
- LLM generation failure → skip LLM-generated keywords for this niche, log warning
- LLM relevance filter failure → skip filter (include all keywords), log warning
- LLM intent classification failure → store intent_class = null, apply confidence deduction
- Embedding generation failure → store embedding_vector = null, skip clustering for this keyword

**Checkpoint:** Written every 50 keywords to `data/checkpoints/{run_id}/stage02_{niche_id}.json`

```json
{
  "run_id": "uuid",
  "stage": 2,
  "niche_id": "prd_ai_saas",
  "seeds_processed": 6,
  "keywords_written": 142,
  "last_keyword_text": "SaaS product roadmap template",
  "timestamp": "2026-05-12T01:23:44Z"
}
```

**Pacing:**
- Fiverr autocomplete: `fiverr_search` pacing config
- Google suggest: `external_default` pacing config
- LLM calls: rate-limited by `llm.max_tpm` — no additional delay needed

---

## Workflow 3 — Fiverr Search Collection Per Keyword (Stage 3)

**Trigger:** Stage 2 complete for a niche. One job per keyword.

**Input:**
- keyword_text, keyword_id, niche_id from keywords table
- NicheJobSpec (priority for queue ordering)
- Authenticated Playwright session context

**Steps:**
1. Check staleness: if search_results row for this keyword exists and is fresh → skip (reuse)
2. Get authenticated page from Session Manager
3. Human Events: maybe_dead_navigate (15% probability)
4. Navigate to `https://www.fiverr.com/search/gigs?query={urllib.parse.quote(keyword_text)}`
5. Wait for page load (`networkidle` or `domcontentloaded` with 30s timeout)
6. Human Events: read_delay, random_scroll
7. Collect total result count (text near top: "X results found")
8. Collect pagination depth (count page navigation links)
9. For each visible gig card on page 1:
   - Extract: gig_url, gig_title, seller_username, seller_level, rating_visible, review_count_visible, review_count_abbreviated, starting_price, delivery_time, tags_visible, sponsored_flag, orders_in_queue_visible, position
10. If `depth == full` and keyword is HIGH_INTENT or TRANSACTIONAL: collect page 2 also
    - Human Events: hover pagination link, click, read_delay, scroll
11. Write search_results row to DB
12. Write individual gig URLs to gig collection queue (for Workflow 4)
13. Apply pacing: `pacing_manager.wait("fiverr_search")`
14. Checkpoint every 50 keywords

**Output:**
- search_results table row per keyword (with total_result_count, pagination_depth, gig_cards JSON)
- Gig URLs added to GIG_DETAIL job queue

**Depth Variants:**
- `full`: collect pages 1–2 for HIGH_INTENT/TRANSACTIONAL keywords; page 1 for others
- `standard`: page 1 only for all keywords
- `keyword_only`: collect page 1 only — gig_cards collected but gig detail NOT queued
- `feasibility`: page 1 only — top 5 gig URLs queued for detail collection

**Error Handling:**
| Error | Action |
|---|---|
| Playwright timeout (page load > 30s) | Retry 3× with 15s backoff |
| Session expired (no login indicator) | Session Manager triggers re-login, retry job |
| No results returned (0 gigs) | Store total_result_count=0, gig_cards=[], do not queue for detail |
| CAPTCHA / challenge page detected | Pause 30 min, retry once; if still challenged → DEAD_LETTER |
| Gig card parse error (selector not found) | Log selector failure, store partial gig_cards, flag for selector review |
| HTTP 5xx | Retry 3× with 30s backoff |

**Checkpoint:** Every 50 searches → `data/checkpoints/{run_id}/stage03_{niche_id}.json`

**Pacing:** `fiverr_search` config (base 4s + jitter 0–3s, max 60/hour)

---

## Workflow 4 — Gig Detail Collection Per Gig URL (Stage 4)

**Trigger:** Gig URL added to GIG_DETAIL queue from Workflow 3. One job per gig URL.

**Input:**
- gig_url, keyword_id, niche_id
- NicheJobSpec (top_n_gigs: 20/10/5/0)
- Authenticated Playwright session

**Steps:**
1. Check staleness: if gigs row exists and is fresh (detail_collected=True) → skip
2. Check deduplication: if this gig_url was already collected this run → skip (gig may rank for multiple keywords)
3. Get authenticated page from Session Manager
4. Human Events: maybe_dead_navigate (10% probability)
5. Navigate to gig_url (wait `domcontentloaded`, 30s timeout)
6. Check for 404 / removed gig page → if detected, mark as DEAD_LETTER, log deleted gig
7. Human Events: read_delay (6s base), random_scroll (simulate reading description)
8. Collect all gig detail fields:
   - gig_title_full (h1 element)
   - description_text (description section)
   - packages (all package tiers: name, price, deliverables list, delivery_days, revisions)
   - gig_extras (name, price for each extra)
   - tags (all 5 tags)
   - faq_text (all FAQ questions and answers as raw text)
   - faq_entries (parsed Q&A pairs)
   - video_present (boolean: video player element present?)
   - portfolio_count (number of portfolio item thumbnails)
   - review_count_exact (integer from review section heading)
   - rating_exact (float from rating display)
   - review_snippets (top 5 visible reviews: reviewer, rating, snippet, date)
   - orders_in_queue (integer if badge visible, else null)
   - thumbnail_url (src attribute of main gig image)
9. Write/update gigs table row
   - If row exists: UPDATE all fields, reset collected_at and ttl_hours
   - If new: INSERT
10. Set gigs.detail_collected = True
11. Add seller_username to SELLER_PROFILE queue if not already collected this run
12. Apply pacing: `pacing_manager.wait("fiverr_gig_detail")`
13. Checkpoint every 50 gigs

**Output:**
- gigs table row (complete detail fields)
- Seller usernames added to SELLER_PROFILE job queue

**Depth Variants:**
- `full`: collect top 20 gigs per keyword (deduped across keywords in niche)
- `standard`: collect top 10 gigs per keyword
- `feasibility`: collect top 5 gigs per keyword
- `keyword_only`: skip — Workflow 4 not invoked

**Error Handling:**
| Error | Action |
|---|---|
| 404 / Gig not found | Mark as DEAD_LETTER, set gig as deleted in DB |
| Parse error on specific field | Store null for that field, continue collecting other fields |
| Description text truncated ("Read more" expand needed) | Click "Read more" button, re-collect description |
| Packages section not found | Store packages=null, apply DEGRADED confidence deduction |
| Session expired | Session Manager re-login, retry job |
| Review count parse error | Store review_count_exact=null, use review_count_visible from search card |

**Checkpoint:** Every 50 gig pages → `data/checkpoints/{run_id}/stage04_{niche_id}.json`

**Pacing:** `fiverr_gig_detail` config (base 6s + jitter 0–4s, max 40/hour)

---

## Workflow 5 — Seller Profile Collection Per Username (Stage 5)

**Trigger:** Seller username added to SELLER_PROFILE queue from Workflow 4.

**Input:**
- seller_username
- niche_id (of the gig that triggered this)
- Authenticated Playwright session

**Steps:**
1. Check staleness: if sellers row for this username exists and is fresh → skip
2. Check run-level deduplication: if this username was already collected this run → skip
3. Get authenticated page from Session Manager
4. Navigate to `https://www.fiverr.com/{seller_username}`
5. Human Events: read_delay (5s base), scroll
6. Collect all seller profile fields:
   - seller_level (badge element)
   - member_since (text in "About" section: "Member since Jan 2022")
   - response_time (displayed in stats bar)
   - response_rate (displayed in stats bar, integer percentage)
   - languages (language list with proficiency levels)
   - bio_text (seller bio/description section)
   - total_reviews (reviews count in profile header)
   - total_gigs (count from gig listing section)
   - active_gig_titles (collect titles of all visible gigs on profile)
   - portfolio_count (count of portfolio thumbnails)
   - badges (collect all badge names and displayed earn dates)
7. Write/update sellers table row
8. Apply pacing: `pacing_manager.wait("fiverr_seller_profile")`
9. Checkpoint every 25 seller pages

**Output:**
- sellers table row

**Depth Variants:**
- `full`: all sellers from top 20 gigs (may be 20+ unique sellers)
- `standard`: top sellers from top 10 gigs
- `feasibility`: sellers from top 5 gigs only
- `keyword_only`: skip — Workflow 5 not invoked

**Error Handling:**
| Error | Action |
|---|---|
| Profile not found (404) | Log warning, skip, do not mark as DEAD_LETTER (seller may have been deactivated) |
| Private/deactivated account | Log, skip |
| Parse error on specific field | Store null, continue |

**Checkpoint:** Every 25 sellers → `data/checkpoints/{run_id}/stage05_{niche_id}.json`

**Pacing:** `fiverr_seller_profile` config (base 5s + jitter 0–3s, max 40/hour)

---

## Workflow 6 — Google Trends Collection Per Niche (Stage 6)

**Trigger:** Stage 5 complete per niche. Run for niches with `external_sources.google_trends = true`.

**Input:**
- Seed keywords for this niche (from config.yaml)
- pytrends TrendReq instance

**Steps:**
1. Group seed keywords into batches of 5 (pytrends max)
2. For each batch:
   a. Build payload: `pytrends.build_payload(kw_list=batch, timeframe="today 12-m", geo="")`
   b. Fetch interest over time: `df = pytrends.interest_over_time()`
   c. If empty DataFrame returned: store signal with score=0, log as "no Trends data for batch"
   d. For each keyword in batch, extract:
      - 12-month average score
      - 3-month average score (last 13 weeks)
      - Weekly data array for slope calculation
   e. Calculate slope: run `numpy.polyfit()` on weekly scores, classify as RISING/FLAT/DECLINING etc.
   f. Fetch related queries: `pytrends.related_queries()`
   g. Fetch related topics: `pytrends.related_topics()`
   h. Write external_signals rows for each keyword
   i. Apply pacing: `pacing_manager.wait("google_trends")`
3. Log total Trends cost: how many keywords had data vs. returned empty
4. Checkpoint after each batch

**Output:**
- external_signals rows (signal_type=google_trends) per keyword with trends_12mo_score, trends_3mo_score, trends_slope, trends_related_queries, trends_related_topics

**Depth Variants:** Same at all depths (trends collected for all keywords regardless of depth).

**Adaptive Pacing (OQ-004 Resolution):**
If pytrends returns HTTP 429 during a run:
1. Immediately pause for `config.pacing.google_trends.rate_limit_pause_minutes` (default 10 minutes)
2. After pause, increase `google_trends.base_delay_seconds` by 50% for the remainder of this run
3. Log: "Google Trends 429 encountered. Increasing delay to {new_delay}s for remainder of run."
4. If 429 occurs again: pause another 10 minutes, increase delay by another 50%
5. If 429 occurs 3+ times: mark remaining Trends jobs as DEAD_LETTER, log confidence deductions

**Error Handling:**
| Error | Action |
|---|---|
| HTTP 429 | Adaptive pacing (see above) |
| TooManyRequestsError | Same as 429 |
| Empty DataFrame (no data) | Store score=0, log as missing data |
| Network timeout | Retry 2× with 15s backoff |
| pytrends library error | Log, skip this batch, continue |

**Checkpoint:** After each batch of 5 keywords → `data/checkpoints/{run_id}/stage06_trends_{niche_id}.json`

**Pacing:** `google_trends` config (base 10s + jitter 0–5s, max 20/hour)

---

## Workflow 7 — Reddit Collection Per Niche (Stage 6)

**Trigger:** Stage 5 complete per niche. Run for niches with `external_sources.reddit = true`.

**Input:**
- Niche seed keywords
- Niche Reddit subreddit list (from config.yaml per niche)
- praw Reddit instance (authenticated with client_id/secret)

**Steps:**
1. For each subreddit in niche's subreddit list:
   a. Check if subreddit is accessible: `reddit.subreddit(name).id` — if error, skip and log
   b. Search subreddit for each seed keyword:
      `results = reddit.subreddit(name).search(seed, sort="relevance", time_filter="year", limit=25)`
   c. Collect: post titles, body snippets (first 200 chars), upvotes, created_utc
   d. Apply pacing between requests: `pacing_manager.wait("reddit_api")`
2. Aggregate all collected posts across all subreddits for this niche
3. Calculate reddit_post_count_90d: count posts with created_utc > 90 days ago
4. Select top 10 posts by upvotes for LLM analysis
5. **LLM Demand Intent Parse** (gpt-4o-mini):
   - Input: top 10 post titles + snippets for this niche
   - Prompt template: `stage06_external/reddit_demand_parse.j2`
   - Output: demand_intent_score (0–10), intent_phrases (list of extracted buyer intent phrases)
   - Check LLM cache before calling API
6. Write external_signals row (signal_type=reddit_demand) for each seed keyword in niche

**Output:**
- external_signals rows (signal_type=reddit_demand) per niche with post count, snippets, LLM demand intent score

**Depth Variants:** Same at all depths.

**Error Handling:**
| Error | Action |
|---|---|
| Subreddit not found | Skip subreddit, continue with next |
| Private subreddit | Skip, log |
| praw TooManyRequests | Pause 60s, retry |
| LLM demand parse failure | Store reddit_demand_intent_score=null, apply confidence deduction −0.05 |

**Checkpoint:** After niche Reddit collection completes → `data/checkpoints/{run_id}/stage06_reddit_{niche_id}.json`

**Pacing:** `reddit_api` config (base 2s + jitter 0–1s, max 60/hour)

---

## Workflow 8 — YouTube Count Collection Per Keyword (Stage 6)

**Trigger:** Stage 5 complete per niche. Run for niches with `external_sources.youtube = true`.

**Input:**
- Seed keywords for niche
- httpx async client

**Steps:**
1. For each seed keyword:
   a. GET `https://www.youtube.com/results?search_query={urllib.parse.quote(keyword_text)}`
   b. Parse response HTML for result count text (pattern: "About X,XXX results")
   c. If count text not found: store youtube_result_count=null (no confidence penalty)
   d. Parse integer from text: remove commas, parse number
   e. Write external_signals row (signal_type=youtube_count)
   f. Apply pacing: `pacing_manager.wait("youtube")`

**Output:**
- external_signals rows (signal_type=youtube_count) per keyword

**Depth Variants:** Same at all depths.

**Error Handling:**
| Error | Action |
|---|---|
| HTTP 429 | Pause 5 min, retry once |
| Parse failure (count not in HTML) | Store null, no retry |
| Connection timeout | Retry 2× with 10s backoff |

**Checkpoint:** Not checkpointed (fast stage, low failure risk)

**Pacing:** `youtube` config (base 3s + jitter 0–2s, max 60/hour)

---

## Workflow 9 — Stale Record Re-Queue (Run Start)

**Trigger:** Run start, before any collection stages begin. Runs as part of Workflow 1.

**Input:**
- All tables with collected_at and ttl_hours fields
- Job queue

**Steps:**
1. Run staleness detection queries against all tables (see FRESHNESS_MODEL.md)
2. For each stale record, determine the appropriate job type and priority
3. Create Job records in the jobs table (status=QUEUED)
4. Priority assignment:
   - PRD niche stale data → CRITICAL
   - Tier 2 high-priority (Slots 5–7) → HIGH
   - Tier 2 standard (Slots 8–9) → STANDARD
   - Gated Tier 1 (Slots 2–3) → LOW
   - MCP (Slot 4) → BACKGROUND
5. Sort stale jobs within each priority by staleness ratio descending (most stale first)
6. Log: "Stale record re-queue: {N} keywords, {M} gigs, {K} sellers, {J} external signals queued for refresh"

**Output:**
- Job rows in jobs table (status=QUEUED) for all stale records

**Error Handling:** Non-blocking — if staleness query fails, log warning and continue with run.

**Checkpoint:** None

**Pacing:** None (DB operation only)

---

## Workflow 10 — Checkpoint Write (During Collection)

**Trigger:** Every 50 records written during any collection stage.

**Input:**
- Current run_id, stage name, niche_id, progress counters, last processed record ID

**Steps:**
1. Construct checkpoint dict with all progress fields
2. Write to `.tmp` file first: `data/checkpoints/{run_id}/{stage}_{niche_id}.tmp`
3. Atomically rename `.tmp` → `.json`:
   `os.replace(tmp_path, json_path)` — atomic on POSIX and Windows (same filesystem)
4. This ensures checkpoint file is never partially written

**Checkpoint JSON Format:**
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "stage04",
  "stage_name": "GIG_DETAIL_COLLECTION",
  "niche_id": "prd_ai_saas",
  "depth": "full",
  "records_complete": 150,
  "records_total": 280,
  "last_record_id": "https://www.fiverr.com/seller/gig-slug",
  "last_keyword_id": 1234,
  "queue_position": 151,
  "started_at": "2026-05-12T00:01:00Z",
  "checkpoint_at": "2026-05-12T00:45:22Z",
  "errors_so_far": 2
}
```

**Error Handling:** If checkpoint write fails (disk full, permissions), log error but DO NOT halt the run. Checkpoints are resilience aids, not blockers.

---

## Workflow 11 — Run Resume (--mode resume)

**Trigger:** User runs `python run.py --mode resume`.

**Steps:**
1. Scan `data/checkpoints/` for the most recent run_id directory
2. Within that directory, find all `.json` checkpoint files
3. For each checkpoint file:
   a. Read checkpoint JSON, validate required fields present
   b. Find corresponding run_log record (status=RUNNING or FAILED)
   c. Find all jobs for this run with status=QUEUED or RUNNING
4. Jobs with status=RUNNING: reset to QUEUED (they were interrupted mid-execution)
5. Re-enqueue all QUEUED jobs starting from the checkpoint position
6. Log: "Resuming run {run_id} from checkpoint: stage={stage}, niche={niche_id}, position={queue_position}"
7. Continue run from that position

**Output:** Run continues from last safe checkpoint state.

**Error Handling:**
- No checkpoint files found → log error, prompt user to run `--mode full` instead
- Checkpoint JSON invalid (corrupt) → skip that checkpoint, re-run that stage from beginning
- run_log not found → create new run_log entry for the resumed run

**Checkpoint:** None (this workflow reads checkpoints, doesn't write them)

---

## Workflow 12 — Session Initialization (Authenticated Login)

**Trigger:** Session Manager called for first time in a run, no valid session file exists.

**Steps:**
1. Check for `data/sessions/fiverr_session.json`
2. If exists: attempt to load and verify (→ Workflow 13)
3. If not exists OR verification fails:
   a. Launch Playwright headed browser: `chromium.launch(headless=False)`
   b. Create new browser context with random viewport and user agent
   c. Navigate to `https://www.fiverr.com/login`
   d. Print to terminal:
      ```
      ============================================================
      ACTION REQUIRED: Please log in to Fiverr in the browser window.
      Complete any 2FA, CAPTCHA, or email verification steps.
      Then press Enter here to continue.
      ============================================================
      ```
   e. Wait for user to press Enter: `input()`
   f. Verify login: check for logged-in UI element (see PLAYWRIGHT_SESSION_DESIGN.md for selector)
   g. If verification fails: print error, prompt again (max 3 attempts)
   h. Save: `await context.storage_state(path="data/sessions/fiverr_session.json")`
   i. Set file permissions: `os.chmod("data/sessions/fiverr_session.json", 0o600)`
   j. Close headed browser
   k. Open headless context with saved session (→ Workflow 13 verify step)
4. Return verified headless context

**Output:** Verified authenticated Playwright browser context.

**Error Handling:**
- Login verification fails after 3 attempts → raise SessionLoginError, halt run, log clear message
- File permission error → log warning, continue (security best-effort)

---

## Workflow 13 — Session Refresh (Expiry Detection)

**Trigger:** Session Manager loads existing session file but verification check fails.

**Steps:**
1. Load `data/sessions/fiverr_session.json` into browser context
2. Navigate to `https://www.fiverr.com`
3. Check for logged-in UI element:
   - If found: session valid → return context
   - If not found: session expired → proceed
4. Print to terminal: "Fiverr session expired. Launching re-login."
5. Close headless context
6. Follow Workflow 12 steps (headed login, save, verify)
7. Return new verified headless context

**Output:** Refreshed authenticated Playwright browser context.

**Checkpoint:** None

---

## Workflow 14 — Auto-Promotion Evaluation (Stage 15, Run 3+)

**Trigger:** End of run, when run_count for at least one Tier 2 niche >= 3.

**Steps:**
1. Query average Final Recommendation Score for each Tier 2 niche across last 3 completed runs:
   ```sql
   SELECT nc.niche_id, AVG(ks.final_score) as avg_score
   FROM niche_configs nc
   JOIN keyword_scores ks ON ks.niche_id = nc.niche_id
   JOIN run_logs rl ON rl.run_id = ks.run_id
   WHERE nc.tier = 2
     AND nc.auto_promotion_eligible = true
     AND rl.status = 'COMPLETE'
     AND rl.run_id IN (SELECT run_id FROM run_logs WHERE status='COMPLETE' ORDER BY started_at DESC LIMIT 3)
   GROUP BY nc.niche_id
   ORDER BY avg_score DESC
   ```
2. Sort results by avg_score descending
3. Apply promotion rules:
   - Rank 1 (if avg_score >= promote_threshold): set depth = `full`
   - Rank 2 (if avg_score >= promote_threshold): set depth = `full`
   - Rank last (if avg_score < demote_threshold): set depth = `keyword_only`
   - All others: set depth = `standard`
4. For each depth change: update niche_configs.current_depth, set depth_reason
5. Log all changes to run_logs.auto_promotion_changes (JSON array)
6. Write alert row (alert_type=AUTO_PROMOTION) for each change
7. Print to run summary: "[Niche X] promoted to full depth (avg score: 71.4)"

**Output:**
- niche_configs.current_depth updated
- run_logs.auto_promotion_changes populated
- alerts rows created

**Error Handling:** If query fails → log error, skip auto-promotion for this run, do not fail the run.

---

## Workflow 15 — Dead Letter Recovery (--mode retry-dead-letter)

**Trigger:** User runs `python run.py --mode retry-dead-letter`.

**Steps:**
1. Query all jobs with status=DEAD_LETTER from the most recent run
2. Display list to user: job_type, niche_id, error_log (last error)
3. Prompt: "Retry all {N} dead letter jobs? (y/n)"
4. If yes:
   a. Reset each job: status=QUEUED, retry_count=0, error_log=[]
   b. Re-enqueue in priority order
   c. Run only the dead-letter jobs (not a full run)
5. Log results: which jobs succeeded, which failed again

**Output:** Dead letter jobs re-queued and executed.

**Error Handling:**
- Jobs that fail again → re-marked as DEAD_LETTER with updated error_log
- If no dead letter jobs found → log message, exit gracefully
