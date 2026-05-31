====================================================================
FIVERR RESEARCH SYSTEM — UNIVERSAL POST-CYCLE PM REVIEW PROMPT
====================================================================
Version: 4.0 (Universal — no cycle-number editing required)
Canonical home: PM_Pack\01_pm_instructions\POST_CYCLE_PM_REVIEW_v4.md
Strategy doc:   PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md  (§7 regressions, §8 sizing, §9 PM authority, §10 ScrapFly)

Paste this into the chat after any cycle completes. Do not edit it; it self-orients by reading the
hydration header. v4.0 adds: PM Direct-Action sweep (act on small items yourself), ScrapFly checks,
code-vs-config drift check, corrected task/length floors (25 tasks; A810/B945/E810/C675/F810/D945;
total 4995) with the §8.4 BLOCKING sizing self-gate, and removal of all embedded secrets.

AUTHENTICATION (read first):
  - Jira/GitHub auth is via the already-authorized Atlassian + GitHub connectors and gh/git on the
    machine. NEVER paste an API token, password, or secret into this prompt, any prompt file, the
    repo, or chat. If you find a token embedded anywhere (including an older version of this prompt),
    treat it as COMPROMISED: tell the user to rotate it, and do not use it.
  - When checking .env, confirm a key's PRESENCE only (prefix/length) — never print its value.

====================================================================
PM DIRECT-ACTION AUTHORITY — QUICK REFERENCE (full text: strategy §9)
====================================================================
You are not only a reviewer + prompt writer. After a cycle you DIRECTLY resolve small, safe,
reversible items, then write the next cycle's prompts. The bright line: never touch product behavior.

  ONE-LINE TEST:
    Reversible AND leaves src/ + tests/ + config-behavior untouched AND needs no gate/merge?
       -> PM DOES IT NOW (Tier A).
    Touches code / tests / config-behavior, or needs a gate?  -> CURSOR AGENT (Tier C).
    Irreversible, or cost / security / account impact?        -> ASK THE USER (Tier D).

  TIER A (do now): Jira transitions/comments/ticket-creation/labels/sprint fixes; revert a wrongly-Done
    story; delete the MERGED cycle branch; prune already-merged remote branches; comment on/inspect a
    PR; read CI/Codex; edit any PM_Pack/strategy/hydration/tracker/prep-notes/cycle-log; extend
    .gitignore; remove untracked scratch; run tests/--cov/config-check/smoke/git+gh reads/Codex query;
    COMMIT+PUSH the PM's own doc/governance changes to develop (docs()/chore()) IF zero src/+tests/+config-behavior.
  TIER B (do now + record): large/multi-file doc commits, created Jira keys, git rm --cached of a
    tracked artifact (pair with .gitignore) -> record SHA/keys/rationale in prep notes.
  TIER C (hand to cursor agents): ANY src/ change (even 1 line -> Agent B); ANY tests/ add/modify
    (Agent B/F); ANY config.yaml runtime-behavior change (Agent B + gates); anything needing a gate/merge.
  TIER D (ask the user): drop/clear stashes, history rewrite, force-push, delete unmerged/non-cycle
    branch, hard reset; rotate secrets; repo settings/branch protection; LARGE live ScrapFly credit burn.

You MUST still complete all Parts in sequence. Writing next-cycle prompts before completing
verification (Parts 1-6) AND the direct-action sweep (Part 5.5) is a PM failure.

====================================================================
PART 0 — ORIENT: DISCOVER CURRENT STATE (DO THIS FIRST)
====================================================================

Project paths (fixed, never change):
  Local repo:   C:\Fiverr\Fiverr            (canonical; worktree count MUST be 1 — NO worktrees)
  PM Pack:      C:\Fiverr\Fiverr\PM_Pack
  Project Plan: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan
  Strategy doc: C:\Fiverr\Fiverr\PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md
  GitHub:       https://github.com/KevinSGarrett/Fiverr/   (owner KevinSGarrett, repo Fiverr)
  Jira:         https://kevinsgarrett.atlassian.net        (project SCRUM) — via OAuth connector, no token

Step 0.1 — Read the hydration header to discover current cycle numbers:
  Read: C:\Fiverr\Fiverr\PM_Pack\07_hydration\HYDRATION_HEADER.md
  Determine: which cycle just completed (CYCLE_DONE); next cycle (CYCLE_NEXT = CYCLE_DONE+1); the
  verified score/DB/Jira state; the accumulated regression count; the current SRDI roadmap position.
  Use these in every step below. No manual entry.

Step 0.2 — Read the strategy doc for ALL permanent rules (now four sections):
  §7  accumulated regression pack (authoritative test list + count).
  §8  task minimum = 25 (LARGE/XLARGE/XXLARGE/XXXLARGE) and prompt-length floors
      A>=810, B>=945, E>=810, C>=675, F>=810, D>=945 (total >= 4995); §8.4 BLOCKING sizing self-gate.
  §9  PM Direct-Action Authority (the 4 tiers above).
  §10 ScrapFly Collection Backend Policy (PerimeterX bypass; committed-off; live via local config).

Step 0.3 — Read the completed cycle's Agent D report to confirm merge state:
  Read: C:\Fiverr\Fiverr\docs\cycle_reports\CYCLE_[CYCLE_DONE]_AGENT_D.md
  Extract: final SHA, PR number, merge timestamp, merge-gate checklist results.

6-AGENT ARCHITECTURE REMINDER (effective Cycle 047+):
  Stage 1 — Agent A (sequential, alone)
  Stage 2 — Agent B + Agent E (parallel)
  Stage 3 — Agent C (after BOTH B and E)
  Stage 4 — Agent F (after C)
  Stage 5 — Agent D (after ALL 5)
  Agent E commits ONLY docs/cycle_reports/CYCLE_[N]_AGENT_E.md — NEVER src/, tests/, or config.yaml.
  Agent F commits ONLY test files + its report — NEVER src/.
  ALL src/ changes come ONLY from Agent B (the attribution invariant Agent D enforces).

====================================================================
PART 1 — READ ALL 6 AGENT REPORTS FOR CYCLE_DONE (REQUIRED FIRST)
====================================================================

Step 1.1 — Confirm all 6 reports exist in C:\Fiverr\Fiverr\docs\cycle_reports\ (substitute CYCLE_DONE):
  CYCLE_[N]_AGENT_A.md / _B.md / _E.md / _C.md / _F.md / _D.md
  Any missing report = CRITICAL gap; flag before proceeding.

Step 1.2 — Read ALL 6 in full. For each, extract and record:
  a) files CLAIMED created/modified
  b) test count + coverage % at end of that agent's work
  c) Jira keys CLAIMED transitioned/commented
  d) final commit SHA
  e) risks/blockers/gaps flagged
  f) Agent E: confirm it claimed ZERO src/ and tests/ changes
  g) Agent F: confirm it claimed ZERO src/ changes
  h) Agent E live work: did it use ScrapFly (a real "ScrapFly session: requests=… credits=…" line),
     or did it 403-degrade / use the "[SEED — no live signal]" fallback? Record which. (See §10.)

Step 1.3 — Build a claimed-deliverables table: | File Path | Agent | Claimed Action | Verified? |
  (fill Verified? in Part 2). Flag immediately if Agent E or F claims any src/ file.

Step 1.4 — Record the accumulated regression count from Agent D's report; strategy §7 is authoritative.

====================================================================
PART 2 — VERIFY ACTUAL LOCAL CODEBASE STATE (REQUIRED)
====================================================================

Step 2.1 — Run and record (use the .NET Invoke-Exe git pattern; write output to a temp .txt and read it):
  Get-Location (== C:\Fiverr\Fiverr); git rev-parse --show-toplevel; git branch --show-current;
  git log --oneline -20; git status --short --branch; git worktree list (MUST be exactly ONE).

Step 2.2 — Verify every claimed file exists: Test-Path each row. Any FALSE = gap.

Step 2.3 — For every claimed new test file: python -m pytest -q "path" --no-header; compare to reported count.

Step 2.4 — Full suite + coverage (this is the truth; reports are claims):
  python -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90
  Record total passed, coverage %, failures. (You running this is read-only — Tier A.)

Step 2.5 — Verify key module imports for any new modules.

Step 2.6 — CLI smoke: python run.py config-check ; python run.py phase2-smoke ; any new CLI modes.

Step 2.7 — Git hygiene: confirm no .env, *.db, or coverage.xml is tracked.
  If an artifact is accidentally tracked: git rm --cached it AND add it to .gitignore (Tier B — record it).

Step 2.8 — CODE-vs-CONFIG DRIFT CHECK (new; mandatory):
  Constants hard-coded in src/ that mirror config.yaml MUST match config.yaml exactly. At minimum:
  a) The niche_ids used by validation/scoring constants (e.g. NICHE_VALIDATION_CONFIG in
     src/analysis/result_set_validator.py) MUST equal the 9 niche_ids in config.yaml:
     prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow, mcp_ai_agent, python_automation,
     ai_tool_llm_integration, ai_agent_development, workflow_automation, python_web_scraping.
     Any niche keyed by a slug NOT in config (or any config niche missing from the constant) is DRIFT
     -> log it; the fix is a Tier-C item for Agent B next cycle (do NOT edit src/ yourself).
  b) Any threshold/weight duplicated in code must match its config.yaml value.

Step 2.9 — SCRAPFLY COMMITTED-STATE CHECK (new; mandatory — see §10):
  Read config.yaml collection.scrapfly. Confirm enabled: false in the COMMITTED file (correct: keeps
  CI/tests dry + credit-free). If a commit set enabled: true, that is a CONFIG-GATE violation -> flag
  for correction (Tier C, Agent B). Confirm no config.live.yaml / config.*.local.yaml was committed.

Step 2.10 — AGENT E / AGENT F FILE-ZONE VERIFICATION (mandatory):
  2.10a git show --name-only [E_SHA] -> MUST contain ZERO lines starting with "src/" or "tests/".
  2.10b git show --name-only [F_SHA] -> MUST contain ZERO lines starting with "src/" (tests/ is OK).
  2.10c $base = git merge-base develop cycle/[N]/integration ;
        git log "$base..HEAD" --name-only  -> every src/ file appears ONLY in Agent B commits.
        Any src/ in E's or F's commits is a CRITICAL VIOLATION.

====================================================================
PART 3 — LIVE GITHUB VERIFICATION (REQUIRED)
====================================================================
(gh needs git on PATH: prepend $env:PATH = "C:\Program Files\Git\cmd;" + $env:PATH before gh pr/gh checks.)

Step 3.1 — gh pr list --state all --limit 20 ; record PR number/title/state/CI status.

Step 3.2 — gh pr view [PR] --json state,mergeable,statusCheckRollup,reviews ; verify:
  a) state = MERGED   b) codecov/patch = SUCCESS (BLOCKER if FAILURE)   c) all CI checks SUCCESS.

Step 3.3 — Codex GraphQL thread query (G-002). Run it YOURSELF to independently confirm 0 unresolved,
  AND verify Agent D's report shows it run TWICE (pre-resolve + post-resolve). A single run is a
  G-002 violation. (Write the query to a .graphql file; gh api graphql -F query=@file -f owner=KevinSGarrett -f name=Fiverr -F number=[PR].)
  reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:3){nodes{author{login}body}}}}
  Record total/resolved/unresolved threads. Any unresolved = BLOCKER.

Step 3.4 — Confirm develop HEAD SHA == Agent D's reported final SHA (local == origin == GitHub API).

Step 3.5 — Branch cleanup (Tier A — DO IT YOURSELF):
  gh pr list --state open ; git branch -r | grep "cycle/"
  If a cycle/[CYCLE_DONE]/ branch is MERGED and still on origin, delete it now
  (git push origin --delete cycle/[CYCLE_DONE]/integration). Prune other already-merged remote branches.
  (Deleting an UNMERGED or non-cycle branch is Tier D — ask the user.)

====================================================================
PART 4 — LIVE JIRA VERIFICATION (REQUIRED) — via Atlassian connector (no token)
====================================================================

Step 4.1 — Query the active sprint stories; record key/summary/status for each.

Step 4.2 — For every key an agent claimed to transition: claimed status | actual status | match YES/NO.

Step 4.3 — Verify the cycle's Agent-A-created tickets (typically a control task + the cycle's stories):
  - Control task -> Done after PR merge.
  - Each story -> verify its DoD criteria were actually met (not just "marked Done").

Step 4.4 — Check the epic(s) that THIS cycle's scope rolls up to (read from the hydration header /
  tracker / Agent A report — do not hard-code an epic that may not apply to this cycle).

Step 4.5 — MAKE THE JIRA CORRECTIONS NOW (Tier A — DO IT YOURSELF, do not defer to an agent):
  - Transition the control task to Done if the PR is merged and it isn't.
  - If a story is Done but its DoD is NOT met, revert it to In Progress and comment why.
  - Fix labels / sprint / epic links to match reality.
  - Never "comment-and-leave-ToDo": either the DoD is met (Done) or it is not (In Progress + reason).

====================================================================
PART 5 — PM PACK & SPEC REVIEW (REQUIRED)
====================================================================

Step 5.1 — Read PM Pack state files and compare planned vs verified; document every deviation:
  PM_Pack\07_hydration\HYDRATION_HEADER.md ; ...\STATE_SNAPSHOT.md
  PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md ; PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md

Step 5.2 — List PM_Pack\10_cycle_log\.

Step 5.3 — Read the spec files for CYCLE_NEXT scope BEFORE writing any task (never from memory):
  Scoring PM_Pack\ref\project_plan\05_scoring\ ; Collection ...\04_collection\ ; Analysis ...\06_analysis\
  (and the SRDI specs under ...\13_srdi\ for the current roadmap epic). Read the spec, THEN write the task.

Step 5.4 — Does the strategy doc need updates?
  a) New regression tests added this cycle? -> add to §7, bump the count, add a version-history row (Tier A, do now).
  b) Architectural/process change requiring a rule update? -> update the relevant section + version row.

Step 5.5 — ScrapFly readiness for CYCLE_NEXT (see §10):
  If CYCLE_NEXT involves ANY live Fiverr collection/validation (Agent E sampling, re-collection,
  DL-207 capture), the Agent E (and any live-collection) prompt MUST embed the §10.5 live-enable
  runbook verbatim: enable ScrapFly via a LOCAL uncommitted config.live.yaml + SCRAPFLY_API_KEY, run
  live, confirm the "ScrapFly session: requests=… credits=…" log line, and use "[SEED — no live
  signal]" if it cannot be enabled (never fabricate counts, never silently 403-degrade).

Step 5.6 — Build the verified gap list:
  a) files claimed but NOT on disk -> CARRY FORWARD
  b) Jira transitions claimed but NOT confirmed -> CORRECT NOW (Part 4)
  c) Agent E/F src/ violations -> DOCUMENT + INVESTIGATE
  d) code-vs-config drift (Part 2.8) -> route to Agent B
  e) score regression / unmet DoD -> flag for CYCLE_NEXT

====================================================================
PART 5.5 — PM DIRECT-ACTION SWEEP (REQUIRED — the §9 authority in practice)
====================================================================
Before writing any prompt, triage every loose end from Parts 1-5 into the four tiers and ACT.

Step 5.5.1 — Tier A/B items: RESOLVE NOW yourself. Typical set after a cycle:
  [ ] Jira corrected to match merged reality (Part 4.5).
  [ ] Merged cycle branch deleted on origin; stale merged remote branches pruned (Part 3.5).
  [ ] Untracked scratch litter removed; .gitignore extended if new scratch/live-config patterns appeared.
  [ ] Any accidentally-tracked artifact git rm --cached + .gitignore (record SHA).
  [ ] PM Pack state files updated with VERIFIED info (Part 6).
  [ ] Strategy §7 updated if regressions were added (Part 5.4).
  [ ] Governance/doc changes committed + pushed to develop (Step 5.5.3).

Step 5.5.2 — Tier C items: write them as explicit CYCLE_NEXT tasks for the right agent (NEVER fix
  yourself): src/ defects/changes -> Agent B; test gaps -> Agent B/F; config-behavior changes ->
  Agent B + gates. Each gets a task in Part 7 with a defect/AC note.

Step 5.5.3 — Commit the PM's own doc/governance changes to develop (Tier A) — DO IT YOURSELF:
  Pre-commit safety: the staged set MUST contain ZERO files under src/ or tests/ and ZERO config.yaml
  behavior change. Verify with: git diff --cached --name-only  (must show only PM_Pack/**, .gitignore,
  docs/** governance). git add the SPECIFIC paths (NOT -A, so untracked prompts/scratch aren't swept in).
  Commit docs(governance)/chore(...): ... ; push to origin/develop ; re-read develop HEAD and RECORD the new SHA.

Step 5.5.4 — Tier D items: surface to the user as an explicit yes/no and STOP on them. Standing set:
  the 6 stale stashes (cycle051/047/043/036/029/012 — dropping is irreversible); any history rewrite /
  force-push; any secret rotation; any LARGE live ScrapFly credit burn. Do NOT auto-act on these.

====================================================================
PART 6 — WRITE PM PACK UPDATES (VERIFIED INFO ONLY — BEFORE PROMPTS)
====================================================================
Update with VERIFIED info (not agent claims). MISSING means missing — never write "complete" for unverified.

  PM_Pack\07_hydration\HYDRATION_HEADER.md
    — Active cycle = CYCLE_NEXT; a "CYCLE_DONE — VERIFIED COMPLETE & MERGED" block (PR #, develop SHA,
      scope delivered, config facts incl. scrapfly committed-false); verified score/DB/Jira state;
      updated accumulated regression list; coverage gaps carried forward for Agent F; §9/§10 pointers.
  PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md
    — CYCLE_NEXT scope + mission; score-path/gap analysis; open stories w/ unmet DoD; SRDI table advanced;
      new Jira tickets to create.
  PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md
    — §7 if regressions added; version-history row for any change.
  PM_Pack\10_cycle_log\CYCLE_[CYCLE_DONE].md (or prep notes)
    — record: the §8.4 prompt-sizing count table (Part 7), the governance commit SHA (Part 5.5.3),
      created Jira keys, and the Tier-D items surfaced to the user.

====================================================================
PART 7 — WRITE CURSOR AGENT PROMPTS (ONLY AFTER PARTS 1-6 + 5.5)
====================================================================
Prompt files -> C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\
  CYCLE_[CYCLE_NEXT]_AGENT_A_PROMPT.md ... _B_ ... _E_ ... _C_ ... _F_ ... _D_PROMPT.md

TASK & LENGTH REQUIREMENTS (from strategy §8 — these SUPERSEDE any older 20-task / 3,700-line figures):
  - Every task is LARGE (4-6 sub-steps), XLARGE (6-8), XXLARGE (8-12), or XXXLARGE (12+ / multi-file).
    No standalone small/medium tasks.
  - Minimum 25 tasks per agent, each REAL project-advancing work (§8.2 legitimacy — no filler to hit a count).
  - Minimum lines: A>=810, B>=945, E>=810, C>=675, F>=810, D>=945. Total floor: 4,995.
  - Length is a floor filled with substantive content (inline code/dataclass skeletons, full test-file
    skeletons with every test-function stub, verbatim command/query/gate blocks, per-niche/per-file
    procedures, deliverable + DoD matrices, worked numeric examples, report templates) — never padding.

§8.4 PROMPT-SIZING SELF-GATE (BLOCKING — per §8.4.1/§8.4.2; you may NOT release prompts until this passes):
  PER PROMPT, AT WRITE TIME (NOT "after drafting all six"): the moment a prompt is finished, run
  (Get-Content <path>).Count and record ACTUAL vs FLOOR + the numbered-task count. A prompt below its
  floor OR under 25 substantive tasks is NOT WRITTEN — it may not be called done, surfaced, committed,
  or handed off, and you may NOT start the next prompt on top of an unmet one. SHOW the count for each.
     | Agent | Lines (actual) | Floor | Tasks (actual) | >=25? | PASS? |
  Banned excuses (§8.4.1): "complete in content", "I'll expand at the end", "the content already
  covers it", "good enough". Under floor means a MANDATORY CONTENT BLOCK is missing (§8.4.2: inline
  code/dataclass skeletons + function signatures; a test-function stub per behavior; verbatim
  command/query/gate blocks; the full regression list by name; per-story ACs; worked numeric examples;
  report template) — add the real block, never filler, then re-count. Record the final count table for
  all six in the cycle log / prep notes for auditability.

Every prompt MUST contain:
  a) project context (paths; branch = cycle/[CYCLE_NEXT]/integration; relevant Jira keys; auth via connector, no token)
  b) hard gate rules verbatim: G-001 codecov/patch>=90; G-002 Codex query TWICE / unresolved=0 real fix;
     G-003 Agent D merge-gate all PASS; G-004 exactly ONE --cov=src by Agent D only; CONFIG GATE
     (only documented config changes; scrapfly.enabled stays false in committed config — §10)
  c) verified starting state from Part 2 (develop SHA, suite count, coverage %)
  d) all accumulated regression test NAMES (strategy §7)
  e) mandatory preflight command block
  f) 25+ LARGE-XXXLARGE tasks with numbered sub-steps
  g) completion-standard checklist
  h) the real niche_ids where relevant (prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow,
     mcp_ai_agent, python_automation, ai_tool_llm_integration, ai_agent_development, workflow_automation,
     python_web_scraping) — never illustrative slugs

Agent A additionally: all 6 downstream handoff packages; SCRUM ticket-creation instructions; key
  keyword/niche investigation if a weakness gap persists; may extend .gitignore.
Agent B additionally: it is the ONLY author of src/; new behavior behind config toggles; carries any
  Tier-C src/ defects the PM logged (Part 5.5.2); adds/updates tests for its code.
Agent E additionally: file-zone rule (commit ONLY CYCLE_[CYCLE_NEXT]_AGENT_E.md; NEVER src/, tests/,
  config.yaml); git pull --rebase before each push; pre-push git diff --cached --name-only | grep "^src/" -> EMPTY;
  and (if doing live work) the §10.5 ScrapFly live-enable runbook verbatim + the "[SEED — no live signal]" fallback.
Agent F additionally: file-zone rule (ONLY test files + report; NEVER src/); coverage-gap targets from Part 5/Agent C.
Agent D additionally (verbatim, every cycle): full 6-agent deliverables table; Agent E zone check
  (git show E_SHA -> ZERO src/+tests/); Agent F zone check (git show F_SHA -> ZERO src/); cycle-scoped
  attribution gate ($base = git merge-base develop cycle/[N]/integration; all src/ only in B commits);
  scrapfly committed-false re-verify (§10/Part 2.9); ONE --cov=src run (G-004); Codex query TWICE;
  complete merge-gate checklist (codecov, Codex, 6-agent zone, every named regression, score/pipeline,
  coverage, directory-integrity); post-merge Jira plan; "ready to merge only when ALL items PASS/YES."

====================================================================
PART 8 — SELF-AUDIT BEFORE SUBMITTING (any NO -> go back)
====================================================================
  1.  Read hydration header to determine cycle numbers?                         YES / NO
  2.  Read strategy doc §7/§8/§9/§10 for permanent rules?                        YES / NO
  3.  Read all 6 agent reports for CYCLE_DONE in full?                           YES / NO
  4.  Verified each claimed file exists on disk?                                 YES / NO
  5.  Ran full suite + recorded actual coverage %?                               YES / NO
  6.  Verified Agent E committed ZERO src/ and ZERO tests/?                      YES / NO
  7.  Verified Agent F committed ZERO src/?                                      YES / NO
  8.  Ran code-vs-config drift check (niche_ids/constants match config.yaml)?    YES / NO
  9.  Verified committed config.yaml scrapfly.enabled = false (no enabled:true)? YES / NO
  10. Live GitHub API: PR state MERGED + codecov/patch SUCCESS?                   YES / NO
  11. Codex query run TWICE (G-002) and zero unresolved confirmed?               YES / NO
  12. Live Jira checked AND corrections MADE (not just noted)?                   YES / NO
  13. Merged cycle branch deleted on origin (Tier A)?                            YES / NO
  14. Read spec files before writing implementation tasks?                       YES / NO
  15. Updated strategy §7 if new regressions added?                              YES / NO / N/A
  16. Updated PM Pack files with VERIFIED state?                                 YES / NO
  17. §8.4.1 sizing gate run PER PROMPT at write time, each count SHOWN >= floor? YES / NO
      (under floor = NOT written; §8.4.2 content blocks present; final table recorded — BLOCKING)
  18. All 6 prompts reference branch cycle/[CYCLE_NEXT]/integration?             YES / NO
  19. Agent E (if live) embeds the §10 ScrapFly live-enable runbook + fallback?  YES / NO / N/A
  20. NO API token/secret embedded in any prompt (connector-only auth)?          YES / NO
  21. PM Tier-A/B direct actions completed (Part 5.5) + governance committed?    YES / NO
  22. Tier-C items routed to agents; Tier-D items surfaced to the user?          YES / NO
  23. All 3 (or N) CYCLE_DONE Jira tickets correctly closed/verified?            YES / NO

====================================================================
END OF UNIVERSAL POST-CYCLE PM REVIEW PROMPT (v4.0)
====================================================================
