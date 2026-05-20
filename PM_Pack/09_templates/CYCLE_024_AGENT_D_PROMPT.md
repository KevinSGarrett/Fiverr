====================================================================
AGENT D — CYCLE 024 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/024/integration
- Python 3.11+ | Playwright async (mocked in tests)

## ⚠️ MANDATORY MERGE GATE — BOTH RULES APPLY

RULE G-001: codecov/patch ≥ 90% — HARD BLOCKER. Never merge while it fails.
  If patch fails: run targeted coverage, add tests, push, re-check, confirm PASS, then merge.

RULE G-003: Codex threads — query, classify, fix VALID_FIXED with regression test,
  reply ALL threads with disposition format, resolve ALL manually.
  Run the EXACT GraphQL query. Document verbatim. Zero unresolved threads at merge.

RULE G-004: Fill the COMPLETE merge gate checklist in your report AND as a PR comment.
  ALL items must show PASS/YES before merge recommendation.

## YOUR ROLE
Agent D owns: (1) Workflow 3 stub (Fiverr Search Collection — Stage 3), (2) patch coverage
audit for all new collection modules, (3) board reconciliation, (4) PR #28 with FULL merge
gate checklist. Workflow 3 is the most important single collection workflow — it navigates
to Fiverr search results, collects gig cards, and queues gig detail jobs.
Spec: COLLECTION_WORKFLOWS.md "Workflow 3 — Fiverr Search Collection Per Keyword (Stage 3)"

## GIT INSTRUCTIONS
1. Ensure on: cycle/024/integration. Pull latest.
2. Read ALL A/B/C handoffs.
3. Commit: feat(collection): Workflow 3 stub and patch coverage [Agent D Cycle 024]
4. gh pr create --base develop --head cycle/024/integration
   --title "feat(cycle-024): collection engine foundation (SessionManager, Queue, Workflows 1-3)"
5. After CI settles: verify ALL checks. codecov/patch MUST be PASS. Handle Codex fully.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass with coverage ≥ 90%.

## TASKS

### Task 1: Read all handoffs + run full suite + read Workflow 3 spec
Read all 3 cycle reports.
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflow 3)
Run: python -m pytest -q --cov=src --cov-fail-under=90
Record test count and coverage.

### Task 2: Read E02 S2.5 Jira story before coding
Query SCRUM-17 children → find S2.5 (Fiverr Search / Workflow 3) story key.
Read full AC/DoD. Transition to In Progress. Post planning comment.

### Task 3: Create src/collection/workflows/fiverr_search.py — Workflow 3 stub
Spec: COLLECTION_WORKFLOWS.md "Workflow 3 — Fiverr Search Collection Per Keyword (Stage 3)"

async def run_fiverr_search_collection(
  keyword_id: int,
  keyword_text: str,
  niche_id: str,
  depth: str,
  run_id: str,
  db,
  session_manager,
  pacing_manager,
  dry_run: bool = True,
) -> dict:
  """
  Stage 3: Fiverr Search Collection Per Keyword.
  Navigates to Fiverr search, collects gig cards, writes search_results row,
  queues gig URLs for detail collection.

  dry_run=True (default): returns stub result without real Playwright navigation.
  Returns: {"keyword_id": int, "keyword_text": str, "total_result_count": int | None,
            "gig_cards_collected": int, "gig_urls_queued": int, "dry_run": bool}
  """
  if dry_run:
    return {
      "keyword_id": keyword_id,
      "keyword_text": keyword_text,
      "niche_id": niche_id,
      "total_result_count": None,
      "gig_cards_collected": 0,
      "gig_urls_queued": 0,
      "pages_collected": 0,
      "dry_run": True,
      "note": "Dry run: no real Playwright navigation performed",
    }
  raise NotImplementedError(
    "Fiverr search collection with real Playwright not yet implemented. "
    "Set dry_run=True for stub execution."
  )

def build_fiverr_search_url(keyword_text: str) -> str:
  """Builds the Fiverr search URL for a keyword."""
  import urllib.parse
  encoded = urllib.parse.quote(keyword_text)
  return f"https://www.fiverr.com/search/gigs?query={encoded}"

def parse_gig_cards_from_page(page_data: dict) -> list[dict]:
  """
  Parses gig card data from a collected page dict.
  Stub: returns empty list. Real implementation uses Playwright selectors.
  page_data: dict with "cards" key from future Playwright collection.
  """
  return page_data.get("cards", [])

def should_collect_page_2(depth: str, intent_class: str) -> bool:
  """
  Returns True if page 2 should be collected per spec.
  Spec: full depth + HIGH_INTENT or TRANSACTIONAL keywords → collect page 2.
  """
  return (
    depth == "full" and
    intent_class in ("HIGH_INTENT", "TRANSACTIONAL")
  )

def is_keyword_only_depth(depth: str) -> bool:
  """Returns True if depth is keyword_only (no gig detail collection)."""
  return depth == "keyword_only"

### Task 4: Write tests for Workflow 3 and collection utilities
Add to tests/unit/test_collection_workflows.py:
- test_fiverr_search_dry_run — dry_run=True → stub result with correct keys
- test_fiverr_search_result_structure — result has all 7 required keys
- test_fiverr_search_raises_without_dry_run — dry_run=False → NotImplementedError
- test_build_fiverr_search_url_basic — "python automation" → correct encoded URL
- test_build_fiverr_search_url_spaces — spaces encoded as %20
- test_build_fiverr_search_url_special_chars — special chars correctly encoded
- test_parse_gig_cards_empty — {"cards": []} → empty list
- test_parse_gig_cards_stub — {"cards": [{"title": "test"}]} → list returned
- test_should_collect_page_2_full_high_intent — True
- test_should_collect_page_2_standard_depth — False (not full)
- test_should_collect_page_2_informational — False (not HIGH_INTENT)
- test_is_keyword_only_depth — "keyword_only" → True, "standard" → False
Minimum 12 new tests.

### Task 5: Run comprehensive patch coverage audit
Run targeted coverage for ALL new collection modules:
  python -m pytest -q --cov=src.collection.session_manager --cov-report=term-missing
  python -m pytest -q --cov=src.collection.fiverr_selectors --cov-report=term-missing
  python -m pytest -q --cov=src.collection.human_events --cov-report=term-missing
  python -m pytest -q --cov=src.collection.pacing --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows --cov-report=term-missing
  python -m pytest -q --cov=src.models.job --cov-report=term-missing
  python -m pytest -q --cov=src.scheduler.queue_processor --cov-report=term-missing
Document: for each file, list uncovered lines.

### Task 6: Add patch gap tests for any uncovered collection code
Add to existing test files. Target: ≥ 90% for ALL new collection modules.
Add minimum 8 targeted gap tests.

### Task 7: Run full validation block
All 6 commands. Target: ≥ 1225 tests. Coverage ≥ 90%.

### Task 8: Board reconciliation
Verify: SCRUM-512 Done, SCRUM-513 In Progress, SCRUM-17 In Progress.
E02 story keys S2.1-S2.5: all In Progress.
SCRUM-19/20/21/22/24/25: In Progress. SCRUM-231: In Review.
Correct any stale statuses.

### Task 9: Post SCRUM-17 (E02 epic) progress comment
Post: "Cycle 024: Collection Engine foundation built.
  - SessionManager + fiverr_selectors.py + human_events.py (Agent A)
  - Job ORM model + QueueProcessor sequential v1 (Agent B)
  - PacingManager + Workflow 1 (Niche Init) + Workflow 2 stub (Agent C)
  - Workflow 3 stub (Fiverr Search) + patch coverage (Agent D)
  All workflows dry_run=True safe. No real Playwright navigation yet.
  Next cycle: real Playwright integration for Workflow 3."

### Task 10: Commit patch gap + Workflow 3 before creating PR

### Task 11: Create PR #28
gh pr create --base develop --head cycle/024/integration \
  --title "feat(cycle-024): collection engine foundation (SessionManager, Queue, Workflows 1-3)"
PR body: summary, Jira keys (SCRUM-513, E02 S2.1-S2.5), changed files, validation, AC/DoD, guardrails.

### Task 12: Monitor ALL CI checks — codecov/patch is a HARD BLOCKER
Wait for ALL checks to settle including codecov/patch.
If codecov/patch FAILURE: add tests for uncovered lines, push, re-check. DO NOT merge.

### Task 13: ⚠️ MANDATORY CODEX DISPOSITION QUERY
Run:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=[PR_NUMBER]
Document raw result and total threads.
If 0 threads: "Codex query confirmed 0 review threads. No disposition required."
If any threads: classify, fix VALID_FIXED + regression test, reply ALL, resolve ALL.

### Task 14: ⚠️ FILL MANDATORY MERGE GATE CHECKLIST
Post EXACTLY in report AND as PR comment:

```
MERGE GATE CHECKLIST — Cycle 024 PR #28
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
[ ] PR #28 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```

### Tasks 15-22: Final cleanup
15. Final SHA freeze. git rev-parse origin/cycle/024/integration.
16. Confirm all 4 agent reports present.
17. Update ACTIVE_STORY_DOD_LEDGER.md (E02 S2.5, SCRUM-513, SCRUM-17).
18. Create docs/cycle_reports/CYCLE_024_AGENT_D.md.
19. Artifact hygiene (no .env, *.db, coverage.xml, data/sessions/ staged).
20. No-main / worktree check.
21. Post SCRUM-513 final steward summary.
22. State: "PR #28 is ready to merge when approved." or list blockers.

## COMMIT INSTRUCTIONS
git add src/collection/workflows/fiverr_search.py tests/unit/test_collection_workflows.py
git add tests/unit/ docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_024_AGENT_D.md
git commit -m "feat(collection): Workflow 3 stub and patch coverage [Agent D Cycle 024]"
====================================================================
END OF AGENT D PROMPT
====================================================================
