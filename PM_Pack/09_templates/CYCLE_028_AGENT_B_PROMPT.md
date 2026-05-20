====================================================================
AGENT B — CYCLE 028 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/028/integration
- Python 3.11+ | pytrends | SQLAlchemy 2.0

## PM VERIFIED STATE (as of 2026-05-19 live checks)
Files confirmed on disk: src/models/external_signal.py ✅ (ExternalSignal ORM ready)
src/collection/workflows/google_trends.py ✅ (bare stub class — YOUR target this cycle)
Live Jira: SCRUM-151 "[COLLECTION] S2.11 Workflow: Google Trends Fetch" = In Progress ✅

## ⚠️ HARD GATE RULES (PERMANENT)
G-001: codecov/patch >= 90% — HARD BLOCKER.
G-003: Codex query MUST run for PR. Fix VALID_FIXED + regression, reply all, resolve all.
G-004: Agent D mandatory merge gate checklist — ALL PASS/YES before merge.

## YOUR ROLE
Agent B implements Workflow 6 — Google Trends Collection (Stage 6).
VERIFIED STATE: google_trends.py is a bare stub class. ExternalSignal ORM
exists (Cycle 027) and is ready to receive writes.
Spec (READ IN FULL BEFORE CODING):
  C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\04_collection\COLLECTION_WORKFLOWS.md
  Workflow 6 — Google Trends Collection Per Niche (Stage 6)

## GIT INSTRUCTIONS
1. Ensure on: cycle/028/integration. git pull origin cycle/028/integration
2. Read Agent A handoff report before coding.
3. Commit: feat(collection): Workflow 6 Google Trends real implementation [Agent B Cycle 028]
4. Do NOT push.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git branch --show-current; git log --oneline -5; git worktree list
  python -m pytest -q tests/unit/test_keyword_expansion.py --no-header
Pass: branch=cycle/028/integration, Agent A tests pass.

## TASKS

### Task 1: Preflight + read Agent A handoff + read spec (REQUIRED)
Read: docs/cycle_reports/CYCLE_028_AGENT_A.md
Read IN FULL: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
  Focus: Workflow 6, all steps, adaptive 429 handling, checkpoint format, pacing.
Read: src/collection/workflows/google_trends.py (current stub)
Read: src/models/external_signal.py (ExternalSignal ORM — understand write_external_signal())

### Task 2: Read SCRUM-151 Jira story before coding
Read full AC/DoD for SCRUM-151 "[COLLECTION] S2.11 Workflow: Google Trends Fetch".
Post planning comment confirming real implementation this cycle.

### Task 3: Implement Workflow 6 in src/collection/workflows/google_trends.py
Spec reference: COLLECTION_WORKFLOWS.md Workflow 6 Steps 1-4.
Replace the bare stub class with a real async function.

async def run_google_trends_collection(
  niche_id: str,
  keywords: list[str],
  run_id: str,
  db,
  pacing_manager,
  dry_run: bool = True,
) -> dict:
  """
  Stage 6: Google Trends collection per niche.
  Spec: COLLECTION_WORKFLOWS.md Workflow 6.
  dry_run=True: returns stub without calling pytrends.
  """
  if dry_run:
    return {"niche_id": niche_id, "keywords_processed": 0,
            "signals_written": 0, "rate_limited": False, "dry_run": True}

  from pytrends.request import TrendReq
  from src.models.external_signal import write_external_signal, SIGNAL_GOOGLE_TRENDS
  import pandas as pd

  # Spec Step 1: Group into batches of 5 (pytrends max)
  batches = [keywords[i:i+5] for i in range(0, len(keywords), 5)]
  signals_written = 0
  rate_limited = False
  rate_limit_count = 0
  current_delay_multiplier = 1.0

  for batch in batches:
    success = False
    for attempt in range(3):
      try:
        pytrends = TrendReq(hl="en-US", tz=360)
        # Spec Step 2a: build_payload with 12-month timeframe
        pytrends.build_payload(kw_list=batch, timeframe="today 12-m", geo="")
        # Spec Step 2b: interest_over_time
        df = pytrends.interest_over_time()

        for kw in batch:
          if df.empty or kw not in df.columns:
            # Spec Step 2c: empty DataFrame → store score=0
            write_external_signal(
              keyword_id=_resolve_keyword_id(kw, db),
              signal_type=SIGNAL_GOOGLE_TRENDS,
              signal_value=0.0,
              signal_json={"trends_12mo_score": 0.0, "trends_3mo_score": 0.0,
                           "no_data": True},
              run_id=run_id, collection_method="pytrends_api", db=db,
            )
          else:
            # Spec Steps 2d-2e: extract 12mo and 3mo averages
            series = df[kw].dropna()
            score_12mo = float(series.mean()) if len(series) > 0 else 0.0
            score_3mo = float(series.tail(13).mean()) if len(series) >= 13 else score_12mo
            # Spec Step 2e: calculate slope
            import numpy as np
            x = np.arange(len(series))
            slope = float(np.polyfit(x, series.values, 1)[0]) if len(series) > 2 else 0.0
            trend_dir = "RISING" if slope > 0.3 else "DECLINING" if slope < -0.3 else "FLAT"
            kw_id = _resolve_keyword_id(kw, db)
            if kw_id:
              write_external_signal(
                keyword_id=kw_id,
                signal_type=SIGNAL_GOOGLE_TRENDS,
                signal_value=score_12mo,
                signal_json={
                  "trends_12mo_score": score_12mo,
                  "trends_3mo_score": score_3mo,
                  "slope": slope,
                  "trend_direction": trend_dir,
                  "weekly_data": series.tolist()[-52:],  # last year of weekly
                },
                run_id=run_id, collection_method="pytrends_api", db=db,
              )
              signals_written += 1

        success = True
        await pacing_manager.wait("google_trends", dry_run=False)
        break

      except Exception as exc:
        exc_str = str(exc)
        if "429" in exc_str or "Too Many Requests" in exc_str:
          # Spec Adaptive Pacing (OQ-004): pause, increase delay, track count
          rate_limited = True
          rate_limit_count += 1
          import asyncio
          if rate_limit_count >= 3:
            # Spec: mark remaining as dead-letter after 3× 429
            break
          pause_mins = 10
          current_delay_multiplier *= 1.5
          await asyncio.sleep(pause_mins * 60)
          continue
        break  # non-429 error: skip batch, continue

  return {
    "niche_id": niche_id,
    "keywords_processed": len(keywords),
    "signals_written": signals_written,
    "rate_limited": rate_limited,
    "rate_limit_count": rate_limit_count,
    "dry_run": False,
  }

def _resolve_keyword_id(keyword_text: str, db) -> int | None:
  """Looks up keyword_id by text. Returns None if not found."""
  from sqlalchemy.orm import Session
  from src.models import Keyword
  if not isinstance(db, Session): return None
  kw = db.query(Keyword).filter(Keyword.keyword_text == keyword_text).first()
  return kw.id if kw else None

### Task 4: Write tests for google_trends.py
Create: tests/unit/test_google_trends.py
Required (minimum 14):
- test_google_trends_dry_run — dry_run=True → stub result, no pytrends called
- test_google_trends_dry_run_default — dry_run=True is default
- test_google_trends_result_structure — result dict has all 5 required keys
- test_google_trends_batches_keywords — 7 keywords → batched into 2 calls (5+2)
- test_google_trends_empty_df — pytrends returns empty DataFrame → score=0 stored
- test_google_trends_writes_signal — mock pytrends data → write_external_signal called
- test_google_trends_signal_type — signal_type == SIGNAL_GOOGLE_TRENDS
- test_google_trends_12mo_score_computed — series average matches signal_value
- test_google_trends_3mo_score_computed — last 13 weeks average in signal_json
- test_google_trends_slope_rising — positive slope → trend_direction="RISING"
- test_google_trends_slope_declining — negative slope → "DECLINING"
- test_google_trends_slope_flat — near-zero slope → "FLAT"
- test_google_trends_429_pauses — HTTP 429 exception → rate_limited=True returned
- test_google_trends_429_three_times — 3× 429 → breaks loop, rate_limit_count=3
- test_resolve_keyword_id_found — Session db + matching keyword → id returned
- test_resolve_keyword_id_missing — no match → None

### Task 5: Verify pytrends is in requirements
Check: pyproject.toml or requirements.txt for pytrends.
If missing: add "pytrends>=4.9,<5.0" to pyproject.toml [project].dependencies.
If present: note the version in your report.

### Task 6: Targeted patch coverage
python -m pytest -q --cov=src.collection.workflows.google_trends --cov-report=term-missing
All new code >= 90% covered.

### Task 7: Full validation block
All 6 commands + python run.py collect-only.
Target: >= 1547 tests. Coverage >= 90%.

### Task 8: Post Jira evidence for SCRUM-151
Post: "Cycle 028 Agent B: Workflow 6 Google Trends real implementation.
  pytrends API → 12-month + 3-month scores, slope, trend direction.
  Writes to external_signals (signal_type=google_trends). Adaptive 429 handling.
  14 tests. DoD remaining: live pytrends call with real keywords, niche config
  external_sources.google_trends = true, authenticated run."

### Tasks 9-16: Standard completion
9. Update ACTIVE_STORY_DOD_LEDGER.md
10. Artifact hygiene check (no .env, *.db, coverage.xml staged)
11. No-main / worktree check. Record SHA. Handoff to Agent C.
12. Create docs/cycle_reports/CYCLE_028_AGENT_B.md
13. Commit scoped files
14. Run python run.py phase2-smoke → must pass
15. Note for Agent C: weakness.py uses GigVisualAnalysis not GigQualityScore — read the actual code
16. Final SHA + test count

## COMMIT INSTRUCTIONS
git add src/collection/workflows/google_trends.py
git add tests/unit/test_google_trends.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_028_AGENT_B.md
git commit -m "feat(collection): Workflow 6 Google Trends real implementation [Agent B Cycle 028]"
====================================================================
END OF AGENT B PROMPT
====================================================================
