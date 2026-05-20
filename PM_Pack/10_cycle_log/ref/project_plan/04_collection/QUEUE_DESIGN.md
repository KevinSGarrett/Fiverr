# Queue Design
# Fiverr Research System — Wave 4

**Document Status:** Complete
**Wave:** 4 — Collection Engine Design
**Purpose:** Jobs table DDL, priority queue processing algorithm, concurrent job limits, dead-letter detection and handling, APScheduler v1 setup, and Celery v2 migration path.

---

## Jobs Table DDL (SQLite)

```sql
-- SQLite DDL for jobs table
-- Mirrors the SQLAlchemy ORM definition in SCHEMA.md

CREATE TABLE IF NOT EXISTS jobs (
    id               INTEGER  PRIMARY KEY AUTOINCREMENT,
    job_id           TEXT     NOT NULL UNIQUE,
    run_id           TEXT     NOT NULL REFERENCES run_logs(run_id) ON DELETE CASCADE,
    job_type         TEXT     NOT NULL,
    stage            INTEGER  NOT NULL,
    niche_id         TEXT     NOT NULL REFERENCES niche_configs(niche_id),
    priority         TEXT     NOT NULL CHECK(priority IN ('CRITICAL','HIGH','STANDARD','LOW','BACKGROUND')),
    status           TEXT     NOT NULL DEFAULT 'QUEUED'
                              CHECK(status IN ('QUEUED','RUNNING','COMPLETE','FAILED','DEAD_LETTER','SKIPPED')),
    payload          TEXT,    -- JSON
    result_ref       TEXT,
    retry_count      INTEGER  NOT NULL DEFAULT 0,
    max_retries      INTEGER  NOT NULL DEFAULT 3,
    error_log        TEXT,    -- JSON array of error strings
    checkpoint_ref   TEXT,
    created_at       TEXT     NOT NULL,
    started_at       TEXT,
    completed_at     TEXT,
    duration_seconds REAL
);

-- Indexes for queue processing
CREATE INDEX IF NOT EXISTS ix_jobs_run_status
    ON jobs (run_id, status);

CREATE INDEX IF NOT EXISTS ix_jobs_priority_stage
    ON jobs (priority, stage);

CREATE INDEX IF NOT EXISTS ix_jobs_niche_status
    ON jobs (niche_id, status);

CREATE INDEX IF NOT EXISTS ix_jobs_type_status
    ON jobs (job_type, status);
```

---

## Priority Queue Processing Algorithm

The Orchestrator pulls jobs from the queue using a priority-ordered query. Jobs are processed one at a time in v1 (sequential execution).

### Queue Selection Query

```sql
-- Pull the next job to execute
-- Priority order: CRITICAL=0, HIGH=1, STANDARD=2, LOW=3, BACKGROUND=4
-- Within same priority: earlier stage first, then HIGH_INTENT/TRANSACTIONAL keywords first,
-- then FIFO (created_at ASC)

SELECT j.*
FROM jobs j
LEFT JOIN keywords k ON j.payload->>'keyword_id' = k.id
WHERE j.run_id = :run_id
  AND j.status = 'QUEUED'
ORDER BY
    CASE j.priority
        WHEN 'CRITICAL'   THEN 0
        WHEN 'HIGH'       THEN 1
        WHEN 'STANDARD'   THEN 2
        WHEN 'LOW'        THEN 3
        WHEN 'BACKGROUND' THEN 4
    END ASC,
    j.stage ASC,
    CASE COALESCE(k.intent_class, 'INFORMATIONAL')
        WHEN 'TRANSACTIONAL'   THEN 0
        WHEN 'HIGH_INTENT'     THEN 1
        WHEN 'CONSIDERATION'   THEN 2
        WHEN 'INFORMATIONAL'   THEN 3
    END ASC,
    j.created_at ASC
LIMIT 1;
```

### Python Queue Processing Loop

```python
# src/scheduler/queue_processor.py

import asyncio
from datetime import datetime
from typing import Callable

class QueueProcessor:
    """
    v1: Sequential single-job processor.
    v2: Will be replaced by Celery workers.
    """

    def __init__(self, db, config, session_manager, pacing_manager):
        self.db = db
        self.config = config
        self.session_manager = session_manager
        self.pacing_manager = pacing_manager
        self._job_handlers: dict[str, Callable] = {}
        self._running = False
        self._processed = 0
        self._failed = 0

    def register_handler(self, job_type: str, handler: Callable):
        """Register a handler function for a specific job type."""
        self._job_handlers[job_type] = handler

    async def run_until_empty(self, run_id: str):
        """
        Processes all QUEUED jobs for the given run_id until none remain.
        v1: Sequential execution (one job at a time).
        """
        self._running = True

        while self._running:
            job = self._pull_next_job(run_id)

            if job is None:
                # No more queued jobs — run complete
                break

            await self._execute_job(job)
            self._processed += 1

            # Log progress every 100 jobs
            if self._processed % 100 == 0:
                remaining = self._count_queued(run_id)
                print(f"[QUEUE] Progress: {self._processed} complete, {remaining} remaining")

        self._running = False
        return self._processed, self._failed

    def stop(self):
        """Gracefully stops the queue processor after current job completes."""
        self._running = False

    def _pull_next_job(self, run_id: str):
        """Pulls the highest-priority queued job."""
        result = self.db.execute(NEXT_JOB_QUERY, {"run_id": run_id}).fetchone()
        if result:
            return self.db.query(Job).filter(Job.job_id == result.job_id).first()
        return None

    async def _execute_job(self, job: Job):
        """Executes a single job using its registered handler."""
        handler = self._job_handlers.get(job.job_type)
        if handler is None:
            job.status = "DEAD_LETTER"
            job.error_log = [f"No handler registered for job_type: {job.job_type}"]
            self.db.commit()
            self._failed += 1
            return

        success = await execute_with_retry(
            job_func=handler,
            job=job,
            pacing_manager=self.pacing_manager,
            session_manager=self.session_manager,
            db=self.db,
        )

        if not success:
            self._failed += 1

    def _count_queued(self, run_id: str) -> int:
        return self.db.query(Job).filter(
            Job.run_id == run_id,
            Job.status == "QUEUED"
        ).count()

    def get_stats(self) -> dict:
        return {
            "processed": self._processed,
            "failed": self._failed,
            "success_rate": (self._processed - self._failed) / max(1, self._processed),
        }
```

---

## Concurrent Job Limits

### v1 — Sequential (Single Job at a Time)

In v1, jobs execute sequentially — one job completes before the next begins. This is the safest approach for:
- Playwright sessions (shared browser context, single page at a time)
- Rate limiting (no risk of exceeding per-hour limits with parallel requests)
- SQLite write contention (sequential writes avoid lock conflicts)

```python
# v1: Sequential processing
# max_concurrent_jobs = 1 (hardcoded)
# All stages run sequentially
```

### v2 — Concurrent via Celery + Redis

In v2, different job types can run concurrently, limited by the concurrency configuration:

```yaml
# config.yaml (v2 only)
celery:
  worker_concurrency: 4          # Global max concurrent tasks
  concurrency_by_type:
    fiverr_search: 1             # Never parallel — shared Playwright session
    fiverr_gig_detail: 1         # Never parallel — shared session
    fiverr_seller_profile: 1     # Never parallel
    google_trends: 1             # Never parallel — rate limit sensitive
    reddit_api: 2                # Can parallelize slightly
    youtube: 4                   # Safe to parallelize
    gig_quality_title: 4         # LLM calls are async-safe
    gig_quality_desc: 2          # Higher cost — limit concurrency
    score_keyword: 8             # CPU-bound Python — safe to parallelize
    recommend_titles: 2          # LLM + write-heavy
```

---

## Dead-Letter Detection and Handling

### Detection

A job becomes DEAD_LETTER when:
1. `retry_count >= max_retries` AND the last attempt failed
2. A non-retryable error occurred (HTTP 404, HTTP 410, permanent error)

```python
def should_dead_letter(job: Job, error: Exception) -> bool:
    """Returns True if job should be moved to DEAD_LETTER."""
    config = RETRY_CONFIG.get(job.job_type, RETRY_CONFIG["_default"])

    # Check for permanent errors
    error_code = classify_error(error)
    if error_code in config["dead_letter_on"]:
        return True

    # Check retry count
    if job.retry_count >= config["max_retries"]:
        return True

    return False


def classify_error(error: Exception) -> str:
    """Maps exception type to error code for retry config lookup."""
    import httpx
    from playwright.async_api import Error as PlaywrightError

    if hasattr(error, "status_code"):
        if error.status_code == 404: return "HTTP_404"
        if error.status_code == 410: return "HTTP_410"
        if error.status_code == 429: return "HTTP_429"
        if error.status_code >= 500: return "HTTP_5XX"
    if isinstance(error, SessionLoginError): return "PERMANENT_BAN"
    if isinstance(error, asyncio.TimeoutError): return "TIMEOUT"
    if isinstance(error, (httpx.ConnectError, httpx.ConnectTimeout)): return "CONNECT_ERROR"
    if isinstance(error, PlaywrightError): return "PLAYWRIGHT_ERROR"
    return "UNKNOWN"
```

### Impact Assessment

When a job becomes DEAD_LETTER, its impact is assessed:

```python
# Job type → impact level
DEAD_LETTER_IMPACT = {
    "KEYWORD_EXPAND":    "HIGH",    # Blocks entire niche for this run
    "FIVERR_SEARCH":     "HIGH",    # Keyword gets no data
    "GIG_DETAIL":        "MEDIUM",  # Scoring degraded for keyword
    "SELLER_PROFILE":    "LOW",     # Competitor analysis degraded
    "GOOGLE_TRENDS":     "MEDIUM",  # Confidence deduction 0.15
    "REDDIT_COLLECT":    "LOW",     # Confidence deduction 0.05
    "YOUTUBE_COLLECT":   "LOW",     # Confidence deduction 0.03
    "GIG_QUALITY_DESC":  "MEDIUM",  # Gig weakness detection missing
    "CLUSTER_SYNTHESIS": "LOW",     # Narrative missing, scores unaffected
    "RECOMMEND_TITLES":  "LOW",     # That recommendation component null
    "SCORE_KEYWORD":     "HIGH",    # No score for this keyword
    "_default":          "LOW",
}
```

### Dead-Letter Dashboard View

The Run History page in Streamlit displays dead-letter jobs:

```
Run 2026-05-12 — 3 DEAD LETTER jobs
┌─────────────────────────────────────────────────────────────────┐
│ Job Type        │ Niche           │ Impact │ Last Error           │
├─────────────────┼─────────────────┼────────┼──────────────────────┤
│ GIG_DETAIL      │ prd_ai_saas     │ MEDIUM │ HTTP 404 after 3 retries│
│ GOOGLE_TRENDS   │ python_auto     │ MEDIUM │ 429 — rate limit exceeded│
│ SELLER_PROFILE  │ ai_agent_dev    │ LOW    │ Profile not found     │
└─────────────────────────────────────────────────────────────────┘
[Retry Dead Letter Jobs]  [Export Dead Letter Report]
```

---

## APScheduler v1 Setup

```python
# src/scheduler/scheduler_setup.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import logging

log = logging.getLogger(__name__)


def setup_scheduler(config, run_pipeline_func) -> AsyncIOScheduler:
    """
    Configures APScheduler for the v1 in-process scheduled runner.
    Uses AsyncIOScheduler to integrate with the async pipeline.
    """
    scheduler = AsyncIOScheduler(
        timezone=config.scheduler.timezone,
        job_defaults={
            "coalesce": True,       # Merge missed runs into one on recovery
            "max_instances": 1,     # Never run more than one instance simultaneously
            "misfire_grace_time": 3600,  # Allow up to 1hr late start
        }
    )

    # Register the weekly full run job
    if config.scheduler.enabled:
        scheduler.add_job(
            func=run_pipeline_func,
            trigger=CronTrigger.from_crontab(
                config.scheduler.jobs.weekly_full_run.cron,
                timezone=config.scheduler.timezone,
            ),
            args=["full"],          # Passes --mode full to run_pipeline
            id="weekly_full_run",
            name="Weekly Full Research Run",
            replace_existing=True,
        )
        log.info(f"Scheduled weekly run: {config.scheduler.jobs.weekly_full_run.cron} "
                 f"({config.scheduler.timezone})")

    # Event listeners for logging
    def on_job_executed(event):
        log.info(f"Scheduled job completed: {event.job_id}")

    def on_job_error(event):
        log.error(f"Scheduled job failed: {event.job_id} — {event.exception}")

    scheduler.add_listener(on_job_executed, EVENT_JOB_EXECUTED)
    scheduler.add_listener(on_job_error, EVENT_JOB_ERROR)

    return scheduler


# Usage in run.py:
# scheduler = setup_scheduler(config, run_pipeline)
# scheduler.start()
# try:
#     asyncio.get_event_loop().run_forever()
# except (KeyboardInterrupt, SystemExit):
#     scheduler.shutdown()
```

---

## Celery + Redis Migration Path (v2)

When ready to migrate from APScheduler (v1) to Celery + Redis (v2), the following changes are needed:

### Step 1 — Add Dependencies
```bash
pip install celery redis kombu
```

### Step 2 — Create Celery App
```python
# src/scheduler/celery_app.py
from celery import Celery

celery_app = Celery(
    "fiverr_research",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=config.scheduler.timezone,
    enable_utc=True,
    task_routes={
        "tasks.collection.*": {"queue": "collection"},
        "tasks.llm.*":        {"queue": "llm_analysis"},
        "tasks.scoring.*":    {"queue": "scoring"},
        "tasks.reporting.*":  {"queue": "reporting"},
    },
)
```

### Step 3 — Convert Job Handlers to Celery Tasks
```python
# src/scheduler/tasks/collection.py
from src.scheduler.celery_app import celery_app

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=15,
    queue="collection",
    routing_key="collection",
)
def collect_fiverr_search(self, job_payload: dict):
    """Celery task wrapping the fiverr_search collection handler."""
    try:
        return asyncio.run(fiverr_search_handler(job_payload))
    except RateLimitError as exc:
        raise self.retry(exc=exc, countdown=600)  # 10 min on 429
    except PermanentError:
        return {"status": "DEAD_LETTER"}
```

### Step 4 — Replace QueueProcessor with Celery Beat
```python
# src/scheduler/celery_beat.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "weekly-full-run": {
        "task": "tasks.orchestrator.run_full_pipeline",
        "schedule": crontab(hour=23, minute=0, day_of_week=0),  # Sunday 11pm
    },
}
```

### Step 5 — Start Workers
```bash
# Start Celery workers (run in separate terminals or via process manager)
celery -A src.scheduler.celery_app worker --queues=collection --concurrency=1
celery -A src.scheduler.celery_app worker --queues=llm_analysis --concurrency=4
celery -A src.scheduler.celery_app worker --queues=scoring --concurrency=8
celery -A src.scheduler.celery_app beat --loglevel=info
```

### What Stays the Same in v2
- All job handler logic (collection, analysis, scoring functions)
- Job schema and database tables
- Retry policies (Celery `max_retries` and `retry_delay`)
- Priority ordering (mapped to Celery task routing keys)
- Checkpoint and resume logic
- Session Manager (still one shared session per collection worker)
