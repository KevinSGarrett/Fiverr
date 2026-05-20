====================================================================
AGENT A — CYCLE 027 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/027/integration
- Python 3.11+ | SQLAlchemy 2.0
- Prior cycle PR: #30 ready to merge (1434 tests, 94.82%, codecov/patch 100%)

## ⚠️ HARD GATE RULES (PERMANENT — APPLY EVERY CYCLE)
G-001: codecov/patch >= 90% — HARD merge blocker. Never merge while FAIL.
G-003: Codex query MUST run for every PR. Classify, fix VALID_FIXED with regression
  test, reply ALL threads with disposition format, resolve ALL manually.
G-004: Agent D completes mandatory merge gate checklist — ALL PASS/YES before merge.

## YOUR ROLE
Agent A: PR gate, branch setup, and ExternalSignal ORM model.
The ExternalSignal table is what the scoring engine reads for Google Trends and Reddit
demand signals. Without it, DemandScoreCalculator and TrendScoreCalculator can only
use None for their external signal components.
Spec: PM_Pack/ref/project_plan/03_data/SCHEMA.md (external_signals table)

## GIT INSTRUCTIONS
1. Verify PR #30: gh pr view 30 --json state,mergeable,statusCheckRollup
   Confirm codecov/project=SUCCESS AND codecov/patch=SUCCESS.
2. Run Codex query for PR #30 (Task 2). Confirm 1 thread isResolved=true.
3. gh pr merge 30 --merge (only when ALL checks SUCCESS and Codex confirmed).
4. git checkout develop && git pull --ff-only origin develop
5. git checkout -b cycle/027/integration && git push -u origin cycle/027/integration
6. Commit: feat(models): ExternalSignal ORM and write helpers [Agent A Cycle 027]
7. Do NOT push final branch — human operator pushes after all 4 agents.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 30 --json state,mergeable,statusCheckRollup
Pass: root=C:\Fiverr\Fiverr. ALL checks SUCCESS including codecov/patch.

## TASKS

### Task 1: Preflight and PR #30 verification
Run all 7 preflight commands. Verify codecov/patch == SUCCESS.

### Task 2: Codex query for PR #30 (MANDATORY)
Run exact GraphQL query for PR #30. Document verbatim.
Agent D confirmed: 1 thread, VALID_FIXED, isResolved=true.
If any thread not resolved: classify and resolve before merging.

### Task 3: Merge PR #30, close SCRUM-515, create branch
- gh pr merge 30 --merge
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90 → expect 1434+
- git checkout -b cycle/027/integration && git push -u origin cycle/027/integration
- Jira: SCRUM-515 → Done with merge SHA comment
- Jira: Create SCRUM-516 as Cycle 027 control → In Progress

### Task 4: Read SCHEMA.md external_signals table + scoring specs
Read: PM_Pack/ref/project_plan/03_data/SCHEMA.md (external_signals table)
Read: src/scoring/demand.py (understand what fields it reads from db for trend signals)
Read: src/scoring/trend.py (understand trends_12mo_score, trends_3mo_score fields)
Read: src/models/ directory (check if ExternalSignal already exists)

### Task 5: Verify ExternalSignal does not already exist
Run: Test-Path "src\models\external_signal.py"
Also check src/models/market.py and __init__.py for any existing ExternalSignal class.
Document findings before coding.

### Task 6: Create src/models/external_signal.py — ExternalSignal ORM

class ExternalSignal(Base):
  __tablename__ = "external_signals"
  id: int (PK autoincrement)
  keyword_id: int (ForeignKey keywords.id, not null, indexed)
  signal_type: str (not null)
    # Standard values: "google_trends", "reddit_demand", "reddit_activity",
    # "google_suggest_volume", "autocomplete_position"
  signal_value: float (nullable)   — primary numeric value for the signal
  signal_json: JSON (nullable)     — full detail dict (12-month series, subreddit data, etc.)
  source_url: str (nullable)       — source URL where signal was collected
  collected_at: datetime (UTC, not null, default now)
  ttl_hours: int (not null, default 168)
  is_stale: bool (not null, default False)
  run_id: str (nullable, indexed)
  collection_method: str (nullable) — "playwright", "pytrends_api", "reddit_api", "llm"
  error_message: str (nullable)     — capture if collection failed

  UniqueConstraint("keyword_id", "signal_type", "run_id")
  Index on (keyword_id, signal_type, collected_at.desc())
  Index on (run_id, signal_type)

Also add class-level signal type constants:
  SIGNAL_GOOGLE_TRENDS = "google_trends"
  SIGNAL_REDDIT_DEMAND = "reddit_demand"
  SIGNAL_REDDIT_ACTIVITY = "reddit_activity"
  SIGNAL_AUTOCOMPLETE_POSITION = "autocomplete_position"

### Task 7: Add write_external_signal() and query helpers

def write_external_signal(
  keyword_id: int, signal_type: str, signal_value: float | None,
  signal_json: dict | None, run_id: str | None, collection_method: str | None, db,
) -> "ExternalSignal | None":
  """Upserts ExternalSignal row. Returns None if not a Session."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return None
  row = ExternalSignal(keyword_id=keyword_id, signal_type=signal_type,
    signal_value=signal_value, signal_json=signal_json, run_id=run_id,
    collection_method=collection_method)
  db.merge(row)
  db.commit()
  return row

def get_signal(keyword_id: int, signal_type: str, db) -> "ExternalSignal | None":
  """Returns the latest ExternalSignal of given type for keyword, or None."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return None
  return (db.query(ExternalSignal)
    .filter(ExternalSignal.keyword_id == keyword_id,
            ExternalSignal.signal_type == signal_type)
    .order_by(ExternalSignal.collected_at.desc()).first())

def get_all_signals(keyword_id: int, db) -> list["ExternalSignal"]:
  """Returns all signals for a keyword ordered by signal_type."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return []
  return (db.query(ExternalSignal)
    .filter(ExternalSignal.keyword_id == keyword_id)
    .order_by(ExternalSignal.signal_type.asc()).all())

### Task 8: Register ExternalSignal in src/models/__init__.py
Add import + __all__ + helper exports. Verify:
  python -c "from src.models import ExternalSignal; print(ExternalSignal.__tablename__)"

### Task 9: Check that scoring calculators can now read ExternalSignal rows
Read: src/scoring/demand.py (_load_signals_from_db method)
Note: It queries ExternalSignal (signal_type="google_trends") for trends_12mo_score.
Verify the field names match your ExternalSignal.signal_json keys.
If there is a mismatch, document it in your report — do NOT change the scoring calculator
this cycle (that is a separate scope item).

### Task 10: Write tests (tests/unit/test_external_signal.py)
Required (minimum 14):
- test_external_signal_table_name → "external_signals"
- test_signal_type_constants → SIGNAL_GOOGLE_TRENDS == "google_trends"
- test_external_signal_insert_minimal → insert, query back
- test_external_signal_insert_full → all fields, no exception
- test_external_signal_nullable_json → signal_json can be None
- test_external_signal_unique_constraint → duplicate (keyword_id, signal_type, run_id) fails
- test_external_signal_index_exists → (keyword_id, signal_type) index registered
- test_write_signal_dict_db → None returned
- test_write_signal_orm → row persisted
- test_write_signal_upsert → second call updates row
- test_get_signal_found → returns correct signal
- test_get_signal_missing → None
- test_get_all_signals_empty → []
- test_get_all_signals_multiple → returns all, ordered by signal_type

### Task 11: Targeted patch coverage
python -m pytest -q --cov=src.models.external_signal --cov-report=term-missing
All new code >= 90% covered.

### Task 12: Full validation block
All 6 commands + python run.py collect-only.
Target: >= 1448 tests. Coverage >= 90%.

### Task 13: Post Jira evidence
Find E02 story for external signals (query SCRUM-17 children — may be SCRUM-15x).
Post: "Cycle 027 Agent A: ExternalSignal ORM created. external_signals table with
  google_trends, reddit_demand, reddit_activity signal types. write_external_signal(),
  get_signal(), get_all_signals() helpers. 14 tests. DoD remaining: Workflows 6/7
  (Google Trends/Reddit collection) write real rows."

### Tasks 14-24: Standard completion
14. Update ACTIVE_STORY_DOD_LEDGER.md
15. Artifact hygiene check
16. No-main / worktree check
17. Record SHA. Handoff to Agent B.
18. Create docs/cycle_reports/CYCLE_027_AGENT_A.md
19. Commit scoped files
20. Run python run.py phase2-smoke → must pass
21. Run python run.py collect-only → must pass
22. Post SCRUM-17 comment: ExternalSignal ORM now available for Workflows 6/7
23. Confirm scoring demand.py can import ExternalSignal without errors
24. Final SHA + test count

## COMMIT INSTRUCTIONS
git add src/models/external_signal.py src/models/__init__.py
git add tests/unit/test_external_signal.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_027_AGENT_A.md
git commit -m "feat(models): ExternalSignal ORM and write helpers [Agent A Cycle 027]"
====================================================================
END OF AGENT A PROMPT
====================================================================
