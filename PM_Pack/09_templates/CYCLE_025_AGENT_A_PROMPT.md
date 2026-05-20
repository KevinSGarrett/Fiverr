====================================================================
AGENT A — CYCLE 025 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/025/integration
- Python 3.11+ | asyncio | SQLAlchemy 2.0
- Prior cycle PR: #28 ready to merge (1274 tests, 94.44%, codecov/patch 100%)

## ⚠️ HARD GATE RULES (PERMANENT)
G-001: codecov/patch ≥ 90% — HARD merge blocker.
G-003: Codex query MUST be run. Classify, fix VALID_FIXED with regression test,
  reply ALL threads with disposition format, resolve ALL threads manually.
G-004: Agent D must complete the mandatory merge gate checklist.

## YOUR ROLE
Agent A owns the PR gate, branch setup, CheckpointManager, and retry_config.py.
These are the two pieces needed before any retry or resume logic can work.
Spec: PM_Pack/ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md (read in full).

## GIT INSTRUCTIONS
1. Verify PR #28: gh pr view 28 --json state,mergeable,statusCheckRollup
   Confirm codecov/project=SUCCESS AND codecov/patch=SUCCESS.
2. Run Codex query for PR #28 (Task 2).
3. gh pr merge 28 --merge (only when all checks SUCCESS and Codex verified).
4. git checkout develop && git pull --ff-only origin develop
5. git checkout -b cycle/025/integration && git push -u origin cycle/025/integration
6. Commit: feat(collection): CheckpointManager and retry_config [Agent A Cycle 025]
7. Do NOT push final branch — human operator pushes.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 28 --json state,mergeable,statusCheckRollup
Pass: root = C:\Fiverr\Fiverr. All checks SUCCESS. Abort if codecov/patch FAILURE.

## TASKS

### Task 1: Preflight and PR #28 verification
Execute all 7 preflight commands. Confirm codecov/patch conclusion == SUCCESS.

### Task 2: Codex disposition query for PR #28 (MANDATORY)
Run:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=28
Confirm Agent D's 2 threads both show isResolved=true.
Document: "Codex query PR #28: [raw result]. Total: 2 threads, both VALID_FIXED, both resolved."

### Task 3: Merge PR #28, close SCRUM-513, create branch
- gh pr merge 28 --merge
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90 → expect 1274+, 94.44%+
- git checkout -b cycle/025/integration && git push -u origin cycle/025/integration
- Jira: SCRUM-513 → Done (post merge SHA comment)
- Jira: Create SCRUM-514 as Cycle 025 control → In Progress

### Task 4: Read RETRY_AND_CHECKPOINT.md spec in full (REQUIRED before coding)
Read: PM_Pack/ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md
Note: CheckpointManager class specification, atomic write pattern (os.replace),
  checkpoint JSON format (schema_version, stage, niche_id, progress fields),
  find_latest_run(), list_checkpoints(), cleanup() behavior.
Also read: src/collection/ directory to confirm checkpoint.py doesn't already exist.
Record design plan in report before writing code.

### Task 5: Identify E02 story keys for checkpoint/retry work
Query SCRUM-17 children. Find stories for:
  - Checkpoint system (S2.6 or similar)
  - Retry/backoff system (S2.7 or similar)
Transition each to In Progress. Post planning comments. Record keys in report.

### Task 6: Create src/collection/checkpoint.py — CheckpointManager
Implement EXACTLY as specced in RETRY_AND_CHECKPOINT.md "Checkpoint Atomic Write":

class CheckpointManager:
  def __init__(self, run_id: str, data_dir: str = "data"):
    self.run_id = run_id
    self.checkpoint_dir = Path(data_dir) / "checkpoints" / run_id
    self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

  def write(self, stage: str, niche_id: str, data: dict) -> None:
    """Atomically writes checkpoint using write-to-tmp-then-os.replace pattern."""
    # filename = f"{stage}_{niche_id}.json"
    # tmp_path = self.checkpoint_dir / f"{filename}.tmp"
    # final_path = self.checkpoint_dir / filename
    # Write JSON with common fields (schema_version, run_id, stage, niche_id, checkpoint_at)
    # merged with data dict → to tmp_path → os.fsync → os.replace(tmp_path, final_path)

  def read(self, stage: str, niche_id: str) -> dict | None:
    """Reads checkpoint file, returns None if missing or corrupt JSON."""

  def cleanup(self) -> None:
    """Removes entire checkpoint directory for this run."""

  def list_checkpoints(self) -> list[dict]:
    """Returns all valid checkpoint dicts sorted by stage."""

  @staticmethod
  def find_latest_run(data_dir: str = "data") -> str | None:
    """Returns most recent run_id with checkpoint files, or None."""

Key implementation details:
- MUST use os.replace() for atomic writes — not shutil.copy or direct writes
- MUST call os.fsync() before os.replace() to force disk write
- write() merges the provided data dict with common fields (do not overwrite them)
- read() returns None on json.JSONDecodeError or OSError (silent failure)
- cleanup() uses shutil.rmtree — only if checkpoint_dir exists
- find_latest_run() sorts by directory mtime descending, returns first with *.json files
- data/checkpoints/ must be gitignored (verify in .gitignore)

### Task 7: Create src/scheduler/retry_config.py
Implement EXACTLY as specced in RETRY_AND_CHECKPOINT.md "Per-Job-Type Retry Configuration":

RETRY_CONFIG: dict[str, dict] = {
  "FIVERR_SEARCH": { max_retries: 3, backoff_base_seconds: 15, backoff_multiplier: 2.0,
    max_backoff_seconds: 120, dead_letter_on: ["HTTP_404","HTTP_410","PERMANENT_BAN"],
    no_retry_on: ["HTTP_404","HTTP_410"], session_refresh_on: ["SESSION_EXPIRED"] },
  "GIG_DETAIL": { ... (as specced) },
  "SELLER_PROFILE": { ... (as specced) },
  "KEYWORD_EXPAND": { ... (as specced) },
  "GOOGLE_TRENDS": { max_retries: 5, backoff_base_seconds: 600, ... },
  "REDDIT_COLLECT": { ... (as specced) },
  "YOUTUBE_COLLECT": { ... (as specced) },
  "GIG_QUALITY_TITLE": { max_retries: 2, backoff_base_seconds: 10, ... },
  "GIG_QUALITY_DESC": { ... },
  "RECOMMEND_TITLES": { ... },
  "SCORE_KEYWORD": { max_retries: 3, backoff_base_seconds: 2, ... },
  "_default": { max_retries: 3, backoff_base_seconds: 10, backoff_multiplier: 2.0,
    max_backoff_seconds: 60, dead_letter_on: [], no_retry_on: [], session_refresh_on: [] },
}

Also implement these helper functions used by retry_handler.py:
def get_retry_config(job_type: str) -> dict:
  """Returns retry config for job_type, falling back to _default."""
  return RETRY_CONFIG.get(job_type, RETRY_CONFIG["_default"])

def should_dead_letter_on_error(job_type: str, error_code: str) -> bool:
  """Returns True if error_code is in dead_letter_on for this job type."""

def is_no_retry_error(job_type: str, error_code: str) -> bool:
  """Returns True if error_code is in no_retry_on for this job type."""

def classify_error(error: Exception) -> str:
  """Maps exception to error code string per RETRY_AND_CHECKPOINT.md table."""
  # HTTP 404 → "HTTP_404", HTTP 410 → "HTTP_410", HTTP 429 → "HTTP_429"
  # asyncio.TimeoutError → "TIMEOUT", ConnectionError → "CONNECT_ERROR"
  # SessionLoginError → "PERMANENT_BAN", else → "UNKNOWN"

### Task 8: Update src/scheduler/__init__.py exports
Add: RETRY_CONFIG, get_retry_config, should_dead_letter_on_error, classify_error

### Task 9: Write tests for CheckpointManager and retry_config
Create: tests/unit/test_checkpoint.py (minimum 14 tests)
- test_checkpoint_write_creates_file — write() creates JSON file at correct path
- test_checkpoint_write_atomic — tmp file removed, final JSON exists
- test_checkpoint_write_merges_common_fields — result has schema_version, run_id, checkpoint_at
- test_checkpoint_write_merges_data — provided data dict fields appear in file
- test_checkpoint_read_existing — read() returns dict from written file
- test_checkpoint_read_missing — read() returns None for missing file
- test_checkpoint_read_corrupt — read() returns None for invalid JSON
- test_checkpoint_cleanup — cleanup() removes directory
- test_checkpoint_cleanup_nonexistent — cleanup() does not crash if dir missing
- test_checkpoint_list_checkpoints — list_checkpoints() returns sorted list
- test_checkpoint_find_latest_run_none — no checkpoints → returns None
- test_checkpoint_find_latest_run_exists — checkpoint exists → returns run_id
- test_get_retry_config_known — FIVERR_SEARCH returns correct config
- test_get_retry_config_default — unknown job type returns _default
- test_should_dead_letter_http404 — FIVERR_SEARCH + HTTP_404 → True
- test_classify_error_timeout — asyncio.TimeoutError → "TIMEOUT"
- test_classify_error_unknown — generic Exception → "UNKNOWN"

### Task 10: Run targeted tests and patch coverage
python -m pytest -q tests/unit/test_checkpoint.py
python -m pytest -q --cov=src.collection.checkpoint --cov-report=term-missing
python -m pytest -q --cov=src.scheduler.retry_config --cov-report=term-missing
All new code ≥ 90% covered.

### Task 11: Run full validation block
python -m ruff check . && python -m mypy src
python -m pytest -q --cov=src --cov-fail-under=90
python run.py config-check && python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle025.db
python run.py phase2-smoke
Target: ≥ 1291 tests. Coverage ≥ 90%. All PASS.

### Task 12: Post Jira evidence for checkpoint/retry stories
Post evidence comments on identified story keys.

### Tasks 13-24: Standard completion
13. Update ACTIVE_STORY_DOD_LEDGER.md.
14. Artifact hygiene: no data/checkpoints/ staged.
15. No-main / worktree check.
16. Record SHA and handoff to Agent B.
17. Create docs/cycle_reports/CYCLE_025_AGENT_A.md.
18. Commit scoped files.
19-24. Smoke tests, handoff note for B.

## FILES CREATED THIS CYCLE (Agent A)
| Action | File |
|---|---|
| CREATE | src/collection/checkpoint.py |
| CREATE | src/scheduler/retry_config.py |
| MODIFY | src/scheduler/__init__.py |
| CREATE | tests/unit/test_checkpoint.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_025_AGENT_A.md |

## COMMIT INSTRUCTIONS
git add src/collection/checkpoint.py src/scheduler/retry_config.py src/scheduler/__init__.py
git add tests/unit/test_checkpoint.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_025_AGENT_A.md
git commit -m "feat(collection): CheckpointManager and retry_config [Agent A Cycle 025]"
====================================================================
END OF AGENT A PROMPT
====================================================================
