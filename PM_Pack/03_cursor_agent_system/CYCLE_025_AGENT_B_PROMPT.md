====================================================================
AGENT B — CYCLE 025 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | Branch: cycle/025/integration
- Python 3.11+ | asyncio | SQLAlchemy 2.0

## ⚠️ HARD GATE REMINDER
codecov/patch ≥ 90% is a hard merge blocker. Run targeted coverage before handoff.

## YOUR ROLE
Agent B implements retry_handler.py — the full execute_with_retry() function with
proper backoff, RateLimitError, SessionExpiredError, and PermanentError handling.
This is the engine that QueueProcessor._execute_job() delegates to for resilient
job execution. Spec: RETRY_AND_CHECKPOINT.md "Backoff Implementation" section.

## GIT INSTRUCTIONS
1. Ensure on: cycle/025/integration. Pull latest.
2. Read Agent A handoff. Confirm CheckpointManager and retry_config.py exist.
3. Commit: feat(collection): retry_handler with full backoff logic [Agent B Cycle 025]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git branch --show-current; git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_checkpoint.py
Pass: branch = cycle/025/integration, Agent A tests pass.

## TASKS

### Task 1: Read Agent A handoff + read retry spec
Read: docs/cycle_reports/CYCLE_025_AGENT_A.md
Read: PM_Pack/ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md ("Backoff Implementation")
Read: src/scheduler/retry_config.py (Agent A's RETRY_CONFIG and helpers)
Read: src/scheduler/queue_processor.py (understand execute_with_retry usage)
Read: src/collection/session_manager.py (understand SessionLoginError)

### Task 2: Read E02 retry story key from SCRUM-17 children before coding
Read full AC/DoD. Transition to In Progress. Post planning comment.

### Task 3: Define custom exception classes in src/scheduler/exceptions.py
Create: src/scheduler/exceptions.py

class RateLimitError(Exception):
  """Raised when a 429 or rate limit is detected during collection."""
  def __init__(self, source: str = "unknown", retry_after_seconds: int = 600):
    self.source = source
    self.retry_after_seconds = retry_after_seconds
    super().__init__(f"Rate limit on {source}. Retry after {retry_after_seconds}s.")

class SessionExpiredError(Exception):
  """Raised when Fiverr session verification fails during collection."""
  pass

class PermanentError(Exception):
  """Raised for non-retryable errors (404, 410, permanent ban)."""
  def __init__(self, error_code: str, message: str = ""):
    self.error_code = error_code
    super().__init__(f"Permanent error [{error_code}]: {message}")

class CollectionError(Exception):
  """Base class for all collection-layer errors."""
  pass

### Task 4: Create src/scheduler/retry_handler.py
Implement EXACTLY as specced in RETRY_AND_CHECKPOINT.md "Backoff Implementation":

async def execute_with_retry(
  job_func: Callable,
  job: "Job",
  pacing_manager: "PacingManager",
  session_manager: "SessionManager",
  db,
) -> bool:
  """
  Executes a job function with full retry/backoff logic.
  Returns True on success, False if job is dead-lettered.
  Uses RETRY_CONFIG per job_type for backoff and dead-letter rules.
  """
  config = get_retry_config(job.job_type)

  for attempt in range(config["max_retries"] + 1):
    try:
      job.status = "RUNNING"
      job.started_at = datetime.now(UTC)
      if isinstance(db, Session): db.commit()

      await job_func(job)

      job.status = "COMPLETE"
      job.completed_at = datetime.now(UTC)
      if job.started_at:
        job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
      if isinstance(db, Session): db.commit()
      return True

    except RateLimitError as e:
      wait = e.retry_after_seconds or config["backoff_base_seconds"]
      job.error_log = (job.error_log or []) + [f"Attempt {attempt+1}: RateLimit — {e.source} — wait {wait}s"]
      job.retry_count += 1
      if isinstance(db, Session): db.commit()
      await asyncio.sleep(wait)

    except SessionExpiredError:
      await session_manager.force_relogin()
      job.error_log = (job.error_log or []) + [f"Attempt {attempt+1}: Session expired — re-logged in"]
      job.retry_count += 1
      if isinstance(db, Session): db.commit()

    except PermanentError as e:
      job.status = "DEAD_LETTER"
      job.error_log = (job.error_log or []) + [f"Permanent error [{e.error_code}]: {str(e)}"]
      job.completed_at = datetime.now(UTC)
      if isinstance(db, Session): db.commit()
      return False

    except Exception as e:
      error_code = classify_error(e)
      if is_no_retry_error(job.job_type, error_code):
        job.status = "DEAD_LETTER"
        job.error_log = (job.error_log or []) + [f"No-retry error [{error_code}]: {str(e)}"]
        job.completed_at = datetime.now(UTC)
        if isinstance(db, Session): db.commit()
        return False

      error_msg = f"Attempt {attempt+1}/{config['max_retries']+1}: {type(e).__name__}: {str(e)[:200]}"
      job.error_log = (job.error_log or []) + [error_msg]
      job.retry_count += 1
      if isinstance(db, Session): db.commit()

      if job.retry_count > config["max_retries"]:
        job.status = "DEAD_LETTER"
        job.completed_at = datetime.now(UTC)
        if isinstance(db, Session): db.commit()
        return False

      wait = min(
        config["backoff_base_seconds"] * (config["backoff_multiplier"] ** attempt),
        config["max_backoff_seconds"],
      )
      await asyncio.sleep(wait)

  job.status = "DEAD_LETTER"
  if isinstance(db, Session): db.commit()
  return False

### Task 5: Update QueueProcessor to use retry_handler
In src/scheduler/queue_processor.py, update _execute_job() to call execute_with_retry
from retry_handler.py instead of the inline execute_with_retry stub from Cycle 024.
Ensure imports do not create circular dependencies.

### Task 6: Update src/scheduler/__init__.py exports
Add: execute_with_retry, RateLimitError, SessionExpiredError, PermanentError, CollectionError

### Task 7: Write tests for retry_handler and exceptions
Create: tests/unit/test_retry_handler.py (minimum 16 tests)
All tests use mock job, mock session_manager, mock pacing_manager, mock db.
Use AsyncMock for async job_func.

- test_execute_with_retry_success — job_func completes → job COMPLETE, returns True
- test_execute_with_retry_updates_job_timing — started_at and completed_at set
- test_execute_with_retry_generic_exception_retries — raises Exception → retry_count +1
- test_execute_with_retry_max_retries_dead_letter — exceed max → DEAD_LETTER, False
- test_execute_with_retry_rate_limit_waits — RateLimitError → asyncio.sleep called
- test_execute_with_retry_session_expired_relogins — SessionExpiredError → force_relogin called
- test_execute_with_retry_permanent_error_dead_letters — PermanentError → DEAD_LETTER, False, no retry
- test_execute_with_retry_no_retry_error_dead_letters — no_retry_on error code → DEAD_LETTER immediately
- test_execute_with_retry_exponential_backoff — backoff grows per attempt
- test_execute_with_retry_max_backoff_capped — backoff capped at max_backoff_seconds
- test_rate_limit_error_attributes — RateLimitError.source and retry_after_seconds
- test_session_expired_error_message — SessionExpiredError is Exception
- test_permanent_error_code — PermanentError.error_code preserved
- test_collection_error_hierarchy — CollectionError is Exception subclass
- test_execute_with_retry_error_log_appends — each failure appends to job.error_log
- test_execute_with_retry_dict_db_no_crash — db=dict does not crash (no .commit())

### Task 8: Run targeted tests and patch coverage
python -m pytest -q tests/unit/test_retry_handler.py
python -m pytest -q --cov=src.scheduler.retry_handler --cov-report=term-missing
python -m pytest -q --cov=src.scheduler.exceptions --cov-report=term-missing
All ≥ 90%.

### Task 9: Run full validation block
All 6 commands. Target: ≥ 1307 tests. Coverage ≥ 90%.

### Task 10: Post Jira evidence for retry story key
Post implementation evidence comment with test count and coverage.

### Tasks 11-16: Standard completion
11. Update ACTIVE_STORY_DOD_LEDGER.md.
12. Artifact hygiene. 13. No-main check. 14. Record SHA. Handoff to C.
15. Create docs/cycle_reports/CYCLE_025_AGENT_B.md.
16. Commit. Message: feat(collection): retry_handler with full backoff logic [Agent B Cycle 025]

## COMMIT INSTRUCTIONS
git add src/scheduler/retry_handler.py src/scheduler/exceptions.py src/scheduler/__init__.py
git add src/scheduler/queue_processor.py tests/unit/test_retry_handler.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_025_AGENT_B.md
git commit -m "feat(collection): retry_handler with full backoff logic [Agent B Cycle 025]"
====================================================================
END OF AGENT B PROMPT
====================================================================
