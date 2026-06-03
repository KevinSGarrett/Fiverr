====================================================================
FIVERR RESEARCH SYSTEM — UNIVERSAL POST-CYCLE PM REVIEW PROMPT

Version: 4.2 (Universal — no cycle-number editing required)
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
  gh = 'C:\Program Files\GitHub CLI\gh.exe'

GH COMMANDS: use gh api with ABSOLUTE REST paths. gh pr list/view/create FAIL (no repo detection).
SQUASH-MERGE CAVEAT: is-ancestor returns 1 even when squash-merged. Verify via merged:true + title "(#PR)".
PYTHON: py -3.12. Bare python = Store stub.
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
  REPLACE [CXXX_SQUASH_SHA] in prompts (§13.2).
TIER B: large/multi-file doc commits; created Jira keys; git rm --cached.
TIER C: ANY src/; ANY tests/ add/modify; ANY config.yaml runtime-behavior; anything needing a gate.
TIER D: drop/clear stashes (standing: 6 stale — cycle051/047/043/036/029/012); history rewrite;
  force-push; delete unmerged branch; rotate secrets; LARGE live ScrapFly burn; baseline DB restore.

====================================================================
PRODUCTION READINESS GATES (track status every cycle — update after each merge)
====================================================================

These 4 gates define whether the system is production-ready. The PM must review the status of
each gate at EVERY cycle review and determine if CYCLE_NEXT scope should advance them.
"All gates OPEN" is not acceptable as a permanent state — each cycle must close or advance at
least one gate, or explicitly defer with documented rationale.

G-A: SRDI LAUNCH ARTIFACTS
  Definition: PM_Pack\ref\project_plan\13_srdi\ contains 11_AI_AGENT_HANDOFF.md,
    12_LAUNCH_READINESS.md, and 13_RISK_COMPLIANCE_COST.md as full (not placeholder) documents.
  Status as of C061: PARTIAL — placeholder files created; full content not yet written.
  Closing criteria: all 3 files contain real content (agent handoff guide, launch checklist,
    risk register) — not just headers.
  CYCLE_NEXT scope if OPEN: assign PM Tier A content completion or Tier C if technical.

G-B: DATA SCHEMA COMPLETENESS
  Definition: All ORM model columns required by the scoring/analysis pipeline are present
    in the committed DB schema (no deferred TC-N items).
  Status as of C061: CLOSED after C061 IF TC-1 migration_11 was applied and PRAGMA-verified.
    TC-1 adds raw_value, relevance_score, trend_direction to external_signals table.
  Verification: PRAGMA check: py -3.12 -c "from sqlalchemy import create_engine, inspect;
    e=create_engine('sqlite:///data/foundation_gate_ci.db');
    cols=sorted([c['name'] for c in inspect(e).get_columns('external_signals')]);
    print(cols)"
    Must contain raw_value + relevance_score + trend_direction.
  Closing criteria: PRAGMA confirms all required columns exist; §11.2 parity table all YES.
  CYCLE_NEXT scope if OPEN: TC-1 is P0 Agent B work.

G-C: DASHBOARD LIVE DATA
  Definition: All dashboard pages query real SQLAlchemy sessions; zero pages call
    build_dashboard_demo_data() or any equivalent sample/mock data function.
  Status as of C061: CLOSED after C061 IF B wired all 9 pages.
  Verification: Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content $_.FullName |
    Select-String "build_dashboard_demo_data" }
    Must return EMPTY.
  Closing criteria: zero demo-data imports; all 9 pages use get_db_session(); empty-DB guard
    renders gracefully (st.info) rather than crashing.
  CYCLE_NEXT scope if OPEN: dashboard live-data wiring is P0 Agent B work.

G-D: WAVE IMPLEMENTATION COVERAGE
  Definition: All wave specs (Waves 0-12) have corresponding implementation in src/.
    Currently the critical gap is Waves 9-12 (Pricing, Discovery, Playbook, Dashboard UX).
  Status as of C061: OPEN — Waves 9-12 unstarted.
  Closing criteria: each wave's spec has implementation verified in src/ (not just spec written).
  CYCLE_NEXT scope if OPEN: start Wave 9 (Pricing Engine) as the next initiative after G-B and G-C close.

When updating this table after each cycle, use this format in the hydration header:
  G-A: PARTIAL | G-B: CLOSED (C061) | G-C: CLOSED (C061) | G-D: OPEN (Waves 9-12)

====================================================================
PART 0 — ORIENT: DISCOVER CURRENT STATE

Step 0.1 — Read the hydration header:
  Read: C:\Fiverr\Fiverr\PM_Pack\07_hydration\HYDRATION_HEADER.md
  Extract: CYCLE_DONE; CYCLE_NEXT; develop SHA; suite count + coverage; regression pack size;
  SRDI roadmap position; Production Readiness Gate status (G-A through G-D); Tier-D items.

Step 0.2 — Read the strategy doc for ALL permanent rules:
  §7 regression pack | §8 sizing + floors | §8.4 BLOCKING gate | §9 PM authority |
  §10 ScrapFly | §11 model-migration parity | §12 parallel contract | §13 PM rules.

Step 0.3 — Read the completed cycle's Agent D report:
  Read: C:\Fiverr\Fiverr\docs\cycle_reports\CYCLE_[CYCLE_DONE]_AGENT_D.md
  Extract: final squash SHA; PR number; gate checklist; golden OFF==legacy result;
  production readiness gate changes this cycle.

6-AGENT ARCHITECTURE (effective C047+; §12.2 authoritative):
  Stage 1 — A solo | Stage 2 — B + E PARALLEL | Stage 3 — C after BOTH B AND E (NEVER after F)
  Stage 4 — F after C GO | Stage 5 — D after ALL 5
  E: commits ONLY CYCLE_[N]_AGENT_E.md — NEVER src/, tests/, config.yaml
  F: commits ONLY test files + report — NEVER src/
  B: ONLY src/ author (attribution invariant)

====================================================================
PART 1 — READ ALL 6 AGENT REPORTS FOR CYCLE_DONE (REQUIRED)

Step 1.1 — Confirm all 6 reports exist: CYCLE_[N]_AGENT_A/B/E/C/F/D.md
Step 1.2 — Read ALL 6 in full. Extract:
  a) files CLAIMED created/modified
  b) test count + coverage %
  c) Jira keys CLAIMED transitioned/commented
  d) final commit SHA
  e) risks/blockers/gaps flagged
  f) Agent E: ZERO src/ and tests/ changes claimed?
  g) Agent F: ZERO src/ changes claimed?
  h) Agent E live work: real ScrapFly session line? Or "[SEED — no live signal]"?
  i) Did any agent report indicate a production readiness gate was advanced? (G-A through G-D)

Step 1.3 — Claimed-deliverables table: | File Path | Agent | Claimed Action | Verified? |
Step 1.4 — Record regression count from D's report. §7 is authoritative.

====================================================================
PART 2 — VERIFY ACTUAL LOCAL CODEBASE STATE (REQUIRED)

Step 2.1 — Run via Invoke-Exe:
  git rev-parse --show-toplevel (== C:\Fiverr\Fiverr)
  git branch --show-current
  git log --oneline -20
  git status --short --branch
  git worktree list (MUST be exactly ONE)

Step 2.2 — Verify every claimed file exists: Test-Path each row.
Step 2.3 — For every claimed test file: py -3.12 -m pytest -q "path" --no-header; compare count.
Step 2.4 — Full suite + coverage: py -3.12 -m pytest -q --cov=src --cov-fail-under=90
  This is truth. Reports are claims.
Step 2.5 — Verify key module imports for new modules.
Step 2.6 — CLI smoke: py -3.12 run.py config-check; py -3.12 run.py phase2-smoke
Step 2.7 — Git hygiene: no .env, *.db, coverage.xml tracked. If tracked: git rm --cached + .gitignore.

Step 2.8 — CODE-vs-CONFIG DRIFT CHECK:
  NICHE_VALIDATION_CONFIG in src/analysis/result_set_validator.py MUST exactly match 9 niche_ids:
    prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow, mcp_ai_agent, python_automation,
    ai_tool_llm_integration, ai_agent_development, workflow_automation, python_web_scraping
  Mismatch = DRIFT → Tier-C for Agent B.

Step 2.9 — SCRAPFLY COMMITTED-STATE CHECK: config.yaml enabled: false confirmed.
Step 2.10 — ZONE VERIFICATION:
  2.10a: git show --name-only [E_SHA] → ZERO src/ or tests/
  2.10b: git show --name-only [F_SHA] → ZERO src/
  2.10c: All src/ files in cycle range appear ONLY in B commits.

Step 2.11 — GOLDEN PARITY + BASELINE INTEGRITY:
  Golden OFF==legacy PASSED. kw=110 ~62.7 / CONDITIONAL_GO. data/cycle037_live.db UNTOUCHED.

Step 2.12 — §11 MODEL-MIGRATION PARITY (if src/models/*.py touched):
  PRAGMA each modified table. Any ORM column absent from DB = parity gap → Tier-C for B.
  After C061: also verify G-B gate: raw_value + relevance_score + trend_direction in external_signals.

Step 2.13 — PRODUCTION READINESS GATE VERIFICATION (every cycle):
  G-B (schema): run PRAGMA on external_signals — confirm TC-1 columns present.
  G-C (dashboard): Get-ChildItem src\dashboard\pages\ | ... Select-String "build_dashboard_demo_data"
    Must return EMPTY post-C061.
  G-A (artifacts): Test-Path each of 11/12/13 in PM_Pack\ref\project_plan\13_srdi\ — are they real docs?
  G-D (waves): read ENHANCEMENT_WAVE_SCHEDULE.md — which waves still have no src/ implementation?
  Record gate status in Part 6 updates.

====================================================================
PART 3 — LIVE GITHUB VERIFICATION (REQUIRED)

Step 3.1 — List PRs: api "repos/KevinSGarrett/Fiverr/pulls?state=all&per_page=20"
Step 3.2 — PR detail + CI: confirm merged=true, ENFORCED gate SUCCESS, codecov/project SUCCESS.
  codecov/patch = ADVISORY. Document if fails; proceed if project floor passed.
Step 3.3 — Codex GraphQL: run YOURSELF (TWICE — G-002). Record both raw JSON outputs.
  Any unresolved thread = BLOCKER.
Step 3.4 — Develop HEAD == squash commit (title ends "(#PR)"). NOT is-ancestor.
Step 3.5 — Branch cleanup (Tier A NOW): delete merged cycle branch on origin.

====================================================================
PART 4 — LIVE JIRA VERIFICATION (REQUIRED)
====================================================================

(cloudId eae77257-a572-4e19-b746-8b184ba2d01f; Done transition id "41")

Step 4.1 — CURRENT CYCLE STORIES: Query active sprint stories; record key/summary/status.
  For every key an agent claimed: claimed status | actual | match?
  Control task → Done. Stories with DoD met → Done. DoD not met → In Progress + comment.

Step 4.2 — CYCLE CLOSURE (Tier A NOW):
  Transition control task to Done (id 41). Leave closeout comment: PR #, SHA, gate results, golden.
  Close all stories whose DoD is verifiably met. Revert if DoD not actually met.

Step 4.3 — EPIC-LEVEL HEALTH CHECK: query all canonical product epics; verify status is correct.
  Canonical epics that must be In Progress until fully implemented:
    SCRUM-16 (Epic 01 Foundation) | SCRUM-17 (Epic 02 Collection) | SCRUM-19 (Epic 04 Scoring)
    SCRUM-20 (Epic 05 Recommendations) | SCRUM-21 (Epic 06 Pricing) | SCRUM-23 (Epic 08 Playbook)
    SCRUM-24 (Epic 09 Dashboard) | SCRUM-25 (Epic 10 Integration/Launch)
  If any canonical epic is marked Done before full implementation verified: REVERT to In Progress.
  If any canonical epic is marked To Do when work is active: ADVANCE to In Progress.

Step 4.4 — FULL BOARD AUDIT (every cycle — Tier A now for obvious closures):
  This step reviews ALL non-Done Jira items against the project plan and code reality.
  It is the PM's job to catch items that have drifted from reality.

  4.4a: Query ALL open issues (not just sprint):
    JQL: project = SCRUM AND status != Done ORDER BY created ASC
    Review each issue and categorize:
      CATEGORY A (done in code, not closed in Jira): close with comment referencing evidence
      CATEGORY B (stale board-setup from Waves 1-9): close ~10-15 per cycle as Tier A
      CATEGORY C (active product work — correct In Progress): leave as is
      CATEGORY D (scope gap — work identified but no Jira story): create story

  4.4b: STALE BOARD-SETUP ISSUES (SCRUM-5 through ~SCRUM-72):
    These are Wave 1-9 governance/planning issues that were completed but never closed.
    Review each against the project state: if the work was done, close it.
    Close ~10-15 per cycle; target 0 stale issues within 4-6 cycles.
    DO NOT close: canonical product epics (SCRUM-16 through SCRUM-25).
    DO NOT close: SCRUM-38 (GitHub repo epic — still In Progress).

  4.4c: JIRA-TO-PLAN CROSS-REFERENCE:
    For each of the 14 project plan tracks, verify there is at least one active Jira story or epic:
      00_meta → SCRUM-6 (Jira governance epic)
      01_vision → no active Jira story needed (vision docs only)
      02_architecture → SCRUM-16 (Foundation epic, which covers architecture)
      03_data → SCRUM-16 (models) + TC-1 story if C061+ work pending
      04_collection → SCRUM-17 (Collection epic) + DL-207 story if pending
      05_scoring → SCRUM-19 (Scoring epic)
      06_analysis → SCRUM-19/20 (Scoring/Recommendations) + toggle stories
      07_reporting → SCRUM-24 (Dashboard epic) + dashboard wiring story
      08_roadmap → SCRUM-16 through SCRUM-25 (the product epic set IS the roadmap)
      09_pricing → SCRUM-21 (Pricing epic) + Wave 9 story when started
      10_discovery → No Jira epic yet (none was created). Create story when Wave 10 begins.
      11_playbook → SCRUM-23 (Playbook epic) + Wave 11 story when started
      12_dashboard_ux → SCRUM-24 (Dashboard epic) + Wave 12 story when started
      13_srdi → SRDI stories (all Done after C060); launch artifact stories if G-A open
    Any track with NO Jira coverage at all = PM must create story (Tier A).

  4.4d: SPRINT HYGIENE: ensure no orphaned stories exist in the sprint without a parent epic.

Step 4.5 — MAKE ALL CORRECTIONS NOW (Tier A). Never leave Jira in a state that contradicts
  verified code/PR reality. Note: Tier D items require user approval before acting.

====================================================================
PART 5 — PM PACK & SPEC REVIEW (REQUIRED)

Step 5.1 — Read PM Pack state files; compare planned vs verified; document every deviation:
  PM_Pack\07_hydration\HYDRATION_HEADER.md
  PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md
  PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md

Step 5.2 — List PM_Pack\10_cycle_log contents.

====================================================================
PART 5.3 — FULL PROJECT PLAN REVIEW [MANDATORY, EVERY CYCLE — BLOCKING]
====================================================================

ROOT CAUSE OF THE C051-C060 DRIFT: For 10 cycles, Part 5.3 only read 4 of 14 plan directories.
SRDI-complete was silently treated as project-complete. Consequences:
  - 9 dashboard pages ran on demo data for 10+ cycles — unnoticed
  - TC-1 ExternalSignal schema deferred 10+ cycles — unnoticed
  - SRDI launch artifacts 11/12/13 missing from disk — unnoticed
  - Waves 9-12 entirely unstarted — unnoticed
  - LLM and external signals toggles off — unnoticed

THIS SECTION IS NOW BLOCKING. No CYCLE_NEXT scope may be determined until ALL sub-steps complete.
"SRDI complete" does NOT mean "project complete." These are two entirely different things.

--- 5.3.1 ENUMERATE all 14 plan tracks ---

  dir C:\Fiverr\Fiverr\PM_Pack\ref\project_plan
  Expected: 00_meta, 01_vision, 02_architecture, 03_data, 04_collection, 05_scoring,
            06_analysis, 07_reporting, 08_roadmap, 09_pricing, 10_discovery,
            11_playbook, 12_dashboard_ux, 13_srdi
  If any directory is missing: STOP. Document as a critical gap.

--- 5.3.2 READ the master wave schedule ---

  Read: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\00_meta\ENHANCEMENT_WAVE_SCHEDULE.md

  CRITICAL: "Design-complete" in the schedule means SPEC WAS WRITTEN, not code deployed.
  For each wave, you MUST verify implementation vs. spec separately.

--- 5.3.3 ASSESS each of the 14 tracks ---

For each track, answer ALL THREE questions by reading spec files AND checking src/ directly:
  a) Is the spec IMPLEMENTED in src/? (check actual code files — not agent claims, not memory)
  b) Is it running in PRODUCTION MODE? (live data? toggles ON? no demo data? no SEED band?)
  c) What are the current blocking technical debts?

HOW TO UPDATE THIS TABLE: for each track, open the spec file AND run the relevant check:
  - 03_data: run PRAGMA on external_signals; open src/models/external_signal.py
  - 07_reporting: run Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content ... | Select-String "build_dashboard_demo_data" }
  - 04_collection: run a test collection and check if RSV band is LIVE or SEED
  - 05_scoring/06_analysis: read config.yaml for toggle values
  DO NOT update from memory. Run the check. Then update.

Current baseline (verified against src/ as of C061 — update each cycle with actual checks):

| Track | Jira Epic(s) | Implementation | Production Mode | Key Blockers |
|-------|-------------|---------------|-----------------|--------------|
| 00_meta | SCRUM-6 | Partial | N/A (governance) | Open questions |
| 01_vision | N/A | Substantial | Yes | None |
| 02_architecture | SCRUM-16 | Substantial | Mostly | v2 future |
| 03_data | SCRUM-16 | Substantial | No — G-B | TC-1 missing cols (C061 closes if done) |
| 04_collection | SCRUM-17 | Partial | No — SEED | DL-207 URL shape; TC-1 blocks ext signals |
| 05_scoring | SCRUM-19 | Substantial | Yes (toggles by design) | LLM/ext signals off |
| 06_analysis | SCRUM-19/20 | Partial | No — toggles off | llm_relevance=false; ext_signals=false |
| 07_reporting | SCRUM-24 | Partial | No — G-C | Demo data (C061 closes if done) |
| 08_roadmap | SCRUM-16-25 | Substantial (v1) | Yes | v2 roadmap future |
| 09_pricing | SCRUM-21 | Partial | No | Wave 9 not started |
| 10_discovery | None yet (create at Wave 10) | Partial | No — SEED | Live data quality blocks |
| 11_playbook | SCRUM-23 | Minimal | No | Wave 11 not started |
| 12_dashboard_ux | SCRUM-24 | Minimal | No | Wave 12 design not built |
| 13_srdi | SRDI stories | Substantial | Partial — G-A | Launch artifacts 11/12/13 incomplete |

After each cycle: re-run the relevant checks above and update the table with dated notes.
Example: "07_reporting: 2026-06-03 verified — 9 pages still use build_dashboard_demo_data()"

--- 5.3.4 RUN mandatory gap checks (every cycle, before writing any task) ---

Run all 5 and record results. These are the 5 checks that would have caught all 10 cycles of drift.

CHECK 1 — Dashboard demo-data dependency (G-C gate):
  Run via scratch .ps1 using Invoke-Exe:
    $pages = Get-ChildItem src\dashboard\pages\ -Filter '*.py'
    foreach ($p in $pages) {
        $hits = Get-Content $p.FullName | Select-String "build_dashboard_demo_data"
        if ($hits) { Write-Host "DEMO_DATA_FOUND: $($p.Name)" }
    }
  MUST produce ZERO output post-C061. Any DEMO_DATA_FOUND line = page still uses demo data.
  G-C remains OPEN. Add that page as P0 Agent B scope in CYCLE_NEXT.

CHECK 2 — Feature toggle posture (is the system actually running live?):
  Get-Content config.yaml | Select-String "external_signals_enabled|llm_relevance|scrapfly"
  Distinguish: disabled-by-debt (should be enabled but isn't) vs disabled-by-design (intentional).
  external_signals_enabled=false after TC-1 verified = DEBT (route to B as P1).
  scrapfly.enabled=false = DESIGN (always committed off; correct).

CHECK 3 — Missing SRDI launch artifacts (G-A gate):
  Get-ChildItem PM_Pack\ref\project_plan\13_srdi\ | Select Name
  Must include: 11_AI_AGENT_HANDOFF.md, 12_LAUNCH_READINESS.md, 13_RISK_COMPLIANCE_COST.md
  If files exist: open each and verify they contain real content (not just headers).
  Placeholder = G-A still failing → add full content to CYCLE_NEXT scope.

CHECK 4 — NICHE_VALIDATION_CONFIG drift:
  Invoke-Exe python '-c "import subprocess; ..."' OR read src/analysis/result_set_validator.py
  NICHE_VALIDATION_CONFIG niche keys must match the 9 niche_ids in config.yaml exactly.
  Mismatch = drift → Tier-C for Agent B.

CHECK 5 — Dashboard page count:
  (Get-ChildItem src\dashboard\pages\ -Filter "*.py" | Where Name -ne "__init__.py").Count
  Must match expected page count. Currently: 9. Any deviation warrants investigation.

--- 5.3.5 BUILD the full-project gap list (BEFORE writing any CYCLE_NEXT task) ---

| Gap | Track | Gate | Prod Ready? | Blocking? | CYCLE_NEXT priority |
|-----|-------|------|-------------|-----------|---------------------|
| TC-1 ExternalSignal schema | 03_data | G-B | No | Yes | P0 (C061 target) |
| DL-207 URL encoding | 04_collection | — | No | Yes — live data | P0 (C061 target) |
| Dashboard demo data (9 pages) | 07_reporting | G-C | No | Yes | P0 (C061 target) |
| SRDI launch artifacts 11/12/13 | 13_srdi | G-A | No | Partial | P0 (C061 partial) |
| external_signals toggle off | 06_analysis | — | No | No (deferred) | P1 post-TC-1 |
| Wave 9 Pricing Engine | 09_pricing | G-D | No | No (future) | P2 (C062+) |
| Wave 10 LLM Discovery | 10_discovery | G-D | No | No (future) | P2 (C062+) |
| Wave 11 Playbook | 11_playbook | G-D | No | No (future) | P2 (C062+) |
| Wave 12 Dashboard UX | 12_dashboard_ux | G-D | No | No (future) | P3 (C063+) |
| (add any new gaps found) | | | | | |

Update this table each PM review. A gap is ONLY removed when implementation is verified by
actually running the relevant check against src/ — not from a git commit message alone.

--- 5.3.6 READ SRDI specs (only if SRDI work is in CYCLE_NEXT scope) ---

Note: SRDI R1-R11 are CLOSED after C060. No more SRDI epic work is expected.
If somehow new SRDI work arises, read BOTH:
  - 13_srdi\epics\R[N]_[EPIC_NAME].md AND the base subsystem spec
  - 13_srdi\07_SEQUENCING_ROADMAP.md, 03_EPIC_BREAKDOWN_MASTER.md, 04_DOD_AND_ACCEPTANCE.md

--- 5.3.7 READ spec files for CYCLE_NEXT scope (BEFORE writing any task — never from memory) ---

  TC-1 schema:         PM_Pack\ref\project_plan\03_data\SCHEMA.md
  Dashboard wiring:    PM_Pack\ref\project_plan\07_reporting\DASHBOARD_PLAN.md
  Wave 9 Pricing:      PM_Pack\ref\project_plan\09_pricing\NEW_SELLER_PRICING_MODEL.md
  Wave 10 Discovery:   PM_Pack\ref\project_plan\10_discovery\DISCOVERY_ENGINE_ARCHITECTURE.md
  Wave 11 Playbook:    PM_Pack\ref\project_plan\11_playbook\SELLER_SETUP_PLAYBOOK.md
  Wave 12 UX:          PM_Pack\ref\project_plan\12_dashboard_ux\DESIGN_SYSTEM.md

====================================================================
PART 5.4 — SCRAPFLY READINESS

If CYCLE_NEXT involves live Fiverr collection (Agent E, DL-207 validation):
  Agent E prompt MUST embed §10.5 runbook verbatim:
    - Enable via LOCAL config.live.yaml + key from .env via load_dotenv() (NOT $env:)
    - Confirm session line: "ScrapFly session: requests=X credits=Y"
    - Use "[SEED — no live signal]" fallback (never fabricate, never silently degrade)
    - Throwaway DB: data/cycle[NEXT]_*_validation.db — NEVER data/cycle037_live.db

====================================================================
PART 5.5 — PM DIRECT-ACTION SWEEP (REQUIRED)

Step 5.5.1 — Tier A/B — RESOLVE NOW:
  [ ] Jira corrected (Part 4.5) — Done (id 41), closeout comment on control task.
  [ ] Merged cycle branch deleted on origin (Part 3.5).
  [ ] Stale board-setup issues closed (Part 4.4b) — ~10-15 per cycle.
  [ ] ALL scratch .ps1 and .txt files deleted from PM_Pack\.
  [ ] Accidentally-tracked artifact: git rm --cached + .gitignore (record SHA).
  [ ] [CXXX_SQUASH_SHA] replaced in all 6 CYCLE_NEXT prompts → zero matches.
  [ ] PM Pack state files updated with VERIFIED info (Part 6).
  [ ] Strategy §7 updated if regressions added.
  [ ] Production readiness gates status updated in hydration header.
  [ ] Governance/doc changes committed + pushed to develop (Step 5.5.3).

Step 5.5.2 — Tier C items — write as explicit CYCLE_NEXT agent tasks.
Step 5.5.3 — Commit PM doc changes: staged set MUST be ZERO src/ + ZERO tests/.
  git add SPECIFIC paths only — NEVER git add -A or git add . (sweeps in scratch and untracked files).
  Verify before committing: Invoke-Exe git 'diff --cached --name-only' → must show only PM_Pack/, docs/.
Step 5.5.4 — Tier D items — surface to user: 6 stale stashes; history rewrite; secrets; large ScrapFly.

====================================================================
PART 5.6 — VERIFIED GAP LIST (synthesize from all Parts above)

  a) Files claimed but NOT on disk → CARRY FORWARD
  b) Jira transitions not confirmed → CORRECT NOW (Part 4)
  c) Agent E/F src/ violations → DOCUMENT + INVESTIGATE
  d) Code-vs-config drift → Tier-C for Agent B
  e) §11 parity gaps → Tier-C for Agent B
  f) Score regression / unmet DoD / baseline pollution → flag for CYCLE_NEXT
  g) Full-project gaps from 5.3.5 → route to appropriate priority and Jira story
  h) Production readiness gate status changes → update hydration header and gate table above

====================================================================
PART 6 — WRITE PM PACK UPDATES (VERIFIED INFO ONLY — BEFORE PROMPTS)

PM_Pack\07_hydration\HYDRATION_HEADER.md:
  - CYCLE_CURRENT = CYCLE_NEXT; CYCLE_DONE verified complete
  - Develop HEAD; suite count + coverage; golden OFF==legacy; regression list
  - Production Readiness Gates: G-A: [status] | G-B: [status] | G-C: [status] | G-D: [status]
  - 14-track gap table status (updated from actual checks, not memory)
  - Open Tier-D items; open Jira gaps; SRDI roadmap position (CLOSED since C060)

PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md:
  - CYCLE_NEXT scope + mission; wave progress; open stories with unmet DoD
  - Gate advancement this cycle; new Jira tickets to create

PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md:
  - §7 if regressions added; version-history row

PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md:
  - §13.8 prompt-sizing table; governance SHA; Jira keys; codecov-patch judgment
  - Gate status before/after; Tier-D items surfaced

====================================================================
PART 7 — WRITE CURSOR AGENT PROMPTS (ONLY AFTER PARTS 1-6 + 5.3 + 5.5)

Prompts → C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\
  CYCLE_[NEXT]_AGENT_A_PROMPT.md ... _B_ ... _E_ ... _C_ ... _F_ ... _D_PROMPT.md

LINE FLOORS (§12.5 — effective C057+):
  A ≥ 500 | B ≥ 650 | E ≥ 500 | C ≥ 425 | F ≥ 525 | D ≥ 650 | TOTAL ≥ 3,250

DEPTH QUALITY GATE (§12.5 — all 7 must pass):
  1. LINE FLOOR met | 2. ≥25 LARGE-XXXLARGE tasks | 3. Every task names specific file/command/key
  4. No consecutive duplicate commands | 5. Inline code/templates (not "go read X")
  6. Stage order correct (C before F) | 7. D contains §12.3 operational playbook

A prompt slightly below floor but passing all depth checks = acceptable with PM documentation.

§13.8 PRE-RELEASE CHECKLIST (BLOCKING):
  STATE: [ ] git log read | [ ] gh open PRs read
  SHA: [ ] [CXXX_SQUASH_SHA] replaced in all 6 → zero matches
  STRUCTURE: [ ] "END OF PROMPT" exactly once per file | [ ] Task 0 in first 30 lines
  STAGE ORDER: [ ] A solo → B+E parallel → C after B+E only → F after C → D after all 5
               [ ] C prompt does NOT list F as prerequisite
  PARALLEL: [ ] B prompt: §12.1 notice in first 25 lines, names Agent E
             [ ] E prompt: §12.1 notice in first 25 lines, names Agent B
             [ ] Both use git show --name-only <OWN_SHA> (NOT git diff origin/develop..HEAD)
  D PLAYBOOK: [ ] override:large-pr | [ ] Codex x2 | [ ] codecov/patch advisory | [ ] mergeable_state
  LINE FLOORS: [ ] A≥500 B≥650 E≥500 C≥425 F≥525 D≥650
  DEPTH: [ ] All 7 quality checks pass per prompt
  FULL PROJECT PLAN: [ ] Parts 5.3.1-5.3.7 completed before writing prompts
                     [ ] 14-track gap table and gate status in Part 6 updates
                     [ ] 5 gap checks run and recorded
                     [ ] CYCLE_NEXT spec files read (not memory)
  SCRATCH: [ ] No .ps1 or .txt files in PM_Pack\ directories

EVERY PROMPT MUST CONTAIN:
  a) Project context: paths; branch cycle/[NEXT]/integration; Jira keys; py -3.12; Invoke-Exe
  b) Hard gate rules verbatim (G-001 through G-005, CONFIG GATE, §11 PARITY, §12.3 D PLAYBOOK)
  c) Verified starting state: develop SHA; suite count; coverage; toggles; gate status
  d) ALL regression test names by exact name (§7 — never "see §7")
  e) Mandatory preflight command block
  f) 25+ LARGE-XXXLARGE tasks
  g) Completion-standard checklist
  h) 9 real niche_ids where relevant

AGENT-SPECIFIC MANDATORY CONTENT:

Agent A:
  - Task 0: SHA_RESOLVER_SCRIPT.ps1 (§13.2)
  - Task 1: Part 5.3 14-track review + 5 gap checks confirmation; 14-track table in A's report
  - Task 2: Production readiness gate status update (G-A through G-D current state in A's report)
  - All 6 downstream handoff packages with file detail + function signatures
  - SCRUM ticket-creation (control task + story tickets for each CYCLE_NEXT gap being worked)
  - Spec files read per §12.4 and §5.3.7 (both named explicitly)
  - Prompt-sizing handoff table; toggle keys; module paths; column names

Agent B:
  - §12.1 PARALLEL notice in first 25 lines (names Agent E)
  - Zone verification: git show --name-only <OWN_SHA> ONLY
  - §11.2 parity table: all Mapped[] → migration → all-YES before commit
  - Preserves golden OFF==legacy (G-005); adds/updates tests

Agent E:
  - §12.1 PARALLEL notice in first 25 lines (names Agent B)
  - Zone: git show --name-only <OWN_SHA> ONLY
  - HARD RULE: commit ONLY CYCLE_[N]_AGENT_E.md — NEVER src/, tests/, config.yaml
  - EXPLICIT PROHIBITION: if a src/ module is missing, record the gap for B — DO NOT add it
  - NO PAD LINES: every line must be substantive content
    "floor-line-NNN: retained for floor compliance" is PROHIBITED
  - Live work: §10.5 runbook verbatim (load_dotenv for key, NOT $env:); SEED fallback;
    throwaway DB only — NEVER cycle037_live.db

Agent C:
  - FIRST 20 LINES: "C runs AFTER B AND E. C runs BEFORE F. DO NOT wait for Agent F."
  - Prerequisites: B AND E only — never F
  - §11.3 PRAGMA (blocking): any model change must be verified in DB
  - TC-1 PRAGMA (if applicable): IMMEDIATE NO-GO if raw_value/relevance_score/trend_direction absent
  - Dashboard demo-data check BLOCKING: zero build_dashboard_demo_data in pages/*.py
  - GO / NO-GO verdict with specific evidence per gate

Agent F:
  - Zone: ONLY test files + F report — NEVER src/
  - Prerequisite: C's GO verdict confirmed
  - Coverage-gap targets from C's report; aims at project floor (G-001)

Agent D:
  - §12.3 OPERATIONAL PLAYBOOK (verbatim, every cycle):
    * PR too large: override:large-pr label command (Invoke-Exe gh 'api -X POST .../issues/<PR>/labels ...')
    * Codex x2: both queries run; both raw JSONs in D report; real fix required for each thread
    * codecov/patch: advisory; document; proceed if project floor passed
    * mergeable_state: clean→proceed; unstable→proceed+document; blocked→stop; unknown→wait 30s then retry
    * CI pending: wait up to 5 minutes, re-query
  - G1 ATTRIBUTION — COMPREHENSIVE (every cycle; this is the fix for C060 issue):
    * Command: Invoke-Exe git 'log --oneline <base_sha>..HEAD' — enumerate EVERY commit
    * For EACH SHA: Invoke-Exe git 'show --name-only <SHA>' — verify zone
    * B: src/ + tests/ + B report only | E: ONLY E report | C: only C report | F: tests/ + F report
    * ANY src/ in E or F commits = ZONE VIOLATION. STOP. Do NOT merge.
    * D must NOT declare E "docs-only" without checking EVERY E commit SHA individually
    * D must NOT rely on C's list of SHAs — enumerate via git log independently
  - §11 PRAGMA re-run (independent — does not trust B or C reports)
  - G-B gate re-verify: PRAGMA confirms TC-1 columns in external_signals
  - G-C gate re-verify: zero build_dashboard_demo_data in pages/*.py (independent check)
  - scrapfly committed-false re-verify
  - Golden OFF==legacy + baseline integrity (G-005)
  - ONE --cov=src run (G-004); coverage % recorded
  - Codex TWICE (G-002); both raw JSONs in D report
  - Full 6-agent deliverables table; complete merge-gate checklist
  - SQUASH-merge; verify via merged:true (NOT is-ancestor)
  - Post-merge: §7 update (new regressions + version bump); Jira all Done; branch deleted
  - Post-merge: update production readiness gate status in hydration header
  - Post-merge: close any Jira stories for gates that were advanced this cycle

====================================================================
PART 8 — SELF-AUDIT BEFORE SUBMITTING (any NO → go back)

STATE & ORIENTATION
[ ] State verification (git log + gh open PRs) run FIRST before anything else?
[ ] Hydration header read (cycle numbers, gate status, regression pack)?
[ ] Strategy doc §7/§8/§9/§10/§11/§12/§13 read?

CYCLE_DONE VERIFICATION
[ ] All 6 agent reports read in full?
[ ] Every claimed file verified on disk?
[ ] Full suite run; actual coverage % recorded?
[ ] Agent E: ZERO src/ and tests/ verified?
[ ] Agent F: ZERO src/ verified?
[ ] Agent E: EACH E commit SHA checked individually (not "probably docs-only")?
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
[ ] Confirmed: "SRDI complete" != "project complete"?

PRODUCTION READINESS GATES
[ ] G-A status verified and updated in hydration header?
[ ] G-B status verified via PRAGMA and updated?
[ ] G-C status verified via demo-data check and updated?
[ ] G-D status verified via wave schedule and updated?
[ ] At least one gate advanced this cycle, OR explicit rationale for deferral documented?

JIRA BOARD AUDIT (not just current cycle)
[ ] ALL non-Done Jira issues reviewed (Part 4.4a JQL query run)?
[ ] ~10-15 stale board-setup issues closed as Tier A (Part 4.4b)?
[ ] Canonical product epics (SCRUM-16 through SCRUM-25) verified In Progress?
[ ] Jira-to-plan cross-reference run (14 tracks vs. Jira epics)?
[ ] Any track with NO Jira coverage → story created?

PM PACK & GOVERNANCE
[ ] Strategy §7 updated if new regressions?
[ ] PM Pack updated with VERIFIED state (including gate status, gap table)?
[ ] ALL scratch .ps1 and .txt files deleted?
[ ] Governance changes committed + pushed to develop?
[ ] Tier-D items surfaced to user?

PROMPT QUALITY (§13.8)
[ ] SHA resolved in all 6 → zero matches?
[ ] Line floors: A≥500 B≥650 E≥500 C≥425 F≥525 D≥650?
[ ] All 7 depth quality checks pass per prompt?
[ ] B and E: §12.1 notice in first 25 lines + correct zone check?
[ ] E: explicit src/ prohibition ("record gap for B, do not add it")?
[ ] E: no pad lines prohibition ("floor-line-NNN PROHIBITED")?
[ ] C: NOT listed as waiting for F?
[ ] D: §12.3 playbook present?
[ ] D: G1 attribution lists ALL commits from git log (not just C's SHAs)?
[ ] D: independent G-B (PRAGMA) and G-C (demo-data) checks?
[ ] E (if live): ScrapFly runbook + fallback + throwaway DB + load_dotenv not $env:?
[ ] No API tokens in prompts?
[ ] "END OF PROMPT" exactly once per file?
[ ] Tier-C items routed to agents?

====================================================================
JIRA BOARD HYGIENE — STANDING CLEANUP TASK (Tier A — chip away each cycle)

~65 stale "To Do" issues from Waves 1-9 board setup need to be closed over time.
The PM (or D) closes ~10-15 per cycle until the board reflects only real active work.

CONFIRMED CAN CLOSE (work done, never closed):
  SCRUM-5 (board architecture) | SCRUM-7 (naming templates) | SCRUM-8 (workflow statuses)
  SCRUM-9 (labels/components) | SCRUM-10 (GitHub alignment) | SCRUM-11 (AI agent metadata)
  SCRUM-12 (board QA checklist) | SCRUM-14 (starter issue triage) | SCRUM-15 (release mapping)
  SCRUM-26 (story count reconciliation)
  SCRUM-49 (duplicate epic audit) | SCRUM-50 (story import control) | SCRUM-51 (backend task import)
  SCRUM-52 (frontend task import) | SCRUM-53 (AI task import) | SCRUM-54 (database task import)
  SCRUM-55 (schema reconciliation) | SCRUM-56 through SCRUM-64 (GitHub governance tasks)
  SCRUM-65 through SCRUM-72 (QA wave tasks)

LEAVE OPEN:
  SCRUM-38 (GitHub repo epic — still active work)
  SCRUM-16 through SCRUM-25 (canonical product epics — NEVER close until fully implemented)

Close comment template: "Board setup work for this wave was completed during initial project
  setup (C001-C010 era). Closing to keep board reflecting active work only."

====================================================================
END OF UNIVERSAL POST-CYCLE PM REVIEW PROMPT (v4.2)
====================================================================
