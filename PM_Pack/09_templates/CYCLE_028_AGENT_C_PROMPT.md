====================================================================
AGENT C — CYCLE 028 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/028/integration
- Python 3.11+ | SQLAlchemy 2.0

## PM VERIFIED STATE (as of 2026-05-19 live checks)
CRITICAL finding from PM spec review:
- weakness.py._load_signals_from_db() uses GigVisualAnalysis (NOT GigQualityScore)
  and joins via SearchResult.gig_id. GigQualityScore ORM was built in Cycle 027
  but weakness.py has NOT been updated to query it.
- weakness.py line 440+: current query is Gig.join(SearchResult).join(GigVisualAnalysis)
- GigQualityScore fields needed: video_present, portfolio_count (for absence rates)
Live Jira: SCRUM-172 "[SCORING] S4.8 Gig Quality Weakness Score" = In Progress ✅
Live Jira: SCRUM-150 "[COLLECTION] S2.10 Workflow: Seller Profile" = In Progress ✅

## ⚠️ HARD GATE RULES (PERMANENT)
G-001: codecov/patch >= 90% — HARD BLOCKER.
G-003: Codex query + reply + resolve: MANDATORY.
G-004: Agent D mandatory merge gate checklist.

## YOUR ROLE
Agent C owns two tasks this cycle:
1. Wire weakness.py to ALSO check GigQualityScore table (additive — do not remove
   the existing GigVisualAnalysis path, add GigQualityScore as a supplementary source)
2. Improve Workflow 5 (seller_profile.py) — add the seller profile URL builder and
   parse helpers so future Playwright implementation has a complete interface

## ⚠️ YOU MUST READ THE ACTUAL weakness.py BEFORE CODING
Read: src/scoring/weakness.py lines 427-500 (the _load_signals_from_db method)
Read: src/models/gig_quality_score.py (fields available: video_present, portfolio_count,
  analysis_complete, weakness_count, description_quality_score, etc.)
Read: PM_Pack/ref/project_plan/05_scoring/SCORING_DIRECTION.md S4.8 inputs
DO NOT assume field names. Read the actual code.

## GIT INSTRUCTIONS
1. Ensure on: cycle/028/integration. Pull latest.
2. Read Agent A + B handoffs.
3. Commit: feat(scoring): wire weakness.py to GigQualityScore + W5 interface [Agent C Cycle 028]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git branch --show-current; git log --oneline -8; git worktree list
  python -m pytest -q tests/unit/test_google_trends.py --no-header
Pass: branch=cycle/028/integration, Agent B tests pass.

## TASKS

### Task 1: Read all handoffs + read actual weakness.py code (REQUIRED)
Read: docs/cycle_reports/CYCLE_028_AGENT_A.md, CYCLE_028_AGENT_B.md
Read: src/scoring/weakness.py lines 1-100 (class, weights, calculate method)
Read: src/scoring/weakness.py lines 427-528 (_load_signals, _load_signals_from_db, helpers)
Read: src/models/gig_quality_score.py (all fields)
Read: PM_Pack/ref/project_plan/05_scoring/SCORING_DIRECTION.md S4.8

Document in your report BEFORE coding:
  a) Current DB query path in _load_signals_from_db() (exact ORM query)
  b) Which fields weakness.py currently reads (exact key names)
  c) Which GigQualityScore fields map to those signals
  d) How you will add GigQualityScore as a supplementary source

### Task 2: Read SCRUM-172 Jira story before coding
Read full AC/DoD for SCRUM-172. Post planning comment with your wiring approach.

### Task 3: Add GigQualityScore as supplementary source in weakness.py
Rule: Do NOT remove the GigVisualAnalysis path. Add GigQualityScore as a
  secondary source that enriches the existing result dict.

In _load_signals_from_db(), after the existing return dict is built, add:

  # Supplementary: check GigQualityScore for confirmed video/portfolio signals
  try:
    from src.models.gig_quality_score import GigQualityScore, get_gig_quality_scores
    quality_rows = get_gig_quality_scores(keyword_id, session)
    if quality_rows:
      # Compute video absence rate from GigQualityScore.video_present
      video_known = [r.video_present for r in quality_rows if r.video_present is not None]
      if video_known:
        video_absence = sum(1 for v in video_known if not v) / len(video_known)
        existing_dict["video_absence_rate"] = video_absence
        existing_dict["top10_has_video"] = [r.video_present for r in quality_rows
                                             if r.video_present is not None]

      # Compute portfolio absence rate from GigQualityScore.portfolio_count
      portfolio_known = [r.portfolio_count for r in quality_rows
                         if r.portfolio_count is not None]
      if portfolio_known:
        portfolio_absence = sum(1 for c in portfolio_known if c == 0) / len(portfolio_known)
        existing_dict["portfolio_absence_rate"] = portfolio_absence

      # Add analysis_complete flag for LLM stub gating
      any_complete = any(r.analysis_complete for r in quality_rows)
      existing_dict["gig_quality_score_available"] = any_complete
  except Exception:
    pass  # GigQualityScore not available — fall through to existing signals

The key principle: if GigQualityScore rows exist, they override the GigVisualAnalysis
path for video_absence_rate and portfolio_absence_rate. If GigQualityScore rows are
absent, existing behavior is preserved exactly.

### Task 4: Verify change does not break existing tests
Run: python -m pytest -q tests/unit/test_scoring_weakness.py (or equivalent)
All existing tests must still pass. If any fail, your addition broke something.
Fix before proceeding.

### Task 5: Add tests for GigQualityScore wiring in weakness.py
Add to tests/unit/test_scoring_weakness.py (or create test_scoring_weakness_gqs.py):
Required (minimum 10 tests):
- test_weakness_gqs_no_rows — no GigQualityScore rows → falls back to existing path
- test_weakness_gqs_video_present_all — all video_present=True → video_absence_rate=0.0
- test_weakness_gqs_video_absent_all — all video_present=False → video_absence_rate=1.0
- test_weakness_gqs_video_mixed — 3 True + 7 False → video_absence_rate=0.7
- test_weakness_gqs_portfolio_zero_all — all portfolio_count=0 → portfolio_absence=1.0
- test_weakness_gqs_portfolio_nonzero — all portfolio_count >= 1 → portfolio_absence=0.0
- test_weakness_gqs_overrides_visual_analysis — when GQS rows exist, GQS values used
- test_weakness_gqs_exception_safe — GigQualityScore import error → no crash, existing path
- test_weakness_gqs_analysis_complete — any analysis_complete=True → flag in signals
- test_weakness_gqs_none_video_skipped — video_present=None rows excluded from rate

### Task 6: Improve seller_profile.py interface (Workflow 5)
Read: src/collection/workflows/seller_profile.py (current state)
Read: COLLECTION_WORKFLOWS.md Workflow 5 (seller profile fields spec)
Add to seller_profile.py (do NOT remove existing stub):

def build_seller_profile_url(seller_username: str) -> str:
  """Spec: COLLECTION_WORKFLOWS.md W5 Step 4 — fiverr.com/{username}"""
  return f"https://www.fiverr.com/{seller_username}"

def parse_member_since(text: str | None) -> str | None:
  """Spec: W5 Step 6 — parse 'Member since Jan 2022' → '2022-01'."""
  import re
  if not text: return None
  months = {"jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
            "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"}
  m = re.search(r"(\w{3})\s+(\d{4})", text.lower())
  if m: return f"{m.group(2)}-{months.get(m.group(1), '01')}"
  return None

def parse_seller_level(level_text: str | None) -> str:
  """Spec: W5 Step 6 — normalize seller level badge text."""
  if not level_text: return "NO_LEVEL"
  t = level_text.lower()
  if "top rated" in t or "trs" in t: return "TRS"
  if "level 2" in t: return "LEVEL_2"
  if "level 1" in t: return "LEVEL_1"
  if "pro" in t: return "PRO"
  return "NO_LEVEL"

def parse_response_rate(text: str | None) -> int | None:
  """Spec: W5 Step 6 — parse '98%' → 98."""
  import re
  if not text: return None
  nums = re.findall(r"\d+", text)
  return int(nums[0]) if nums else None

### Task 7: Write tests for seller_profile.py helpers
Add to existing tests/unit/test_seller_profile.py:
Required (minimum 8 new tests):
- test_build_seller_url — correct https://www.fiverr.com/{username}
- test_parse_member_since_jan — "Member since Jan 2022" → "2022-01"
- test_parse_member_since_none → None
- test_parse_seller_level_trs → "TRS"
- test_parse_seller_level_no_level — None → "NO_LEVEL"
- test_parse_response_rate_percent — "98%" → 98
- test_parse_response_rate_none → None
- test_parse_response_rate_no_digits — "N/A" → None

### Task 8: Targeted patch coverage
python -m pytest -q --cov=src.scoring.weakness --cov-report=term-missing
python -m pytest -q --cov=src.collection.workflows.seller_profile --cov-report=term-missing
All new code >= 90% covered.

### Task 9: Full validation block
All 6 commands. Target: >= 1558 tests. Coverage >= 90%.

### Task 10: Post Jira evidence for SCRUM-172 and SCRUM-150
SCRUM-172: "Cycle 028 Agent C: weakness.py now reads from gig_quality_scores table.
  GigQualityScore provides video_presence and portfolio_count signals. Falls back to
  GigVisualAnalysis if no GQS rows exist. 10 tests. DoD remaining: real LLM analysis
  writes GQS rows, weakness score validated against real data."
SCRUM-150: "Cycle 028 Agent C: seller_profile.py helpers added (build_url, parse_level,
  parse_member_since, parse_response_rate). Full spec interface ready for Playwright
  implementation next cycle."

### Tasks 11-16: Standard completion
11. Update ACTIVE_STORY_DOD_LEDGER.md
12. Artifact hygiene check
13. No-main / worktree check. Record SHA. Handoff to Agent D.
14. Create docs/cycle_reports/CYCLE_028_AGENT_C.md
15. Commit scoped files
16. Run python run.py phase2-smoke → must pass

## COMMIT INSTRUCTIONS
git add src/scoring/weakness.py src/collection/workflows/seller_profile.py
git add tests/unit/test_seller_profile.py
git add tests/unit/test_scoring_weakness_gqs.py (or extend existing test file)
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_028_AGENT_C.md
git commit -m "feat(scoring): wire weakness.py to GigQualityScore + W5 interface [Agent C Cycle 028]"
====================================================================
END OF AGENT C PROMPT
====================================================================
