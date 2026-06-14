# POST-CYCLE PM REVIEW REQUEST — Cycle 077

## Facts
```json
{
  "cycle": 77,
  "mode": "POST_CYCLE_PM_REVIEW",
  "collected_at": "2026-06-13T08:11:35.089017+00:00",
  "head_sha": "41bac8c5f9e06854970a7f6df8df0ac6a66cc2eb",
  "develop_sha": "e0c9753b023c3c96b5214d73dd4d441816c969d8",
  "pr_number": 1,
  "pr_merged": true,
  "merge_sha": "7e3be60ac39d84fc9be76170035cbaeb4ade65c2",
  "ci_passed": false,
  "codecov_project": "UNKNOWN",
  "codecov_patch": "UNKNOWN",
  "codex_threads_resolved": false,
  "local_ruff": false,
  "local_mypy": false,
  "local_pytest": false,
  "local_coverage_pct": 0.0,
  "baseline_db_mtime_unchanged": true,
  "scrapfly_enabled_false": true,
  "cycle_control_done": false,
  "next_cycle_control_created": false,
  "agent_reports_present": {
    "A": true,
    "B": true,
    "E": true,
    "C": true,
    "F": true,
    "D": true
  },
  "score1_internal_pct": 0.0,
  "score2_e2e_pct": 0.0,
  "tierd2_stages": {}
}
```

## Review Prompt
====================================================================
FIVERR RESEARCH SYSTEM — UNIVERSAL POST-CYCLE PM REVIEW PROMPT

Version: 4.5 (Universal — no cycle-number editing required)
Canonical home: PM_Pack\01_pm_instructions\POST_CYCLE_PM_REVIEW_v4.md
Strategy doc:   PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md
  (§7 regressions; §8 sizing; §9 PM authority; §10 ScrapFly;
   §11 model-migration parity; §12 parallel contract; §13 PM operating rules)
Local Project Directory: C:\Fiverr\Fiverr\
Project Manager Pack:    C:\Fiverr\Fiverr\PM_Pack\
Project Technical Plans: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan
SRDI Specs:              C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\13_srdi\
GitHub Repo:             https://github.com/KevinSGarrett/Fiverr/
Jira Project:            https://kevinsgarrett.atlassian.net/jira/software/projects/SCRUM/summary
.env file:               C:\Fiverr\Fiverr\.env

Paste this into the chat after any cycle completes. Do not edit it.
It self-orients by reading the hydration header and git state.

v4.0: PM Direct-Action sweep; ScrapFly checks; code-vs-config drift; 25-task floors; secrets removed.
v4.1: Invoke-Exe pattern; squash-merge caveat; codecov policy; golden parity; Jira id 41.
v4.2: §12 parallel contract (B+E notice; zone check fix; C before F; D playbook); §13 PM rules;
      revised line floors (A500/B650/E500/C425/F525/D650); depth quality gate; Part 5.3 REPLACED
      with mandatory full 14-track project plan review (root-cause fix for 10-cycle drift where
      SRDI-complete was treated as project-complete); 5 mandatory gap checks; production readiness
      gates G-A through G-D defined; comprehensive Jira board audit (not just sprint stories);
      D's G1 attribution fix (enumerate ALL commits, not just C's report SHAs); E zone/pad fix;
      Jira-to-plan cross-reference; wave status table; updated Part 7 and Part 8.
v4.3: TASK MINIMUM RAISED 25 -> 55 (effective C067+). TASK CATEGORY: LARGE-XXLARGE only
      (XXXLARGE retired — decompose into 2-3 XXLARGE tasks). NEW LINE FLOORS:
      A:1000 | B:1200 | E:950 | C:900 | F:1000 | D:1200 | TOTAL:6,250.
      Compliance shorthand: A>=1000, B>=1200, E>=950, C>=900, F>=1000, D>=1200.
      Old floors (A500/B650/E500/C425/F525/D650 = 3,250) applied C057-C066 only.
      RATIONALE: 55 LARGE-XXLARGE tasks × ~18-22 lines = 1,000-1,200 lines per agent,
      ensuring substantive inline code, test stubs, and commands per task that drive
      project toward full production-grade completion.
v4.4: PROJECT COMPLETION ESTIMATE added (Part 5.7). After every cycle the PM calculates
      a 0-100% production-readiness score using a fixed 12-track weighted model
      (weights never change; only the track % values update each cycle). The score is
      recorded in the hydration header, Part 6, and Part 8 self-audit checklist, so
      progress toward full end-to-end production completion is always visible.
v4.5: PM GOVERNANCE CORRECTION (2026-06-09). CRITICAL — READ BEFORE USING THIS PROMPT.
      The single ~60% score used in v4.4 was Internal Engineering Build Progress
      MISLABELED as production-ready. This is now corrected.

      MANDATORY TWO-SCORE MODEL (effective C074+):
        Score 1 — Internal Engineering Build Progress (~67% after C074)
        Score 2 — End-to-End Production-Grade Readiness (~48-50% after C074)
      These two scores must NEVER be conflated. See Part 5.7 for the corrected model.

      HARD CAPS ON SCORE 2 (never claim above these without evidence):
        Live collection not proven:           cap at 50%
        Live collection done, no scoring:     cap at 60%
        No live recommendations:              cap at 65%
        Dashboard/export not operator-usable: cap at 70%
        No playbook from live data:           cap at 78%
        No repeated unattended runs:          cap at 82%
        No release/operator docs:             cap at 90%

      TierD-2 STAGED CREDIT RULES (never add +10-15% on approval alone):
        Approval + budget + controls: small unlock credit only
        Infrastructure built: +3-5%
        First live collection success: +3-5% more
        Full pipeline validated (all 8 stages): +5-10% more
        Repeated unattended runs: full production credit

      NEVER-BREAK TASK FLOOR RULE (see AGENT_TASK_FLOOR_ENFORCEMENT.md):
        Every agent prompt must have >= 55 LARGE-XXLARGE tasks.
        Agent A TASK 1 must run the enforcement check before authorizing B.
        Violation = HARD STOP. No exceptions.

      18 PM GOVERNANCE DOCUMENTS created at PM_Pack/:
        CURRENT_STATE_CANONICAL.md, PRODUCTION_READINESS_SCORECARD.md,
        TASK_SUBSTANCE_GATE.md, CYCLE_PRODUCTION_ADVANCEMENT_GATE.md,
        STALE_DOCUMENT_REGISTER.md, BUILD_SEQUENCE_EXCEPTION_LOG.md,
        LIVE_VALIDATION_MASTER_GATE.md, PROMPT_QUALITY_REVIEW_GATE.md,
        POST_SRDI_BUILD_SEQUENCE_MAP.md, CYCLE_074_PROMPT_CORRECTION_PROTOCOL.md,
        CYCLE_074_PROMPT_CORRECTION_REPORT.md, LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md,
        PROMPT_RED_TEAM_REVIEW_GATE.md, C060_C073_PROMPT_RETROSPECTIVE_AUDIT.md,
        CYCLE_READINESS_FORECAST_TEMPLATE.md, TASK_PRODUCTION_IMPACT_LEDGER.md,
        AGENT_TASK_FLOOR_ENFORCEMENT.md, PM_CORRECTION_MASTER_REPORT.md

      Part 5.7 COMPLETELY REWRITTEN with corrected two-score model and updated baselines.
      New Part 5.8: TierD-2 Live Validation Stage Tracking.
      Part 7 UPDATED: task floor enforcement mandatory in every agent prompt.
      Part 8 UPDATED: new self-audit checklist items for governance compliance.

AUTHENTICATION (read first):
- Jira/GitHub auth is via the already-authorized Atlassian + GitHub connectors.
  NEVER paste an API token, password, or secret into any prompt, file, repo, or chat.
  If you find a token embedded anywhere, treat it as COMPROMISED: tell the user to rotate it.
- When checking .env, confirm a key's PRESENCE only (prefix/length) — never print its value.

====================================================================
MANDATORY FIRST ACTION — STATE VERIFICATION (§13.1 — before ANYTHING else)

Before reading the hydration header, before answering any question, before writing any prompt:

  Invoke-Exe git 'log origin/develop --oneline -5'
  Invoke-Exe gh 'api "repos/KevinSGarrett/Fiverr/pulls?state=open" --jq ".[].number + \": \" + .title"'

From git log: determine which cycle just completed (top squash commit ends "(#NN)").
From open PRs: determine if any cycle is still in progress.

ONLY AFTER reading both: proceed to Part 0. Never answer from memory.
Root cause: told user to run C055+C056 prompts when both were already merged.

====================================================================
EXECUTION ENVIRONMENT NOTES

GIT/GH OUTPUT CAPTURE: git is at C:\Program Files\Git\cmd\git.exe — NOT on PATH.
PowerShell call operator returns EMPTY. Use .NET ProcessStartInfo "Invoke-Exe" helper.
Arguments must be a single STRING (never ArgumentList — Windows PS 5.1 ignores it silently).

  function Invoke-Exe { param([string]$File,[string]$ArgString)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName=$File; $psi.WorkingDirectory='C:\Fiverr\Fiverr'; $psi.Arguments=$ArgString
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $p=[System.Diagnostics.Process]::Start($psi)
    $o=$p.StandardOutput.ReadToEnd(); $e=$p.StandardError.ReadToEnd(); $p.WaitForExit()
    return [pscustomobject]@{ Out=$o.TrimEnd(); Err=$e.TrimEnd(); Code=$p.ExitCode } }
  $gh = 'C:\Program Files\GitHub CLI\gh.exe'

GH COMMANDS: use gh api with ABSOLUTE REST paths. gh pr list/view/create FAIL (no repo detection).
SQUASH-MERGE CAVEAT: is-ancestor returns 1 even when squash-merged. Verify via merged:true + title "(#PR)".
PYTHON: C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe
SCRATCH FILES (§13.3): Create → use → delete. Never accumulate scratch.

====================================================================
PM DIRECT-ACTION AUTHORITY (strategy §9)

ONE-LINE TEST:
  Reversible AND leaves src/ + tests/ + config-behavior untouched AND needs no gate?
    → PM DOES IT NOW (Tier A).
  Touches code/tests/config-behavior, or needs a gate?  → CURSOR AGENT (Tier C).
  Irreversible, or cost/security/account impact?        → ASK USER (Tier D).

TIER A (do now): Jira transitions/comments/tickets/labels/sprint; delete MERGED cycle branch;
  prune merged remote branches; inspect PR/CI/Codex; edit PM_Pack/hydration/tracker/cycle-log;
  extend .gitignore; remove scratch; run tests/--cov/config-check/smoke (read-only);
  COMMIT+PUSH PM doc changes to develop IF zero src/+tests/+config-behavior;
  REPLACE [CXXX_SQUASH_SHA] in prompts (§13.2);
  UPDATE AGENT_TASK_FLOOR_ENFORCEMENT.md with any new violations found;
  UPDATE PRODUCTION_READINESS_SCORECARD.md with cycle delta and new track % values;
  UPDATE CURRENT_STATE_CANONICAL.md with new cycle state.
TIER B: large/multi-file doc commits; created Jira keys; git rm --cached.
TIER C: ANY src/; ANY tests/ add/modify; ANY config.yaml runtime-behavior; anything needing a gate.
TIER D: drop/clear stashes (standing: 12 stale — cycle051/047/043/036/029/012 + 6 more);
  history rewrite; force-push; delete unmerged branch; rotate secrets;
  LARGE live ScrapFly burn (> 500 credits); baseline DB restore.

====================================================================
PM GOVERNANCE CORRECTION REFERENCE (v4.5 — effective C074+)

The PM Governance Correction (commit 42ae369, 2026-06-09) created 18 documents at PM_Pack/.
Every PM review must reference these documents, not memory.

SINGLE SOURCE OF TRUTH:           PM_Pack/CURRENT_STATE_CANONICAL.md
PRODUCTION SCORECARD (two-score): PM_Pack/PRODUCTION_READINESS_SCORECARD.md
TASK SUBSTANCE RULES:             PM_Pack/TASK_SUBSTANCE_GATE.md
CYCLE ADVANCEMENT GATE (+5% E2E): PM_Pack/CYCLE_PRODUCTION_ADVANCEMENT_GATE.md
TASK FLOOR ENFORCEMENT:           PM_Pack/AGENT_TASK_FLOOR_ENFORCEMENT.md
LARGE-XXLARGE DEFINITIONS:        PM_Pack/LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md
PROMPT QUALITY GATES:             PM_Pack/PROMPT_QUALITY_REVIEW_GATE.md
PROMPT RED-TEAM GATE:             PM_Pack/PROMPT_RED_TEAM_REVIEW_GATE.md
LIVE VALIDATION STAGES:           PM_Pack/LIVE_VALIDATION_MASTER_GATE.md
BUILD SEQUENCE MAP:               PM_Pack/POST_SRDI_BUILD_SEQUENCE_MAP.md
EXCEPTION LOG:                    PM_Pack/BUILD_SEQUENCE_EXCEPTION_LOG.md
TASK IMPACT LEDGER:               PM_Pack/TASK_PRODUCTION_IMPACT_LEDGER.md
CYCLE FORECAST TEMPLATE:          PM_Pack/CYCLE_READINESS_FORECAST_TEMPLATE.md
STALE DOCUMENT REGISTER:          PM_Pack/STALE_DOCUMENT_REGISTER.md
RETROSPECTIVE AUDIT:              PM_Pack/C060_C073_PROMPT_RETROSPECTIVE_AUDIT.md
CORRECTION MASTER REPORT:         PM_Pack/PM_CORRECTION_MASTER_REPORT.md
C074 CORRECTION PROTOCOL:         PM_Pack/CYCLE_074_PROMPT_CORRECTION_PROTOCOL.md
C074 CORRECTION REPORT:           PM_Pack/CYCLE_074_PROMPT_CORRECTION_REPORT.md

NEVER BREAK RULES (from AGENT_TASK_FLOOR_ENFORCEMENT.md):
  1. Every agent prompt >= 55 LARGE-XXLARGE tasks. No exceptions.
  2. Agent A TASK 1 must run the task floor verification script before authorizing B.
  3. No task is LARGE because it has many words. Production impact determines size.
  4. No prompt is approved until TASK_SUBSTANCE_GATE.md PQ-0 through PQ-7 pass.
  5. Every cycle must target >= +5% E2E Production-Grade Readiness increase.
  6. E2E score cap rules must be applied (see hard caps table in header).
  7. TierD-2 staged credit rules must be applied (never +10-15% on approval alone).
  8. scrapfly.enabled must stay FALSE in committed config.yaml.
  9. Internal Build Progress must never be labeled as production-ready.

====================================================================
PRODUCTION READINESS GATES (track status every cycle — update after each merge)

These 4 gates define whether the system is production-ready. The PM must review the status of
each gate at EVERY cycle review and determine if CYCLE_NEXT scope should advance them.
"All gates OPEN" is not acceptable as a permanent state — each cycle must close or advance at
least one gate, or explicitly defer with documented rationale.

G-A: SRDI LAUNCH ARTIFACTS
  Status: CLOSED (files present — 47/37/33 lines each as of C066).

G-B: DATA SCHEMA COMPLETENESS
  Status: CLOSED (TC-1 migration_11 applied; raw_value, relevance_score, trend_direction confirmed).
  Verification: python.exe -c "from sqlalchemy import create_engine, inspect;
    e=create_engine('sqlite:///data/foundation_gate_ci.db');
    cols=sorted([c['name'] for c in inspect(e).get_columns('external_signals')]); print(cols)"
    Must contain raw_value + relevance_score + trend_direction.

G-C: DASHBOARD LIVE DATA
  Status: CLOSED (9 pages use get_db_session(); zero demo-data calls confirmed C061+).
  Verification: Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content $_.FullName |
    Select-String "build_dashboard_demo_data" } — must return EMPTY.

G-D: WAVE IMPLEMENTATION COVERAGE
  Status: OPEN — Wave 11 S8.1-S8.2 unstarted after C074; Wave 12 not started.
  Closing criteria: Wave 11 fully implemented and connected to live data; Wave 12 complete.
  CYCLE_NEXT scope if OPEN: advance the lowest-numbered incomplete Wave 11 story (S8.1 → C075).

When updating this table after each cycle, use this format in the hydration header:
  G-A: CLOSED | G-B: CLOSED | G-C: CLOSED | G-D: OPEN (Wave 11 S8.1-S8.2; Wave 12)

TIERD-2 LIVE VALIDATION STAGES (see LIVE_VALIDATION_MASTER_GATE.md for full detail)
V-1: TierD-2 approved + budget + controls  | Status: EARNED (small unlock)
V-2: ScrapFly infrastructure built          | Status: EARNED (+3-5%, C074)
V-3: First live collection success           | Status: PENDING (user runs pilot post-C074)
V-4: Live data persists in DB                | Status: PENDING
V-5: Live data flows into scoring            | Status: PENDING
V-6: Live data flows into recommendations    | Status: PENDING
V-7: Recommendations flow into playbook      | Status: PENDING
V-8: Dashboard/export from live data         | Status: PENDING
V-9: Repeated unattended runs pass           | Status: FUTURE

Hard cap rule: E2E cannot exceed 50% until V-3 is confirmed.
Score update: each V-stage completion unlocks additional E2E credit per the ledger.
User action required to advance V-3: python run.py live-validate --niche python_automation

====================================================================
PART 0 — ORIENT: DISCOVER CURRENT STATE

Step 0.1 — Read the hydration header (HYDRATION_HEADER.md at PM_Pack/07_hydration/).
           IMPORTANT (v4.5): The hydration header now uses the TWO-SCORE model.
           Read BOTH scores: Internal Build Progress AND E2E Production-Grade Readiness.
           Do not treat them as interchangeable.
Step 0.2 — Read the strategy doc for ALL permanent rules.
Step 0.3 — Read the completed cycle's Agent D report.
Step 0.4 — (v4.5 NEW) Read CURRENT_STATE_CANONICAL.md to confirm single source of truth.

6-AGENT ARCHITECTURE (effective C047+; §12.2 authoritative):
  Stage 1 — A solo         | Creates all spec artifacts, authorizes B
  Stage 2 — B + E PARALLEL | B implements, E observes B's commits (E waits for B's first commit)
  Stage 3 — C after BOTH B AND E (NEVER after F only)
  Stage 4 — F after C GO   | Edge case tests
  Stage 5 — D after ALL 5  | Merge gate, Jira closeout, hydration update

  E: commits ONLY CYCLE_[N]_AGENT_E.md — NEVER src/, tests/, config.yaml
  F: commits ONLY test files + report — NEVER src/
  B: ONLY src/ author (attribution invariant)

  (v4.5) A TASK 1 MANDATORY: A must run the task floor verification script before
  authorizing B. See AGENT_TASK_FLOOR_ENFORCEMENT.md. If any agent < 55 tasks: HALT.

====================================================================
PART 1 — READ ALL 6 AGENT REPORTS FOR CYCLE_DONE (REQUIRED)

Read docs/cycle_reports/CYCLE_[DONE]_AGENT_{A,B,C,D,E,F}.md.
Record for each: commit SHAs, files changed, test delta, gate results, deferred scope.
Verify Agent E committed zero src/ files. Verify Agent F committed zero src/ files.
Verify Agent B is the only src/ author across all commits.

====================================================================
PART 2 — VERIFY ACTUAL LOCAL CODEBASE STATE (REQUIRED)

2.1 Pull develop: Invoke-Exe git 'checkout develop' then 'pull origin develop'
2.2 Run full test suite and record actual count + coverage %
2.3 Run golden parity: run.py score --golden → must return kw=110 62.7/CONDITIONAL_GO
2.4 Verify baseline DB untouched: mtime of data/cycle037_live.db must == 1780553758
2.5 Verify scrapfly.enabled=False in config.yaml
2.6 Verify no new migration files added if not expected
2.7 (v4.5) Run task floor verification for the completed cycle's prompts:
    import re; [(print(ag, len(re.findall(r'## (?:TASK|GATE) [0-9]', open(f'PM_Pack/03_cursor_agent_system/CYCLE_{N}_AGENT_{ag}_PROMPT.md').read()))), ) for ag in 'ABECFD']
    All agents must be >= 55.

====================================================================
PART 3 — LIVE GITHUB VERIFICATION (REQUIRED)

3.1 Confirm merge: merged:true + squash commit visible + title contains (#NN)
3.2 Confirm CI passed: all checks green on merged commit
3.3 Confirm codecov patch state and record
3.4 Delete merged cycle branch from origin
3.5 Confirm no outstanding open PRs for completed cycle

====================================================================
PART 4 — LIVE JIRA VERIFICATION (REQUIRED)

4.1 Transition SCRUM cycle control ticket to Done (ID 41)
4.2 Create CYCLE_NEXT control ticket
4.3 Update wave stories (transition completed stories to Done)
4.4a Run JQL: project=SCRUM AND status != Done ORDER BY created DESC
     Review ALL non-Done issues, not just sprint stories
4.4b Close ~10-15 stale board-setup issues as Tier A (if present)
4.5 Verify canonical epics SCRUM-16 through SCRUM-25 are In Progress as appropriate
4.6 Jira-to-plan cross-reference: 14 tracks vs Jira epics; any track with NO coverage → create story
4.7 (v4.5) Verify TierD-2 live validation stage tickets exist if pilot has been run

====================================================================
PART 5 — PM PACK & SPEC REVIEW (REQUIRED)

5.1 Read HYDRATION_HEADER.md — verify it uses TWO-SCORE model (v4.5 requirement)
    The header must show BOTH:
      INTERNAL_BUILD_PROGRESS: ~XX%
      END_TO_END_PRODUCTION_READINESS: ~XX% (range XX-XX%)
    If either is missing or conflated: update immediately as Tier A action.

5.2 Read EPIC_STATUS_TRACKER.md — verify it reflects current cycle state
5.3 Full 14-track project plan review (see PART 5.3 section below)
5.4 ScrapFly readiness check (see PART 5.4 section below)
5.5 PM Direct-Action sweep (see PART 5.5 section below)
5.6 Verified gap list (synthesize from all Parts above)
5.7 Project completion estimate — BOTH SCORES (see PART 5.7 section below)
5.8 TierD-2 live validation stage tracking (see PART 5.8 section below) [NEW v4.5]

====================================================================
PART 5.3 — FULL PROJECT PLAN REVIEW [MANDATORY, EVERY CYCLE — BLOCKING]

5.3.1 Enumerate all 14 track directories from disk:
  ls PM_Pack/ref/project_plan/ → record all directories and file counts

5.3.2 Read ENHANCEMENT_WAVE_SCHEDULE.md — verify wave status table is current

5.3.3 For each of the 14 tracks, answer 3 questions via actual src/ inspection:
  Q1: What is implemented vs stubbed?
  Q2: Does it run with live data or fixture data?
  Q3: What is the acceptance gap between current state and production-ready?

5.3.4 Run these 5 mandatory gap checks:
  CHECK 1 (demo data zero): Get-ChildItem src\dashboard\pages\ | Select-String "build_dashboard_demo_data" → must be EMPTY
  CHECK 2 (toggle posture): Verify ext_signals=True, llm_relevance=False, scrapfly=False in config.yaml
  CHECK 3 (SRDI artifacts): Verify PM_Pack/ref/project_plan/13_srdi/ files 11/12/13 exist AND content is real (not placeholder)
  CHECK 4 (NICHE_VALIDATION_CONFIG): Verify 9 niche IDs in src/analysis/result_set_validator.py match config.yaml
  CHECK 5 (dashboard page count): Verify >= 9 pages in src/dashboard/pages/ that are not __init__.py

5.3.5 Build full-project gap list BEFORE writing CYCLE_NEXT scope

5.3.6 Confirm: "SRDI complete" != "project complete"
  (Root cause of C060-C073 low advancement: SRDI was done but live collection, playbook,
   and dashboard UX were all still missing. See C060_C073_PROMPT_RETROSPECTIVE_AUDIT.md)

5.3.7 Read spec files for CYCLE_NEXT from disk (not from memory)

====================================================================
PART 5.4 — SCRAPFLY READINESS

Verify scrapfly.enabled=False in committed config.yaml (NEVER True in committed code).
TierD-2 STAGED STATUS (update each cycle):
  V-1 through V-9 stages per LIVE_VALIDATION_MASTER_GATE.md
  Record: which stages are EARNED, which are PENDING, which are FUTURE
  Check: does any V-stage need to advance this cycle?
  Check: has the user run python run.py live-validate --niche python_automation post-C074?
  If pilot evidence exists: update E2E score per staged credit rules in TASK_PRODUCTION_IMPACT_LEDGER.md
ScrapFly runbook: PM_Pack/C074_COST_CONTROL_PROTOCOL.md
Evidence bundle check: data/live_validation_evidence.json (if exists, record stage results)

====================================================================
PART 5.5 — PM DIRECT-ACTION SWEEP (REQUIRED)

Run all Tier A actions before writing prompts:
  1. Jira: transitions, new control ticket, wave story updates
  2. Branch: delete merged cycle branch from origin
  3. HYDRATION_HEADER.md: update to reflect BOTH scores (v4.5)
  4. CURRENT_STATE_CANONICAL.md: update to new cycle state (v4.5)
  5. PRODUCTION_READINESS_SCORECARD.md: update both scores with cycle delta (v4.5)
  6. EPIC_STATUS_TRACKER.md: advance to new cycle state
  7. CYCLE_[DONE].md: fill all placeholders with real SHAs and line counts
  8. Scratch files: delete all C:\Fiverr\*.py, *.json, *.txt scratch
  9. (v4.5) BUILD_SEQUENCE_EXCEPTION_LOG.md: add any new violations found this cycle
  10. (v4.5) STALE_DOCUMENT_REGISTER.md: add any stale documents found this cycle

====================================================================
PART 5.6 — VERIFIED GAP LIST (synthesize from all Parts above)

Build a gap table with columns:
  Gap | Track | Blocker type | E2E credit when resolved | Target cycle | TierD dependency

Rank gaps by E2E production-readiness credit (largest first).
This gap table drives CYCLE_NEXT scope selection.

====================================================================
PART 5.7 — PROJECT COMPLETION ESTIMATE (two-score model — REQUIRED every cycle)

PURPOSE: Report TWO scores after every cycle so progress toward full end-to-end completion
is always visible and never mislabeled. This was the root cause of C060-C073 drift:
the single ~60% score was Internal Build Progress mislabeled as production-ready.

DEFINITION OF 100% (BOTH SCORES):
  Internal Build Progress 100%: all 12 tracks fully implemented in code with tests.
  E2E Production-Grade Readiness 100%: A seller can run a LIVE collection cycle on real
  Fiverr data, get GO/PASS/CONDITIONAL_GO decisions, pricing recommendations, a complete
  gig-creation playbook, and view everything in a polished dashboard. No fixture data,
  no disabled toggles, no Wave 11/12 stubs missing.

--- SCORE 1: INTERNAL ENGINEERING BUILD PROGRESS ---

PURPOSE: Measures how much planned internal build work has been implemented.
Counts: specs, scaffolding, merged PRs, unit tests, module implementation, governance
artifacts, internal scoring, internal dashboard widgets, internal data models.
IMPORTANT: This score can be high even when the system cannot run live in production.

FIXED WEIGHT TABLE — SCORE 1 (weights never change; update % values each cycle):

  Track / Feature                    | Weight | Evidence basis for % value
  -----------------------------------|--------|----------------------------
  01 Foundation + arch + config      |   5%   | CLI passes; config-check OK; 1 worktree
  02 Data schema + models + SRDI     |   8%   | Migration count; no open TC-N items
  03 Collection engine (live data)   |  14%   | Code done=60%; TierD-2 V-2 EARNED=65%; V-3=80%; V-9=100%
  04 Scoring engine                  |  10%   | All 7 dims; golden kw=110 PASS
  05 Analysis pipeline               |   9%   | ext_signals toggle; llm_relevance toggle
  06 LLM recommendations             |   9%   | Task count; run live vs real data?
  07 Dashboard + reporting           |   7%   | 9 pages live; discovery/playbook stubs?
  08 Pricing engine (Wave 9)         |   8%   | S6.1-S6.8 done; CLI wired
  09 Discovery engine (Wave 10)      |  10%   | stories_done / 9 × quality factor
  10 Gig creation playbook (Wave 11) |  10%   | Pipeline built; PDF output; visual analysis
  11 Dashboard UX (Wave 12)          |   7%   | Design system applied; UX complete
  12 SRDI + data integrity           |   3%   | R1-R11 done; G-A closed; integrity checks
  TOTAL                              | 100%   |

--- SCORE 2: END-TO-END PRODUCTION-GRADE READINESS ---

PURPOSE: Measures proven ability to run the full system from live collection through
analysis, scoring, recommendations, dashboard, and exports WITHOUT manual patching.
This score is what matters for production use. It is always LOWER than Score 1.

Hard cap rules (never claim above these without evidence):
  Live collection not proven:           cap Score 2 at 50%
  Live collection done, no scoring:     cap Score 2 at 60%
  No live recommendations:              cap Score 2 at 65%
  Dashboard/export not operator-usable: cap Score 2 at 70%
  No playbook from live data:           cap Score 2 at 78%
  No repeated unattended runs:          cap Score 2 at 82%
  No release/operator docs complete:    cap Score 2 at 90%

Score 2 evidence: Use TierD-2 live validation stages V-1 through V-9 from
LIVE_VALIDATION_MASTER_GATE.md. Only count credit for stages that have evidence.

--- CORRECTED BASELINE (after PM Governance Correction, C074) ---

  As of C074 (2026-06-09):
    SCORE 1 — INTERNAL BUILD PROGRESS: ~67%
    Track 01 Foundation:       93%  | CLI passes, config-check OK
    Track 02 Data/models:      92%  | 30+ ORM models, migrations 1-13, ext_signals live
    Track 03 Collection:       60%  | Code done; TierD-2 V-2 infrastructure built (C074)
    Track 04 Scoring:          90%  | All 7 dims live; golden kw=110 62.7/CONDITIONAL_GO
    Track 05 Analysis:         78%  | ext_signals=True; llm_relevance=False (by design)
    Track 06 LLM recs:         70%  | 12 tasks built; not run live against real data
    Track 07 Dashboard:        77%  | 9 pages live; playbook widget stub
    Track 08 Pricing:          88%  | S6.1-S6.8 complete; pricing-export CLI wired
    Track 09 Discovery:        78%  | S7.1-S7.9 ALL DONE (Wave 10 COMPLETE, SCRUM-22 CLOSED)
    Track 10 Playbook:         15%  | S8.3 scaffold done (C074); S8.1-S8.2 pending
    Track 11 Dashboard UX:     10%  | Spec done; Streamlit defaults; Wave 12 unstarted
    Track 12 SRDI:             90%  | R1-R11 done; G-A CLOSED; all checks pass

  Score 1 calculation:
    (0.05×93)+(0.08×92)+(0.14×60)+(0.10×90)+(0.09×78)+(0.09×70)
   +(0.07×77)+(0.08×88)+(0.10×78)+(0.10×15)+(0.07×10)+(0.03×90)
  = 4.65+7.36+8.40+9.00+7.02+6.30+5.39+7.04+7.80+1.50+0.70+2.70 = ~67.9%

  SCORE 2 — E2E PRODUCTION-GRADE READINESS: ~48-50%
    Hard cap applied: ~50% (live collection V-3 not yet proven)
    TierD-2 V-2 credit earned by C074 build: +3-5%
    Additional credit PENDING: user must run python run.py live-validate --niche python_automation
    After successful pilot: Score 2 expected to reach ~55-60%

  PREVIOUS SINGLE-SCORE CALCULATION (v4.4 WRONG):
    The v4.4 score of ~60.4% (C067 baseline) was Internal Build Progress.
    It was NEVER E2E production-ready and should NEVER have been labeled as such.
    See C060_C073_PROMPT_RETROSPECTIVE_AUDIT.md for root cause analysis.

--- HOW TO CALCULATE EACH CYCLE ---

  Score 1 (Internal Build Progress):
  1. Update track % values using gate checks already run in Parts 2 and 5.3.
  2. A track is NOT 100% until it runs in production mode (live data, toggles on, no stubs).
  3. Track 03 Collection cannot exceed 60% while TierD-2 V-2 is the latest earned stage.
  4. Track 09 Discovery: base = (stories_done / 9) × 100; discount if stories are stubs.
  5. Never inflate from memory. Never deflate without evidence.
  6. Weighted Score 1 = sum of (weight × track_%) for all 12 tracks.

  Score 2 (E2E Production-Grade Readiness):
  1. Start from Score 1.
  2. Apply hard caps (see table above).
  3. Apply staged TierD-2 credit per LIVE_VALIDATION_MASTER_GATE.md.
  4. Score 2 <= Score 1 always (it can never be higher than internal build progress).
  5. Record which cap is active and what evidence would break it.

--- REPORT FORMAT (include in every PM review output) ---

  ╔══════════════════════════════════════════════════════════════════════════╗
  ║  SCORE 1 — INTERNAL BUILD PROGRESS:         ~XX% (C0NN, YYYY-MM-DD)   ║
  ║  SCORE 2 — E2E PRODUCTION-GRADE READINESS:  ~XX% (range XX-XX%)       ║
  ║  Active cap: [what's capping Score 2 and what evidence breaks it]      ║
  ║  Delta from last cycle: Score 1 +X%, Score 2 +X% ([what moved])       ║
  ║  Biggest lever for Score 2: [single action that would move it most]    ║
  ║  TierD-2 stage: V-X [EARNED/PENDING] → next: V-X requires [action]    ║
  ║  Next milestone: Score 2 ~YY% after [CYCLE_NEXT scope] completes       ║
  ╚══════════════════════════════════════════════════════════════════════════╝

====================================================================
PART 5.8 — TIERD-2 LIVE VALIDATION STAGE TRACKING (NEW v4.5)

Every PM review must record the current TierD-2 stage and what is needed to advance.
See LIVE_VALIDATION_MASTER_GATE.md for full stage definitions and credit amounts.

CURRENT STAGE TABLE (update each cycle):

  Stage | Requirement                        | E2E Credit | Status
  V-1   | TierD-2 approved + controls        | +0.5%      | EARNED (small unlock)
  V-2   | Infrastructure built (C074)         | +1-2%      | EARNED (collect-live, live-validate, PilotLogger)
  V-3   | First live collection succeeds      | +3-5%      | PENDING (user runs pilot post-C074)
  V-4   | Live data persists in DB            | +1-2%      | PENDING
  V-5   | Live data flows into scoring        | +1-2%      | PENDING
  V-6   | Live data flows into recommendations| +1-2%      | PENDING
  V-7   | Recommendations flow into playbook  | +1-2%      | PENDING
  V-8   | Dashboard/export from live data     | +2-4%      | PENDING
  V-9   | Repeated unattended runs pass       | Full credit | FUTURE

PM ACTIONS EACH CYCLE:
  Check: has user run python run.py live-validate --niche python_automation?
  If yes: read data/live_validation_evidence.json and advance appropriate stages.
  Record: credits_used, gigs_collected, stages_passed, has_full_data in E.md/cycle log.
  Update: LIVE_VALIDATION_MASTER_GATE.md with new stage statuses.
  Update: Score 2 based on newly earned stage credits.

EVIDENCE BUNDLE LOCATION: data/live_validation_evidence.json
LOG LOCATION: data/live_pilot_log.jsonl
PILOT COMMAND: python run.py live-validate --niche python_automation
QUICK TEST: python run.py collect-live --niche python_automation --budget 100

====================================================================
PART 6 — WRITE PM PACK UPDATES (VERIFIED INFO ONLY — BEFORE PROMPTS)

PM_Pack\07_hydration\HYDRATION_HEADER.md (v4.5 TWO-SCORE REQUIRED FORMAT):
  - CYCLE_CURRENT = CYCLE_NEXT; CYCLE_DONE verified complete
  - C_[DONE]_SQUASH_SHA: [SHA from D's merge]
  - INTERNAL_BUILD_PROGRESS: ~XX% (list changed tracks with before/after %)
  - END_TO_END_PRODUCTION_READINESS: ~XX% (range XX-XX%, active cap: [what caps it])
  - Hard cap: [what evidence breaks the current cap]
  - TierD-2 stage: V-X [status], next: V-X requires [action]
  - Develop HEAD; suite count + coverage; golden OFF==legacy; regression list
  - Production Readiness Gates: G-A: [status] | G-B: [status] | G-C: [status] | G-D: [status]
  - TierD-2 live validation stages V-1 through V-9 with EARNED/PENDING/FUTURE
  - Open Tier-D items (TierD-1: 12 stases; TierD-2: pilot status)
  - Open Jira gaps; SRDI roadmap position (CLOSED since C060)
  - Wave status table: Wave 0-8 DONE | Wave 9 DONE | Wave 10 DONE | Wave 11 [status] | Wave 12 [status]
  - CRITICAL USER ACTION (if pilot pending): python run.py live-validate --niche python_automation
  - DO NOT CLAIM section: list things that must not be claimed (e.g. E2E > 50% before V-3)

PM_Pack\CURRENT_STATE_CANONICAL.md (v4.5 — update every cycle):
  Single source of truth. Must reflect new CYCLE_CURRENT and both scores.

PM_Pack\PRODUCTION_READINESS_SCORECARD.md (v4.5 — update every cycle):
  All 12 track % values with dated evidence.
  Score 1 weighted calculation.
  Score 2 with active cap and how to break it.
  Delta from previous cycle with explanation.

PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md:
  - CYCLE_NEXT scope + mission; wave progress; open stories with unmet DoD
  - Gate advancement this cycle; new Jira tickets to create
  - V-stage advancement if pilot was run

PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md:
  - §7 if regressions added; version-history row

PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md:
  - §13.8 prompt-sizing table; governance SHA; Jira keys; codecov-patch judgment
  - Gate status before/after; Tier-D items surfaced
  - TierD-2 stage at cycle close
  - BOTH scores recorded (Score 1 and Score 2)

PM_Pack\BUILD_SEQUENCE_EXCEPTION_LOG.md (v4.5 — add any new violations):
  If any prompt was found to violate the 55-task floor: add entry.
  If any governance document was found stale: add entry.

====================================================================
PART 7 — WRITE CURSOR AGENT PROMPTS (ONLY AFTER PARTS 1-6 + 5.3 + 5.5 + 5.7 + 5.8)

MANDATORY PRE-PROMPT CHECKLIST (v4.5 additions):
  [ ] Part 5.7 two-score model calculated and recorded before writing prompts
  [ ] Score 2 cap identified — cycle scope targets advancing that cap
  [ ] TierD-2 stage checked — does CYCLE_NEXT need to run the live pilot?
  [ ] +5% E2E gate calculated per CYCLE_PRODUCTION_ADVANCEMENT_GATE.md
  [ ] If +5% cannot honestly be reached: stop and explain blocker (do not write prompts)
  [ ] CYCLE_READINESS_FORECAST_TEMPLATE.md filled before writing agent prompts
  [ ] 18 governance documents read; no conflicts with planned scope

AGENT PROMPT REQUIREMENTS (effective C067+):

LINE FLOORS (§8.3 v4.3 — effective C067+):
  A >= 1,000 | B >= 1,200 | E >= 950 | C >= 900 | F >= 1,000 | D >= 1,200 | TOTAL >= 6,250

TASK FLOOR (v4.3 — effective C067+ — NEVER-BREAK RULE per AGENT_TASK_FLOOR_ENFORCEMENT.md):
  Every agent: >= 55 LARGE-XXLARGE tasks minimum.
  XXXLARGE RETIRED: decompose into 2-3 XXLARGE tasks.
  A TASK 1 MANDATORY: must include the task floor verification script.

TASK FLOOR VERIFICATION (A must run as TASK 1):
  import re
  floors = {'A':55,'B':55,'E':55,'C':55,'F':55,'D':55}
  for ag in ['A','B','E','C','F','D']:
      content = open(f'PM_Pack/03_cursor_agent_system/CYCLE_{N}_AGENT_{ag}_PROMPT.md').read()
      count = len(re.findall(r'## (?:TASK|GATE) [0-9]', content))
      assert count >= floors[ag], f'HARD STOP: Agent {ag} = {count} (need {floors[ag]})'
  print('ALL 6 AGENTS PASS')
  If any agent fails: HALT. Never proceed with B. Fix the prompt first.

TASK QUALITY REQUIREMENTS (per TASK_SUBSTANCE_GATE.md):
  Every task must score >= 4 in Production Outcome, Evidence Strength, E2E Readiness.
  SMALL tasks (check import, verify file exists, record SHA, git pull) do NOT count.
  See LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md for per-role LARGE definitions.

CYCLE-LEVEL +5% E2E GATE (per CYCLE_PRODUCTION_ADVANCEMENT_GATE.md):
  Every cycle must credibly target >= +5% E2E Production-Grade Readiness advancement.
  Agent A must include a production-readiness forecast using CYCLE_READINESS_FORECAST_TEMPLATE.md.
  If +5% cannot honestly be achieved: PM must stop, explain blocker, request rescope.

PROMPT QUALITY GATES (run before releasing any prompt):
  PQ-0: Task count >= 55 per agent (run enforcement script)
  PQ-1: Pre-flight source gate (CURRENT_STATE_CANONICAL.md, not memory)
  PQ-2: Task substance gate (6-dimension scoring per TASK_SUBSTANCE_GATE.md)
  PQ-3: Anti-filler gate (no SMALL tasks counted toward floor)
  PQ-4: +5% E2E forecast gate (credible advancement plan)
  PQ-5: LARGE-XXLARGE classification gate (per LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md)
  PQ-6: No-stale-source gate (no old completion %, stale hydration, old scores)
  PQ-7: Prompt red-team review (15 questions from PROMPT_RED_TEAM_REVIEW_GATE.md)

AGENT-SPECIFIC RULES:
  A: produces spec artifacts (not just handoff outlines); each spec has API contract + acceptance criteria
     TASK 1 must include task floor verification script
     Must include cycle production-readiness forecast
     Must write CYCLE_READINESS_FORECAST.md for this cycle
  B: ONLY src/ author; §12.1 notice in first 25 lines; correct zone check
     Must implement all TierD-2 conditions if cycle involves live collection
  E: ONLY CYCLE_[N]_AGENT_E.md; no src/ prohibition explicit in prompt
     No pad lines ("floor-line-NNN PROHIBITED")
     Each task is a production validation probe with specific measured values
  C: NOT listed as waiting for F (C runs after B+E, before F)
     Independent G-B (PRAGMA) and G-C (demo-data) checks
  F: ONLY test files + report; no src/; each task is an actual test implementation
  D: §12.3 playbook present; G1 attribution lists ALL commits from git log
     Independent G-B and G-C checks
     Records BOTH scores (Score 1 and Score 2) in hydration update
     TierD-2 stage update in hydration
     Includes user post-merge instructions if live pilot is pending

OTHER PROMPT RULES:
  SHA resolved: zero [CXXX_SQUASH_SHA] matches in any prompt
  No API tokens in prompts
  "END OF PROMPT" exactly once per file
  Tier-C items routed to agents (never executed by PM directly)
  scrapfly.enabled=False in committed config.yaml — verify before writing collection prompts

====================================================================
PART 8 — SELF-AUDIT BEFORE SUBMITTING (any NO → go back)

STATE & ORIENTATION
[ ] State verification (git log + gh open PRs) run FIRST before anything else?
[ ] Hydration header read (BOTH scores: Internal Build + E2E Readiness)? [v4.5]
[ ] Strategy doc §7/§8/§9/§10/§11/§12/§13 read?
[ ] CURRENT_STATE_CANONICAL.md read (single source of truth)? [v4.5]

CYCLE_DONE VERIFICATION
[ ] All 6 agent reports read in full?
[ ] Every claimed file verified on disk?
[ ] Full suite run; actual coverage % recorded?
[ ] Agent E: ZERO src/ and tests/ verified?
[ ] Agent F: ZERO src/ verified?
[ ] Agent E: EACH E commit SHA checked individually?
[ ] §11 PRAGMA check run for any touched models?
[ ] Code-vs-config drift check run (9 niche_ids)?
[ ] scrapfly committed enabled=false confirmed?
[ ] Git/gh via Invoke-Exe ProcessStartInfo?
[ ] GitHub: merged=true + ENFORCED CI + codecov/project SUCCESS?
[ ] codecov/patch state recorded + merge-over documented?
[ ] Merge confirmed via merged:true + squash commit (NOT is-ancestor)?
[ ] Golden OFF==legacy confirmed; baseline cycle037_live.db untouched?
[ ] Codex run TWICE (G-002); both JSONs recorded; zero unresolved?
[ ] Live Jira: corrections MADE (not just noted)?
[ ] Merged cycle branch deleted on origin?

FULL-PROJECT PLAN REVIEW (BLOCKING — all must be YES)
[ ] 5.3.1: all 14 track directories enumerated from disk?
[ ] 5.3.2: ENHANCEMENT_WAVE_SCHEDULE.md read?
[ ] 5.3.3: 3 questions answered per track via actual src/ inspection (not memory)?
[ ] 5.3.4 CHECK 1: dashboard demo-data check run?
[ ] 5.3.4 CHECK 2: toggle posture checked (external_signals, llm_relevance, scrapfly)?
[ ] 5.3.4 CHECK 3: SRDI launch artifacts 11/12/13 verified on disk AND content is real?
[ ] 5.3.4 CHECK 4: NICHE_VALIDATION_CONFIG drift check run?
[ ] 5.3.4 CHECK 5: dashboard page count verified?
[ ] 5.3.5: full-project gap list built BEFORE writing CYCLE_NEXT scope?
[ ] 5.3.7: spec files for CYCLE_NEXT read from disk (not from memory)?
[ ] Confirmed: "SRDI complete" != "project complete"? [v4.5: see C060-C073 audit]

PRODUCTION READINESS GATES
[ ] G-A status verified and updated in hydration header?
[ ] G-B status verified via PRAGMA and updated?
[ ] G-C status verified via demo-data check and updated?
[ ] G-D status verified via wave schedule and updated?
[ ] At least one gate advanced this cycle, OR explicit rationale for deferral documented?

TWO-SCORE MODEL (NEW v4.5 — ALL MUST BE YES)
[ ] Score 1 (Internal Build Progress) calculated with all 12 tracks from disk evidence?
[ ] Score 2 (E2E Readiness) calculated separately from Score 1?
[ ] Active Score 2 hard cap identified (which cap is currently limiting the score)?
[ ] Evidence required to break the current cap documented?
[ ] TierD-2 staged credit applied correctly (no inflated approval-only credit)?
[ ] Score 2 confirmed <= Score 1?
[ ] Neither score labeled "production-ready" without Score 2 evidence?
[ ] Delta from last cycle stated for BOTH scores?
[ ] Biggest lever for Score 2 stated?
[ ] PRODUCTION_READINESS_SCORECARD.md updated with new values?
[ ] CURRENT_STATE_CANONICAL.md updated with new cycle state?
[ ] Hydration header shows BOTH scores (not a single combined score)?

TIERD-2 LIVE VALIDATION TRACKING (NEW v4.5)
[ ] Current V-stage status recorded (V-1 through V-9)?
[ ] Has user run live-validate post-C074? (check if data/live_validation_evidence.json exists)
[ ] If evidence exists: stages advanced and E2E credit updated?
[ ] LIVE_VALIDATION_MASTER_GATE.md updated with current stage status?
[ ] User post-merge action documented in D prompt if pilot still pending?
[ ] Stage progression plan included in CYCLE_NEXT scope if pilot has not been run?

TASK FLOOR ENFORCEMENT (NEW v4.5 — NEVER-BREAK RULE)
[ ] Task floor verification script run for ALL 6 prompts?
[ ] All 6 agents >= 55 tasks confirmed (A>=55, B>=55, E>=55, C>=55, F>=55, D>=55)?
[ ] A TASK 1 includes the mandatory task floor verification script?
[ ] All tasks classified as LARGE/XLARGE/XXLARGE under LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md?
[ ] SMALL tasks (check import, verify file, git pull, SHA record) NOT counted toward floor?
[ ] If any agent failed floor check: BUILD_SEQUENCE_EXCEPTION_LOG.md updated with violation?

JIRA BOARD AUDIT (not just current cycle)
[ ] ALL non-Done Jira issues reviewed (Part 4.4a JQL query run)?
[ ] ~10-15 stale board-setup issues closed as Tier A (Part 4.4b)?
[ ] Canonical product epics (SCRUM-16 through SCRUM-25) verified In Progress?
[ ] Jira-to-plan cross-reference run (14 tracks vs. Jira epics)?
[ ] Any track with NO Jira coverage → story created?
[ ] CYCLE_NEXT control task created in Jira (D's responsibility post-merge)?
[ ] TierD-2 pilot result ticket created if pilot has been run?

PM PACK & GOVERNANCE
[ ] Strategy §7 updated if new regressions?
[ ] PM Pack updated with VERIFIED state (including BOTH gate status and BOTH scores)?
[ ] ALL scratch files deleted (C:\Fiverr\*.py, *.json, *.txt and PM_Pack\ directories)?
[ ] Governance changes committed + pushed to develop?
[ ] Tier-D items surfaced to user (TierD-1: 12 stashes; TierD-2: V-stage status)?
[ ] BOTH scores calculated per Part 5.7 and recorded in hydration header?
[ ] All 12 track % values assigned from actual src/ evidence (not memory)?
[ ] Delta from last cycle, biggest lever, and next milestone stated for BOTH scores?
[ ] CYCLE_READINESS_FORECAST_TEMPLATE.md completed for CYCLE_NEXT?
[ ] 18 PM governance documents all present (run doc existence check)?
[ ] AGENT_TASK_FLOOR_ENFORCEMENT.md present and referenced in A TASK 1?

PROMPT QUALITY (§13.8)
[ ] SHA resolved in all 6 → zero [CXXX_SQUASH_SHA] matches?
[ ] Line floors (v4.3 C067+): A>=1000 B>=1200 E>=950 C>=900 F>=1000 D>=1200?
[ ] All 7 depth quality checks pass per prompt?
[ ] 55+ LARGE-XXLARGE tasks per prompt (XXXLARGE PROHIBITED)?
[ ] Task floor verification script in A TASK 1? [v4.5 NEW]
[ ] All tasks actually LARGE under LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md? [v4.5 NEW]
[ ] PQ-0 through PQ-7 gates passed per PROMPT_QUALITY_REVIEW_GATE.md? [v4.5 NEW]
[ ] Cycle-level +5% E2E forecast in A prompt? [v4.5 NEW]
[ ] CYCLE_READINESS_FORECAST_TEMPLATE.md filled? [v4.5 NEW]
[ ] B and E: §12.1 notice in first 25 lines + correct zone check?
[ ] E: explicit src/ prohibition ("record gap for B, do not add it")?
[ ] E: no pad lines prohibition ("floor-line-NNN PROHIBITED")?
[ ] E: each task is a production validation probe with specific measured values? [v4.5 NEW]
[ ] C: NOT listed as waiting for F?
[ ] D: §12.3 playbook present?
[ ] D: G1 attribution lists ALL commits from git log (not just C's SHAs)?
[ ] D: independent G-B (PRAGMA) and G-C (demo-data) checks?
[ ] D: records BOTH scores in hydration update? [v4.5 NEW]
[ ] D: TierD-2 stage update in hydration? [v4.5 NEW]
[ ] D: user post-merge instructions if live pilot is pending? [v4.5 NEW]
[ ] E (if live): ScrapFly runbook + fallback + throwaway DB + load_dotenv not $env:?
[ ] No API tokens in prompts?
[ ] "END OF PROMPT" exactly once per file?
[ ] Tier-C items routed to agents?

====================================================================
JIRA BOARD HYGIENE — STANDING CLEANUP TASK (Tier A — chip away each cycle)

Every cycle review, close/clean a batch of stale board-setup issues:
  JQL: project=SCRUM AND status = "To Do" AND created <= -90d ORDER BY created ASC
  Close as "Done" with comment "Stale board-setup ticket — closing during C0NN PM review."
  Target: 10-15 issues per cycle until the board is clean.
  This is Tier A: do it immediately, no agent needed.

====================================================================
WAVE STATUS TABLE (update every cycle)

  Wave | Name                          | Status
  0-8  | Foundation through Reporting  | COMPLETE
  9    | Pricing Strategy Engine        | COMPLETE (C062-C065, S6.1-S6.8)
  10   | Niche Discovery Engine         | COMPLETE (C066-C073, SCRUM-22 CLOSED, S7.1-S7.9)
  11   | Gig Creation Playbook          | IN PROGRESS
         S8.3 Seller Setup Playbook      DONE (C074)
         S8.1 Gig Visual Analysis        To Do (C075)
         S8.2 Seller Profile Optimization To Do (C076)
  12   | Dashboard UX Overhaul          | NOT STARTED

G-D closes when Wave 11 and Wave 12 are fully implemented and connected to live data.

====================================================================
END OF UNIVERSAL POST-CYCLE PM REVIEW PROMPT (v4.5)

