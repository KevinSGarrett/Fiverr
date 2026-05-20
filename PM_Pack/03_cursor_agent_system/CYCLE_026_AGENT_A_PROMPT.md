====================================================================
AGENT A — CYCLE 026 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/026/integration
- Python 3.11+ | SQLAlchemy 2.0
- Prior cycle PR: #29 ready to merge (1347 tests, 94.69%, codecov/patch 100%)

## ⚠️ HARD GATE RULES (PERMANENT — APPLY EVERY CYCLE)
G-001: codecov/patch >= 90% — HARD merge blocker. Never merge while FAIL.
G-003: Codex query MUST run for every PR. Classify, fix VALID_FIXED with regression
  test, reply ALL threads with disposition format, resolve ALL manually.
G-004: Agent D completes mandatory merge gate checklist — ALL PASS/YES before merge.

## ⚠️ SCOPE GAP CONTEXT

Cycle 025 agents pivoted from the planned SearchResult ORM to infrastructure work.
The SearchResult ORM was NEVER built. Cycle 026 Agent A owns this gap.
Without SearchResult ORM, Workflow 3 cannot write collected data to the DB.
This is the highest priority item for Cycle 026.

## YOUR ROLE
Agent A: PR gate, branch setup, and SearchResult ORM model.
Spec: PM_Pack/ref/project_plan/03_data/SCHEMA.md (search_results table section).
      PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflow 3 output).

## GIT INSTRUCTIONS
1. Verify PR #29: gh pr view 29 --json state,mergeable,statusCheckRollup
   Confirm codecov/project=SUCCESS AND codecov/patch=SUCCESS.
2. Run Codex query for PR #29 (Task 2). Confirm 2 threads isResolved=true.
3. gh pr merge 29 --merge (only when ALL checks SUCCESS and Codex confirmed).
4. git checkout develop && git pull --ff-only origin develop
5. git checkout -b cycle/026/integration && git push -u origin cycle/026/integration
6. Commit: feat(models): SearchResult ORM and write helper [Agent A Cycle 026]
7. Do NOT push final branch — human operator pushes after all 4 agents.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 29 --json state,mergeable,statusCheckRollup
Pass: root=C:\Fiverr\Fiverr. ALL checks SUCCESS including codecov/patch.

## TASKS

### Task 1: Preflight and PR #29 verification
Run all 7 preflight commands. Verify codecov/patch == SUCCESS.

### Task 2: Codex query for PR #29 (MANDATORY)
Run:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=29
Document: "Codex query PR #29: total threads=2, both isResolved=true (Agent D confirmed)."
If any not resolved: classify and resolve before merging.

### Task 3: Merge PR #29, close SCRUM-514, create branch
- gh pr merge 29 --merge
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90
- git checkout -b cycle/026/integration && git push -u origin cycle/026/integration
- Jira: SCRUM-514 → Done with merge SHA comment
- Jira: Create SCRUM-515 as Cycle 026 control → In Progress

### Task 4: Read SCHEMA.md and COLLECTION_WORKFLOWS.md (Workflow 3 output)
Read: PM_Pack/ref/project_plan/03_data/SCHEMA.md (search_results table section)
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (W3 output spec)
Read: src/models/ directory (understand existing ORM Base pattern)
Query SCRUM-17 children → find the search_results/search collection story (likely SCRUM-141 or nearby).

### Task 5: Verify src/models/search_result.py does not already exist
Run: Test-Path "src\models\search_result.py"
If TRUE: read the file and document what exists, then extend if needed.
If FALSE: create it fresh per spec.

### Task 6: Create src/models/search_result.py — SearchResult ORM model

class SearchResult(Base):
  __tablename__ = "search_results"
  id: int (PK autoincrement)
  keyword_id: int (ForeignKey to keywords.id, not null, indexed)
  run_id: str (not null, indexed)
  total_result_count: int (nullable — text like "1,234 results")
  pagination_depth: int (nullable — how many pages available)
  gig_cards: JSON (nullable — list of raw gig card dicts from Workflow 3)
  page_collected: int (not null, default 1)
  collected_at: datetime (UTC, not null, default now)
  ttl_hours: int (not null, default 168)
  is_stale: bool (not null, default False)
  raw_html_ref: str (nullable)

  UniqueConstraint("keyword_id", "run_id", "page_collected")
  Index on (keyword_id, collected_at.desc())
  Index on (run_id, keyword_id)

### Task 7: Add write_search_result() helper to src/models/search_result.py

def write_search_result(
  keyword_id: int,
  run_id: str,
  total_result_count: int | None,
  pagination_depth: int | None,
  gig_cards: list[dict],
  page_collected: int,
  db,
) -> "SearchResult | None":
  """Upserts a SearchResult row. Returns None if db is not a Session."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session):
    return None
  row = SearchResult(
    keyword_id=keyword_id, run_id=run_id,
    total_result_count=total_result_count, pagination_depth=pagination_depth,
    gig_cards=gig_cards, page_collected=page_collected,
  )
  db.merge(row)
  db.commit()
  return row

def get_latest_search_result(keyword_id: int, db) -> "SearchResult | None":
  """Returns most recent SearchResult for this keyword, or None."""
  from sqlalchemy.orm import Session
  if not isinstance(db, Session):
    return None
  return (db.query(SearchResult)
    .filter(SearchResult.keyword_id == keyword_id)
    .order_by(SearchResult.collected_at.desc())
    .first())

### Task 8: Register SearchResult in src/models/__init__.py
Add import and __all__ entry. Verify:
  python -c "from src.models import SearchResult; print(SearchResult.__tablename__)"

### Task 9: Ensure init_db creates search_results table
Run: python run.py init-db
Or: python -c "from src.models import Base; from src.scripts.init_db import init_db; init_db()"
Verify "search_results" appears in table list.

### Task 10: Write tests (tests/unit/test_search_result.py)
Required (minimum 14):
- test_search_result_table_name → "search_results"
- test_search_result_insert_minimal → insert, query back
- test_search_result_insert_full → all fields, no exception
- test_search_result_gig_cards_json → stores list of dicts
- test_search_result_nullable_fields → total_result_count, pagination_depth can be None
- test_search_result_default_ttl → ttl_hours = 168
- test_search_result_default_page → page_collected = 1
- test_search_result_unique_constraint → duplicate (keyword_id, run_id, page) fails
- test_search_result_index_exists → (keyword_id, collected_at) index registered
- test_write_search_result_dict_db → dict db → None returned
- test_write_search_result_orm → Session db → row persisted
- test_write_search_result_upsert → second call updates row
- test_get_latest_search_result_found → returns newest row
- test_get_latest_search_result_missing → no rows → None

### Task 11: Targeted patch coverage
python -m pytest -q --cov=src.models.search_result --cov-report=term-missing
All new code >= 90% covered.

### Task 12: Full validation block
All 6 commands. Target: >= 1361 tests. Coverage >= 90%.

### Task 13: Post Jira evidence for search_results story
Post on SCRUM-141 or relevant E02 search story: "Cycle 026 Agent A: SearchResult ORM
  created (search_results table, UniqueConstraint, indexes, write_search_result() helper,
  get_latest_search_result() query). 14 tests. DoD remaining: Workflow 3 writes rows
  via real Playwright (Agent B this cycle)."

### Tasks 14-24: Standard completion
14. Update ACTIVE_STORY_DOD_LEDGER.md
15. Artifact hygiene: no .env, *.db, coverage.xml, data/sessions/ staged
16. No-main / worktree check
17. Record SHA. Handoff to Agent B.
18. Create docs/cycle_reports/CYCLE_026_AGENT_A.md
19. Commit scoped files only
20. Run python run.py phase2-smoke → must pass
21. Run python run.py collect-only → must pass
22. Post SCRUM-17 comment noting SearchResult ORM now available for Workflow 3
23. Confirm .cursorrules compliance
24. Final SHA + test count recorded

## COMMIT INSTRUCTIONS
git add src/models/search_result.py src/models/__init__.py
git add tests/unit/test_search_result.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_026_AGENT_A.md
git commit -m "feat(models): SearchResult ORM and write helper [Agent A Cycle 026]"
====================================================================
END OF AGENT A PROMPT
====================================================================
