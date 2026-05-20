====================================================================
AGENT C — CYCLE 025 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | Branch: cycle/025/integration
- Python 3.11+ | asyncio | SQLAlchemy 2.0

## ⚠️ HARD GATE REMINDER
codecov/patch ≥ 90% is hard merge blocker. Run targeted coverage before handoff.
All workflow functions must accept dry_run=True parameter (default True).

## YOUR ROLE
Agent C builds Workflow 4 (Gig Detail Collection — Stage 4) and Workflow 5 (Seller Profile
Collection — Stage 5) as dry_run-safe stubs with all required interfaces, helper functions,
and error handling stubs specified in COLLECTION_WORKFLOWS.md.
Spec: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflows 4 and 5)

## GIT INSTRUCTIONS
1. Ensure on: cycle/025/integration. Pull latest.
2. Read Agents A + B handoffs.
3. Commit: feat(collection): Workflow 4 and 5 stubs [Agent C Cycle 025]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git branch --show-current; git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_checkpoint.py tests/unit/test_retry_handler.py
Pass: all A+B tests pass.

## TASKS

### Task 1: Read handoffs + read Workflow 4 and 5 specs
Read: docs/cycle_reports/CYCLE_025_AGENT_A.md, CYCLE_025_AGENT_B.md
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md (Workflows 4 and 5)
Note from Workflow 4 spec: steps 1-13, error handling table, depth variants, checkpoint spec.
Note from Workflow 5 spec: steps 1-9, seller profile fields, depth variants.

### Task 2: Read E02 story keys for Workflow 4 and 5 from SCRUM-17 children
Find story keys for S2.x (Gig Detail) and S2.x (Seller Profile). Transition to In Progress.

### Task 3: Create src/collection/workflows/gig_detail.py — Workflow 4 stub
Spec: COLLECTION_WORKFLOWS.md "Workflow 4 — Gig Detail Collection Per Gig URL"

async def run_gig_detail_collection(
  gig_url: str,
  keyword_id: int,
  niche_id: str,
  depth: str,
  run_id: str,
  db,
  session_manager,
  pacing_manager,
  checkpoint_manager,
  dry_run: bool = True,
) -> dict:
  """
  Stage 4: Gig Detail Collection Per Gig URL.
  Navigates to a gig URL, collects all gig detail fields, updates gig row in DB,
  queues seller username for Stage 5.
  dry_run=True: returns stub result without real Playwright navigation.
  Returns: {"gig_url": str, "collected": bool, "seller_queued": bool,
            "fields_collected": list[str], "dry_run": bool}
  """
  if dry_run:
    return {
      "gig_url": gig_url,
      "keyword_id": keyword_id,
      "collected": False,
      "seller_queued": False,
      "fields_collected": [],
      "dry_run": True,
      "note": "Dry run: no Playwright navigation performed",
    }
  raise NotImplementedError(
    "Gig detail collection with real Playwright not yet implemented. "
    "Set dry_run=True."
  )

def get_top_n_gig_urls_for_keyword(keyword_id: int, depth: str, db) -> list[str]:
  """
  Returns the top-N gig URLs for a keyword based on depth.
  Depth: full=20, standard=10, feasibility=5, keyword_only=0.
  Returns empty list if no gig cards collected for this keyword.
  """
  TOP_N = {"full": 20, "standard": 10, "feasibility": 5, "keyword_only": 0}
  n = TOP_N.get(depth, 10)
  if n == 0:
    return []
  try:
    from sqlalchemy.orm import Session
    if not isinstance(db, Session):
      return []
    # Stub: return empty — real impl queries SearchResult.gig_cards JSON
    return []
  except Exception:
    return []

def parse_gig_detail_fields(page_data: dict) -> dict:
  """
  Parses all gig detail fields from collected page data.
  Stub: returns dict with all expected field keys set to None.
  Real implementation uses fiverr_selectors constants.
  """
  return {
    "gig_title_full": None,
    "description_text": None,
    "packages": None,
    "gig_extras": None,
    "tags": None,
    "faq_text": None,
    "faq_entries": None,
    "video_present": None,
    "portfolio_count": None,
    "review_count_exact": None,
    "rating_exact": None,
    "review_snippets": None,
    "orders_in_queue": None,
    "thumbnail_url": None,
  }

def is_gig_removed(page_data: dict) -> bool:
  """Returns True if gig page indicates 404 or removed gig."""
  return page_data.get("status_code") == 404 or page_data.get("gig_removed", False)

def should_skip_gig_detail(gig_url: str, run_id: str, db) -> bool:
  """Returns True if gig was already collected this run (deduplication)."""
  # Stub: always False — real impl checks gigs table collected_at and detail_collected
  return False

### Task 4: Create src/collection/workflows/seller_profile.py — Workflow 5 stub
Spec: COLLECTION_WORKFLOWS.md "Workflow 5 — Seller Profile Collection Per Username"

async def run_seller_profile_collection(
  seller_username: str,
  niche_id: str,
  run_id: str,
  db,
  session_manager,
  pacing_manager,
  checkpoint_manager,
  dry_run: bool = True,
) -> dict:
  """
  Stage 5: Seller Profile Collection Per Username.
  Navigates to seller profile page, collects all seller fields, writes sellers row.
  dry_run=True: returns stub result without real Playwright navigation.
  Returns: {"seller_username": str, "collected": bool, "fields_collected": list[str], "dry_run": bool}
  """
  if dry_run:
    return {
      "seller_username": seller_username,
      "collected": False,
      "fields_collected": [],
      "dry_run": True,
      "note": "Dry run: no Playwright navigation performed",
    }
  raise NotImplementedError(
    "Seller profile collection with real Playwright not yet implemented. "
    "Set dry_run=True."
  )

def build_seller_profile_url(seller_username: str) -> str:
  """Builds the Fiverr seller profile URL."""
  return f"https://www.fiverr.com/{seller_username}"

def parse_seller_profile_fields(page_data: dict) -> dict:
  """
  Parses seller profile fields from collected page data.
  Stub: returns all fields as None.
  """
  return {
    "seller_level": None,
    "member_since": None,
    "response_time": None,
    "response_rate": None,
    "languages": None,
    "bio_text": None,
    "total_reviews": None,
    "total_gigs": None,
    "active_gig_titles": None,
    "portfolio_count": None,
    "badges": None,
  }

def should_skip_seller_profile(seller_username: str, run_id: str, db) -> bool:
  """Returns True if seller was already collected this run (deduplication)."""
  return False  # Stub: always False

### Task 5: Update src/collection/workflows/__init__.py exports
Add: run_gig_detail_collection, run_seller_profile_collection,
  get_top_n_gig_urls_for_keyword, parse_gig_detail_fields, build_seller_profile_url

### Task 6: Write tests for Workflows 4 and 5
Add to tests/unit/test_collection_workflows.py:
- test_gig_detail_dry_run — returns correct stub structure
- test_gig_detail_result_keys — all 7 required keys present
- test_gig_detail_not_implemented — dry_run=False → NotImplementedError
- test_get_top_n_full_depth — full → n=20
- test_get_top_n_keyword_only — keyword_only → empty list
- test_get_top_n_dict_db — dict db → empty list (graceful)
- test_parse_gig_detail_fields_stub — returns dict with all 13 field keys set to None
- test_is_gig_removed_404 — status_code=404 → True
- test_is_gig_removed_false — normal page → False
- test_should_skip_gig_stub — always False (stub)
- test_seller_profile_dry_run — correct stub structure
- test_seller_profile_not_implemented — dry_run=False → NotImplementedError
- test_build_seller_profile_url — correct URL format
- test_parse_seller_fields_stub — all 11 field keys present, all None
- test_should_skip_seller_stub — always False
Minimum 15 new tests.

### Task 7: Run targeted patch coverage
python -m pytest -q --cov=src.collection.workflows --cov-report=term-missing
All new workflow code ≥ 90%.

### Task 8: Run full validation block
All 6 commands. Target: ≥ 1322 tests. Coverage ≥ 90%.

### Task 9: Post Jira evidence for Workflow 4 and 5 story keys

### Tasks 10-16: Standard completion
10. Update ACTIVE_STORY_DOD_LEDGER.md. 11. Artifact hygiene.
12. No-main check. 13. Record SHA. Handoff to D.
14. Create docs/cycle_reports/CYCLE_025_AGENT_C.md.
15. Commit. Message: feat(collection): Workflow 4 and 5 stubs [Agent C Cycle 025]
16. Smoke test pass.

## COMMIT INSTRUCTIONS
git add src/collection/workflows/gig_detail.py src/collection/workflows/seller_profile.py
git add src/collection/workflows/__init__.py tests/unit/test_collection_workflows.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_025_AGENT_C.md
git commit -m "feat(collection): Workflow 4 and 5 stubs [Agent C Cycle 025]"
====================================================================
END OF AGENT C PROMPT
====================================================================
