====================================================================
AGENT D — CYCLE 026 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/026/integration
- Python 3.11+ | SQLAlchemy 2.0 | GitHub CLI

## ⚠️ MANDATORY MERGE GATE — NO EXCEPTIONS

RULE G-001: codecov/patch >= 90% — HARD BLOCKER. Add tests if FAIL. Re-check. Never merge.
RULE G-003: Run Codex query. Classify ALL threads. Fix VALID_FIXED with regression test.
  Reply ALL threads. Resolve ALL manually. Document verbatim.
RULE G-004: Fill COMPLETE merge gate checklist in report AND PR comment. ALL PASS/YES.

## YOUR ROLE
Agent D owns: (1) Seller ORM model — the third missing write target, (2) comprehensive
patch coverage audit for all new collection models, (3) board reconciliation, (4) PR #30
with complete mandatory merge gate checklist.

## GIT INSTRUCTIONS
1. Ensure on: cycle/026/integration. Pull latest.
2. Read ALL A/B/C handoffs.
3. Commit: feat(models): Seller ORM and patch coverage [Agent D Cycle 026]
4. gh pr create --base develop --head cycle/026/integration
   --title "feat(cycle-026): SearchResult+Gig+Seller ORMs, Workflow 3 real implementation"
5. After CI: verify ALL checks. codecov/patch MUST be PASS. Handle Codex. Fill checklist.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass, coverage >= 90%.

## TASKS

### Task 1: Read all A/B/C handoffs + run full suite
Read all 3 cycle reports. Run full validation. Record count and coverage.

### Task 2: Read E02 S2.10 Jira story (SCRUM-150) before coding
Read full AC/DoD for seller profile collection. Post planning comment.

### Task 3: Create src/models/seller.py — Seller ORM model
Spec: PM_Pack/ref/project_plan/03_data/SCHEMA.md (sellers table)

class Seller(Base):
  __tablename__ = "sellers"
  id: int (PK autoincrement)
  seller_username: str (unique, not null)
  run_id: str (nullable, indexed)
  seller_level: str (nullable) — "NO_LEVEL", "LEVEL_1", "LEVEL_2", "TRS", "PRO"
  member_since: str (nullable) — "YYYY-MM" format
  response_time: str (nullable) — "1 hour", "24 hours", etc.
  response_rate: str (nullable) — "98%"
  languages: JSON (nullable) — list of language strings
  bio_text: str (nullable)
  total_reviews: int (nullable)
  total_gigs: int (nullable)
  gig_titles: JSON (nullable) — list of gig title strings
  portfolio_item_count: int (nullable)
  badges: JSON (nullable)
  profile_url: str (nullable)
  profile_collected: bool (default False)
  profile_collected_at: datetime (nullable)
  ttl_hours: int (default 720) — 30 days for seller profiles

  Index on (seller_level)
  Index on (run_id)

### Task 4: Add write_seller_profile() helper to src/models/seller.py

def write_seller_profile(
  seller_username: str,
  run_id: str,
  seller_level: str | None,
  member_since: str | None,
  response_time: str | None,
  total_reviews: int | None,
  total_gigs: int | None,
  db,
) -> "Seller | None":
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return None
  row = Seller(
    seller_username=seller_username, run_id=run_id,
    seller_level=seller_level, member_since=member_since,
    response_time=response_time, total_reviews=total_reviews,
    total_gigs=total_gigs, profile_collected=True,
    profile_collected_at=datetime.now(UTC),
  )
  db.merge(row)
  db.commit()
  return row

def get_seller(seller_username: str, db) -> "Seller | None":
  from sqlalchemy.orm import Session
  if not isinstance(db, Session): return None
  return db.query(Seller).filter(Seller.seller_username == seller_username).first()

### Task 5: Register Seller in src/models/__init__.py
Add import + __all__ entry. Verify:
  python -c "from src.models import Seller; print(Seller.__tablename__)"

### Task 6: Write tests for Seller model (tests/unit/test_seller_model.py)
Required (minimum 12):
- test_seller_table_name → "sellers"
- test_seller_insert_minimal → seller_username only, query back
- test_seller_insert_full → all fields, no exception
- test_seller_unique_username → duplicate username fails
- test_seller_default_ttl → ttl_hours = 720
- test_seller_profile_collected_default → False
- test_write_seller_dict_db → None returned
- test_write_seller_orm → row persisted, profile_collected=True
- test_write_seller_upsert → second call updates row
- test_get_seller_found → returns Seller
- test_get_seller_missing → None
- test_seller_in_base_metadata → "sellers" in Base.metadata.tables

### Task 7: Comprehensive patch coverage audit
Run targeted coverage for ALL new collection models (cycles 025-026):
  python -m pytest -q --cov=src.models.search_result --cov-report=term-missing
  python -m pytest -q --cov=src.models.gig --cov-report=term-missing
  python -m pytest -q --cov=src.models.seller --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows.fiverr_search --cov-report=term-missing
  python -m pytest -q --cov=src.collection.checkpoint --cov-report=term-missing
  python -m pytest -q --cov=src.scheduler.retry_handler --cov-report=term-missing
Document every uncovered line per file.

### Task 8: Add patch gap tests for any uncovered lines
Add to existing test files. Minimum 8 targeted gap tests.
Target: >= 90% for ALL new models and collection modules.

### Task 9: Run full validation block
All 6 commands. Target: >= 1405 tests. Coverage >= 90%.

### Task 10: Board reconciliation
Verify: SCRUM-514 Done, SCRUM-515 In Progress, SCRUM-17 In Progress.
E02 stories SCRUM-141-156: In Progress. SCRUM-231: In Review.
SCRUM-19/20/21/22/24/25: In Progress.

### Task 11: Post SCRUM-17 progress comment
Post: "Cycle 026: Three ORM models added (SearchResult, Gig, Seller) + Workflow 3 real
  Playwright implementation. collect-only mode now has real write targets for all three
  collection stages. First cycle where collected data can actually flow to the DB.
  Next cycle: Workflow 4 real implementation + integration run with mock session."

### Task 12: Commit patch gaps + Seller model before creating PR

### Task 13: Create PR #30
gh pr create --base develop --head cycle/026/integration \
  --title "feat(cycle-026): SearchResult+Gig+Seller ORMs, Workflow 3 real implementation"
PR body: all deliverables, Jira keys (SCRUM-515, SCRUM-141, SCRUM-148, SCRUM-149, SCRUM-150),
  changed files, validation, AC/DoD table, guardrails.

### Task 14: Monitor ALL CI checks — codecov/patch HARD BLOCKER
Wait for ALL checks. If codecov/patch FAILURE: add tests, push, re-check. DO NOT merge.

### Task 15: ⚠️ MANDATORY CODEX DISPOSITION QUERY
Run GraphQL query for PR #30. Document verbatim.
If 0: "0 threads confirmed. No disposition required."
If any: classify → fix VALID_FIXED + regression → reply ALL → resolve ALL.

### Task 16: ⚠️ FILL MANDATORY MERGE GATE CHECKLIST
Post EXACTLY in report AND as PR comment on PR #30:

```
MERGE GATE CHECKLIST — Cycle 026 PR #30
==========================================
CODECOV:
[ ] codecov/project: [PASS/FAIL] — [exact %]
[ ] codecov/patch: [PASS/FAIL] — [exact %]
[ ] Local --cov-fail-under=90: [PASS/FAIL]
[ ] All new lines covered by tests: [YES/NO]
  If NO, uncovered files: [list or N/A]

CODEX:
[ ] reviewThreads query executed: YES
[ ] Total threads found: [N]
[ ] All threads dispositioned: [YES/N/A]
[ ] All VALID_FIXED threads have regression tests: [YES/N/A]
[ ] All threads manually resolved with reply: [YES/N/A]
[ ] Zero unresolved threads: [YES]

FINAL:
[ ] PR #30 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```

ALL items MUST show PASS/YES before recommending merge.

### Tasks 17-22: Final cleanup
17. Final SHA freeze. git rev-parse origin/cycle/026/integration.
18. Confirm all 4 agent reports present.
19. Update ACTIVE_STORY_DOD_LEDGER.md
20. Create docs/cycle_reports/CYCLE_026_AGENT_D.md
21. Artifact hygiene (no .env, *.db, coverage.xml, data/sessions/ staged)
22. "PR #30 is ready to merge when approved." or list blockers.

## COMMIT INSTRUCTIONS
git add src/models/seller.py src/models/__init__.py
git add tests/unit/test_seller_model.py tests/unit/
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_026_AGENT_D.md
git commit -m "feat(models): Seller ORM and patch coverage [Agent D Cycle 026]"
====================================================================
END OF AGENT D PROMPT
====================================================================
