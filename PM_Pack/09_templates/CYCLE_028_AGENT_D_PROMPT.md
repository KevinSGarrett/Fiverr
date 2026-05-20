====================================================================
AGENT D — CYCLE 028 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/028/integration
- Python 3.11+ | GitHub CLI

## PM VERIFIED STATE (as of 2026-05-19 live checks)
- reddit_signals.py: verified on disk — BARE STUB (your W7 target)
- src/models/external_signal.py: ✅ SIGNAL_REDDIT_DEMAND constant available
- All cycle 027 modules verified at 100% patch coverage by Agent D Cycle 027
- Live Jira: SCRUM-17 In Progress, SCRUM-231 In Review, all epics In Progress

## ⚠️ MANDATORY MERGE GATE — NO EXCEPTIONS

RULE G-001: codecov/patch >= 90% — HARD BLOCKER. Add tests if FAIL. Never merge.
RULE G-003: Run Codex query. Classify ALL threads. Fix VALID_FIXED with regression test.
  Reply ALL threads with disposition format. Resolve ALL manually. Document verbatim.
RULE G-004: Fill COMPLETE merge gate checklist in your report AND PR comment.
  ALL items must show PASS/YES. This is non-negotiable.

## YOUR ROLE
Agent D owns: (1) Workflow 7 stub (Reddit Signals) with full interface contract,
(2) comprehensive patch coverage audit for ALL modules changed this cycle,
(3) board reconciliation, (4) PR #32 with full mandatory merge gate checklist.
Spec (READ before coding):
  C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\04_collection\COLLECTION_WORKFLOWS.md
  Workflow 7 — Reddit Collection Per Niche (Stage 6)

## GIT INSTRUCTIONS
1. Ensure on: cycle/028/integration. Pull latest.
2. Read ALL A/B/C handoffs.
3. Commit: feat(collection): Workflow 7 stub and patch coverage [Agent D Cycle 028]
4. gh pr create --base develop --head cycle/028/integration
   --title "feat(cycle-028): W2 keyword expansion partial, W6 Google Trends, weakness wiring, W7 stub"
5. After CI: verify ALL checks. codecov/patch MUST be PASS. Handle Codex. Fill checklist.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git branch --show-current; git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass, coverage >= 90%.

## TASKS

### Task 1: Read all A/B/C handoffs + run full suite
Read all 3 cycle reports. Run full validation block. Record count and coverage.

### Task 2: Read COLLECTION_WORKFLOWS.md Workflow 7 before coding (REQUIRED)
Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
  Focus: Workflow 7 — Reddit Collection Per Niche (Stage 6)
  Extract: input/output spec, praw usage pattern, LLM demand intent parse,
  subreddit search, signal fields, error handling table, checkpoint format.
Read: src/collection/workflows/reddit_signals.py (current stub)
Read: src/models/external_signal.py (SIGNAL_REDDIT_DEMAND, SIGNAL_REDDIT_ACTIVITY)

### Task 3: Find E02 Reddit story key in Jira
Query SCRUM-17 children for Reddit/social signals story (likely SCRUM-152).
Read full AC/DoD. Post planning comment.

### Task 4: Implement Workflow 7 stub in src/collection/workflows/reddit_signals.py
Replace bare stub class with proper async stub interface.
Spec reference: COLLECTION_WORKFLOWS.md Workflow 7 Steps 1-6.

async def run_reddit_signals_collection(
  niche_id: str,
  seed_keywords: list[str],
  subreddits: list[str],
  run_id: str,
  db,
  pacing_manager,
  dry_run: bool = True,
) -> dict:
  """
  Stage 6: Reddit collection per niche.
  Spec: COLLECTION_WORKFLOWS.md Workflow 7.
  Uses praw Reddit client for subreddit search + LLM demand intent parse.
  dry_run=True (default): returns stub without real praw calls.
  dry_run=False: raises NotImplementedError (praw auth not yet configured).
  """
  if dry_run:
    return {
      "niche_id": niche_id,
      "subreddits_searched": 0,
      "posts_collected": 0,
      "signals_written": 0,
      "demand_intent_score": None,
      "dry_run": True,
      "note": "Dry run: no real praw calls made",
    }
  raise NotImplementedError(
    "Reddit collection with real praw not yet implemented. "
    "Requires: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET in .env. "
    "Set dry_run=True for stub execution."
  )

def build_subreddit_search_url(subreddit: str, query: str) -> str:
  """Spec W7 Step 1b: subreddit.search() URL for reference/debugging."""
  import urllib.parse
  return f"https://www.reddit.com/r/{subreddit}/search/?q={urllib.parse.quote(query)}&restrict_sr=1&t=year"

def parse_reddit_post_count_90d(posts: list[dict]) -> int:
  """Spec W7 Step 3: count posts with created_utc > 90 days ago."""
  import time
  cutoff = time.time() - (90 * 24 * 3600)
  return sum(1 for p in posts if p.get("created_utc", 0) > cutoff)

def select_top_posts_for_llm(posts: list[dict], n: int = 10) -> list[dict]:
  """Spec W7 Step 4: select top-N posts by upvotes for LLM analysis."""
  return sorted(posts, key=lambda p: p.get("upvotes", 0), reverse=True)[:n]

def build_reddit_demand_signal_json(
  post_count_90d: int,
  demand_intent_score: float | None,
  intent_phrases: list[str],
  subreddits_searched: list[str],
) -> dict:
  """Builds the signal_json payload for external_signals write."""
  return {
    "reddit_post_count_90d": post_count_90d,
    "demand_intent_score": demand_intent_score,
    "intent_phrases": intent_phrases,
    "subreddits_searched": subreddits_searched,
  }

### Task 5: Write tests for reddit_signals.py
Create: tests/unit/test_reddit_signals.py
Required (minimum 12):
- test_reddit_dry_run — dry_run=True → stub result with all 6 keys
- test_reddit_dry_run_default — dry_run=True is default
- test_reddit_raises_without_dry_run — dry_run=False → NotImplementedError
- test_reddit_result_has_niche_id — result["niche_id"] matches input
- test_build_subreddit_search_url — correct URL format for subreddit + query
- test_build_subreddit_search_url_encodes_spaces — spaces → %20 in URL
- test_parse_post_count_90d_all_recent — all posts < 90 days → count = len
- test_parse_post_count_90d_all_old — all posts > 90 days → count = 0
- test_parse_post_count_90d_mixed — 3 recent + 2 old → count = 3
- test_select_top_posts_by_upvotes — returns sorted by upvotes desc
- test_select_top_posts_limit — limit to n posts
- test_build_demand_signal_json — all fields present in output dict

### Task 6: Comprehensive patch coverage audit (ALL cycle 028 modules)
Run exact commands:
  python -m pytest -q --cov=src.collection.workflows.keyword_expansion --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows.google_trends --cov-report=term-missing
  python -m pytest -q --cov=src.scoring.weakness --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows.seller_profile --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows.reddit_signals --cov-report=term-missing
Document every uncovered line per file. Add gap tests (minimum 8) for any < 90%.

### Task 7: Run full validation block
All 6 commands + python run.py collect-only.
Target: >= 1570 tests. Coverage >= 90%.

### Task 8: Board reconciliation
Verify via live query:
  SCRUM-516 = Done, SCRUM-517 = In Progress, SCRUM-17 = In Progress
  SCRUM-151 (Google Trends) = In Progress, SCRUM-172 (Weakness) = In Progress
  SCRUM-152 (Reddit, if exists) = In Progress
  SCRUM-231 = In Review, all epics In Progress
Correct any stale statuses found.

### Task 9: Post SCRUM-231 progress update
Post: "Cycle 028 progress for SCRUM-231:
  - Workflow 2 partial real (Google Suggest + dedup): keywords table can now be populated
  - Workflow 6 Google Trends: real pytrends implementation, writes to external_signals
  - weakness.py now reads from gig_quality_scores table (supplementary)
  - Workflow 7 Reddit: full stub interface with spec-aligned helpers
  Status: keep In Review. Next milestone: authenticated collect-only run with real Fiverr session."

### Task 10: Commit before PR creation

### Task 11: Create PR #32
gh pr create --base develop --head cycle/028/integration \
  --title "feat(cycle-028): W2 keyword expansion partial, W6 Google Trends, weakness wiring, W7 stub"
PR body: all deliverables, Jira keys (SCRUM-517, SCRUM-143/W2 story, SCRUM-151, SCRUM-172,
  SCRUM-150, SCRUM-152, SCRUM-231), changed files, validation, AC/DoD, guardrails.

### Task 12: Monitor ALL CI checks — codecov/patch IS a HARD BLOCKER
Wait for ALL checks to settle. If codecov/patch FAILURE: add tests, push, re-check.
DO NOT merge with codecov/patch FAILURE.

### Task 13: ⚠️ MANDATORY CODEX DISPOSITION QUERY (PR #32)
Run:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=[PR_NUMBER]
Document raw result verbatim.
If 0 threads: "Codex query confirmed 0 review threads. No disposition required."
If any threads: classify → VALID_FIXED: fix + regression test + push + CI + reply + resolve.
  Others: evidence reply + resolve.

### Task 14: ⚠️ FILL MANDATORY MERGE GATE CHECKLIST
Post EXACTLY in report AND as PR comment on PR #32:

```
MERGE GATE CHECKLIST — Cycle 028 PR #32
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
[ ] PR #32 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```

ALL items MUST show PASS/YES before recommending merge.

### Tasks 15-22: Final cleanup
15. Final SHA freeze: git rev-parse origin/cycle/028/integration
16. Confirm all 4 agent reports present
17. Update ACTIVE_STORY_DOD_LEDGER.md
18. Create docs/cycle_reports/CYCLE_028_AGENT_D.md
19. Artifact hygiene (no .env, *.db, coverage.xml, data/sessions/ staged)
20. No-main / worktree check
21. Post SCRUM-517 final steward summary
22. "PR #32 is ready to merge when approved." or list blockers.

## COMMIT INSTRUCTIONS
git add src/collection/workflows/reddit_signals.py
git add tests/unit/test_reddit_signals.py tests/unit/
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_028_AGENT_D.md
git commit -m "feat(collection): Workflow 7 stub and patch coverage [Agent D Cycle 028]"
====================================================================
END OF AGENT D PROMPT
====================================================================
