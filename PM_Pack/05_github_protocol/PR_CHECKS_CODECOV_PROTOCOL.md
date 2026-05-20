# PR CHECKS AND CODECOV PROTOCOL
# Added: Cycle 005 — Permanent PM/GitHub Governance Rule

## Purpose

The Fiverr Research System must not rely only on local validation claims. Every PR must run GitHub Actions checks and Codecov coverage reporting before it can merge.

## Required PR Checks

Every PR into `develop` must run and pass these checks:

1. `python -m ruff check .`
2. `python -m mypy src`
3. `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
4. `python run.py config-check`
5. `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci.db`
6. `python run.py phase2-smoke`
7. Codecov upload and Codecov project/patch coverage status.
8. Codex review threads fully dispositioned and resolved.

## Codecov Coverage Gate

Coverage is a blocker.

- Minimum project coverage: `90%`.
- Minimum patch coverage: `90%`.
- The local pytest coverage command must use `--cov-fail-under=90`.
- `coverage.xml` must be uploaded to Codecov from GitHub Actions.
- If Codecov status is pending, missing, failing, or unavailable, the PR must not merge.

## GitHub Actions Workflow Requirements

The repository must contain `.github/workflows/ci.yml` with:

- Trigger: `pull_request` targeting `develop` and `main`.
- Trigger: `push` to `develop`, `main`, and `cycle/**/integration` branches.
- Python version: `3.11` initially. Add `3.12` once dependencies are stable.
- Install command: `python -m pip install --upgrade pip && python -m pip install -e ".[dev]"`.
- Lint/type/test commands listed above.
- Codecov upload using `codecov/codecov-action`.
- Artifact upload for `coverage.xml` even if Codecov upload fails, so review evidence remains available.

## Required Branch Protection Strategy

`develop` must be the integration branch and should be protected with required status checks:

- CI / lint
- CI / type-check
- CI / tests-coverage
- CI / smoke-gates
- Codecov project coverage
- Codecov patch coverage

`main` must be release-only and protected with the same checks plus PM release approval.

If the Cursor/GitHub Steward agent cannot configure branch protection through `gh` or GitHub UI permissions, it must report this as a blocker and provide the exact settings for Kevin/PM to apply.

## Default Branch Policy

The repository default branch must not be a cycle branch. It should be `develop` during active development unless Kevin chooses `main` after the first stable release. Cycle 005 live GitHub review found the default branch set to `cycle/002/integration`; that is incorrect and must be corrected.

## Required PR Template

The repository must contain a PR template requiring:

- Summary.
- Jira keys.
- Codex disposition table.
- Validation commands.
- Codecov result link/status.
- Confirmation that no direct `main` push occurred.
- Confirmation that all Codex threads are resolved or formally dispositioned.

## Merge Blockers

A PR is blocked if any of the following are true:

- No GitHub Actions workflow ran for the PR head SHA.
- Any required workflow job failed, was cancelled, or is pending beyond expected runtime.
- Codecov report is missing or below 90%.
- Any Codex thread remains unresolved.
- Any Codex thread was resolved without a disposition reply.
- The PR branch is not based on the latest `develop`.
- The repo working tree used for push contains generated runtime DBs, caches, secrets, browser sessions, or local-only artifacts.
- The PR attempts to target `main` outside of an approved release cycle.

## Integration/GitHub Steward Checklist

The final steward agent must run:

```bash
git fetch --all --prune
git status --short
git log --oneline --decorate -12
git merge-base --is-ancestor origin/develop HEAD
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci_local.db
python run.py phase2-smoke
```

Then verify on GitHub:

- PR exists and targets `develop`.
- GitHub Actions checks are present and passing.
- Codecov statuses are present and passing.
- Codex review threads are resolved after disposition.
- No PR is merged until all required gates pass.


## Cycle 006 Update — Project Status Visibility

The project coverage gate must be visible as a GitHub/Codecov status, not only as local pytest output. If the PR only shows `codecov/patch`, the steward must investigate why project status is absent. Until project status is visible and successful, merge readiness is `BLOCKED` unless PM/operator grants a documented temporary exception.

Required steward evidence:

- CI check name and conclusion.
- Codecov patch status name, target, and conclusion.
- Codecov project status name, target, and conclusion.
- Local coverage command output with `--cov-fail-under=90`.
- Explanation for any missing status and whether it is a hard blocker.

---

# CYCLE 022 ADDENDUM — MANDATORY PATCH COVERAGE PROTOCOL

## The codecov/patch Check Is Always a Hard Blocker

Previous cycles incorrectly treated codecov/patch as "non-blocking." It is not.

codecov/patch reports coverage of the NEW LINES added in a PR.
If it fails, it means the code added in this PR has < 90% test coverage.
This is a hard merge blocker, same as codecov/project.

## How to Fix a codecov/patch Failure

Step 1: Identify uncovered lines
```powershell
python -m pytest -q --cov=src/[module_you_changed] --cov-report=term-missing
```
Look for lines marked with ">" (not covered) in the output.

Step 2: Add tests targeting those exact lines
- Each uncovered branch/function/line needs at least one test
- Add tests to the SAME test file that covers the module
- Name tests: test_[function]_[scenario]

Step 3: Push and recheck
```powershell
git add tests/unit/test_[module].py
git commit -m "test([module]): add patch coverage for [function] [Cycle NNN Agent D]"
git push
```
Wait for GitHub Actions to run. codecov/patch must show PASS.

Step 4: Confirm before merge
```
codecov/project: [PASS / FAIL] — [exact %]
codecov/patch: [PASS / FAIL] — [exact %]
```
Both must be PASS before any merge recommendation.

## Zero Codex Findings — Still Must Be Confirmed

If you believe there are 0 Codex review threads on your PR, you must STILL run
the query and confirm explicitly. Do not assume — verify:

```bash
gh api graphql -f query='
{
  repository(owner:"KevinSGarrett", name:"Fiverr") {
    pullRequest(number: PR_NUMBER_HERE) {
      reviewThreads(first: 50) {
        nodes {
          id
          isResolved
          isOutdated
          comments(first: 3) {
            nodes {
              author { login }
              body
            }
          }
        }
      }
    }
  }
}'
```

Expected response for zero findings:
```json
{ "data": { "repository": { "pullRequest": { "reviewThreads": { "nodes": [] } } } } }
```

Document in your report: "Codex query run. Result: 0 threads. No disposition required."

## Codex Disposition When Findings Exist

For each thread node returned by the query above:

1. Read the body of the Codex comment
2. Review the current code at the referenced location
3. Classify: VALID_FIXED | VALID_DEFERRED_BLOCKER | VALID_DEFERRED_NONBLOCKING |
   NOT_APPLICABLE | FALSE_POSITIVE | DUPLICATE
4. If VALID_FIXED:
   - Fix the code
   - Add regression test (must FAIL before fix, PASS after)
   - Push to PR branch
   - Wait for CI to pass
   - Reply to thread with:
     "Codex disposition: VALID_FIXED
      Decision: [what was wrong and what was fixed]
      Evidence: File: [path], Test: [command], Commit: [sha]
      Resolution: Fixed."
   - Resolve the thread
5. If any other category:
   - Reply with evidence: "Codex disposition: [CATEGORY]. Evidence: [...]"
   - Request PM approval in the PR body
   - Resolve the thread only after PM approval is visible
6. A thread is NOT resolved by pushing a fix commit — you must manually reply + resolve

## Agent D Mandatory Merge Gate Checklist (Every PR)

Copy this block into your report AND the final PR freeze comment:

```
MERGE GATE CHECKLIST — Cycle [NNN] PR #[N]
==========================================
CODECOV:
[ ] codecov/project: [PASS/FAIL] — [exact %]
[ ] codecov/patch: [PASS/FAIL] — [exact %]
[ ] Local --cov-fail-under=90: [PASS/FAIL]
[ ] All new lines covered by tests: [YES/NO — if NO, list uncovered files]

CODEX:
[ ] reviewThreads query executed: YES
[ ] Total threads found: [N]
[ ] All threads dispositioned: [YES/N/A]
[ ] All VALID_FIXED threads have regression tests: [YES/N/A]
[ ] All threads manually resolved with reply: [YES/N/A]
[ ] Zero unresolved threads: [YES]

FINAL:
[ ] PR is ready to merge: [YES/NO]
[ ] Blocker(s) if NO: [list]
```

This checklist must be filled in before any merge recommendation is made.
If any item shows FAIL or NO, the PR MUST NOT merge until it is resolved.

---

# CYCLE 029 ADDENDUM — COVERAGE AUDIT CONSOLIDATION (Rule R-092)

## Problem (Operator-identified, Cycle 028 retro)

Every cycle, all 4 agents were running expensive coverage operations:
- Full pytest --cov on entire src/ directory
- Coverage report generation
- A "validation block" with full coverage
- Patch coverage for their module

On a 1500+ test suite, this took several minutes per agent run, multiplied
by 4-5 runs per cycle = an hour or more of redundant coverage work per cycle.

## Insight

Codecov already runs on every PR as the canonical coverage gate (Rule G-001).
The local --cov runs by every agent are redundant developer-convenience checks.

## Three-Tier Coverage Strategy (PERMANENT — every cycle)

### Tier 1: Agents A, B, C (FAST — targeted patch only)

After implementing their changes, each of Agents A/B/C runs ONLY:

```powershell
# Their new test file (the file they wrote)
python -m pytest -q tests/unit/[their_new_test_file].py --no-header

# Targeted patch coverage on JUST the module they changed
python -m pytest -q --cov=src.[their_changed_module] --cov-report=term-missing tests/unit/[their_test_file].py
```

This is fast — seconds, not minutes — because it only loads tests for the
file they wrote and measures coverage of the single module they changed.

**Agents A/B/C do NOT run:**
- The full pytest suite
- Full coverage report on src/
- Coverage XML generation
- The 6-command "validation block"

**Agents A/B/C target:**
- Their new test file passes 100%
- Their changed module has >=90% patch coverage

### Tier 2: Agent D (COMPREHENSIVE — single end-of-cycle audit)

Agent D runs the full audit ONCE before creating the PR:

```powershell
# Full ruff and mypy
python -m ruff check .
python -m mypy src

# Full pytest with coverage gate
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90

# Comprehensive patch coverage audit for EVERY module changed this cycle
python -m pytest -q --cov=src.collection.workflows.keyword_expansion --cov-report=term-missing
python -m pytest -q --cov=src.collection.workflows.google_trends --cov-report=term-missing
python -m pytest -q --cov=src.scoring.weakness --cov-report=term-missing
# (etc. for every module touched in the cycle)

# Smoke tests
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle{N}.db
python run.py phase2-smoke
python run.py collect-only
```

Agent D records the final test count and coverage % from this single audit.
Agent D documents any uncovered lines per file and adds gap tests.

### Tier 3: Codecov on PR (CANONICAL GATE — Rule G-001)

The PR check `codecov/patch` is the only canonical coverage gate.
It must show PASS (>=90%) on every PR before merge.
This is enforced by Rule G-001 and Agent D's mandatory checklist (Rule G-004).

## What Each Agent's "Validation" Section Looks Like Now

### Agents A, B, C (NEW — FAST):

```
### Validation (targeted only — full audit is Agent D's job per R-092)
python -m pytest -q tests/unit/test_[your_new_file].py
python -m pytest -q --cov=src.[your_module] --cov-report=term-missing tests/unit/test_[your_new_file].py
```

### Agent D (COMPREHENSIVE):

```
### Full validation block (R-092 Tier 2 — Agent D only)
[All commands from Tier 2 above]
```

## Expected Effect

- Cycle execution time per Agent A/B/C: 50-65% reduction
- Coverage safety: unchanged (codecov on PR is the canonical gate, Agent D
  runs the full audit before PR creation)
- Cumulative cycle wall-clock time: significantly reduced

## Failure Modes

If Agent D's full audit reveals coverage below 90% on ANY module they
expected to be covered by Agents A/B/C: that means those agents skipped
the targeted patch coverage check. Agent D documents this in their report
and addresses the gap with additional tests before PR creation.

If codecov/patch on the PR shows FAILURE despite Agent D's local audit
showing PASS: that is a Codecov configuration issue. Agent D investigates
and resolves before merge.
