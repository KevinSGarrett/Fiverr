# Automation Operating Model
# Fiverr Research System — Wave 0 Rev 3

**Version:** 0.3 — Full Authenticated Session + Complete LLM Integration Across All Stages

---

## Core Principle

**Natural-rate automation with human-paced session behavior.**

After initial configuration, the user runs one command. The system executes all 15 pipeline stages unattended — collecting, analyzing, scoring, and reporting across all 9 research niches — without further human input. All Fiverr collection runs through the user's own authenticated Fiverr account at natural human browsing speed. LLM intelligence is embedded at every stage where it adds value.

---

## The 15 Pipeline Stages

| Stage | Name | LLM Involved | Model(s) |
|---|---|---|---|
| 1 | Seed Keyword Intake | Optional niche expansion brainstorm | gpt-4o-mini |
| 2 | Keyword Expansion | Synonyms, variants, intent classification, embeddings | gpt-4o-mini + text-embedding-3-small |
| 3 | Fiverr Search Collection | No | — |
| 4 | Gig Detail Collection | No | — |
| 5 | Competitor Scan | No | — |
| 6 | External Demand Validation | Reddit demand intent parsing | gpt-4o-mini |
| 7 | Gig Quality Analysis | Title, description, weakness, thumbnail, FAQ | gpt-4o + gpt-4o-mini |
| 8 | Seller Strength Analysis | Bio parsing, cluster synthesis, weakness IDs | gpt-4o + gpt-4o-mini |
| 9 | Keyword Clustering | Embeddings + cluster labeling + opportunity narrative | text-embedding-3-small + gpt-4o-mini + gpt-4o |
| 10 | Score Calculation | No (deterministic Python) | — |
| 11 | Confidence Scoring | No (deterministic) | — |
| 12 | Opportunity Ranking | No (deterministic sort) | — |
| 13 | Gig Recommendation Generation | Titles, tags, packages, description, FAQ, persona, red flags | gpt-4o + gpt-4o-mini |
| 14 | Report and Dashboard Refresh | Score explanations, trend/saturation narratives, competitor summaries | gpt-4o + gpt-4o-mini |
| 15 | Run Logging | Natural language run summary | gpt-4o-mini |

---

## 9-Niche Run Architecture

All 9 niches are processed in a single run with priority-based collection depth:

```yaml
# Niche depth levels applied per run
Slot 1 — PRD:                full         (all 15 stages, top 20 gigs per keyword)
Slot 2 — Support-KB:         keyword_only (stages 1–3 only, until PRD signal gate passed)
Slot 3 — Gumloop/Lindy:      keyword_only (stages 1–3 only, until sandbox proof gate)
Slot 4 — MCP:                feasibility  (stages 1–3 + top 5 gig detail only)
Slot 5 — Python Automation:  standard     (stages 1–9 + scoring, top 10 gigs)
Slot 6 — AI Tool/LLM:        standard     (stages 1–9 + scoring, top 10 gigs)
Slot 7 — AI Agent Dev:       standard     (stages 1–9 + scoring, top 10 gigs)
Slot 8 — Workflow Auto:      standard     (stages 1–9 + scoring, top 10 gigs)
Slot 9 — Python Scraping:    standard     (stages 1–9 + scoring, top 10 gigs)
```

After 3 completed runs, the system evaluates Tier 2 Final Recommendation Scores and auto-promotes the top 2 scoring niches from `standard` to `full` depth, and deprioritizes the lowest-scoring niche to `keyword_only`.

---

## Fiverr Authenticated Session Architecture

### Session Flow
```
FIRST RUN:
  1. Check for data/sessions/fiverr_session.json — not found
  2. Launch Playwright in HEADED mode (visible browser window)
  3. Navigate to fiverr.com
  4. Prompt in terminal: "Please log in to Fiverr. Press Enter when complete."
  5. User logs in manually (including any 2FA)
  6. Verify login state (check for logged-in UI element)
  7. Save browser_context.storage_state() to data/sessions/fiverr_session.json
  8. Continue collection in HEADLESS mode using saved session

SUBSEQUENT RUNS:
  1. Load storage state from fiverr_session.json
  2. Navigate to fiverr.com — verify session valid
  3. If valid: proceed headlessly
  4. If expired: trigger re-login (headed mode), re-save, continue

FORCED RE-LOGIN:
  python run.py --mode relogin
```

### Human-Event Simulation (All Fiverr Sessions)
- Random scroll events after page load (simulates reading)
- Hover events before clicking (simulates mouse movement)
- Variable dwell time per page (2–8 seconds + random jitter)
- Randomized click timing (100–400ms delay after element focus)
- Occasional dead navigation (loading adjacent page before target)
- Random window sizing (not always 1920×1080)

### Session Security
- Credentials in .env only — never in config.yaml or source code
- data/sessions/ in .gitignore — never committed
- File permissions: chmod 600 on session file (owner read/write only)

---

## LLM Architecture

### Provider Configuration (config.yaml)
```yaml
llm:
  provider: openai
  openai_api_key: ${OPENAI_API_KEY}
  cache_enabled: true
  cache_ttl_hours: 72
  max_tpm: 90000
  cost_alert_daily_usd: 5.00
  log_all_calls: true
  models:
    tier_high: gpt-4o
    tier_low: gpt-4o-mini
    embeddings: text-embedding-3-small
```

### LLM Cache
- Table: llm_cache in SQLite
- Key: SHA-256(model + temperature + prompt_text)
- Cache hit: return stored response, log hit, skip API call
- Cache miss: call API, store response, log token usage and cost
- Invalidation: when source data is refreshed beyond TTL

### Structured Output
1. OpenAI JSON mode for all structured responses
2. Parse into typed Pydantic model
3. On ValidationError: self-correction retry once
4. On second failure: log null, decrement confidence score
5. All prompts stored as Jinja2 templates in src/llm/prompts/

---

## Pacing Configuration (config.yaml)
```yaml
pacing:
  fiverr_search:
    base_delay_seconds: 4
    jitter_seconds: 3
    max_requests_per_hour: 60
    human_events: true
  fiverr_gig_detail:
    base_delay_seconds: 6
    jitter_seconds: 4
    max_requests_per_hour: 40
    human_events: true
  fiverr_seller_profile:
    base_delay_seconds: 5
    jitter_seconds: 3
    max_requests_per_hour: 40
    human_events: true
  google_trends:
    base_delay_seconds: 10
    jitter_seconds: 5
    max_requests_per_hour: 20
  reddit_api:
    base_delay_seconds: 2
    jitter_seconds: 1
    max_requests_per_hour: 60
```

---

## Retry and Checkpoint Model

| Scenario | Behavior |
|---|---|
| HTTP 429 (rate limited) | Pause 5 min, exponential backoff, retry up to 3x |
| HTTP 5xx | Retry with 30s backoff, up to 3x |
| HTTP 404 / 410 | Log permanent failure, skip |
| Network timeout | Retry with 10s backoff, up to 3x |
| Playwright crash | Re-launch, restore session, resume from checkpoint |
| LLM API error | Retry once; if fails mark null, decrement confidence |
| LLM parse error | Self-correction retry; if fails mark null, decrement confidence |

Checkpoints written every 50 records to data/checkpoints/[run_id]/[stage].json

---

## Run Modes

| Mode | Stages | Use Case |
|---|---|---|
| full | All 15 | Weekly full refresh |
| collect-only | 1–6 | Re-collect without re-analyzing |
| analyze-only | 7–12 | Re-run analysis + LLM on existing data |
| score-only | 10–12 | Recalculate scores after weight change |
| report-only | 13–15 | Regenerate recommendations and reports |
| keyword-only | 1–3 | Quick niche scan |
| resume | From checkpoint | Recover after interruption |
| relogin | Session only | Force Fiverr re-authentication |

---

## Normal User Workflow
```
1. cp .env.example .env → add OPENAI_API_KEY
2. Edit config.yaml → seed keywords, niche profiles, scoring weights, pacing
3. python run.py --mode relogin → authenticate Fiverr, save session
4. python run.py --mode full → all 15 stages across all 9 niches, unattended
5. open http://localhost:8501 → Streamlit dashboard
6. Review top opportunities, LLM recommendations, competitor weakness reports
7. Export reports from dashboard or data/exports/
8. Schedule future runs via APScheduler config or crontab
```
