====================================================================
AGENT B — CYCLE 024 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/024/integration
- Python 3.11+ | SQLAlchemy 2.0 | APScheduler

## ⚠️ HARD GATE + COLLECTION PIVOT
codecov/patch ≥ 90% is a hard merge blocker. Run targeted coverage on all new files.
This cycle pivots to E02 Collection Engine infrastructure.
Spec: PM_Pack/ref/project_plan/04_collection/QUEUE_DESIGN.md (read in full).

## YOUR ROLE
Agent B builds the job queue infrastructure: the Job ORM model and QueueProcessor.
These two pieces are what the collection orchestrator uses to manage, dispatch, retry,
and dead-letter all collection tasks. The spec is fully detailed in QUEUE_DESIGN.md.

## GIT INSTRUCTIONS
1. Ensure on: cycle/024/integration. Pull latest.
2. Read Agent A handoff before coding.
3. Commit: feat(collection): Job ORM and QueueProcessor [Agent B Cycle 024]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_session_manager.py
Pass: branch = cycle/024/integration, Agent A tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + read spec
Read: docs/cycle_reports/CYCLE_024_AGENT_A.md
Read in full: PM_Pack/ref/project_plan/04_collection/QUEUE_DESIGN.md
Read: PM_Pack/ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md
Read: src/models/ directory (understand existing ORM pattern)

### Task 2: Read E02 S2.2 Jira story before coding
Query SCRUM-17 children → find S2.2 (Job model / queue). Read full AC/DoD.
Transition to In Progress. Post planning comment. Record key in report.

### Task 3: Create src/models/job.py — Job ORM model
Implement EXACTLY matching QUEUE_DESIGN.md DDL:

class Job(Base):
  __tablename__ = "jobs"
  id: int (PK autoincrement)
  job_id: str (unique, not null) — e.g. "job_20260518_fiverr_search_kw123"
  run_id: str (ForeignKey run_logs.run_id ON DELETE CASCADE, not null, indexed)
  job_type: str (not null) — e.g. "FIVERR_SEARCH", "GIG_DETAIL", "SELLER_PROFILE", etc.
  stage: int (not null) — stage number (1-15)
  niche_id: str (not null) — FK to niche_configs.niche_id
  priority: str (CHECK in ('CRITICAL','HIGH','STANDARD','LOW','BACKGROUND'), not null)
  status: str (CHECK in ('QUEUED','RUNNING','COMPLETE','FAILED','DEAD_LETTER','SKIPPED'),
    not null, default 'QUEUED')
  payload: JSON (nullable) — job input data dict
  result_ref: str (nullable) — reference to result row
  retry_count: int (not null, default 0)
  max_retries: int (not null, default 3)
  error_log: JSON (nullable) — list of error strings
  checkpoint_ref: str (nullable) — path to checkpoint file
  created_at: datetime (UTC, not null, default now)
  started_at: datetime (nullable)
  completed_at: datetime (nullable)
  duration_seconds: float (nullable)

Indexes:
  Index on (run_id, status)
  Index on (priority, stage)
  Index on (niche_id, status)
  Index on (job_type, status)

Also add helper methods:
  def mark_running(self): self.status = "RUNNING"; self.started_at = datetime.now(UTC)
  def mark_complete(self): self.status = "COMPLETE"; self.completed_at = datetime.now(UTC)
    self.duration_seconds = (self.completed_at - self.started_at).total_seconds() if self.started_at else None
  def mark_failed(self, error: str): self.retry_count += 1; self.error_log = (self.error_log or []) + [error]
    self.status = "FAILED" if self.retry_count < self.max_retries else "DEAD_LETTER"
  def should_dead_letter(self) -> bool: return self.status == "DEAD_LETTER"

### Task 4: Register Job in src/models/__init__.py
Add import and __all__ entry. Verify:
  python -c "from src.models import Job; print(Job.__tablename__)" → "jobs"
  python run.py init-db → should show jobs table created (or already exists)

### Task 5: Create src/scheduler/queue_processor.py
Implement EXACTLY as specced in QUEUE_DESIGN.md "Python Queue Processing Loop":

class QueueProcessor:
  def __init__(self, db, config, session_manager, pacing_manager):
    self.db = db
    self.config = config
    self.session_manager = session_manager
    self.pacing_manager = pacing_manager
    self._job_handlers: dict[str, Callable] = {}
    self._running = False
    self._processed = 0
    self._failed = 0

  def register_handler(self, job_type: str, handler: Callable) -> None
  async def run_until_empty(self, run_id: str) -> tuple[int, int]:
    """Sequential v1: processes jobs one at a time until none remain."""
  def stop(self) -> None
  def _pull_next_job(self, run_id: str) -> Job | None:
    """Implements QUEUE_DESIGN.md priority query."""
  async def _execute_job(self, job: Job) -> None
  def _count_queued(self, run_id: str) -> int
  def get_stats(self) -> dict

Also implement execute_with_retry():
async def execute_with_retry(job_func, job: Job, pacing_manager, session_manager, db) -> bool:
  """Runs job_func with retry logic. Marks job COMPLETE, FAILED, or DEAD_LETTER."""
  job.mark_running()
  db.commit()
  try:
    await job_func(job, session_manager=session_manager, pacing_manager=pacing_manager, db=db)
    job.mark_complete()
    db.commit()
    return True
  except Exception as e:
    job.mark_failed(str(e))
    db.commit()
    return False

### Task 6: Create priority query constant NEXT_JOB_QUERY
In queue_processor.py, define the SQL query from QUEUE_DESIGN.md "Queue Selection Query"
as a text() query or equivalent ORM query. This is what _pull_next_job() uses.
ORM equivalent:
  from sqlalchemy import case, asc
  return (db.query(Job)
    .filter(Job.run_id == run_id, Job.status == "QUEUED")
    .order_by(
      case({
        "CRITICAL": 0, "HIGH": 1, "STANDARD": 2, "LOW": 3, "BACKGROUND": 4
      }, value=Job.priority).asc(),
      Job.stage.asc(),
      Job.created_at.asc(),
    ).first())

### Task 7: Create src/scheduler/__init__.py with exports
Export: QueueProcessor, execute_with_retry

### Task 8: Write tests for Job model and QueueProcessor
Create: tests/unit/test_queue_processor.py
Use in-memory SQLite session for all DB tests.
Required tests (minimum 14):
- test_job_table_name → "jobs"
- test_job_insert_minimal → insert with required fields, query back
- test_job_mark_running → status=RUNNING, started_at set
- test_job_mark_complete → status=COMPLETE, completed_at set, duration_seconds computed
- test_job_mark_failed_first_failure → retry_count=1, status=FAILED (not dead letter)
- test_job_mark_failed_max_retries → retry_count=max_retries → status=DEAD_LETTER
- test_job_error_log_appends → successive failures append to error_log list
- test_job_priority_enum → invalid priority → constraint violation
- test_job_status_enum → invalid status → constraint violation
- test_queue_processor_register_handler → handler registered correctly
- test_queue_processor_no_jobs → run_until_empty with no queued jobs → (0, 0)
- test_queue_processor_processes_job → one QUEUED job → handler called, job marked COMPLETE
- test_queue_processor_handler_failure → handler raises → job marked FAILED
- test_queue_processor_stop → stop() sets _running=False, loop exits
- test_execute_with_retry_success → returns True, job COMPLETE
- test_execute_with_retry_failure → returns False, job FAILED

### Task 9: Run targeted patch coverage
python -m pytest -q --cov=src.models.job --cov-report=term-missing
python -m pytest -q --cov=src.scheduler.queue_processor --cov-report=term-missing
All new code ≥ 90% covered.

### Task 10: Run full validation block
All 6 commands. Target: ≥ 1191 tests. Coverage ≥ 90%.

### Task 11: Post Jira evidence for E02 S2.2
Post: "Cycle 024 Agent B: Job ORM model created (jobs table, all priority/status constraints,
  indexes). QueueProcessor sequential v1 with priority ordering. execute_with_retry() helper.
  16 tests. DoD remaining: integration with real collection run, checkpoint file writes."

### Tasks 12-16: Standard completion
12. Update ACTIVE_STORY_DOD_LEDGER.md.
13. Artifact hygiene check.
14. No-main / worktree check. Record SHA.
15. Create docs/cycle_reports/CYCLE_024_AGENT_B.md.
16. Commit. Message: feat(collection): Job ORM and QueueProcessor [Agent B Cycle 024]

## COMMIT INSTRUCTIONS
git add src/models/job.py src/models/__init__.py src/scheduler/
git add tests/unit/test_queue_processor.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_024_AGENT_B.md
git commit -m "feat(collection): Job ORM and QueueProcessor [Agent B Cycle 024]"
====================================================================
END OF AGENT B PROMPT
====================================================================
