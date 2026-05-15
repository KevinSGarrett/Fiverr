# Job Architecture
# Fiverr Research System — Wave 2

**Document Status:** Complete
**Wave:** 2 — Technical Architecture
**Purpose:** All job types, schemas, priority tier assignments, scheduling design, retry policy, and dead-letter queue for all 15 pipeline stages across 9 niches.

---

## Job Architecture Principles

1. Every pipeline action that can fail, be retried, or be individually resumed is a job
2. Jobs are typed, prioritized, and scheduled independently — no monolithic pipeline blocks
3. Every job has a schema, a status, a retry count, and a checkpoint reference
4. Priority determines which niche's work runs first when resources are shared
5. The dead-letter queue catches permanently failed jobs without stopping the run
6. APScheduler handles scheduling for v1; the job queue is broker-agnostic (Celery-ready for v2)

---

## Job Type Taxonomy

### Collection Jobs (Stages 1–6)

| Job Type | Stage | Description | Typical Duration |
|---|---|---|---|
| SEED_INTAKE | 1 | Load and validate seeds for one niche | <1s |
| KEYWORD_EXPAND | 2 | Expand seeds for one niche (autocomplete + LLM + embeddings) | 2–5 min |
| FIVERR_SEARCH | 3 | Collect search results for one keyword | 10–30s |
| GIG_DETAIL | 4 | Collect detail page for one gig | 15–40s |
| SELLER_PROFILE | 5 | Collect seller profile page for one seller | 10–30s |
| GOOGLE_TRENDS | 6 | Collect Google Trends for one keyword batch (5 seeds) | 15–60s |
| REDDIT_COLLECT | 6 | Collect Reddit signals for one niche | 30–90s |
| YOUTUBE_COLLECT | 6 | Collect YouTube search counts for one niche | 10–30s |

### Analysis Jobs (Stages 7–9)

| Job Type | Stage | Description | Typical Duration |
|---|---|---|---|
| GIG_QUALITY_TITLE | 7 | LLM title quality scoring for one gig batch | 5–15s |
| GIG_QUALITY_DESC | 7 | LLM description quality + weakness for one gig | 10–30s |
| GIG_QUALITY_THUMBNAIL | 7 | LLM thumbnail assessment for one gig batch | 5–10s |
| GIG_QUALITY_FAQ | 7 | LLM FAQ scoring for one gig batch | 5–10s |
| SELLER_BIO_PARSE | 8 | LLM seller bio authority parse for one seller | 5–10s |
| CLUSTER_SYNTHESIS | 8 | LLM competitor cluster synthesis for one cluster | 15–45s |
| SELLER_WEAKNESS | 8 | LLM seller weakness identification for top sellers | 10–30s |
| KEYWORD_CLUSTER | 9 | sklearn clustering for one niche keyword set | 5–30s |
| CLUSTER_LABEL | 9 | LLM cluster labeling for one cluster | 5–10s |
| CLUSTER_NARRATIVE | 9 | LLM cluster opportunity narrative for one cluster | 10–30s |

### Scoring Jobs (Stages 10–12)

| Job Type | Stage | Description | Typical Duration |
|---|---|---|---|
| SCORE_KEYWORD | 10 | Calculate all applicable scores for one keyword | 1–3s |
| SCORE_CONFIDENCE | 11 | Calculate confidence modifier for one keyword | <1s |
| RANK_OPPORTUNITY | 12 | Apply GO/PASS tag and rank one keyword | <1s |

### Recommendation Jobs (Stage 13)

| Job Type | Stage | Description | Typical Duration |
|---|---|---|---|
| RECOMMEND_TITLES | 13 | Generate 5 gig title variants for one keyword | 10–20s |
| RECOMMEND_TAGS | 13 | Generate tag sets for one keyword | 5–10s |
| RECOMMEND_PACKAGES | 13 | Generate package structure for one keyword | 10–20s |
| RECOMMEND_DESCRIPTION | 13 | Generate description outline for one keyword | 15–30s |
| RECOMMEND_FAQ | 13 | Generate FAQ entries for one keyword | 5–15s |
| RECOMMEND_DIFF_ANGLE | 13 | Generate differentiation angle for one keyword | 10–25s |
| RECOMMEND_PERSONA | 13 | Generate buyer persona for one keyword | 5–10s |
| RECOMMEND_THUMBNAIL | 13 | Generate thumbnail direction for one keyword | 5–10s |
| RECOMMEND_UPSELL | 13 | Generate upsell structure for one keyword | 5–10s |
| RECOMMEND_RED_FLAGS | 13 | Generate red flags for one keyword | 10–20s |
| RECOMMEND_VIABILITY | 13 | Generate niche viability assessment for one keyword | 15–30s |

### Reporting Jobs (Stages 14–15)

| Job Type | Stage | Description | Typical Duration |
|---|---|---|---|
| REPORT_SCORE_EXPLAIN | 14 | LLM score explanation for one keyword | 10–20s |
| REPORT_TREND_NARRATIVE | 14 | LLM trend narrative for one cluster | 5–15s |
| REPORT_SATURATION | 14 | LLM saturation narrative for one keyword | 3–8s |
| REPORT_COMPETITOR_SUMMARY | 14 | LLM competitor landscape summary for one niche | 15–30s |
| EXPORT_CSV | 14 | Write CSV export for one niche | 1–5s |
| EXPORT_EXCEL | 14 | Write Excel export for one niche | 2–10s |
| EXPORT_PDF | 14 | Render PDF report for one niche | 5–30s |
| EXPORT_MARKDOWN | 14 | Write markdown run summary | 1–3s |
| RUN_LOG_WRITE | 15 | Write run log record | <1s |
| RUN_SUMMARY_LLM | 15 | LLM run summary generation | 10–20s |
| AUTO_PROMOTE_EVAL | 15 | Auto-promotion evaluation (run 3+) | 2–10s |

---

## Job Schema

Every job is represented as a JobRecord object, stored in the jobs table in SQLite:

```python
class JobRecord(BaseModel):
    job_id: str              # UUID4, generated at job creation
    run_id: str              # FK to run_logs.run_id
    job_type: str            # from job type taxonomy above (e.g., "GIG_DETAIL")
    stage: int               # pipeline stage number (1–15)
    niche_id: str            # FK to niche_configs.niche_id (e.g., "prd_ai_saas")
    priority: str            # CRITICAL | HIGH | STANDARD | LOW | BACKGROUND
    status: str              # QUEUED | RUNNING | COMPLETE | FAILED | DEAD_LETTER | SKIPPED
    payload: dict            # job-specific input data (keyword_id, gig_url, seller_username, etc.)
    result_ref: str | None   # pointer to output record (table + row_id, e.g., "gigs:12345")
    retry_count: int         # number of times this job has been retried (default 0)
    max_retries: int         # maximum allowed retries (default 3)
    error_log: list[str]     # list of error messages from each attempt
    checkpoint_ref: str | None  # path to checkpoint file if applicable
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    duration_seconds: float | None
```

---

## Priority Tier Assignments

Priority is assigned by Niche Depth Dispatcher based on niche slot and job type:

### Tier Definitions

| Priority | Queue Position | Description | Delay Tolerance |
|---|---|---|---|
| CRITICAL | 1st | PRD (Slot 1) — primary niche, always first | None — run immediately |
| HIGH | 2nd | Slots 5, 6, 7 (Python Auto, AI Tool, AI Agent) | Minimal — high AOV potential |
| STANDARD | 3rd | Slots 8, 9 (Workflow Auto, Python Scraping) | Acceptable — standard research |
| LOW | 4th | Slots 2, 3 (Support-KB, Gumloop/Lindy — keyword_only) | High — minimal data collected |
| BACKGROUND | 5th | Slot 4 (MCP — feasibility mode) | Highest — runs last |

### Priority Assignment Rules

```python
def assign_priority(niche_id: str, job_type: str) -> str:
    slot = get_niche_slot(niche_id)
    
    if slot == 1:                      # PRD
        return "CRITICAL"
    elif slot in (5, 6, 7):            # Python Auto, AI Tool, AI Agent
        return "HIGH"
    elif slot in (8, 9):               # Workflow Auto, Python Scraping
        return "STANDARD"
    elif slot in (2, 3):               # Support-KB, Gumloop/Lindy (gated)
        return "LOW"
    elif slot == 4:                    # MCP (feasibility)
        return "BACKGROUND"
    else:
        return "STANDARD"              # default fallback
```

### Job Queue Processing Order

Within the same priority tier, jobs are ordered by:
1. Stage number (earlier stages first)
2. Intent class of the keyword (HIGH_INTENT and TRANSACTIONAL before INFORMATIONAL)
3. Creation timestamp (FIFO within same priority + stage + intent)

---

## Scheduling Design

### v1 — APScheduler (In-Process)

**Weekly Full Run:**
```yaml
# config.yaml
scheduler:
  enabled: true
  jobs:
    weekly_full_run:
      mode: full
      cron: "0 23 * * 0"    # Every Sunday at 11:00 PM
      timezone: "America/Chicago"
      on_overlap: skip       # If previous run still active, skip this trigger
```

**APScheduler Setup (src/scheduler/jobs.py):**
```python
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler(timezone=config.scheduler.timezone)

scheduler.add_job(
    func=run_pipeline,
    trigger=CronTrigger.from_crontab(config.scheduler.jobs.weekly_full_run.cron),
    id="weekly_full_run",
    name="Weekly Full Research Run",
    replace_existing=True,
    max_instances=1,          # Never run more than one instance simultaneously
    coalesce=True,            # If multiple triggers missed, run only once on recovery
    misfire_grace_time=3600,  # Allow up to 1 hour late start before skipping
)
```

**Manual Trigger:**
```bash
python run.py --mode full          # Immediate full run
python run.py --mode score-only    # Recalculate scores only
python run.py --mode relogin       # Re-authenticate Fiverr session
python run.py --mode resume        # Resume from last checkpoint
```

### v2 — Celery + Redis (Distributed)

In v2, the APScheduler cron triggers a Celery beat task. Individual jobs are submitted to a Redis-backed Celery queue with routing based on priority:

```python
# Celery routing for v2
task_routes = {
    "jobs.collection.*": {"queue": "collection"},
    "jobs.llm.*": {"queue": "llm_analysis"},
    "jobs.scoring.*": {"queue": "scoring"},
    "jobs.reporting.*": {"queue": "reporting"},
}

# Celery priority queues
CELERY_TASK_QUEUES = (
    Queue("critical", routing_key="critical"),
    Queue("high", routing_key="high"),
    Queue("standard", routing_key="standard"),
    Queue("low", routing_key="low"),
    Queue("background", routing_key="background"),
)
```

---

## Retry Policy

Every job type has a retry policy defined in src/scheduler/jobs.py:

### Standard Retry Policy (most jobs)

```python
STANDARD_RETRY = RetryPolicy(
    max_retries=3,
    backoff_multiplier=2.0,
    initial_wait_seconds=5,
    max_wait_seconds=60,
    retryable_errors=[
        RequestTimeout, ConnectionError, httpx.TimeoutException,
        PlaywrightTimeoutError, RateLimitError,
    ],
    non_retryable_errors=[
        HTTP404, HTTP410, PermanentBan, InvalidCredentials,
    ]
)
```

### Retry Behavior by Error Type

| Error | Behavior | Wait Before Retry |
|---|---|---|
| HTTP 429 (rate limited) | Retry up to 3× | 5 minutes (configurable), then exponential |
| HTTP 5xx (server error) | Retry up to 3× | 30s → 60s → 120s |
| HTTP 404 / 410 | Mark DEAD_LETTER immediately | None |
| Network timeout | Retry up to 3× | 10s → 20s → 40s |
| Playwright crash | Re-launch browser + restore session, retry | 15s |
| LLM API error | Retry once with same prompt | 10s |
| LLM parse error (ValidationError) | Retry once with self-correction prompt appended | 5s |
| LLM 2nd failure | Mark field as null, continue (not dead-letter) | None |
| Fiverr session expired | Trigger re-login (headed), save session, retry original job | 60s |
| SQLite lock (write conflict) | Retry up to 5× with short backoff | 0.5s → 1s → 2s |

### Per-Job-Type Max Retries Override

```python
MAX_RETRIES_BY_TYPE = {
    "GIG_DETAIL": 3,           # Standard
    "SELLER_PROFILE": 3,       # Standard
    "FIVERR_SEARCH": 3,        # Standard
    "GOOGLE_TRENDS": 5,        # More retries — frequent 429s
    "REDDIT_COLLECT": 2,       # Fewer retries — Reddit API is stable
    "GIG_QUALITY_DESC": 2,     # LLM jobs — 1 standard retry + 1 self-correction
    "CLUSTER_SYNTHESIS": 2,    # LLM jobs
    "RECOMMEND_TITLES": 2,     # LLM jobs
    # Default for all others: 3
}
```

---

## Dead-Letter Queue

Jobs that exceed max_retries are moved to the dead-letter queue rather than crashing the run.

### Dead-Letter Behavior

```python
def handle_dead_letter(job: JobRecord):
    job.status = "DEAD_LETTER"
    job.completed_at = datetime.utcnow()
    db.session.commit()
    
    # Log to run_logs
    run_log.errors.append({
        "job_id": job.job_id,
        "job_type": job.job_type,
        "niche_id": job.niche_id,
        "error_log": job.error_log,
        "impact": assess_impact(job),   # "LOW" | "MEDIUM" | "HIGH"
    })
    
    # Assess impact on downstream stages
    if job.job_type in BLOCKING_JOB_TYPES:
        # Skip downstream jobs that depend on this job's output
        cancel_dependent_jobs(job)
        log_confidence_deduction(job)
    else:
        # Non-blocking: continue run, confidence score will reflect missing data
        pass
    
    # Alert if HIGH impact
    if assess_impact(job) == "HIGH":
        alert_system.fire("JOB_DEAD_LETTER_HIGH_IMPACT", job)
```

### Blocking vs. Non-Blocking Job Types

| Job Type | Blocking? | Impact if Dead-Letter |
|---|---|---|
| KEYWORD_EXPAND | Yes (blocks Stage 3) | HIGH — niche skipped for this run |
| FIVERR_SEARCH | Yes (blocks Stage 4) | HIGH — keyword skipped for this run |
| GIG_DETAIL | No | MEDIUM — confidence reduced, scoring limited |
| SELLER_PROFILE | No | LOW — competitor analysis skipped |
| GOOGLE_TRENDS | No | MEDIUM — confidence reduced by 0.15 |
| GIG_QUALITY_DESC | No | MEDIUM — weakness detection missing |
| CLUSTER_SYNTHESIS | No | LOW — narrative missing, scores unaffected |
| RECOMMEND_TITLES | No | LOW — that recommendation component null |

### Dead-Letter Report

Dead-letter jobs are summarized in the run summary (Stage 15) and displayed in the Run History dashboard page with:
- Job type, niche, error history, impact assessment
- "Retry Dead Letter Jobs" button (triggers re-queue for all DEAD_LETTER jobs from the last run)

---

## Job Queue Capacity Estimates

For a full run across all 9 niches (default configuration):

| Stage | Est. Jobs | Notes |
|---|---|---|
| 1–2 | 9 SEED_INTAKE + ~90–180 KEYWORD_EXPAND | ~10–20 keywords per seed across 9 niches |
| 3 | ~810–1,350 FIVERR_SEARCH | ~90–150 expanded keywords × 9 niches |
| 4 | ~405–675 GIG_DETAIL | Top 20 (PRD) + top 10 (Tier 2) across all niches |
| 5 | ~200–400 SELLER_PROFILE | Deduped across niches |
| 6 | ~54 external signal jobs | 9 niches × 3 sources (Trends, Reddit, YouTube) |
| 7 | ~500–900 LLM analysis jobs | Title + desc + weakness + thumbnail + FAQ per gig |
| 8 | ~100–200 LLM synthesis jobs | Seller bios + cluster syntheses |
| 9 | ~50–100 clustering jobs | Cluster + label + narrative |
| 10–12 | ~810–1,350 scoring jobs | One SCORE_KEYWORD per keyword |
| 13 | ~220–550 recommendation jobs | ~20–50 GO keywords × 11 tasks each |
| 14–15 | ~100–200 reporting jobs | Score explanations + narratives + exports |
| **Total** | **~3,300–5,700 jobs** | **For a full run across all 9 niches** |

**Estimated total run time (default pacing):** 3–6 hours for a full run.
**Estimated total run time (keyword-only niches only):** 45–90 minutes.
