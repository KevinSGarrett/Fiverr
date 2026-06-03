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
.env file:               C:\Fiverr\Fiverr\.env (openai, scrapfly, reddit, cache, log, db, jira, github)

Paste this into the chat after any cycle completes. Do not edit it.
It self-orients by reading the hydration header and git state.

v4.0: PM Direct-Action sweep; ScrapFly checks; code-vs-config drift check;
      25-task floors; §8.4 BLOCKING sizing self-gate; secrets removed.
v4.1: Invoke-Exe execution pattern; squash-merge caveat; corrected codecov policy;
      golden-parity + baseline-integrity check; Jira transition id (41).
v4.2: §12 parallel execution contract (B+E notice; zone check fix; C before F;
      D operational playbook); §13 PM operating rules; revised line floors
      (A500/B650/E500/C425/F525/D650 = 3,250); depth quality gate replacing pure
      line counting; 13_srdi spec navigation; Part 5.3 REPLACED with mandatory
      full 14-track project plan review (root-cause fix for 10-cycle drift);
      5 mandatory gap checks added; updated Part 7 and Part 8.

AUTHENTICATION (read first):
- Jira/GitHub auth is via the already-authorized Atlassian + GitHub connectors.
  NEVER paste an API token, password, or secret into any prompt, file, repo, or chat.
  If you find a token embedded anywhere, treat it as COMPROMISED: tell the user to rotate
  it, and do not use it.
- When checking .env, confirm a key's PRESENCE only (prefix/length) — never print its value.

====================================================================
MANDATORY FIRST ACTION — STATE VERIFICATION (§13.1 — do before ANYTHING else)

Before reading the hydration header, before answering any question, before writing any
prompt: run these two commands and read the output. This is non-negotiable.

  Invoke-Exe git 'log origin/develop --oneline -5'
  Invoke-Exe gh 'api "repos/KevinSGarrett/Fiverr/pulls?state=open" --jq ".[].number + \": \" + .title"'

From the git log output: determine which cycle just completed (top squash commit "(#NN)").
From the open PRs output: determine if any cycle is still in progress.

ONLY AFTER reading both outputs: proceed to Part 0.
Never answer "what cycle are we on" or "what do I run next" from memory.

Root cause: told user to run C055+C056 prompts when both were already merged (C056 session).

====================================================================
EXECUTION ENVIRONMENT NOTES (read once)

GIT/GH OUTPUT CAPTURE: git is installed (C:\Program Files\Git\cmd\git.exe) but NOT on PATH.
PowerShell call operator returns EMPTY output. Use .NET ProcessStartInfo "Invoke-Exe" helper
with a single Arguments STRING (never ArgumentList — Windows PowerShell 5.1 ignores it silently).
Script must Out-File result to .txt then read the .txt. Child process stdout does NOT relay.

  Reusable helper (paste into each scratch .ps1):
  function Invoke-Exe { param([string]$File,[string]$ArgString)
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName=$File; $psi.WorkingDirectory='C:\Fiverr\Fiverr'; $psi.Arguments=$ArgString
    $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
    $p=[System.Diagnostics.Process]::Start($psi)
    $o=$p.StandardOutput.ReadToEnd(); $e=$p.StandardError.ReadToEnd(); $p.WaitForExit()
    return [pscustomobject]@{ Out=$o.TrimEnd(); Err=$e.TrimEnd(); Code=$p.ExitCode } }
  Paths: git = 'C:\Program Files\Git\cmd\git.exe'; gh = 'C:\Program Files\GitHub CLI\gh.exe'.

GH COMMANDS: repo-detecting commands (gh pr list/view/create/merge) FAIL.
Use gh api with ABSOLUTE REST paths. Run gh through Invoke-Exe.
GraphQL: pass query as quoted Arguments string with escaped \" around string literals.

SQUASH-MERGE CAVEAT: git merge-base --is-ancestor returns 1 even when PR is merged via squash.
Verify by: PR JSON merged:true + state:closed + squash commit visible in git log (title ends "(#PR)").

PYTHON: real interpreter is py -3.12. Bare python is the Store stub.
SCRATCH FILES (§13.3): Create → use → delete immediately. Never accumulate scratch.
The PM never asks the user to run PowerShell commands (§13.4c).

====================================================================
PM DIRECT-ACTION AUTHORITY (full text: strategy §9)

ONE-LINE TEST:
  Reversible AND leaves src/ + tests/ + config-behavior untouched AND needs no gate/merge?
    → PM DOES IT NOW (Tier A).
  Touches code/tests/config-behavior, or needs a gate?  → CURSOR AGENT (Tier C).
  Irreversible, or cost/security/account impact?        → ASK USER (Tier D).

TIER A (do now): Jira transitions/comments/ticket-creation/labels/sprint fixes; delete MERGED
  cycle branch; prune merged remote branches; comment on/inspect PR; read CI/Codex;
  edit any PM_Pack/strategy/hydration/tracker/prep-notes/cycle-log; extend .gitignore;
  remove scratch; run tests/--cov/config-check/smoke/golden-OFF (read-only)/git+gh reads;
  COMMIT+PUSH PM doc/governance changes to develop IF zero src/+tests/+config-behavior.
  REPLACE [CXXX_SQUASH_SHA] placeholders in next-cycle prompts (§13.2 — Tier A, do now).
TIER B (do now + record): large/multi-file doc commits; created Jira keys; git rm --cached.
TIER C (hand to cursor agents): ANY src/ change; ANY tests/ add/modify; ANY config.yaml
  runtime-behavior change; anything needing a gate/merge.
TIER D (ask the user): drop/clear stashes (standing: 6 stale stashes cycle051/047/043/036/029/012);
  history rewrite; force-push; delete unmerged branch; rotate secrets; LARGE live ScrapFly burn;
  baseline-DB restore/regenerate.

====================================================================
PART 0 — ORIENT: DISCOVER CURRENT STATE

Step 0.1 — Read the hydration header:
  Read: C:\Fiverr\Fiverr\PM_Pack\07_hydration\HYDRATION_HEADER.md
  Determine: CYCLE_DONE; CYCLE_NEXT (= CYCLE_DONE+1); develop SHA; suite count + coverage;
  regression pack size; SRDI roadmap position; open Tier-D items.

Step 0.2 — Read the strategy doc for ALL permanent rules:
  §7  accumulated regression pack (authoritative test list + count).
  §8  task minimum = 25; prompt-length floors (see Part 7).
  §8.4 BLOCKING sizing self-gate.
  §9  PM Direct-Action Authority.
  §10 ScrapFly Collection Backend Policy.
  §11 MODEL-MIGRATION PARITY RULE (Agent B parity table + Agent C PRAGMA cross-check).
  §12 PARALLEL EXECUTION CONTRACT (B+E notice; C-before-F; D operational playbook;
      SRDI spec navigation; revised line floors + depth quality gate).
  §13 PM OPERATING RULES (verify-state; SHA resolution; scratch cleanup; structural rules;
      stage order; pre-release checklist; hard prohibitions).

Step 0.3 — Read the completed cycle's Agent D report:
  Read: C:\Fiverr\Fiverr\docs\cycle_reports\CYCLE_[CYCLE_DONE]_AGENT_D.md
  Extract: final squash SHA; PR number; gate checklist results; golden OFF==legacy result.

6-AGENT ARCHITECTURE (effective Cycle 047+; §12.2 is authoritative):
  Stage 1 — Agent A (solo — no other agent starts until A has pushed and PR is open)
  Stage 2 — Agent B + Agent E (PARALLEL — both run simultaneously, independent)
  Stage 3 — Agent C (after BOTH B AND E — NEVER after F; C runs BEFORE F)
  Stage 4 — Agent F (after C issues GO verdict)
  Stage 5 — Agent D (after ALL 5 agents have pushed)
  Agent E commits ONLY CYCLE_[N]_AGENT_E.md — NEVER src/, tests/, config.yaml.
  Agent F commits ONLY test files + its report — NEVER src/.
  Agent B is the ONLY author of src/ commits (attribution invariant).

SRDI SPEC NAVIGATION (§12.4): for any SRDI epic work, agents read BOTH:
  - PM_Pack\ref\project_plan\13_srdi\epics\R[N]_[EPIC].md (SRDI-specific spec)
  - PM_Pack\ref\project_plan\[subsystem]\ (base system spec)
  "Read the project plan" without naming both files is insufficient.

====================================================================
PART 1 — READ ALL 6 AGENT REPORTS FOR CYCLE_DONE (REQUIRED FIRST)

Step 1.1 — Confirm all 6 reports exist in C:\Fiverr\Fiverr\docs\cycle_reports\:
  CYCLE_[N]_AGENT_A.md / _B.md / _E.md / _C.md / _F.md / _D.md
  Any missing = CRITICAL gap; flag before proceeding.

Step 1.2 — Read ALL 6 in full. For each extract and record:
  a) files CLAIMED created/modified
  b) test count + coverage % at end of that agent's work
  c) Jira keys CLAIMED transitioned/commented
  d) final commit SHA
  e) risks/blockers/gaps flagged
  f) Agent E: confirm ZERO src/ and tests/ changes claimed
  g) Agent F: confirm ZERO src/ changes claimed
  h) Agent E live work: real ScrapFly session ("ScrapFly session: requests=… credits=…"
     line present)? Or 403-degraded / "[SEED — no live signal]" fallback? Record which.

Step 1.3 — Build a claimed-deliverables table:
  | File Path | Agent | Claimed Action | Verified? |
  Flag immediately if Agent E or F claims any src/ file.

Step 1.4 — Record accumulated regression count from Agent D's report; strategy §7 is authoritative.

====================================================================
PART 2 — VERIFY ACTUAL LOCAL CODEBASE STATE (REQUIRED)

Step 2.1 — Run and record via Invoke-Exe:
  rev-parse --show-toplevel (== C:\Fiverr\Fiverr)
  branch --show-current
  log --oneline -20
  status --short --branch
  worktree list (MUST be exactly ONE worktree)

Step 2.2 — Verify every claimed file exists: Test-Path each row. Any FALSE = gap.

Step 2.3 — For every claimed new test file:
  py -3.12 -m pytest -q "path" --no-header; compare to reported count.

Step 2.4 — Full suite + coverage (this is truth; reports are claims):
  py -3.12 -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90
  Record total passed, coverage %, failures. (Read-only — Tier A.)

Step 2.5 — Verify key module imports for any new modules added this cycle.

Step 2.6 — CLI smoke:
  py -3.12 run.py config-check
  py -3.12 run.py phase2-smoke
  Any new CLI modes added this cycle.

Step 2.7 — Git hygiene: confirm no .env, *.db, or coverage.xml is tracked.
  If accidentally tracked: git rm --cached AND add to .gitignore (Tier B — record it).

Step 2.8 — CODE-vs-CONFIG DRIFT CHECK (mandatory):
  a) NICHE_VALIDATION_CONFIG keys in src/analysis/result_set_validator.py MUST exactly match
     the 9 niche_ids in config.yaml:
     prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow, mcp_ai_agent,
     python_automation, ai_tool_llm_integration, ai_agent_development,
     workflow_automation, python_web_scraping
     Any mismatch = DRIFT → Tier-C item for Agent B (do NOT edit src/ yourself).
  b) Any threshold/weight duplicated in code must match its config.yaml value.
  c) For SRDI cycles: NICHE_EXPECTED_SERVICE_DESCRIPTIONS (if R5 or later) must cover all 9 niches.

Step 2.9 — SCRAPFLY COMMITTED-STATE CHECK (mandatory — §10):
  Read config.yaml collection.scrapfly. Confirm enabled: false in committed file.
  A committed enabled: true = CONFIG-GATE violation → flag (Tier C, Agent B).
  Confirm no config.live.yaml or config.*.local.yaml was committed.

Step 2.10 — AGENT E / AGENT F FILE-ZONE VERIFICATION (mandatory; §12.1):
  2.10a: Invoke-Exe git 'show --name-only [E_SHA]'
         → MUST contain ZERO lines starting with "src/" or "tests/".
  2.10b: Invoke-Exe git 'show --name-only [F_SHA]'
         → MUST contain ZERO lines starting with "src/" (tests/ is OK).
  2.10c: Every src/ file in the cycle range must appear ONLY in Agent B commits.
  Any src/ in E's or F's commits = CRITICAL VIOLATION.

Step 2.11 — GOLDEN PARITY + BASELINE INTEGRITY (mandatory):
  a) Confirm from Agent D's report: golden OFF==legacy PASSED.
     kw=110 CONDITIONAL_GO ~62.7 / CM 1.0.
  b) data/cycle037_live.db MUST be untouched. Golden runs target parity_off.db / parity_on.db.
     If anchors wrong → baseline POLLUTED → surface to user (Tier D restore decision).

Step 2.12 — §11 MODEL-MIGRATION PARITY CHECK (mandatory if src/models/*.py was touched):
  For every modified model file, run PRAGMA and compare against ORM Mapped[] columns:
  py -3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine(
    'sqlite:///data/foundation_gate_ci.db'); print(sorted([c['name'] for c in
    inspect(e).get_columns('<tablename>')]))"
  Any ORM column absent from DB = parity gap → Tier-C item for Agent B.

====================================================================
PART 3 — LIVE GITHUB VERIFICATION (REQUIRED) — via gh api, NOT gh pr

Step 3.1 — List PRs:
  api "repos/KevinSGarrett/Fiverr/pulls?state=all&per_page=20"
    --jq ".[] | {number,title,state,merged}"
  Record cycle PR number/title/state.

Step 3.2 — PR detail + CI checks:
  api repos/KevinSGarrett/Fiverr/pulls/[PR]
    --jq "{state,merged,mergeable,mergeable_state,merge_commit_sha,labels:[.labels[].name]}"
  AND api repos/KevinSGarrett/Fiverr/commits/[head_sha]/check-runs
    --jq ".check_runs[] | {name,status,conclusion}"
  Verify:
  a) merged = true (state closed).
  b) ENFORCED gate "Lint, Typecheck, Tests, and Gates" = success AND codecov/project = success.
  c) codecov/patch = ADVISORY / NON-REQUIRED. Failing alone does NOT block merge.
     Prefer coverage pass when diff is real logic; accept merge-over when migration
     boilerplate / defensive branches AND project floor passed.

Step 3.3 — Codex GraphQL thread query (G-002):
  Run YOURSELF via Invoke-Exe(gh) graphql.
  Verify Agent D's report shows this query run TWICE (pre-resolve + post-resolve).
  A single run is a G-002 violation.
  Record total/resolved/unresolved. Any unresolved = BLOCKER.

Step 3.4 — Confirm develop HEAD == merge commit.
  For squash: new squash commit title ends "(#[PR])". Do NOT use is-ancestor.

Step 3.5 — Branch cleanup (Tier A — DO IT NOW):
  If MERGED cycle/[CYCLE_DONE]/integration branch still exists on origin: delete it.
  api -X DELETE repos/KevinSGarrett/Fiverr/git/refs/heads/cycle/[CYCLE_DONE]/integration

====================================================================
PART 4 — LIVE JIRA VERIFICATION (REQUIRED) — via Atlassian connector (no token)

(project SCRUM; cloudId eae77257-a572-4e19-b746-8b184ba2d01f; Done transition id "41")

Step 4.1 — Query active sprint stories; record key/summary/status for each.
Step 4.2 — For every key an agent claimed to transition: claimed status | actual | match?
Step 4.3 — Verify cycle's Agent-A-created tickets (control task + stories):
  Control task → Done after PR merge.
  Each story → verify DoD criteria actually met (not just "marked Done").
Step 4.4 — Check epic(s) this cycle's scope rolls up to (from hydration header / tracker).
Step 4.5 — MAKE JIRA CORRECTIONS NOW (Tier A):
  Transition control task to Done (id 41) if merged and not Done.
  Transition each story whose DoD is fully met to Done.
  If Done but DoD not met: revert to In Progress with comment.
  Leave closeout comment on control task: PR #, develop SHA, gate results, golden parity.

====================================================================
PART 5 — PM PACK & SPEC REVIEW (REQUIRED)

Step 5.1 — Read PM Pack state files; compare planned vs verified; document every deviation:
  PM_Pack\07_hydration\HYDRATION_HEADER.md
  PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md
  PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md (or prep notes)

Step 5.2 — List PM_Pack\10_cycle_log contents.

====================================================================
PART 5.3 — FULL PROJECT PLAN REVIEW [MANDATORY, EVERY CYCLE]
====================================================================

ROOT CAUSE NOTE: For 10 consecutive cycles (C051-C060), Part 5.3 only read 4 of 14 plan
directories. SRDI-complete was silently treated as project-complete. The consequences:
  - 9 dashboard pages ran on demo data unnoticed
  - TC-1 ExternalSignal schema deferred unnoticed
  - 3 SRDI launch artifacts missing unnoticed
  - Waves 9-12 unstarted unnoticed
This section is now a BLOCKING step. No CYCLE_NEXT scope may be determined until ALL
sub-steps complete. "SRDI complete" does NOT mean "project complete."

--- 5.3.1 ENUMERATE all 14 plan tracks ---

  dir C:\Fiverr\Fiverr\PM_Pack\ref\project_plan
  Expected directories:
    00_meta, 01_vision, 02_architecture, 03_data, 04_collection, 05_scoring,
    06_analysis, 07_reporting, 08_roadmap, 09_pricing, 10_discovery,
    11_playbook, 12_dashboard_ux, 13_srdi

  If any directory is missing: STOP. Document as a critical gap before proceeding.

--- 5.3.2 READ the master wave schedule ---

  Read: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\00_meta\ENHANCEMENT_WAVE_SCHEDULE.md

  CRITICAL DISTINCTION: "Design-complete" (spec written) != "Implementation-complete" (code in src/).
  "COMPLETE" in the wave schedule means the SPEC was written, NOT that the feature is
  production-ready. You MUST check implementation vs. spec for each wave.

  Current wave status (as of C061 start — update this each cycle):
    Waves 0-8:  Spec-complete. Implementation varies by track (see 5.3.3 below).
    Wave 9:     Pricing Strategy Engine — spec complete. Implementation: NOT STARTED.
    Wave 10:    LLM-Powered Niche Discovery — spec complete. Implementation: NOT STARTED.
    Wave 11:    Gig Creation Playbook — spec complete. Implementation: PARTIAL (seed_guidance.py).
    Wave 12:    Dashboard UX Overhaul — spec complete. Implementation: NOT STARTED.

--- 5.3.3 ASSESS each of the 14 tracks (3 questions per track) ---

For each track, answer ALL THREE by reading the spec file(s) and checking src/:
  a) Is the spec IMPLEMENTED in src/? (read actual files, not agent claims)
  b) Is it running in PRODUCTION MODE? (live data? toggles ON? not demo data?)
  c) What are the blocking technical debts? (deferred schema, disabled toggles, missing files)

Current baseline table (update this after every cycle by verifying against src/):

| Track | Implementation | Production Mode | Key Blockers |
|-------|---------------|-----------------|--------------|
| 00_meta | Partial | N/A | Open questions unresolved |
| 01_vision | Substantial | Yes | None |
| 02_architecture | Substantial | Mostly | v2 roadmap items future |
| 03_data | Substantial | No -- TC-1 gap | TC-1 ExternalSignal schema incomplete |
| 04_collection | Partial | No -- SEED band | DL-207 URL shape; TC-1 blocks signals |
| 05_scoring | Substantial | Yes (toggles by design) | LLM/ext signals off |
| 06_analysis | Partial | No -- toggles off | llm_relevance=false; ext_signals=false |
| 07_reporting | Partial | No -- demo data | 9 pages use build_dashboard_demo_data() |
| 08_roadmap | Substantial (v1) | Yes | v2 is future work |
| 09_pricing | Partial | No | Wave 9 implementation not started |
| 10_discovery | Partial | No -- SEED | Live data quality constrains activation |
| 11_playbook | Minimal | No | Wave 11 not started |
| 12_dashboard_ux | Minimal | No | Wave 12 design system not built |
| 13_srdi | Substantial | Partial | Launch artifacts 11/12/13 missing |

Update the table above each cycle. Only remove a gap when implementation is verified in src/.

--- 5.3.4 RUN mandatory gap checks (every cycle, before writing any task) ---

Run all 5 checks and record results before writing CYCLE_NEXT scope:

CHECK 1: Dashboard demo-data dependency
  Command: Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content $_.FullName | Select-String "build_dashboard_demo_data" }
  Result MUST be empty for production readiness (G-C gate).
  Any match = page still uses demo data → add to CYCLE_NEXT P0 scope.

CHECK 2: Feature toggle posture
  Command: Get-Content config.yaml | Select-String "external_signals_enabled|llm_relevance|scrapfly"
  Expected committed state: scrapfly.enabled=false, external_signals_enabled=false (until TC-1), llm_relevance_enabled=false.
  Track: disabled-by-debt vs. disabled-by-design.

CHECK 3: Missing SRDI launch artifacts
  Command: Get-ChildItem PM_Pack\ref\project_plan\13_srdi\ | Select Name
  Must include: 11_AI_AGENT_HANDOFF.md, 12_LAUNCH_READINESS.md, 13_RISK_COMPLIANCE_COST.md
  Any missing = G-A gate failing → add to CYCLE_NEXT scope.

CHECK 4: NICHE_VALIDATION_CONFIG drift (same as Step 2.8)
  src/analysis/result_set_validator.py NICHE_VALIDATION_CONFIG niche keys must match
  the 9 niche_ids in config.yaml exactly.
  Any mismatch = code-vs-config drift → add to CYCLE_NEXT Agent B scope (Tier C).

CHECK 5: Dashboard page count verification
  Command: (Get-ChildItem src\dashboard\pages\ -Filter "*.py" | Where Name -ne "__init__.py").Count
  Current: 9 pages. Verify count matches expected.

--- 5.3.5 BUILD the full-project gap list ---

Build this table BEFORE writing any CYCLE_NEXT task. Do not skip or abbreviate.

| Gap | Track | Production Ready? | Blocking? | CYCLE_NEXT priority |
|-----|-------|-------------------|-----------|---------------------|
| TC-1 ExternalSignal schema | 03_data | No | Yes -- G-B | P0 |
| DL-207 URL shape | 04_collection | No | Yes -- live data | P0 |
| Dashboard demo data (9 pages) | 07_reporting | No | Yes -- G-C | P0 |
| SRDI launch artifacts | 13_srdi | No | Partial -- G-A | P0 |
| external_signals toggle off | 06_analysis | No | No (deferred) | P1 |
| Wave 9 Pricing Engine | 09_pricing | No | No (future) | P2 |
| Wave 10 Discovery Engine | 10_discovery | No | No (future) | P2 |
| Wave 11 Playbook | 11_playbook | No | No (future) | P2 |
| Wave 12 Dashboard UX | 12_dashboard_ux | No | No (future) | P3 |
| (add any new gaps found this cycle) | | | | |

Update this table each PM review. Only remove gaps when implementation is verified in src/.

--- 5.3.6 READ SRDI specs (if SRDI work is in CYCLE_NEXT scope) ---

If CYCLE_NEXT contains SRDI work, read BOTH (§12.4 navigation rule):
  - PM_Pack\ref\project_plan\13_srdi\epics\R[N]_[EPIC_NAME].md
  - AND the base subsystem spec:
      R1: 04_collection\ + R1 epic
      R2: 06_analysis\ + R2 epic
      R4: 05_scoring\ + R4 epic
      R5: 06_analysis\ + R5 epic
      R6: 10_discovery\ + R6 epic
      R7: 06_analysis\ + R7 epic
      R9: 13_srdi\06_TEST_PLAN_REGRESSION.md + R9 epic
  Also read: 13_srdi\07_SEQUENCING_ROADMAP.md (tier position)
             13_srdi\03_EPIC_BREAKDOWN_MASTER.md (story list + Jira keys)
             13_srdi\04_DOD_AND_ACCEPTANCE.md (DoD / AC tables)
             13_srdi\06_TEST_PLAN_REGRESSION.md (regression test names)

  Note: SRDI R1-R11 are CLOSED after C060. No more SRDI epics.

--- 5.3.7 READ spec files for CYCLE_NEXT implementation scope ---

For each non-SRDI deliverable in CYCLE_NEXT, read the spec file BEFORE writing any task:
  TC-1 (ExternalSignal): PM_Pack\ref\project_plan\03_data\SCHEMA.md
  Dashboard wiring:       PM_Pack\ref\project_plan\07_reporting\DASHBOARD_PLAN.md
  Pricing Engine (W9):   PM_Pack\ref\project_plan\09_pricing\NEW_SELLER_PRICING_MODEL.md
  Discovery Engine (W10): PM_Pack\ref\project_plan\10_discovery\DISCOVERY_ENGINE_ARCHITECTURE.md
  Playbook (W11):         PM_Pack\ref\project_plan\11_playbook\SELLER_SETUP_PLAYBOOK.md
  Dashboard UX (W12):    PM_Pack\ref\project_plan\12_dashboard_ux\DESIGN_SYSTEM.md

  Read the spec BEFORE writing the task. NEVER write from memory.

====================================================================
PART 5.4 — SCRAPFLY READINESS FOR CYCLE_NEXT

If CYCLE_NEXT involves any live Fiverr collection (Agent E sampling, DL-207 validation):
  Agent E prompt MUST embed §10.5 live-enable runbook verbatim:
    - Enable via LOCAL config.live.yaml + SCRAPFLY_API_KEY (from .env via load_dotenv, NOT $env:)
    - Confirm session log line: "ScrapFly session: requests=X credits=Y"
    - Use "[SEED — no live signal]" fallback (never fabricate, never silently degrade)
    - Target dedicated throwaway DB (data/cycle[NEXT]_*_validation.db)
    - NEVER use the golden baseline data/cycle037_live.db

====================================================================
PART 5.5 — PM DIRECT-ACTION SWEEP (REQUIRED — §9 authority in practice)

Step 5.5.1 — Tier A/B items — RESOLVE NOW:
  [ ] Jira corrected (Part 4.5) — Done (id 41), evidence comment on control task.
  [ ] Merged cycle branch deleted; stale merged remote branches pruned (Part 3.5).
  [ ] ALL scratch .ps1 and .txt files deleted from PM_Pack\ (§13.3).
  [ ] Any accidentally-tracked artifact: git rm --cached + .gitignore (record SHA).
  [ ] [CXXX_SQUASH_SHA] placeholder replaced in all 6 CYCLE_NEXT prompts (§13.2):
      Run SHA_RESOLVER_SCRIPT.ps1 OR replace directly via Desktop Commander.
      Verify: Select-String '\[C0\d\d_SQUASH_SHA\]' in all 6 prompts → zero matches.
  [ ] PM Pack state files updated with VERIFIED info (Part 6).
  [ ] Strategy §7 updated if regressions added.
  [ ] Governance/doc changes committed + pushed to develop (Step 5.5.3).

Step 5.5.2 — Tier C items — write as explicit CYCLE_NEXT agent tasks:
  src/ defects → Agent B.
  Test gaps → Agent B or F.
  Config-behavior changes → Agent B + gates.
  §11 parity gaps → Agent B.
  Code-vs-config drift → Agent B.

Step 5.5.3 — Commit PM's doc/governance changes to develop (Tier A):
  Staged set MUST contain ZERO files under src/ or tests/ and ZERO config.yaml changes.
  Verify: Invoke-Exe git 'diff --cached --name-only' → only PM_Pack/, .gitignore, docs/.
  git add SPECIFIC paths (NOT -A). Commit docs(governance) or chore(). Push to develop.
  Re-read develop HEAD; record the new SHA.

Step 5.5.4 — Tier D items — surface to user, STOP:
  - 6 stale stashes (cycle051/047/043/036/029/012)
  - Any history rewrite / force-push
  - Secret rotation
  - LARGE live ScrapFly credit burn
  - Baseline DB restore / regenerate

====================================================================
PART 5.6 — VERIFIED GAP LIST

Build this list from Parts 1-5 and 5.3:
  a) Files claimed but NOT on disk → CARRY FORWARD
  b) Jira transitions not confirmed → CORRECT NOW (Part 4)
  c) Agent E/F src/ violations → DOCUMENT + INVESTIGATE
  d) Code-vs-config drift (Part 2.8) → Tier-C item for Agent B
  e) §11 parity gaps (Part 2.12) → Tier-C item for Agent B
  f) Score regression / unmet DoD / baseline pollution (Part 2.11) → flag for CYCLE_NEXT
  g) Full-project gaps from 5.3.5 table → route to appropriate priority

====================================================================
PART 6 — WRITE PM PACK UPDATES (VERIFIED INFO ONLY — BEFORE PROMPTS)

Update with VERIFIED info only. MISSING means missing — never write "complete" for unverified.

PM_Pack\07_hydration\HYDRATION_HEADER.md:
  Active cycle = CYCLE_NEXT; CYCLE_DONE verified complete + merged block (PR #, squash SHA,
  scope, config facts incl. scrapfly=false); develop HEAD; suite count + coverage;
  golden OFF==legacy result; accumulated regression list; open Tier-D items;
  SRDI roadmap position; next cycle scope; 14-track gap table status.

PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md:
  CYCLE_NEXT scope + mission; SRDI table advanced; open stories with unmet DoD;
  new Jira tickets to create; wave progress.

PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md:
  §7 if regressions added; version-history row for any change.

PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md:
  §13.8 prompt-sizing count table (Part 7); governance commit SHA (Part 5.5.3);
  created Jira keys; merge SHA + codecov-patch judgment call; Tier-D items surfaced;
  14-track gap table snapshot.

====================================================================
PART 7 — WRITE CURSOR AGENT PROMPTS (ONLY AFTER PARTS 1-6 + 5.3 + 5.5)

Prompt files → C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\
  CYCLE_[CYCLE_NEXT]_AGENT_A_PROMPT.md ... _B_ ... _E_ ... _C_ ... _F_ ... _D_PROMPT.md

--------------------------------------------------------------------
TASK & LENGTH REQUIREMENTS (§8 + §12.5):

Every task = LARGE (4-6 sub-steps), XLARGE (6-8), XXLARGE (8-12), or XXXLARGE (12+).
No standalone small/medium tasks. Minimum 25 tasks per agent, each REAL project-advancing work.

REVISED LINE FLOORS (§12.5 — effective Cycle 057+):
  A ≥ 500 | B ≥ 650 | E ≥ 500 | C ≥ 425 | F ≥ 525 | D ≥ 650 | TOTAL ≥ 3,250

DEPTH QUALITY GATE (§12.5 — primary quality signal):
Every prompt must pass ALL 7 checks before release:
  1. LINE FLOOR: meets the per-agent floor above
  2. TASK COUNT: ≥ 25 tasks, each LARGE-XXXLARGE with numbered sub-steps
  3. SPECIFICITY: every task names ≥ 1 specific file, command, Jira key, or function
  4. NO DUPLICATION: no two consecutive tasks share the same command structure
  5. INLINE CONTENT: code/command/report templates are INLINE (not "go read X")
  6. STAGE CORRECTNESS: agent prerequisites match §12.2 exactly (C before F, never after)
  7. OPERATIONAL COMPLETENESS: D's prompt contains §12.3 operational issues playbook

A prompt at/above floor but failing any depth check = NOT DONE.
A prompt slightly below floor but passing all depth checks = acceptable if PM documents why.

--------------------------------------------------------------------
§13.8 PRE-RELEASE CHECKLIST (BLOCKING — run before handing any prompt to an agent):

  STATE VERIFICATION
  [ ] git log origin/develop --oneline -5 read → prior cycles confirmed merged
  [ ] gh api open PRs read → no unexpected open PRs

  SHA RESOLUTION
  [ ] [CXXX_SQUASH_SHA] placeholder replaced in ALL 6 prompts
      Select-String '\[C0\d\d_SQUASH_SHA\]' → zero matches in every file

  STRUCTURAL
  [ ] "END OF PROMPT" appears exactly once in each file (not twice or more)
  [ ] Task 0 (if present) is in first 30 lines — not appended at end

  STAGE ORDER (§12.2)
  [ ] A: solo | B: parallel with E | C: after B+E, NOT F | F: after C | D: after all 5
  [ ] Agent C prompt does NOT list F as a prerequisite

  PARALLEL AGENTS (§12.1)
  [ ] B prompt: §12.1 notice in first 25 lines, names Agent E
  [ ] E prompt: §12.1 notice in first 25 lines, names Agent B
  [ ] Both use `git show --name-only <OWN_SHA>` for zone verification
      NOT `git diff --name-only origin/develop..HEAD`

  AGENT D PLAYBOOK (§12.3)
  [ ] PR too large → override:large-pr label command present
  [ ] Codex x2 resolution procedure present
  [ ] codecov/patch advisory language present
  [ ] mergeable_state guide present

  LINE FLOORS AND DEPTH
  [ ] A≥500, B≥650, E≥500, C≥425, F≥525, D≥650
  [ ] All 7 depth quality checks pass per file

  FULL-PROJECT PLAN CHECK (§13.10 — v4.2 addition)
  [ ] Part 5.3.1 through 5.3.7 all completed before writing prompts?
  [ ] 14-track gap table (5.3.5) built and included in Part 6 updates?
  [ ] 5 mandatory gap checks (5.3.4) run and results recorded?
  [ ] Spec files for CYCLE_NEXT deliverables read (not from memory)?

  SCRATCH CLEANUP
  [ ] No .ps1 or temporary .txt files in PM_Pack\ or PM_Pack\03_cursor_agent_system\

--------------------------------------------------------------------
EVERY PROMPT MUST CONTAIN:

a) Project context: paths; branch = cycle/[CYCLE_NEXT]/integration; Jira keys; connector
   auth (no token); Python: py -3.12; Working dir: C:\Fiverr\Fiverr; git via Invoke-Exe.

b) Hard gate rules verbatim:
   G-001 COVERAGE: ENFORCED = "Lint, Typecheck, Tests, and Gates" CI + codecov/project.
     codecov/patch = ADVISORY / NON-REQUIRED. Patch miss must be surfaced + documented;
     prefer coverage pass when uncovered diff is real logic; accept merge-over when
     migration boilerplate / defensive branches AND project floor passed.
   G-002: Codex GraphQL query TWICE (pre + post-resolve). Unresolved=0. Real fix required.
   G-003: Agent D merge-gate all PASS before squash-merge.
   G-004: EXACTLY ONE --cov=src run, by Agent D only.
   G-005: Golden OFF==legacy PASS. kw=110 CONDITIONAL_GO ~62.7. Baseline UNTOUCHED.
     Golden targets parity_off.db / parity_on.db.
   CONFIG GATE: scrapfly.enabled stays false in committed config (§10). New toggles default off.
   §11 PARITY: any src/models/*.py change requires parity table (Agent B) + PRAGMA
     cross-check (Agent C). "Tests pass" is NOT evidence. PRAGMA is the test.
   §12.3 D PLAYBOOK: PR>1000 lines → override:large-pr label. Codex x2. codecov/patch
     advisory. mergeable_state: clean=proceed; unstable=proceed+document; blocked=stop.

c) Verified starting state (develop SHA; suite count; coverage %; active toggles).

d) ALL accumulated regression test NAMES by exact name (strategy §7 — never "see §7").

e) Mandatory preflight command block (real commands; Invoke-Exe pattern).

f) 25+ LARGE-XXXLARGE tasks with numbered sub-steps.

g) Completion-standard checklist.

h) The 9 real niche_ids where relevant:
   prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow, mcp_ai_agent,
   python_automation, ai_tool_llm_integration, ai_agent_development,
   workflow_automation, python_web_scraping

--------------------------------------------------------------------
AGENT-SPECIFIC MANDATORY CONTENT:

Agent A additionally:
  - Task 0: resolve [CXXX_SQUASH_SHA] via SHA_RESOLVER_SCRIPT.ps1 (§13.2)
  - Task 1: Part 5.3 14-track review confirmation (3 questions per track, 5 gap checks)
  - Full-project gap table (5.3.5) included in A's report and handoffs
  - All 6 downstream handoff packages with file-by-file detail + function signatures
  - SCRUM ticket-creation (control task + story tickets)
  - SRDI spec read per §12.4 (13_srdi epic file + base subsystem spec, both named)
  - Prompt-sizing handoff table
  - Exact config toggle keys, module paths, new column names (so B builds to confirmed names)
  - §12.1 parallel notice text for B handoff AND E handoff
  - Stage order stated for all 6 agents

Agent B additionally:
  - §12.1 PARALLEL EXECUTION NOTICE in first 25 lines (names Agent E explicitly)
  - Zone verification via `git show --name-only <OWN_SHA>` ONLY
  - ONLY author of src/; new behavior behind toggles (default OFF); Tier-C defects from PM
  - §11.2 parity table: enumerate all Mapped[] → map to migration → all-YES before commit
  - Adds/updates tests for its code; preserves golden OFF==legacy parity (G-005)

Agent E additionally:
  - §12.1 PARALLEL EXECUTION NOTICE in first 25 lines (names Agent B explicitly)
  - Zone verification via `git show --name-only <OWN_SHA>` ONLY
  - File-zone rule: commit ONLY CYCLE_[N]_AGENT_E.md; NEVER src/, tests/, config.yaml
    EXPLICIT PROHIBITION: if a src/ file is missing, record the gap for Agent B — DO NOT add it
  - NO PAD LINES: every line must be substantive project content
    "floor-line-NNN: retained for floor compliance" is PROHIBITED
  - If live work: §10.5 ScrapFly runbook verbatim (load key from .env via load_dotenv, NOT $env:) +
    "[SEED — no live signal]" fallback + dedicated throwaway DB — NEVER the golden baseline

Agent C additionally:
  - CRITICAL ORDERING NOTE in first 20 lines: "C runs AFTER B and E. C runs BEFORE F.
    F depends on C's GO. DO NOT wait for Agent F."
  - Prerequisites: B AND E only — never F
  - §11.3 PRAGMA cross-check (blocking) for any model files in B's diff
  - TC-1 PRAGMA (if applicable): all 3 columns must be present — IMMEDIATE NO-GO if absent
  - Dashboard demo-data check: zero build_dashboard_demo_data imports in pages/*.py — BLOCKING
  - GO / NO-GO verdict with specific evidence per gate

Agent F additionally:
  - File-zone rule: ONLY test files + report; NEVER src/
  - Prerequisite: Agent C's GO verdict confirmed in CYCLE_[N]_AGENT_C.md
  - Coverage-gap targets from Part 5 / Agent C's report
  - Aims diff at enforced project floor (G-001)

Agent D additionally (verbatim, every cycle):
  - §12.3 OPERATIONAL ISSUES PLAYBOOK (mandatory):
    * PR too large: Invoke-Exe gh 'api -X POST .../issues/<PR>/labels --field "labels[]=override:large-pr"'
    * Codex x2: reply with fix SHA; resolve via UI or mutation; both queries recorded
    * codecov/patch: advisory; document; proceed if project floor passed
    * mergeable_state: clean → proceed; unstable → proceed+document; blocked → stop; unknown → wait
    * CI pending: wait up to 5 minutes, re-query before concluding
  - G1 ATTRIBUTION — COMPREHENSIVE COMMIT CHECK (every cycle):
    * Command: Invoke-Exe git 'log --oneline <base_sha>..HEAD' to enumerate ALL cycle commits
    * For EACH SHA: Invoke-Exe git 'show --name-only <SHA>' and verify zone
    * B commits: only src/ + tests/ + B report | E commits: only E report | C: only C report | F: tests/ + F report
    * ANY src/ in E's or F's commits = ZONE VIOLATION. STOP.
    * D must NOT declare E "docs-only" without checking EACH E commit SHA individually
  - §11 independent PRAGMA re-run (does NOT trust B or C reports)
  - scrapfly committed-false re-verify (§10)
  - Dashboard demo-data independent check: zero build_dashboard_demo_data imports
  - Golden OFF==legacy parity run + baseline integrity (G-005)
  - ONE --cov=src run (G-004); exact count + coverage % recorded
  - Codex query TWICE (both raw JSON outputs in D's report)
  - Full 6-agent deliverables verification table
  - Complete merge-gate checklist (all gates PASS before merge)
  - SQUASH-merge method; verify via merged:true (NOT is-ancestor)
  - Post-merge: strategy §7 update (new regressions + version bump); Jira all Done; branch delete
  - Post-merge signal to PM with cycle summary + next cycle announcement

--------------------------------------------------------------------
SHA RESOLVER SCRIPT (§13.2 — use to replace placeholders):
  PM_Pack\03_cursor_agent_system\SHA_RESOLVER_SCRIPT.ps1
  Parameters: -CycleNum "0NN" -PlaceholderPRNum "NN"
  After running: Select-String '\[C0\d\d_SQUASH_SHA\]' in all 6 prompts → zero matches.

====================================================================
PART 8 — SELF-AUDIT BEFORE SUBMITTING (any NO → go back)

STATE & ORIENTATION
[ ] State verification commands run (git log + gh open PRs) BEFORE any other action?
[ ] Hydration header read to determine current cycle numbers?
[ ] Strategy doc §7/§8/§9/§10/§11/§12/§13 read for permanent rules?

CYCLE_DONE VERIFICATION
[ ] All 6 agent reports for CYCLE_DONE read in full?
[ ] Verified each claimed file exists on disk?
[ ] Ran full suite + recorded actual coverage %?
[ ] Verified Agent E committed ZERO src/ and ZERO tests/?
[ ] Verified Agent F committed ZERO src/?
[ ] §11 model-migration PRAGMA check run (if src/models/ touched)?
[ ] Code-vs-config drift check run (niche_ids / constants match config.yaml)?
[ ] scrapfly committed-state check: config.yaml enabled=false confirmed?
[ ] Git/gh run via ProcessStartInfo Invoke-Exe (Arguments STRING, not ArgumentList)?
[ ] Live GitHub via gh api: merged=true + ENFORCED CI gate + codecov/project SUCCESS?
[ ] codecov/patch state recorded + merge-over documented if applicable? (YES / NO / N-A)
[ ] Merge confirmed via merged:true + squash commit on develop (NOT is-ancestor)?
[ ] Golden OFF==legacy confirmed AND baseline cycle037_live.db untouched?
[ ] Codex query run TWICE (G-002) and zero unresolved confirmed?
[ ] Live Jira checked AND corrections MADE (id 41), not just noted?
[ ] Merged cycle branch deleted on origin?

FULL-PROJECT PLAN REVIEW (§13.10 — v4.2 addition; BLOCKING)
[ ] Part 5.3.1: all 14 plan track directories enumerated?
[ ] Part 5.3.2: ENHANCEMENT_WAVE_SCHEDULE.md read?
[ ] Part 5.3.3: 3 questions answered per track (implemented? production? blockers)?
[ ] Part 5.3.4: all 5 mandatory gap checks run and results recorded?
       CHECK 1: dashboard demo-data imports check? YES / NO
       CHECK 2: feature toggle posture check? YES / NO
       CHECK 3: SRDI launch artifacts check? YES / NO
       CHECK 4: NICHE_VALIDATION_CONFIG drift check? YES / NO
       CHECK 5: dashboard page count verified? YES / NO
[ ] Part 5.3.5: full-project gap list built before determining CYCLE_NEXT scope?
[ ] Part 5.3.6: SRDI spec files read (if applicable; §12.4)?
[ ] Part 5.3.7: CYCLE_NEXT spec files read (not from memory)?
[ ] Confirmed: "SRDI complete" does NOT mean "project complete"?

PM PACK & GOVERNANCE
[ ] Strategy §7 updated if new regressions added? (YES / NO / N-A)
[ ] PM Pack files updated with VERIFIED state (including 14-track gap table)?
[ ] ALL scratch .ps1 and .txt files deleted from PM_Pack\?
[ ] Governance/doc changes committed + pushed to develop?
[ ] Tier-D items surfaced to user?

PROMPT QUALITY (§13.8 PRE-RELEASE CHECKLIST — all must be YES)
[ ] §13.8 checklist run against all 6 prompts and all items PASS?
[ ] [CXXX_SQUASH_SHA] placeholder resolved in all 6 prompts (zero matches)?
[ ] Line floors met: A≥500, B≥650, E≥500, C≥425, F≥525, D≥650?
[ ] All 7 depth quality checks pass per prompt?
[ ] All 6 prompts reference branch cycle/[CYCLE_NEXT]/integration?
[ ] Agent prompts carry G-001..G-005 verbatim (incl. corrected codecov + golden parity + §11)?
[ ] B and E: §12.1 parallel notice in first 25 lines + correct zone check?
[ ] E: explicit src/ PROHIBITION (not just zone rule, but "if missing module, record for B")?
[ ] E: no pad lines prohibition stated ("floor-line-NNN" style PROHIBITED)?
[ ] C: does NOT list F as prerequisite?
[ ] D: §12.3 operational playbook present (PR size, Codex, codecov/patch, mergeable_state)?
[ ] D: G1 attribution lists ALL commits from git log (not just SHAs from C's report)?
[ ] Agent E (if live): §10 ScrapFly runbook + fallback + throwaway DB + load_dotenv not $env:?
[ ] NO API token/secret embedded in any prompt?
[ ] Task 0 (if present) is in first 30 lines of Agent A's prompt?
[ ] "END OF PROMPT" appears exactly once in each file?
[ ] Tier-C items routed to agents?

ADDITIONAL CHECKS (v4.2)
[ ] Full-project gap list built before determining CYCLE_NEXT scope (5.3.5)? YES / NO
    (Must confirm: "SRDI complete" != "project complete")
[ ] Dashboard demo-data check: zero build_dashboard_demo_data imports in pages/*.py
    OR verified gap is in CYCLE_NEXT P0 scope? YES / NO
[ ] Production toggle posture verified (external_signals, llm_relevance, scrapfly)? YES / NO
[ ] SRDI launch artifacts 11/12/13 verified on disk, OR gap in CYCLE_NEXT scope? YES / NO
[ ] Wave 9-12 gap acknowledged; at least one non-SRDI deliverable in CYCLE_NEXT scope
    OR explicitly deferred with rationale? YES / NO

====================================================================
JIRA BOARD HYGIENE (from C061 PM review — ongoing Tier A action)

The board contains ~65 stale "To Do" issues (SCRUM-5 through ~SCRUM-72) from Waves 1-9
Jira board setup. Most of this planning work was completed but never closed in Jira.

These are Tier A actions (PM closes directly, D may also close some each cycle):
  - SCRUM-5 through SCRUM-15: Board architecture/governance setup (Done -- close)
  - SCRUM-26: Story count reconciliation (Done -- close)
  - SCRUM-38: GitHub repo epic (In Progress -- leave as is)
  - SCRUM-49 through SCRUM-55: Wave 3-7 import controls (Done -- close most)
  - SCRUM-56 through SCRUM-64: GitHub governance tasks (partially done via CI setup)
  - SCRUM-65 through SCRUM-72: QA wave tasks (partially done via SRDI R9 testing)

Close ~10-15 per cycle as Tier A until board is clean. Do NOT close without verifying done.

Canonical product epics (NEVER close until full implementation complete):
  SCRUM-16 (Epic 01 Foundation) | SCRUM-17 (Epic 02 Collection) | SCRUM-19 (Epic 04 Scoring)
  SCRUM-20 (Epic 05 Recommendations) | SCRUM-21 (Epic 06 Pricing) | SCRUM-23 (Epic 08 Playbook)
  SCRUM-24 (Epic 09 Dashboard) | SCRUM-25 (Epic 10 Integration/Launch)

====================================================================
END OF UNIVERSAL POST-CYCLE PM REVIEW PROMPT (v4.2)
====================================================================
