====================================================================
AGENT A — CYCLE 028 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/028/integration
- Python 3.11+ | httpx | SQLAlchemy 2.0
- Prior cycle PR: #31 ready to merge (1521 tests, 94.91%, codecov/patch 100%)

## PM VERIFIED STATE (as of Part 2 verification, 2026-05-19)
Files confirmed present on disk:
- src/models/external_signal.py ✅  src/models/gig_quality_score.py ✅
- src/collection/workflows/gig_detail.py ✅  tests/integration/test_collect_only_e2e.py ✅
- src/collection/workflows/keyword_expansion.py ✅ (but NotImplementedError for real path)
- src/collection/workflows/google_trends.py ✅ (but bare stub class)
Live Jira verified: SCRUM-515=Done, SCRUM-516=In Progress, all epics In Progress

## ⚠️ HARD GATE RULES (PERMANENT)
G-001: codecov/patch >= 90% — HARD BLOCKER. Never merge while FAIL.
G-003: Codex query MUST run for PR. Classify, fix VALID_FIXED + regression test,
  reply ALL threads with disposition format, resolve ALL manually.
G-004: Agent D completes mandatory merge gate checklist — ALL PASS/YES before merge.

## YOUR ROLE
Agent A: PR gate, branch setup, and Workflow 2 partial real implementation.
VERIFIED GAP: keyword_expansion.py raises NotImplementedError for dry_run=False.
Without keyword expansion, the keywords table stays empty and all scoring is blocked.
This cycle implements Steps 2b (Google Suggest via httpx) and 2e (deduplication).
Steps 2a/2c/2d/2f/2g remain stubs with feature flags.
Spec source (READ THIS BEFORE CODING):
  C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\04_collection\COLLECTION_WORKFLOWS.md
  Workflow 2 — Keyword Expansion Per Niche (Stage 2), Steps 2b and 2e.

## GIT INSTRUCTIONS
1. Verify PR #31: gh pr view 31 --json state,mergeable,statusCheckRollup
2. Run Codex query for PR #31 (Task 2). Confirm 1 thread isResolved=true.
3. gh pr merge 31 --merge (only when all checks SUCCESS)
4. git checkout develop && git pull --ff-only origin develop
5. git checkout -b cycle/028/integration && git push -u origin cycle/028/integration
6. Commit: feat(collection): Workflow 2 partial real impl (Google Suggest + dedup) [Agent A Cycle 028]
7. Do NOT push final branch — human operator pushes after all 4 agents.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 31 --json state,mergeable,statusCheckRollup
Pass: root=C:\Fiverr\Fiverr. ALL checks SUCCESS including codecov/patch.

## TASKS

### Task 1: Preflight + PR #31 verification
Run all 7 preflight commands. Verify codecov/patch == SUCCESS.

### Task 2: Codex query for PR #31 (MANDATORY)
Run exact GraphQL query for PR #31.
Agent D confirmed 1 thread (PRRT_kwDOSbqwNc6DPdfn), VALID_FIXED, isResolved=true.
Document: "Codex query PR #31: 1 thread, both resolved=true confirmed."

### Task 3: Merge PR #31, close SCRUM-516, create branch
- gh pr merge 31 --merge
- Baseline test run: python -m pytest -q --cov=src --cov-fail-under=90
- Verify: 1521 tests, 94.91%+ pass
- git checkout -b cycle/028/integration && git push -u origin cycle/028/integration
- Jira: SCRUM-516 → Done (post merge SHA comment)
- Jira: Create SCRUM-517 as Cycle 028 control → In Progress

### Task 4: READ spec before coding (REQUIRED)
Read in full: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\04_collection\COLLECTION_WORKFLOWS.md
Focus on Workflow 2 Steps 2b and 2e. Extract:
- Google Suggest URL format: https://suggestqueries.google.com/complete/search?q={seed}&client=firefox
- Expected JSON response format
- Deduplication requirements (case-insensitive, strip whitespace)
- Output format: keywords table rows with source, autocomplete_position (None for suggest)
Read: src/collection/workflows/keyword_expansion.py (current stub state)
Read: src/models/ to confirm Keyword model fields

### Task 5: Implement Step 2b in keyword_expansion.py — Google Suggest via httpx
Spec reference: COLLECTION_WORKFLOWS.md Workflow 2 Step 2b.

Replace NotImplementedError in run_keyword_expansion() with a partial real path.
For dry_run=False, implement Step 2b only:

async def _fetch_google_suggest(seed: str, pacing_manager) -> list[str]:
  """Fetches Google Suggest completions for a seed keyword.
  Spec: COLLECTION_WORKFLOWS.md W2 Step 2b — GET suggestqueries.google.com"""
  import httpx
  url = f"https://suggestqueries.google.com/complete/search?q={seed}&client=firefox"
  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
      resp.raise_for_status()
      data = resp.json()
      # Google Suggest returns [query_string, [suggestion_list], ...]
      return data[1] if isinstance(data, list) and len(data) > 1 else []
  except Exception:
    return []  # Spec: "retry 2×, skip on failure, continue"
  finally:
    await pacing_manager.wait("external_default", dry_run=False)

### Task 6: Implement Step 2e — deduplication
def _deduplicate_keywords(keyword_list: list[str]) -> list[str]:
  """Spec: COLLECTION_WORKFLOWS.md W2 Step 2e — case-insensitive deduplication."""
  seen = set()
  result = []
  for kw in keyword_list:
    normalized = kw.strip().lower()
    if normalized and normalized not in seen:
      seen.add(normalized)
      result.append(kw.strip())
  return result

### Task 7: Update run_keyword_expansion() to use partial real path
For dry_run=False:
  - Run Step 2b (Google Suggest) for each seed
  - Run Step 2e (deduplication) on combined results
  - Stub Steps 2a/2c/2d/2f/2g with feature flags (empty result + warning log)
  - Write keywords to DB if db is a Session (use Keyword model)
  - Return result dict with keywords_queued count per source
  - NotImplementedError is now REMOVED

Return format: {
  "niche_id": niche_id,
  "keywords_queued": int,
  "sources": {"fiverr_autocomplete": 0, "google_suggest": count, "llm_generated": 0},
  "dry_run": False,
}

### Task 8: Find E02 Workflow 2 Jira story and read AC/DoD
Query SCRUM-17 children for story matching "keyword expansion" or "Stage 2".
Read full AC/DoD. Post planning comment with Google Suggest + dedup scope.

### Task 9: Write tests for Workflow 2 partial real path
Create: tests/unit/test_keyword_expansion.py (new file)
Required (minimum 12 tests):
- test_fetch_google_suggest_returns_list — mock httpx, valid response → list of strings
- test_fetch_google_suggest_empty_response — mock returns [] → empty list
- test_fetch_google_suggest_http_error — mock raises httpx.HTTPError → empty list (no crash)
- test_fetch_google_suggest_timeout — mock raises asyncio.TimeoutError → empty list
- test_deduplicate_case_insensitive — ["AI Chatbot", "ai chatbot"] → 1 result
- test_deduplicate_strips_whitespace — [" AI Chatbot "] → ["AI Chatbot"]
- test_deduplicate_removes_empty — ["AI", "", "  "] → ["AI"]
- test_run_keyword_expansion_dry_run — dry_run=True → stub result unchanged
- test_run_keyword_expansion_real_google_suggest — mock httpx, dry_run=False → keywords_queued > 0
- test_run_keyword_expansion_real_writes_to_db — Session db → Keyword rows created
- test_run_keyword_expansion_real_deduplicates — duplicate seeds → single keyword stored
- test_run_keyword_expansion_pacing_called — pacing_manager.wait called during suggest fetch

### Task 10: Targeted patch coverage
python -m pytest -q --cov=src.collection.workflows.keyword_expansion --cov-report=term-missing
All new code >= 90% covered.

### Task 11: Full validation block
python -m ruff check . && python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle028.db
python run.py phase2-smoke && python run.py collect-only
Target: >= 1533 tests. Coverage >= 90%.

### Task 12: Post Jira evidence
Post on SCRUM-143 or W2 story key: "Cycle 028 Agent A: Workflow 2 Step 2b (Google Suggest
  via httpx) + Step 2e (deduplication) implemented. NotImplementedError removed.
  Feature flags stub Steps 2a/2c/2d/2f/2g. 12 tests. DoD remaining: Step 2a (Fiverr
  Autocomplete, requires authenticated session), LLM steps 2c/2d/2f/2g."

### Tasks 13-24: Standard completion
13. Update ACTIVE_STORY_DOD_LEDGER.md
14. Artifact hygiene: no .env, *.db, coverage.xml, data/sessions/ staged
15. No-main / worktree check
16. Record SHA. Handoff to Agent B.
17. Create docs/cycle_reports/CYCLE_028_AGENT_A.md
18. Commit scoped files only
19. Run python run.py collect-only → must pass (keyword expansion now partially real)
20. Post SCRUM-17 comment: keyword expansion partial impl available
21. Confirm .cursorrules compliance
22-24. Final SHA + test count for handoff

## COMMIT INSTRUCTIONS
git add src/collection/workflows/keyword_expansion.py
git add tests/unit/test_keyword_expansion.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_028_AGENT_A.md
git commit -m "feat(collection): Workflow 2 partial real impl (Google Suggest + dedup) [Agent A Cycle 028]"
====================================================================
END OF AGENT A PROMPT
====================================================================
