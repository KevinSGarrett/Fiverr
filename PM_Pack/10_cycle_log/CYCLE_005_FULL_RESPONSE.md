# CYCLE 005 — 2026-05-14

Focus: Governance / CI / Codex review recovery before further Phase 2 expansion  
Branch: `cycle/005/integration` or direct continuation on `cycle/004/integration` only for PR #3 remediation if the GitHub Steward confirms that is safer  
Active PR: PR #3 — `cycle/004/integration` -> `develop`  
Blocking Jira: `SCRUM-247` — Codex review disposition and required PR checks with Codecov blocker

---

## 1. REVIEW OF PRIOR AGENT WORK / CURRENT REPO STATE

### Inputs Reviewed

- Uploaded PM Pack Cycle 004.
- Uploaded local repository archive: `Fiverr_004.zip`.
- Live GitHub repository metadata for `KevinSGarrett/Fiverr`.
- Live PR #3 metadata.
- Live PR #3 Codex review threads.
- Live status-check/workflow-run state for PR #3 head SHA.

### Current Findings

| Area | Finding | Merge Impact |
|---|---|---|
| PR #3 | Open, mergeable, not merged, targets `develop` | Do not merge yet |
| PR #3 head | `5282328dcaf1070eb77cf52d9aafbc013e12aafb` | Use as live verification target |
| Codex review | 2 unresolved Codex threads | Blocking |
| Codex thread 1 | `src/orchestrator.py` forwards non-positive `sample_size` as `max_candidates` | Valid issue; fix required |
| Codex thread 2 | `src/collection/gig_detail.py` `data-testid` regex can truncate nested markup | Valid issue; fix required |
| GitHub Actions | No workflow runs found for PR #3 head SHA | Blocking |
| Status checks | No combined statuses found for PR #3 head SHA | Blocking |
| Repo workflow files | Uploaded repo archive contains no `.github/workflows` files | CI must be added |
| Codecov | No Codecov workflow/status currently present | Codecov must be added and configured |
| Default branch | Live GitHub reported default branch as `cycle/002/integration` | Must be corrected to `develop` or reported as admin blocker |
| Local test in PM container | Could not run because dependencies such as SQLAlchemy are not installed in this review container | Cursor/GitHub Actions validation required |

### PM Decision

PR #3 must **not** merge until:

1. Both Codex threads are fixed or formally dispositioned.
2. Regression tests cover both fixes.
3. GitHub Actions workflow exists and runs on the PR.
4. Codecov upload/status exists.
5. Coverage is at least 90%.
6. All Codex review threads are replied to and resolved.
7. Branch protection/default branch settings are verified or documented as blocked by permissions.

---

## 2. JIRA BOARD UPDATE

### Completed Jira Actions

| Jira Key | Action |
|---|---|
| `SCRUM-247` | Created: `[PM/GITHUB] Add Codex review disposition and required PR checks with Codecov blocker` |
| `SCRUM-247` | Moved to `In Progress` |

### Jira Status / Governance Notes

`SCRUM-247` is now the active governance blocker for this cycle. It should not move to Done until the repository has working PR checks, Codecov is reporting at least 90% coverage, and the PM Pack permanently contains Codex review disposition rules.

### GitHub PR Comment Added

A PM governance comment was added to PR #3 stating that the PR should not merge until the two Codex issues are fixed/formally dispositioned and required checks are present/passing.

---

## 3. PERMANENT PM PACK UPDATES MADE

The PM Pack has been updated so this does not need to be re-explained in future cycles.

### New PM Pack Files

| File | Purpose |
|---|---|
| `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md` | Permanent Codex review comment handling protocol |
| `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md` | Permanent GitHub Actions, Codecov, branch protection, and merge-check protocol |

### Updated PM Pack Files

| File | Update |
|---|---|
| `07_hydration/HYDRATION_HEADER.md` | Cycle 005 state and Codex/CI blocker rules added |
| `07_hydration/STATE_SNAPSHOT.md` | PR #3, missing checks, unresolved Codex threads, default branch issue, and SCRUM-247 captured |
| `05_github_protocol/MERGE_PROTOCOL.md` | Codex unresolved threads, CI, and Codecov are merge blockers |
| `05_github_protocol/BRANCH_WORKFLOW.md` | Integration/GitHub Steward owns push/PR/check/Codex handling |
| `03_cursor_agent_system/PROMPT_RULES.md` | Steward prompts must include Codex and Codecov duties |
| `06_review_and_qa/QA_GATES.md` | PR gate now requires checks and Codecov >=90% |
| `10_cycle_log/CYCLE_005.md` | Cycle 005 review and plan logged |
| `WAVE_SCHEDULE.md` | Cycle 005 governance recovery noted |

---

## 4. CYCLE 005 PLAN

### Strategic Goal

Stop feature expansion long enough to install the missing quality gates. The project cannot continue merging PRs based only on local validation reports. PR #3 already shows why: Codex found legitimate issues and GitHub has no required checks running.

### Assignment Summary

| Agent | Role This Cycle | Primary Output |
|---|---|---|
| Agent A | CI / GitHub governance engineer | GitHub Actions CI, Codecov config, PR template, branch/default policy docs |
| Agent B | Collection engineer | Fix the two live Codex issues and add regression tests |
| Agent C | Analysis/LLM coverage engineer | Improve test coverage and CI parity for analysis/LLM paths |
| Agent D | Documentation + Integration/GitHub Steward | Codex thread dispositions, PR replies/resolution, final validation, push/PR/update, check verification |

### Required Branch Strategy

Agent A must begin by verifying PR #3 live. There are two acceptable paths:

#### Preferred Path — PR #3 Remediation on Existing Branch

If PR #3 is still open and the branch `cycle/004/integration` is editable, Agents A-D may work directly on `cycle/004/integration` to fix Codex issues and add CI files, then push the new commits to update PR #3.

#### Alternate Path — Follow-Up Cycle Branch

If PR #3 cannot be updated safely, create:

```bash
cycle/005/integration
```

from the latest `cycle/004/integration` head or from updated `develop` only if PR #3 has already merged. The PR body must clearly explain which path was used and why.

### Main Policy

No one pushes directly to `main`. `main` remains release-only.

---

## 5. AGENT PROMPTS

## Agent A Prompt — CI, Codecov, PR Template, and Repo Branch Governance

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local repository path used by agents: C:\Fiverr\Fiverr. Important: the parent C:\Fiverr is not the git repository; the nested C:\Fiverr\Fiverr folder is the git repository. Active PR at Cycle 005 start: PR #3, title `feat(cycle-004): expand collection and analysis dry-run workflows`, head branch `cycle/004/integration`, base branch `develop`. PM review found no GitHub Actions workflow files in the uploaded archive and no workflow/status checks for PR #3 head SHA. Live GitHub also reported the repository default branch as `cycle/002/integration`, which is wrong for this project workflow. The current priority is governance/CI recovery, not new feature expansion.

YOUR ROLE
You are Agent A — Infrastructure, CI, and GitHub Governance Engineer for Cycle 005. You own `.github/workflows/ci.yml`, `codecov.yml`, coverage configuration in `pyproject.toml` if needed, GitHub/branch-policy documentation under `docs/`, and CI validation scripts if they fall under `src/scripts/`. You must not touch collection parser implementation files owned by Agent B, analysis/LLM implementation files owned by Agent C, or dashboard/report docs owned by Agent D unless explicitly listed below. You are also the first GitHub gatekeeper for this cycle: verify whether PR #3 should be updated directly or whether a new `cycle/005/integration` branch is required.

GIT / BRANCH INSTRUCTIONS
Start inside `C:\Fiverr\Fiverr`. Run `git status --short`, `git branch --show-current`, `git fetch --all --prune`, and `git log --oneline --decorate -12`. If PR #3 is still open and `cycle/004/integration` is checked out or can be checked out, prefer updating `cycle/004/integration` directly so the fixes land in the existing PR. If PR #3 has already merged or the branch cannot be updated safely, create `cycle/005/integration` from the correct latest base. Do not push to `main`. Do not merge to `develop` or `main`. You may commit your assigned files only. Commit message: `ci(github): add required pr checks and codecov gate [Agent A]`.

TASK A1 — LIVE REPO / PR GOVERNANCE VERIFICATION
Story/Epic Reference: SCRUM-247 / PM-GitHub governance. Spec Reference: PM Pack `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md`, `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`, and `05_github_protocol/BRANCH_WORKFLOW.md`. Files to create/modify: `docs/CYCLE_005_GITHUB_GOVERNANCE_REPORT.md` only for this task. Implementation Details: Create a concise but evidence-based governance report recording current branch, current HEAD, `origin/develop`, PR #3 state if visible through `gh pr view 3`, whether PR #3 has check runs, whether Codecov is installed/visible, whether the default branch is `develop`, and whether branch protection is configured. Use `gh` CLI when available; otherwise use `git ls-remote` and document what could not be verified. If the default branch is still `cycle/002/integration`, attempt to correct it to `develop` only if GitHub permissions and project policy allow. Acceptable command if authenticated and authorized: `gh repo edit KevinSGarrett/Fiverr --default-branch develop`. If this fails, do not hack around it; document the exact blocker and required manual setting. Required Tests/Validation: (1) `git ls-remote --heads origin develop cycle/004/integration` returns visible refs, or the report documents failure. (2) Report includes default-branch status and branch-protection status. DOD: The report gives the PM and Agent D a clear live-state baseline before any PR merge readiness decision.

TASK A2 — ADD REQUIRED GITHUB ACTIONS CI WORKFLOW
Story/Epic Reference: SCRUM-247 / Required PR checks. Spec Reference: PM Pack `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`. Files to create/modify: `.github/workflows/ci.yml`. Implementation Details: Add a GitHub Actions workflow named `CI`. It must trigger on `pull_request` targeting `develop` and `main`, and on `push` to `develop`, `main`, and `cycle/**/integration`. It must run on Ubuntu latest with Python 3.11. It must install the project with dev dependencies using `python -m pip install --upgrade pip` and `python -m pip install -e ".[dev]"`. It must run separate clearly named steps for Ruff, Mypy, Pytest with coverage, config-check, foundation gate, and phase2 smoke. The pytest step must run `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`. Upload `coverage.xml` as an artifact. Add Codecov upload using `codecov/codecov-action@v4`. Do not require a Codecov token if the public repo can upload tokenless; include `fail_ci_if_error: true` so missing/failed Codecov upload is visible. Required Tests/Validation: (1) YAML syntax is valid. (2) Workflow includes all required commands. DOD: New PRs produce real status checks and coverage artifacts.

TASK A3 — ADD CODECOV CONFIGURATION
Story/Epic Reference: SCRUM-247 / Codecov blocker. Spec Reference: PM Pack `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`. Files to create/modify: `codecov.yml`. Implementation Details: Add Codecov configuration requiring project and patch status coverage targets at 90%. Use `coverage: status: project: default: target: 90%` and `patch: default: target: 90%`. Set reasonable threshold to 0% or at most 1% only if initial Codecov noise requires it; the operator requested at least 90% coverage and Codecov must be a blocker, so do not weaken the target. Include comments explaining that Codecov status must be required in branch protection after the first run creates the status check names. Required Tests/Validation: (1) Config is valid YAML. (2) Targets are 90%. DOD: Codecov is configured to block below 90% once connected.

TASK A4 — ADD / UPDATE COVERAGE CONFIG IN PYPROJECT
Story/Epic Reference: SCRUM-247 / CI parity. Spec Reference: PM Pack `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`. Files to modify: `pyproject.toml`. Implementation Details: Add `[tool.coverage.run]` and `[tool.coverage.report]` sections if absent. Source should be `src`. Omit generated/cache paths, tests, `__pycache__`, and any local runtime data. Set `show_missing = true`, `skip_empty = true`, and `fail_under = 90` where supported. Confirm `pytest-cov` already exists in dev dependencies; if not, add it. Do not remove existing dependency constraints. Required Tests/Validation: (1) `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90` runs locally in the Cursor environment. (2) `coverage.xml` is generated. DOD: Local and CI coverage commands use the same coverage standard.

TASK A5 — ADD PR TEMPLATE WITH CODEX / CHECKS / CODECOV TABLES
Story/Epic Reference: SCRUM-247 / PR governance. Spec Reference: PM Pack `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md` and `PR_CHECKS_CODECOV_PROTOCOL.md`. Files to create/modify: `.github/pull_request_template.md`. Implementation Details: Add a PR template that makes it impossible to omit Codex and checks evidence. Required sections: Summary, Jira Keys, Changed Areas, Validation Commands, Codecov Status, Codex Review Disposition Table, Branch Policy, Merge Readiness Checklist. The Codex table must have columns: Thread/Comment, File, Disposition, Fix Commit/Test, Resolution Status. Include checklist items requiring all Codex review threads to be replied to and resolved, GitHub Actions to pass, Codecov project/patch >=90%, no direct main push, and no runtime artifacts. Required Tests/Validation: (1) Template includes all required sections. (2) Template names PR target as `develop` for cycle PRs. DOD: Future PRs force clear evidence.

TASK A6 — ADD BRANCH PROTECTION / DEFAULT BRANCH RUNBOOK
Story/Epic Reference: SCRUM-247 / branch policy. Spec Reference: PM Pack `05_github_protocol/BRANCH_WORKFLOW.md`, `MERGE_PROTOCOL.md`, and `PR_CHECKS_CODECOV_PROTOCOL.md`. Files to create/modify: `docs/BRANCH_PROTECTION_AND_REQUIRED_CHECKS.md`. Implementation Details: Create a clear runbook for configuring GitHub branch protection. Include the correct default branch policy: default branch should be `develop` during active development, not a cycle branch. Include required checks once the CI workflow first runs: Ruff, Mypy, tests/coverage, smoke gates, Codecov project, Codecov patch. Include release-only `main` policy and develop integration policy. Include `gh` CLI examples if authenticated: `gh repo edit KevinSGarrett/Fiverr --default-branch develop` and a note that branch protection might require GitHub UI or REST API if the connector/agent lacks permission. Do not claim branch protection was set unless you verify it. Required Tests/Validation: (1) Runbook is accurate and does not claim completed settings without evidence. (2) It clearly states merge blockers. DOD: Agent D can use this runbook for final steward verification.

TASK A7 — VALIDATION AND HANDOFF
Files to create/modify: `docs/cycle_reports/CYCLE_005_AGENT_A.md`. Implementation Details: Run targeted validation for files you own. If dependencies are installed, run `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`, `python -m ruff check .`, `python -m mypy src`, `python run.py config-check`, `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle005.db`, and `python run.py phase2-smoke`. If any command fails because the new coverage threshold exposes low coverage, do not hide it; document the modules below threshold for Agents C/D to address. Required Tests/Validation: Commands above or explicit blocker report. DOD: Agent A handoff tells Agent B/C/D exactly whether CI config is ready and whether coverage is currently passing.

FINAL VALIDATION COMMANDS
Run:
- `python -m ruff check .github codecov.yml pyproject.toml docs`
- `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
- `python -m mypy src`
- `python run.py config-check`
- `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle005.db`
- `python run.py phase2-smoke`

COMMIT INSTRUCTIONS
Commit only assigned files:
`git add .github/workflows/ci.yml .github/pull_request_template.md codecov.yml pyproject.toml docs/BRANCH_PROTECTION_AND_REQUIRED_CHECKS.md docs/CYCLE_005_GITHUB_GOVERNANCE_REPORT.md docs/cycle_reports/CYCLE_005_AGENT_A.md && git commit -m "ci(github): add required pr checks and codecov gate [Agent A]"`
```

## Agent B Prompt — Fix Live Codex Findings in Collection Code

```text
PROJECT CONTEXT
Project: Fiverr Research System. Repository path: C:\Fiverr\Fiverr. Active PR: PR #3. Cycle 005 is a governance and PR-fix cycle. PM reviewed live Codex feedback on PR #3 and determined both Codex comments are legitimate. Your job is to fix the two code-level Codex findings, add regression tests, and prepare clear disposition evidence for Agent D to post back to the PR review threads.

YOUR ROLE
You are Agent B — Collection Engineer. You own `src/collection/`, collection-related CLI/orchestrator integration where explicitly assigned, and collection tests. For this cycle, you may modify `src/orchestrator.py` only for the Codex-reported dry-run sample-size bug. You may modify `src/collection/gig_detail.py`, and if you choose to centralize parsing helpers, you may add `src/collection/html_text.py` or a similarly named helper under `src/collection/`. You may modify `tests/unit/test_cli.py`, `tests/unit/test_collection.py`, and collection fixtures under `tests/fixtures/collection/`. Do not modify GitHub workflow files, Codecov config, pyproject, analysis modules, LLM modules, dashboard/report modules, or PM docs.

GIT INSTRUCTIONS
Work after Agent A commits. Remain on the same branch selected by Agent A: either direct PR #3 remediation on `cycle/004/integration` or new `cycle/005/integration`. Do not push. Do not merge. Commit message: `fix(collection): resolve codex dry-run and gig detail feedback [Agent B]`.

TASK B1 — FIX CODEX ISSUE 1: NON-POSITIVE SAMPLE SIZE BREAKS UNCAPPED DRY RUN
Story/Epic Reference: SCRUM-247 plus PR #3 Codex thread on `src/orchestrator.py`. Spec Reference: PM Pack `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md`; collection dry-run behavior from current code. Files to modify: `src/orchestrator.py`, `tests/unit/test_cli.py` or a focused collection/CLI test. Implementation Details: Current code sets `selected_seeds = trimmed_seeds` when `sample_size <= 0`, but still forwards `max_candidates=sample_size` downstream. `src.collection.keyword_expansion.expand_keywords()` rejects `max_candidates <= 0`, so the intended “use all records” branch can fail. Fix this by forwarding a positive max_candidates value when sample_size is non-positive. Preferred behavior: if sample_size > 0, keep the current cap; if sample_size <= 0, compute a safe positive cap from the number of selected seeds and configured modifiers, or pass a documented default such as `max(50, len(selected_seeds) * 10)`. Do not silently change sample-size semantics for positive values. Required Tests: (1) CLI or orchestrator dry-run with `--sample-size 0` succeeds against a fixture with usable seeds. (2) CLI or orchestrator dry-run with a negative sample size either uses all seeds safely or is rejected early with a clear validation error; choose one behavior and document it. (3) Existing positive sample-size tests still pass. DOD: Codex thread can be dispositioned `VALID_FIXED` with regression test evidence.

TASK B2 — FIX CODEX ISSUE 2: DATA-TESTID TEXT EXTRACTION TRUNCATES NESTED MARKUP
Story/Epic Reference: SCRUM-247 plus PR #3 Codex thread on `src/collection/gig_detail.py`. Spec Reference: PM Pack `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md`; collection parser safety requirements. Files to modify/create: `src/collection/gig_detail.py`, optional `src/collection/html_text.py`, `tests/unit/test_collection.py`, optional fixture update under `tests/fixtures/collection/`. Implementation Details: Current `_extract_text()` uses a regex ending with `</[^>]+>`, which can stop at the first child closing tag instead of the matching parent closing tag. Replace this with a safer parser. Preferred implementation: use Python standard library `html.parser.HTMLParser` to collect text inside the element whose `data-testid` equals the requested value, tracking element depth so nested tags are included until the matched element closes. If you choose a regex fallback, it must at least capture the opening tag name and match the same closing tag with a named backreference, but parser-based extraction is preferred. Required Tests: (1) nested markup such as `<div data-testid="gig-description"><span>Fast</span><strong> delivery</strong></div>` returns `Fast delivery`, not only `Fast`. (2) Existing simple title/package extraction still works. (3) Missing data-testid still returns None. DOD: Codex thread can be dispositioned `VALID_FIXED` with regression test evidence.

TASK B3 — CONSIDER SHARED EXTRACTION FOR SELLER PROFILE WITHOUT OVER-SCOPING
Story/Epic Reference: Epic 02 collection parser stability. Files possibly modified: `src/collection/seller_profile.py`, only if you introduce a shared helper. Implementation Details: `seller_profile.py` currently has a similar `_extract_text()` regex. If your safe parser helper can be reused with minimal risk, update seller profile extraction too. If this would make the PR too broad, leave seller profile unchanged and document a follow-up Jira candidate for similar hardening. Required Tests: If modified, add a seller profile nested-markup test. If not modified, document why in `docs/cycle_reports/CYCLE_005_AGENT_B.md`. DOD: No unnecessary scope creep, but known parallel risk is not hidden.

TASK B4 — ADD CODEX DISPOSITION EVIDENCE FILE
Story/Epic Reference: SCRUM-247 / Codex disposition. Files to create/modify: `docs/cycle_reports/CYCLE_005_AGENT_B.md`. Implementation Details: Create a report section for each Codex item: thread file/line, disposition `VALID_FIXED`, root cause, files changed, tests added, commands run, and commit hash placeholder if not known yet. Agent D will use this report to reply to Codex threads and resolve them. Required Tests: Report exists and maps both Codex comments exactly. DOD: Agent D can copy evidence from your report into PR replies.

TASK B5 — TARGETED REGRESSION TEST RUN
Files modified: none beyond tests. Implementation Details: Run collection/CLI targeted tests first: `python -m pytest tests/unit/test_collection.py tests/unit/test_cli.py -q`. Then run broader smoke if dependencies are present: `python run.py phase2-smoke`. Required Tests: Targeted tests pass. If the new global coverage gate fails because of unrelated coverage, report that separately but do not skip your targeted regression evidence. DOD: Handoff reports targeted results clearly.

TASK B6 — FULL LOCAL QUALITY GATE
Implementation Details: Run `python -m ruff check src/collection src/orchestrator.py tests/unit/test_collection.py tests/unit/test_cli.py` and `python -m mypy src/collection src/orchestrator.py`. If Mypy includes unrelated existing errors outside your files, restrict to assigned paths and document. Required Tests: Ruff and Mypy pass for touched paths. DOD: Your collection fixes are clean.

TASK B7 — HANDOFF FOR AGENT D
Files to modify: `docs/cycle_reports/CYCLE_005_AGENT_B.md`. Implementation Details: Include exact PR reply text draft for both Codex threads using the required format from the PM Pack protocol. Include whether each thread should be resolved after push/checks. Required Tests: Handoff contains `Codex disposition: VALID_FIXED` for both. DOD: Agent D can complete GitHub thread replies/resolution without guessing.

COMMIT INSTRUCTIONS
`git add src/orchestrator.py src/collection tests/unit/test_collection.py tests/unit/test_cli.py docs/cycle_reports/CYCLE_005_AGENT_B.md && git commit -m "fix(collection): resolve codex dry-run and gig detail feedback [Agent B]"`
```

## Agent C Prompt — Coverage Hardening and CI Parity for Analysis/LLM Paths

```text
PROJECT CONTEXT
Project: Fiverr Research System. Repository path: C:\Fiverr\Fiverr. Cycle 005 installs real PR checks and Codecov. Once Agent A adds `--cov-fail-under=90`, the project may fail if coverage is below target. Your job is to strengthen tests for analysis and LLM paths, improve coverage without fake tests, and ensure CI parity. Do not treat coverage as a vanity metric; tests must verify meaningful behavior and edge cases.

YOUR ROLE
You are Agent C — Analysis, Scoring, LLM, and Coverage Engineer. You may modify `src/analysis/`, `src/llm/`, `tests/unit/test_analysis.py`, `tests/unit/test_llm.py`, and analysis fixtures under `tests/fixtures/analysis/`. You may create `docs/cycle_reports/CYCLE_005_AGENT_C.md`. Do not modify collection files fixed by Agent B, GitHub workflow files owned by Agent A, or dashboard/report files owned by Agent D.

GIT INSTRUCTIONS
Work after Agent B commits. Remain on the branch selected by Agent A. Do not push. Do not merge. Commit message: `test(analysis-llm): harden coverage for ci gate [Agent C]`.

TASK C1 — RUN COVERAGE BASELINE AND IDENTIFY GAPS
Story/Epic Reference: SCRUM-247 / Codecov blocker. Spec Reference: PM Pack `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`. Files to create/modify: `docs/cycle_reports/CYCLE_005_AGENT_C.md`. Implementation Details: Run `python -m pytest -q --cov=src --cov-report=term-missing --cov-report=xml --cov-fail-under=90`. If it passes, record project coverage and high-risk low-covered modules. If it fails, identify the lowest coverage modules in `src/analysis` and `src/llm` first. Required Tests: Coverage command attempted and result documented. DOD: Agent D has concrete coverage evidence.

TASK C2 — ADD ANALYSIS ORCHESTRATOR EDGE-CASE TESTS
Files to modify: `tests/unit/test_analysis.py`; optionally `tests/fixtures/analysis/*.json`. Implementation Details: Add tests around `src.analysis.orchestrator` for complete payloads, sparse payloads, missing optional review data, empty competitor/seller lists, and deterministic stage ordering. These tests should verify returned status, warnings, output keys, and no crashes on sparse input. Required Tests: At least 4 new meaningful tests. DOD: Analysis orchestration coverage improves with real behavior checks.

TASK C3 — ADD SELLER / SATURATION / REVIEW / INTENT EDGE TESTS
Files to modify: `tests/unit/test_analysis.py`. Implementation Details: Add focused tests for seller strength, saturation model, review analysis, and intent classification modules. Cover missing values, low-confidence values, and representative successful values. Do not merely import modules; assert computed scores/categories/warnings. Required Tests: At least one meaningful test per module listed. DOD: Tests verify actual analytical output and edge handling.

TASK C4 — ADD LLM PROVIDER / RETRY / VALIDATION TESTS
Files to modify: `tests/unit/test_llm.py`. Implementation Details: Add tests for mocked provider success, provider malformed response, validation retry prompt, cost metadata, cache hit/miss metadata, and no API key leakage. Do not use live OpenAI calls. Required Tests: At least 5 new LLM tests with injected fake provider/cache. DOD: LLM paths become CI-safe and coverage-useful.

TASK C5 — CHECK CACHING AND METADATA FOR CODECOV-RELEVANT BRANCHES
Files to modify: `tests/unit/test_llm.py` and possibly `src/llm/cache.py` only if a real bug is discovered. Implementation Details: Exercise cache TTL expiration, deterministic cache key, cache hit usage event metadata, and invalid cache record behavior. If a real bug is discovered, fix it minimally and document. Required Tests: Cache tests pass without network/filesystem pollution. DOD: LLM cache coverage is stable and useful.

TASK C6 — ENSURE NO TESTS REQUIRE SECRETS OR NETWORK
Files to modify: tests only if needed. Implementation Details: Search tests for live network/API assumptions. Any LLM/OpenAI behavior must be mocked. Add or update tests to verify no real `OPENAI_API_KEY` is required. Required Tests: `unset OPENAI_API_KEY` or equivalent does not break your targeted tests. DOD: CI can run in GitHub Actions without secrets except Codecov token if configured.

TASK C7 — FULL TARGETED VALIDATION AND HANDOFF
Files to create/modify: `docs/cycle_reports/CYCLE_005_AGENT_C.md`. Implementation Details: Run `python -m pytest tests/unit/test_analysis.py tests/unit/test_llm.py -q`, then run the full coverage command if dependencies and time allow. Record exact results, coverage percentage, and any remaining modules below target. Required Tests: Targeted tests pass. DOD: Agent D has evidence for PR template and Codecov expectation.

COMMIT INSTRUCTIONS
`git add src/analysis src/llm tests/unit/test_analysis.py tests/unit/test_llm.py tests/fixtures/analysis docs/cycle_reports/CYCLE_005_AGENT_C.md && git commit -m "test(analysis-llm): harden coverage for ci gate [Agent C]"`
```

## Agent D Prompt — Documentation, Codex Thread Resolution, and Final GitHub Stewardship

```text
PROJECT CONTEXT
Project: Fiverr Research System. Repository path: C:\Fiverr\Fiverr. Cycle 005 is a governance/CI recovery cycle. PR #3 currently has two Codex comments and missing GitHub PR checks. Agents A/B/C will add CI/Codecov, fix Codex code issues, and add coverage tests. You are the final Integration/GitHub Steward and must not merge until the gates pass.

YOUR ROLE
You are Agent D — Dashboard/Presentation Engineer and Final Integration/GitHub Steward. You may modify documentation under `docs/`, `README.md`, dashboard/report docs if needed, and `docs/cycle_reports/CYCLE_005_AGENT_D.md`. You own final validation, PR update, Codex review replies/resolution, Codecov/check verification, and merge-readiness reporting. You may not push to `main`. You may not resolve Codex threads until Agent B fixes are pushed and checks pass, unless PM explicitly approves a non-fix disposition.

GIT INSTRUCTIONS
Work after Agent C commits. Remain on the branch selected by Agent A. Do not merge to `develop` unless all gates pass and PM/operator policy authorizes the merge. Do not push to `main`. Commit message for your docs/steward updates: `docs(governance): document codex and pr check process [Agent D]`.

TASK D1 — DOCUMENT THE NEW CODEX REVIEW PROCESS IN REPO DOCS
Story/Epic Reference: SCRUM-247 / Codex protocol. Spec Reference: PM Pack `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md`. Files to create/modify: `docs/CODEX_REVIEW_DISPOSITION.md`, possibly `README.md`. Implementation Details: Create repo-facing documentation explaining how Codex comments are handled. Include disposition categories, required reply format, when to fix, when to ignore, when to defer, and when a PR is blocked. Mention that Codex comments are guidance, but every thread must be reviewed and resolved with evidence. Required Tests/Validation: Docs include every required category: `VALID_FIXED`, `VALID_DEFERRED_BLOCKER`, `VALID_DEFERRED_NONBLOCKING`, `NOT_APPLICABLE`, `FALSE_POSITIVE`, and `DUPLICATE`. DOD: Future Cursor stewards can follow the doc without PM re-explaining.

TASK D2 — DOCUMENT REQUIRED PR CHECKS AND CODECOV BLOCKER
Story/Epic Reference: SCRUM-247 / PR checks. Spec Reference: PM Pack `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`. Files to create/modify: `docs/PR_CHECKS_AND_CODECOV.md`, possibly `README.md`. Implementation Details: Document that every PR must have GitHub Actions checks and Codecov project/patch coverage at least 90%. Include the required local parity commands and the rule that missing checks are blockers. Required Tests/Validation: Docs name all commands and 90% threshold. DOD: Repo docs match PM Pack governance.

TASK D3 — REVIEW AGENT A/B/C REPORTS AND BUILD FINAL CYCLE REPORT
Files to create/modify: `docs/cycle_reports/CYCLE_005_AGENT_D.md`. Implementation Details: Read Agent A/B/C reports. Summarize whether CI workflow exists, Codecov config exists, PR template exists, Codex fixes are implemented, targeted tests pass, and coverage passes. Include a merge-readiness table with PASS/BLOCKED/UNKNOWN for each gate. Required Tests/Validation: Report does not claim green checks until GitHub confirms them. DOD: PM can review the final report to decide if PR #3 is merge-ready.

TASK D4 — REPLY TO EACH CODEX THREAD WITH FORMAL DISPOSITION
Story/Epic Reference: SCRUM-247 / Codex disposition. Tool/Execution: Use GitHub PR UI or `gh` CLI if available. Implementation Details: For each Codex review thread, reply using the PM Pack required format. For the `src/orchestrator.py` sample-size issue, use Agent B's evidence and classify as `VALID_FIXED` if fixed. For the `src/collection/gig_detail.py` nested markup issue, use Agent B's evidence and classify as `VALID_FIXED` if fixed. If Agent B did not fix either issue, do not resolve that thread and mark PR blocked. Required Tests/Validation: Replies are visible in PR #3. DOD: Every Codex thread has a disposition reply.

TASK D5 — RESOLVE CODEX THREADS ONLY AFTER FIXES AND CHECKS
Story/Epic Reference: SCRUM-247 / merge gate. Tool/Execution: GitHub PR UI or API through available tooling. Implementation Details: After Agent B fixes are committed and pushed, and after checks pass, resolve Codex review threads. If GitHub does not allow resolution via CLI or current account, report the exact blocker and leave the thread unresolved rather than pretending it is resolved. Required Tests/Validation: GitHub PR review threads show resolved=true, or report exact reason. DOD: No silent unresolved threads.

TASK D6 — FINAL VALIDATION / PUSH / PR UPDATE
Story/Epic Reference: SCRUM-247 / Integration steward. Implementation Details: Run final local parity commands: `git status --short`, `git log --oneline --decorate -12`, `python -m ruff check .`, `python -m mypy src`, `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`, `python run.py config-check`, `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle005.db`, and `python run.py phase2-smoke`. Remove generated runtime DBs before commit/push. Push the branch. If updating PR #3, update the PR body with Codex dispositions and check/Codecov status. If a new PR is required, create it targeting `develop` with the PR template. Required Tests/Validation: Push succeeds; PR body is updated; checks trigger. DOD: PR has real checks running.

TASK D7 — VERIFY GITHUB ACTIONS AND CODECOV STATUS
Implementation Details: After push, inspect the PR checks. Confirm GitHub Actions ran. Confirm Codecov status appears. If checks are pending, say pending. If failed, report failure and do not merge. If missing, report blocker and do not merge. Required Tests/Validation: PR check list captured in `docs/cycle_reports/CYCLE_005_AGENT_D.md`. DOD: Merge readiness is evidence-based.

TASK D8 — MERGE POLICY / NO MAIN CONFIRMATION
Implementation Details: Confirm no direct `main` checkout, push, or merge occurred. Confirm PR target is `develop`. Confirm repo default branch status if Agent A attempted correction. If all gates pass and PM/operator policy authorizes merge, use squash merge only. If not authorized or gates are incomplete, leave PR open and report. Required Tests/Validation: Report includes `main untouched: yes/no`. DOD: No accidental production/main changes.

COMMIT INSTRUCTIONS
`git add docs README.md && git commit -m "docs(governance): document codex and pr check process [Agent D]"`

FINAL STEWARD REPORT MUST INCLUDE
- Branch used.
- PR number and URL.
- Codex disposition table.
- Thread resolution status.
- GitHub Actions check status.
- Codecov status and coverage percentage.
- Full validation command results.
- Whether PR is merge-ready.
- Whether `main` was untouched.
```

---

## 6. GITHUB / CODEX STRATEGY GOING FORWARD

### Permanent Rule

Every PR must have a Codex disposition table. Codex comments are neither blindly accepted nor blindly ignored. The Integration/GitHub Steward reviews, classifies, fixes or rejects with evidence, replies, and resolves.

### Required PR Checks

Every PR must have:

```text
Ruff
Mypy
Pytest + coverage XML
Coverage fail-under 90
Config check
Foundation gate
Phase 2 smoke
Codecov project coverage >=90
Codecov patch coverage >=90
Codex threads resolved
```

### Merge Blockers

```text
No GitHub Actions run = blocked
No Codecov status = blocked
Coverage below 90 = blocked
Unresolved Codex thread = blocked
Codex thread resolved without disposition = blocked
PR targeting main outside release = blocked
Default branch set to a cycle branch = governance blocker
```

---

## 7. STATE UPDATE

Updated PM Pack state now records:

- Cycle 005 as active.
- SCRUM-247 as active governance blocker.
- PR #3 as open and blocked.
- Missing GitHub checks as a blocker.
- Missing Codecov as a blocker.
- Two unresolved Codex comments as blockers.
- Default branch currently reported incorrectly as `cycle/002/integration`.
- New permanent Codex/Codecov PM protocols.

---

## 8. NEXT CYCLE PREVIEW

Cycle 006 should be one of two paths:

### If Cycle 005 passes

- Review CI/Codecov evidence.
- Confirm Codex threads resolved.
- Move SCRUM-247 to Done or In Review depending on branch protection status.
- Resume Phase 2 feature expansion.

### If Cycle 005 fails or checks are blocked

- Keep PR open.
- Create/assign rework prompts focused only on failed checks, missing Codecov, unresolved Codex comments, or branch protection blockers.
- Do not resume feature expansion.

---

END OF CYCLE 005
