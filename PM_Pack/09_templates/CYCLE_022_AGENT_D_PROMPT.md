====================================================================
AGENT D — CYCLE 022 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/022/integration
- Python 3.11+ | GitHub CLI | Jira API

## ⚠️ CRITICAL PROTOCOL — READ FIRST, APPLY TO EVERY TASK

Two failures from prior cycles are now fixed. Both MUST be followed in this cycle:

FAILURE 1 CORRECTED: PRs #24 and #25 merged with codecov/patch FAILING.
  codecov/patch is NOT optional. It is a HARD merge blocker.
  Before you recommend merge for PR #26:
  1. Get the EXACT codecov/patch % from the GitHub PR check
  2. It must be >= 90%
  3. If it is below 90%, do NOT merge — run targeted coverage, add tests, push, re-check
  Never merge while codecov/patch shows FAIL.

FAILURE 2 CORRECTED: Codex threads not queried/dispositioned in some prior cycles.
  You MUST run the GraphQL query for PR #26 and document the result.
  You MUST classify and reply to EVERY thread found.
  You MUST resolve every thread (with a disposition reply posted first).
  Completing this checklist IS the completion standard for this cycle's PR gate.

## YOUR ROLE
Agent D owns: (1) patch-coverage gap cleanup for any files from prior cycles still
below 90% patch coverage, (2) board reconciliation, (3) PR #26 with FULL mandatory
merge gate checklist, (4) Codex disposition — query, classify, fix/reply, resolve ALL.

## GIT INSTRUCTIONS
1. Ensure on: cycle/022/integration. Pull latest.
2. Read ALL A/B/C handoffs.
3. Commit: feat(integration): patch coverage and PR #26 gate [Agent D Cycle 022]
4. gh pr create --base develop --head cycle/022/integration
   --title "feat(cycle-022): Stage 14, pricing pipeline, patch coverage"
5. After CI settles: verify codecov/patch, handle Codex, fill checklist, recommend merge.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass with coverage >= 90%.

## TASKS

### Task 1: Read all A/B/C handoffs + run full suite
Read: docs/cycle_reports/CYCLE_022_AGENT_A.md, B.md, C.md
Run: python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
Record: exact test count and coverage %.

### Task 2: Run comprehensive patch coverage audit
Run targeted coverage for EVERY module touched in cycles 020, 021, and 022:
  python -m pytest -q --cov=src/scoring/pipeline.py --cov-report=term-missing
  python -m pytest -q --cov=src/recommendations --cov-report=term-missing
  python -m pytest -q --cov=src/models/keyword_score.py --cov-report=term-missing
  python -m pytest -q --cov=src/models/pricing.py --cov-report=term-missing
  python -m pytest -q --cov=src/pricing --cov-report=term-missing

For each file: list ALL lines still showing as uncovered (marked with ">").
Document in your report: "Patch coverage audit: [file]: [list of uncovered lines]"

### Task 3: Add patch-coverage gap tests
For every uncovered line found in Task 2, add targeted tests.
These should be added to the EXISTING test files for each module:
  - Uncovered pipeline.py lines → tests/unit/test_scoring_pipeline.py
  - Uncovered recommendations/ lines → tests/unit/test_recommendations.py
  - Uncovered keyword_score.py lines → tests/unit/test_keyword_score.py
  - Uncovered pricing/ lines → tests/unit/test_pricing.py, test_pricing_analysis.py

Target: bring patch coverage for ALL new code to >= 90%.
Add minimum 10 targeted patch-gap tests.

### Task 4: Run targeted tests to confirm patch gap is closed
After adding tests:
  python -m pytest -q --cov=src/scoring/pipeline.py --cov-report=term-missing
  python -m pytest -q --cov=src/recommendations --cov-report=term-missing
  python -m pytest -q --cov=src/pricing --cov-report=term-missing
Each module must show >= 90% in the targeted run.

### Task 5: Run full validation block
  python -m ruff check .
  python -m mypy src
  python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
  python run.py config-check
  python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle022.db
  python run.py phase2-smoke
Total tests must be >= 1044. Coverage must be >= 90%.

### Task 6: Board reconciliation
Audit these keys:
- SCRUM-510: Done (verify)
- SCRUM-511: In Progress (verify)
- SCRUM-19 (E04): In Progress (verify)
- SCRUM-20 (E05): In Progress (verify)
- SCRUM-21 (E06): In Progress (verify)
- E06 S6.3, S6.4, S6.5 story keys: In Progress (verify)
- SCRUM-231: In Review (verify)
Correct any stale statuses. Document.

### Task 7: Post Jira comment on SCRUM-231 with pricing pipeline evidence
Comment: "Cycle 022 Agent D: pricing pipeline stage wired. run.py now supports:
  - python run.py --mode score-only (scoring pipeline)
  - python run.py recommendations-only (Stage 13)
  - python run.py price-analysis (Stage 10.5)
Full pipeline CLI coverage: scoring → recommendations → pricing all callable.
Status: Keep In Review pending real-data collection run."

### Task 8: Commit patch-gap tests before creating PR
Commit scope: test additions for patch coverage gaps + this report.
Message: feat(integration): patch coverage cleanup and PR #26 gate [Agent D Cycle 022]

### Task 9: Create PR #26
gh pr create --base develop --head cycle/022/integration \
  --title "feat(cycle-022): Stage 14, pricing pipeline, patch coverage"

PR body must include:
- Summary covering all 4 agent deliverables
- Jira Keys: SCRUM-511 + E04/E05/E06 story keys + SCRUM-231
- Changed Files: pipeline.py, run.py, pricing/analysis.py, pricing/orchestrator.py,
  pricing/new_seller_pricing.py, 4 new/extended test files
- Validation: ruff clean, mypy clean, [count] tests, [%] coverage
- AC/DoD table per story
- Guardrail confirmations: no main, no worktrees, no secrets

### Task 10: Monitor PR #26 CI — wait for ALL checks including codecov/patch
Run: gh pr checks [PR_NUMBER] and wait for ALL checks to settle.
DO NOT merge until you see ALL of these as SUCCESS:
  - Lint, Typecheck, Tests, and Gates: SUCCESS
  - codecov/project: SUCCESS
  - codecov/patch: SUCCESS
  - Dependency Audit: SUCCESS
  - Secret Scan: SUCCESS
  - Validate PR: SUCCESS

If codecov/patch shows FAILURE:
  1. Run: python -m pytest -q --cov=src/[failing_module] --cov-report=term-missing
  2. Add tests for uncovered lines
  3. git add + commit + push
  4. Wait for new CI run
  5. Confirm codecov/patch is now SUCCESS
  6. Only then proceed to merge recommendation

### Task 11: ⚠️ MANDATORY CODEX DISPOSITION — Run the query, handle every thread

Run this EXACT query:
  gh api graphql -f query='{repository(owner:"KevinSGarrett",name:"Fiverr"){pullRequest(number:REPLACE_WITH_PR_NUMBER){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:3){nodes{author{login}body}}}}}}}'

Document in your report:
  "Codex review query for PR #26 (number [N]):
   Raw result: [paste the JSON]
   Total threads found: [N]"

IF 0 threads found:
  Document: "Codex query confirmed 0 review threads. No disposition required."

IF any threads found:
  For EACH thread:
  1. Read the comment body and the code it references
  2. Classify: VALID_FIXED | VALID_DEFERRED_BLOCKER | VALID_DEFERRED_NONBLOCKING |
               NOT_APPLICABLE | FALSE_POSITIVE | DUPLICATE
  3. For VALID_FIXED:
     - Fix the code
     - Add regression test (must FAIL before fix, PASS after)
     - Push fix commit
     - Wait for CI to re-run and pass
     - Reply to thread:
       "Codex disposition: VALID_FIXED
        Decision: [what was fixed]
        Evidence: File: [path], Test: [command], Commit: [sha]
        Resolution: Fixed."
     - Resolve the thread
  4. For all other categories:
     - Reply with evidence:
       "Codex disposition: [CATEGORY]
        Decision: [reasoning]
        Evidence: [test/code reference]
        Resolution: [deferred/not-applicable/false-positive with reason]"
     - Note in PR body: "Thread [ID]: [CATEGORY] — [brief note]"
     - Resolve the thread after reply is posted

### Task 12: Fill and post MANDATORY MERGE GATE CHECKLIST
Copy this EXACTLY into your report AND into a PR comment:

```
MERGE GATE CHECKLIST — Cycle 022 PR #26
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
[ ] PR #26 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```

This checklist MUST have NO failures before merge is recommended.
If any item is NO or FAIL: fix it before recommending merge.

### Task 13: Final SHA freeze
git rev-parse origin/cycle/022/integration → final pushed SHA.
Verify SHA matches PR head.
Post freeze comment to PR #26.

### Task 14: Confirm all 4 agent reports exist
  docs/cycle_reports/CYCLE_022_AGENT_A.md
  docs/cycle_reports/CYCLE_022_AGENT_B.md
  docs/cycle_reports/CYCLE_022_AGENT_C.md
  docs/cycle_reports/CYCLE_022_AGENT_D.md

### Task 15: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent D rows
Rows for SCRUM-511, SCRUM-231, E06 S6.3/S6.4/S6.5 keys.

### Task 16: Post SCRUM-511 (Cycle 022 control) final summary
Comment with: PR #26 URL, final SHA, test count, coverage %, Codex thread count,
codecov/patch status, merge readiness.

### Task 17: Create Agent D report docs/cycle_reports/CYCLE_022_AGENT_D.md
Sections: Preflight, patch coverage audit (all modules with uncovered lines listed),
patch gap tests added (+10), full validation output, board reconciliation, PR #26 URL,
CI check results (ALL checks listed), Codex query result (verbatim), Codex disposition
(each thread classified and resolved), FULL merge gate checklist filled in,
final SHA, merge readiness recommendation.

### Task 18: Merge readiness recommendation
State explicitly: "PR #26 is ready to merge when approved." OR list specific blockers.
DO NOT recommend merge unless BOTH codecov/project and codecov/patch show SUCCESS
and ZERO Codex threads are unresolved.

### Tasks 19-22: Final cleanup
19. Artifact hygiene — no .env, *.db, coverage.xml staged.
20. No-main / worktree check.
21. python run.py recommendations-only → must pass.
22. python run.py price-analysis → must pass.

## FILES CREATED THIS CYCLE (Agent D)
| Action | File |
|---|---|
| MODIFY | tests/unit/test_scoring_pipeline.py |
| MODIFY | tests/unit/test_recommendations.py |
| MODIFY | tests/unit/test_keyword_score.py |
| MODIFY | tests/unit/test_pricing.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_022_AGENT_D.md |

## COMMIT INSTRUCTIONS
git add tests/unit/test_scoring_pipeline.py tests/unit/test_recommendations.py
git add tests/unit/test_keyword_score.py tests/unit/test_pricing.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_022_AGENT_D.md
git commit -m "feat(integration): patch coverage cleanup and PR #26 gate [Agent D Cycle 022]"
====================================================================
END OF AGENT D PROMPT
====================================================================
