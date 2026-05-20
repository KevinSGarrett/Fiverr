# Retry and Checkpoint Design
# Fiverr Research System — Wave 4

**Document Status:** Complete
**Wave:** 4 — Collection Engine Design
**Purpose:** Complete retry policy per job type and error type, checkpoint JSON format spec, atomic write implementation, resume algorithm, checkpoint cleanup, and backoff implementation.

---

## Retry Policy — Complete Table

Every job type has a defined maximum retry count and behavior per error type.

### Error Type Classification

| Error Category | Python Exception / HTTP Code | Retry? | Notes |
|---|---|---|---|
| Rate limited | HTTP 429, TooManyRequests | Yes | Long pause, adaptive pacing |
| Server error | HTTP 5xx | Yes | Transient — retry with backoff |
| Not found | HTTP 404, 410 | No | Permanent — gig/page deleted |
| Auth expired | Session verification fails | Yes | Re-login then retry |
| Network timeout | asyncio.TimeoutError, PlaywrightTimeoutError | Yes | Transient |
| Connection error | httpx.ConnectError, ConnectionRefusedError | Yes | Transient |
| Parse error | AttributeError, KeyError (selector fail) | Partial | Store null for field, continue |
| LLM API error | openai.APIError | Yes (once) | Single retry |
| LLM parse error | pydantic.ValidationError | Yes (once) | Self-correction retry |
| LLM 2nd failure | ValidationError on retry | No | Store null, confidence deduction |
| Browser crash | playwright.Error (process died) | Yes | Re-launch browser |
| DB write error | sqlalchemy.exc.OperationalError | Yes | SQLite lock — short backoff |
| Config error | ValueError, KeyError on config read | No | Fatal — halt run |

---

### Per-Job-Type Retry Configuration

```python
# src/scheduler/retry_config.py

RETRY_CONFIG: dict[str, dict] = {
    # ── Fiverr Collection ────────────────────────────────────────────
    "FIVERR_SEARCH": {
        "max_retries": 3,
        "backoff_base_seconds": 15,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 120,
        "dead_letter_on": ["HTTP_404", "HTTP_410", "PERMANENT_BAN"],
        "no_retry_on": ["HTTP_404", "HTTP_410"],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },
    "GIG_DETAIL": {
        "max_retries": 3,
        "backoff_base_seconds": 15,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 120,
        "dead_letter_on": ["HTTP_404", "HTTP_410"],
        "no_retry_on": ["HTTP_404", "HTTP_410"],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },
    "SELLER_PROFILE": {
        "max_retries": 3,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60,
        "dead_letter_on": ["HTTP_404"],
        "no_retry_on": ["HTTP_404"],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },

    # ── Keyword Expansion ────────────────────────────────────────────
    "KEYWORD_EXPAND": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": ["SESSION_EXPIRED"],
    },

    # ── External Sources ─────────────────────────────────────────────
    "GOOGLE_TRENDS": {
        "max_retries": 5,            # More retries — 429s are common
        "backoff_base_seconds": 600, # 10 minutes on first 429
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 3600, # Max 1 hour wait
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "REDDIT_COLLECT": {
        "max_retries": 2,
        "backoff_base_seconds": 60,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 300,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "YOUTUBE_COLLECT": {
        "max_retries": 2,
        "backoff_base_seconds": 300,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 600,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },

    # ── LLM Analysis Jobs ────────────────────────────────────────────
    "GIG_QUALITY_TITLE": {
        "max_retries": 2,            # 1 standard + 1 self-correction
        "backoff_base_seconds": 10,
        "backoff_multiplier": 1.0,   # No exponential for LLM — just wait 10s
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    "GIG_QUALITY_DESC": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 1.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
    # All other LLM jobs use same config as GIG_QUALITY_TITLE

    # ── Recommendation Jobs ──────────────────────────────────────────
    "RECOMMEND_TITLES": {
        "max_retries": 2,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 1.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },

    # ── Scoring and Reporting ────────────────────────────────────────
    "SCORE_KEYWORD": {
        "max_retries": 3,
        "backoff_base_seconds": 2,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 10,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },

    # ── Default (applied to any unlisted job type) ───────────────────
    "_default": {
        "max_retries": 3,
        "backoff_base_seconds": 10,
        "backoff_multiplier": 2.0,
        "max_backoff_seconds": 60,
        "dead_letter_on": [],
        "no_retry_on": [],
        "session_refresh_on": [],
    },
}
```

---

## Backoff Implementation

```python
# src/scheduler/retry_handler.py

import asyncio
import math
from datetime import datetime

async def execute_with_retry(
    job_func,
    job: Job,
    pacing_manager: PacingManager,
    session_manager: SessionManager,
    db,
) -> bool:
    """
    Executes a job function with retry logic.
    Returns True on success, False if job is dead-lettered.
    """
    config = RETRY_CONFIG.get(job.job_type, RETRY_CONFIG["_default"])

    for attempt in range(config["max_retries"] + 1):
        try:
            job.status = "RUNNING"
            job.started_at = datetime.utcnow()
            db.commit()

            result = await job_func(job)

            # Success
            job.status = "COMPLETE"
            job.completed_at = datetime.utcnow()
            job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            db.commit()
            return True

        except RateLimitError as e:
            # 429 handling — long pause + adaptive pacing
            pacing_manager.on_rate_limit_error(job_type_to_source(job.job_type))
            wait = config["backoff_base_seconds"]
            job.error_log = (job.error_log or []) + [f"Attempt {attempt+1}: RateLimit — pausing {wait}s"]
            job.retry_count += 1
            db.commit()
            await asyncio.sleep(wait)

        except SessionExpiredError:
            # Session refresh and retry
            await session_manager.force_relogin()
            job.error_log = (job.error_log or []) + [f"Attempt {attempt+1}: Session expired — re-logged in"]
            job.retry_count += 1
            db.commit()

        except PermanentError as e:
            # Non-retryable — go straight to dead letter
            job.status = "DEAD_LETTER"
            job.error_log = (job.error_log or []) + [f"Permanent error: {str(e)}"]
            job.completed_at = datetime.utcnow()
            db.commit()
            return False

        except Exception as e:
            error_msg = f"Attempt {attempt+1}/{config['max_retries']+1}: {type(e).__name__}: {str(e)}"
            job.error_log = (job.error_log or []) + [error_msg]
            job.retry_count += 1
            db.commit()

            if job.retry_count > config["max_retries"]:
                # Exceeded max retries — dead letter
                job.status = "DEAD_LETTER"
                job.completed_at = datetime.utcnow()
                db.commit()
                return False

            # Exponential backoff
            wait = min(
                config["backoff_base_seconds"] * (config["backoff_multiplier"] ** attempt),
                config["max_backoff_seconds"]
            )
            await asyncio.sleep(wait)

    # Should not reach here, but safety net
    job.status = "DEAD_LETTER"
    db.commit()
    return False
```

---

## Checkpoint JSON Format Specification

All checkpoint files are stored in `data/checkpoints/{run_id}/{stage}_{niche_id}.json`.

### Common Fields (all checkpoints)

```json
{
  "schema_version": "1.0",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "stage04",
  "stage_name": "GIG_DETAIL_COLLECTION",
  "niche_id": "prd_ai_saas",
  "depth": "full",
  "records_complete": 150,
  "records_total": 280,
  "progress_pct": 53.6,
  "started_at": "2026-05-12T00:01:00Z",
  "checkpoint_at": "2026-05-12T00:45:22Z",
  "errors_so_far": 2,
  "dead_letters_so_far": 0
}
```

### Stage-Specific Fields

**Stage 2 (Keyword Expansion):**
```json
{
  "last_seed_processed": "AI product roadmap",
  "seeds_complete": 5,
  "seeds_total": 8,
  "keywords_written": 127,
  "llm_calls_made": 12,
  "llm_cache_hits": 3
}
```

**Stage 3 (Fiverr Search):**
```json
{
  "last_keyword_id": 1234,
  "last_keyword_text": "MVP PRD",
  "queue_position": 51,
  "gig_urls_queued": 892
}
```

**Stage 4 (Gig Detail):**
```json
{
  "last_gig_url": "https://www.fiverr.com/seller/gig-slug",
  "last_gig_id": 5678,
  "gig_urls_remaining": 130,
  "sellers_queued": 45
}
```

**Stage 5 (Seller Profile):**
```json
{
  "last_seller_username": "example_seller",
  "sellers_remaining": 23
}
```

**Stage 6 (External Signals):**
```json
{
  "google_trends_batches_complete": 3,
  "google_trends_batches_total": 6,
  "reddit_complete": false,
  "youtube_complete": false
}
```

---

## Checkpoint Atomic Write Implementation

Checkpoint writes use the atomic rename pattern to prevent corrupt checkpoint files.

```python
# src/collection/checkpoint.py

import json
import os
from pathlib import Path
from datetime import datetime


class CheckpointManager:
    def __init__(self, run_id: str, data_dir: str = "data"):
        self.run_id = run_id
        self.checkpoint_dir = Path(data_dir) / "checkpoints" / run_id
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def write(self, stage: str, niche_id: str, data: dict):
        """
        Atomically writes a checkpoint file.
        Uses write-to-tmp-then-rename to prevent partial writes.
        """
        filename = f"{stage}_{niche_id}.json"
        tmp_path = self.checkpoint_dir / f"{filename}.tmp"
        final_path = self.checkpoint_dir / filename

        # Add common fields
        checkpoint_data = {
            "schema_version": "1.0",
            "run_id": self.run_id,
            "stage": stage,
            "niche_id": niche_id,
            "checkpoint_at": datetime.utcnow().isoformat() + "Z",
            **data,
        }

        # Write to .tmp file first
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk

        # Atomic rename: .tmp → .json
        # On POSIX (Linux/Mac): os.replace is atomic
        # On Windows: os.replace is atomic within the same filesystem
        os.replace(tmp_path, final_path)

    def read(self, stage: str, niche_id: str) -> dict | None:
        """Reads a checkpoint file, returns None if not found or invalid."""
        path = self.checkpoint_dir / f"{stage}_{niche_id}.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None  # Corrupt checkpoint — treat as missing

    def cleanup(self):
        """Removes all checkpoint files for this run after successful completion."""
        import shutil
        if self.checkpoint_dir.exists():
            shutil.rmtree(self.checkpoint_dir)

    def list_checkpoints(self) -> list[dict]:
        """Returns all checkpoint files for this run, sorted by stage."""
        checkpoints = []
        for path in sorted(self.checkpoint_dir.glob("*.json")):
            data = self.read(path.stem.split("_")[0], "_".join(path.stem.split("_")[1:]))
            if data:
                checkpoints.append(data)
        return checkpoints

    @staticmethod
    def find_latest_run(data_dir: str = "data") -> str | None:
        """Finds the most recent run_id with checkpoint files."""
        checkpoint_root = Path(data_dir) / "checkpoints"
        if not checkpoint_root.exists():
            return None
        run_dirs = sorted(checkpoint_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        valid_dirs = [d for d in run_dirs if d.is_dir() and list(d.glob("*.json"))]
        return valid_dirs[0].name if valid_dirs else None
```

---

## Resume Algorithm (--mode resume)

```python
# src/core/orchestrator.py (resume mode)

async def resume_run(data_dir: str, db, config):
    """
    Finds the most recent interrupted run and resumes it from the last checkpoint.
    """
    # Step 1: Find latest run with checkpoints
    run_id = CheckpointManager.find_latest_run(data_dir)
    if not run_id:
        print("No checkpoint files found. Please run 'python run.py --mode full' instead.")
        return

    print(f"Found interrupted run: {run_id}")

    # Step 2: Load run log
    run_log = db.query(RunLog).filter(RunLog.run_id == run_id).first()
    if not run_log:
        print(f"Run log not found for {run_id}. Cannot resume.")
        return

    if run_log.status == "COMPLETE":
        print(f"Run {run_id} is already marked COMPLETE. Nothing to resume.")
        return

    print(f"Resuming run {run_id} (status: {run_log.status}, mode: {run_log.mode})")

    # Step 3: Load all checkpoints for this run
    checkpoint_mgr = CheckpointManager(run_id, data_dir)
    checkpoints = checkpoint_mgr.list_checkpoints()
    print(f"Found {len(checkpoints)} checkpoint file(s).")

    # Step 4: Reset any RUNNING jobs back to QUEUED
    running_jobs = db.query(Job).filter(
        Job.run_id == run_id,
        Job.status == "RUNNING"
    ).all()
    for job in running_jobs:
        job.status = "QUEUED"
        job.started_at = None
    db.commit()
    print(f"Reset {len(running_jobs)} interrupted RUNNING jobs to QUEUED.")

    # Step 5: For each checkpoint, validate and determine resume position
    for checkpoint in checkpoints:
        stage = checkpoint["stage"]
        niche_id = checkpoint["niche_id"]
        position = checkpoint.get("queue_position", 0)
        print(f"  Checkpoint: {stage} / {niche_id} — resuming from position {position}")

        # Re-enqueue incomplete jobs from this checkpoint position
        incomplete_jobs = db.query(Job).filter(
            Job.run_id == run_id,
            Job.niche_id == niche_id,
            Job.stage == stage_to_int(stage),
            Job.status == "QUEUED",
        ).order_by(Job.created_at).offset(position).all()

        for job in incomplete_jobs:
            job.status = "QUEUED"  # Ensure queued (may have been SKIPPED)

    db.commit()

    # Step 6: Update run log status
    run_log.status = "RUNNING"
    db.commit()

    # Step 7: Continue run from job queue
    await run_from_queue(run_id, db, config)
    print(f"Run {run_id} resumed and completed.")
```

---

## Checkpoint Cleanup Rules

```python
# After successful run completion (Stage 15):
checkpoint_mgr.cleanup()
# Removes: data/checkpoints/{run_id}/ directory and all files within it

# After --mode resume completes successfully:
checkpoint_mgr.cleanup()

# NOT cleaned up when:
# - Run ends in FAILED status (keep for next resume attempt)
# - Run is interrupted (keep for next resume attempt)
# - User runs --mode retry-dead-letter (keep original run checkpoints)

# Orphaned checkpoints (runs older than 30 days with no matching run_log):
# Cleaned up by: python run.py --mode cleanup-checkpoints
```

---

## Partial Run vs. Interrupted Run

| Scenario | Checkpoint State | Resume Behavior |
|---|---|---|
| Run interrupted mid-collection (power loss, Ctrl+C) | Checkpoint exists at last 50-record boundary | Resume from checkpoint position |
| Run completed Stage 3 but crashed before Stage 4 | Stage 3 checkpoint marked complete; Stage 4 checkpoint absent | Resume from Stage 4, start of queue |
| `--mode collect-only` run (by design partial) | Stages 1–6 checkpointed | `--mode resume` continues with Stage 7+ |
| Run fully complete | All checkpoints cleaned up | No resume needed — `--mode full` starts fresh |
| Run failed with all jobs DEAD_LETTER | Checkpoints exist | `--mode retry-dead-letter` re-queues DEAD_LETTER jobs |
