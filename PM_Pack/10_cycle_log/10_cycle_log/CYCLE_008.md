============================================================
CYCLE 008 — 2026-05-14
Focus: Jira story-mapping correction + Phase 2 Collection/Analysis/Dashboard continuation
Branch: cycle/008/integration
Base: develop after merged PR #6
GitHub: https://github.com/KevinSGarrett/Fiverr
PR baseline reviewed: PR #6 merged into develop
============================================================

## 1. REVIEW OF PRIOR AGENT WORK

### Source inputs reviewed

- Uploaded repository archive: `Fiverr_007.zip`
- Uploaded PM Pack: `PM_Pack_Cycle_007_READY (1).zip`
- Live GitHub repository: `KevinSGarrett/Fiverr`
- Live GitHub PR history and PR #6 review threads
- Jira board through JQL queries across governance, Collection, Analysis, Dashboard, Reporting, Export, and cycle-related tickets

### GitHub / PR review

Live GitHub confirms PR #6, `feat(cycle-007): resume phase 2 after codex and coverage gate closure`, is closed and merged into `develop`. PR #6 targeted `develop`, came from `cycle/007/integration`, merged at `2026-05-14T22:53:30Z`, and used merge commit `686c25ecdf995fc93118f98ae610649fc5ef51f3`.

PR #6 review-thread review confirmed two Codex threads existed and both were resolved:

1. `src/collection/orchestrator.py` — `records_written` undercounted stage 7/8 metadata before final fix. Disposition path: `VALID_DEFERRED_BLOCKER` then `VALID_FIXED`, fixed by commit `8feb66f`.
2. `src/analysis/orchestrator.py` — demand readiness was overstated from raw keywords when analysis stages failed. Disposition path: `VALID_DEFERRED_BLOCKER` then `VALID_FIXED`, fixed by commit `8feb66f`.

Agent D’s Cycle 007 report records final local parity evidence:

- `python -m ruff check .` — pass
- `python -m mypy src` — pass, 76 source files
- `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90` — pass, 292 tests, 93.30% coverage
- `python run.py config-check` — pass
- `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle007.db` — pass
- `python run.py phase2-smoke` — pass

### Jira management issue found

The operator’s concern was valid. Recent PM cycles correctly tracked governance blockers, but Jira management drifted because product story tickets touched by merged code were not always searched, transitioned, and commented. The same governance items were updated repeatedly while story tickets such as Collection S2.14, Collection S2.16, Analysis S3.8, Analysis S3.7, Dashboard S9.1, Dashboard S9.2, and Dashboard S9.14 lagged behind the actual merged code state.

Root cause:

- Cycle planning and review over-weighted governance blockers after failures around prompt quality, GitHub stewardship, CI, Codecov, and Codex reviews.
- The PM process did not enforce a mandatory “changed files → Jira story tickets” mapping before final Jira update.
- The prior Jira update table listed governance tickets but did not require product tickets for every changed file group.

Correction applied in Cycle 008:

- Created Jira task `SCRUM-250 — [PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates`.
- Added PM Pack protocol `04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md`.
- Added corrective rule file `01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_008.md`.
- Transitioned/commented missed product tickets that mapped to Cycle 007 merged code.
- Cycle 008 prompt now requires every agent to list Jira story keys in their final report and requires Agent D to audit changed files against Jira before PR handoff.

### Prior-cycle confidence scores

| Agent | Confidence | Rationale |
|---|---:|---|
| Agent A | 93 | Correctly gated PR #5, merged under checks, created Cycle 007 branch, audited default branch/protection, documented governance gaps. |
| Agent B | 88 | Strong fixture-backed collection hardening and tests; targeted collection-only coverage was below 90 due broader package modules, but full-repo coverage passed. |
| Agent C | 92 | Analysis dry-run reliability, scoring-readiness, nullish intent fallback, and no-live-LLM assurance were well tested. |
| Agent D | 94 | Final GitHub stewardship was strong: Codex threads resolved, PR #6 created, checks and coverage green, branch policy preserved. |

Cycle confidence: 91/100. Main caveat: Jira mapping was incomplete until this Cycle 008 correction pass.

---

## 2. JIRA BOARD UPDATE

### Confirmed issue

The Jira board was not being fully managed across all touched stories. Governance items were handled, but product work was not consistently reflected on story tickets.

### Jira updates completed in this Cycle 008 pass

| Jira Key | Area | Action | Status After Update | Rationale |
|---|---|---|---|---|
| SCRUM-247 | PM/GitHub governance | Transitioned | Done | Codex review disposition protocol, PR checks, Codecov workflows, and PM Pack protocol were implemented/merged. |
| SCRUM-248 | Cycle 006 governance/fix | Transitioned | Done | PR #5 fixed intent fallback and Codecov project-gate visibility; PR #6 continued with clean baseline. |
| SCRUM-249 | Cycle 007 governance | Transitioned + comment | Done | PR #5 closure and Cycle 007 PR #6 merge are complete; Codex threads resolved and checks green. |
| SCRUM-250 | PM/Jira correction | Created + transition + comment | In Progress | New permanent correction ticket for cycle-to-story Jira mapping drift. |
| SCRUM-154 | Collection S2.14 Stage Orchestration Wiring | Transitioned + comment | In Progress | Cycle 007 touched collection orchestration/dry-run behavior. Partial story progress only. |
| SCRUM-156 | Collection S2.16 End-to-End Collection Smoke Test | Transitioned + comment | In Progress | Cycle 007 added deterministic fixture-backed collection smoke coverage. Partial story progress only. |
| SCRUM-149 | Collection S2.9 Gig Detail Collection | Transitioned + comment | In Progress | Cycle 007 touched nested `data-testid` extraction and gig-detail-adjacent fixture coverage. Partial story progress only. |
| SCRUM-164 | Analysis S3.8 Stage Wiring | Transitioned + comment | In Progress | Cycle 007 touched analysis stage metadata, partial-failure behavior, and scoring-readiness summaries. Partial story progress only. |
| SCRUM-163 | Analysis S3.7 Intent Classification | Transitioned + comment | In Progress | Cycle 006/007 touched null/blank/literal-None intent fallback and classification-adjacent behavior. Partial story progress only. |
| SCRUM-212 | Dashboard S9.1 Design System Implementation | Transitioned + comment | In Progress | Cycle 007 touched dashboard presentation/status categorization. Partial story progress only. |
| SCRUM-213 | Dashboard S9.2 Reusable Component Library | Transitioned + comment | In Progress | Cycle 007 touched dashboard/report/export component contracts. Partial story progress only. |
| SCRUM-228 | Dashboard S9.14 App Entry Point | Transitioned + comment | In Progress | Cycle 007 touched `src/dashboard/app.py`, dashboard app/presentation behavior, and tests. Partial story progress only. |

### Jira updates queued for Cycle 008 Agent A/D verification

Because the current chat pass prioritized the most directly touched tickets, Cycle 008 agents must verify whether these should also be moved/commented after checking changed files and story DOD mapping:

| Jira Key | Reason to audit |
|---|---|
| SCRUM-226 — S9.12 Export System | Cycle 007 touched `src/exports/placeholders.py` and export tests. |
| SCRUM-219 — S9.7 Run History | Cycle 007 surfaced run/check/status categories in reports; verify exact scope match before transition. |
| SCRUM-225 — S9.11 Query Layer | If Cycle 008 adds dashboard query contracts, update this ticket. |
| SCRUM-157 — S3.1 Keyword Clustering | If readiness work begins to require clustering outputs beyond placeholders, update this ticket. |

Permanent Jira rule: no cycle is complete until the changed-file list is mapped to exact Jira stories and every touched ticket is commented or explicitly marked “not updated with reason.”

---

## 3. CYCLE 008 PLAN

### Goal

Cycle 008 resumes Phase 2 development from a clean merged `develop`, while enforcing the corrected Jira management protocol. This cycle should not be treated as pure governance; it should advance Collection, Analysis, and Dashboard/Reporting while preserving Codex/CI/Codecov gates.

### Branch and PR target

```text
Branch: cycle/008/integration
Base: develop
PR target: develop
Main: untouched / release-only
```

### Agent allocation

| Agent | Focus | Jira Keys |
|---|---|---|
| Agent A | Jira mapping protocol, branch setup, governance docs, final ticket audit scaffolding | SCRUM-250, SCRUM-246, SCRUM-247, SCRUM-248, SCRUM-249 |
| Agent B | Collection stage orchestration, smoke-test evidence, fixture-backed gig-detail path | SCRUM-154, SCRUM-156, SCRUM-149 |
| Agent C | Analysis stage wiring, intent readiness, partial-failure scoring-readiness contracts | SCRUM-164, SCRUM-163 |
| Agent D | Dashboard/report/export visibility, Jira mapping table, final GitHub steward duties | SCRUM-212, SCRUM-213, SCRUM-228, SCRUM-226 |

---

## 4. AGENT PROMPTS

### Agent A Prompt — Infrastructure / Jira Mapping / Governance Steward

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local repository path: C:\Fiverr\Fiverr. You are working in Cycle 008. The prior PR, PR #6, has been merged into develop. Current workflow requires one cycle branch per cycle and one PR into develop. Main is release-only and must not be touched. This cycle is a Jira-management correction and Phase 2 continuation cycle. The most important process correction is that PM/Jira updates may no longer focus only on governance tickets; every cycle must map changed files and agent tasks to exact Jira product stories.

YOUR ROLE
You are Agent A — Infrastructure, Governance, and Jira Mapping Steward. You own branch setup, governance docs, PM/Jira protocol implementation inside the repo docs, and cycle-reporting scaffolding. You do not own implementation changes in src/collection, src/analysis, src/dashboard, src/reports, or src/exports except for reading them to create mapping docs. You may edit docs/, .github/ only if necessary, and docs/cycle_reports/.

GIT INSTRUCTIONS
Start from updated develop only:
1. cd C:\Fiverr\Fiverr
2. git fetch origin --prune
3. git checkout develop
4. git pull --ff-only origin develop
5. git checkout -b cycle/008/integration
6. Verify ancestry: git merge-base --is-ancestor origin/develop HEAD
7. Push branch for downstream agents only after you have made your committed governance changes: git push -u origin cycle/008/integration
Do not push to main. Do not merge any PR. Do not modify product implementation code.

TASKS FOR THIS CYCLE

Task A1 — Verify clean baseline after PR #6 merge.
Jira: SCRUM-250, SCRUM-249.
Files to touch: docs/cycle_reports/CYCLE_008_AGENT_A.md.
Implementation detail: Verify the repo default branch is develop, PR #6 is merged, no PRs are currently open, and cycle/008/integration starts from latest origin/develop. Record the live command outputs, branch SHA, and ancestry evidence. Include a section named “Cycle 008 Baseline Verification.” If PR #6 is not merged or develop is not current, stop and write a blocker report instead of continuing.
Tests/validation: git status --short --branch; git log --oneline --decorate -12; gh pr list --repo KevinSGarrett/Fiverr --state open; gh repo view KevinSGarrett/Fiverr --json defaultBranchRef.
Definition of done: baseline is verified and documented.

Task A2 — Add repo-side Jira cycle mapping guide.
Jira: SCRUM-250.
Files to touch: docs/JIRA_CYCLE_STORY_MAPPING.md, docs/cycle_reports/CYCLE_008_AGENT_A.md.
Implementation detail: Create a concise but enforceable repository guide explaining that every cycle must map changed files to product Jira stories. Include path-based mapping rules: src/collection/tests collection docs -> Epic 02; src/analysis/tests analysis -> Epic 03; src/scoring -> Epic 04; src/recommendations -> Epic 05; src/pricing -> Epic 06; src/discovery -> Epic 07; src/playbook -> Epic 08; src/dashboard/src/reports/src/exports -> Epic 09; src/orchestrator/run.py integration -> Epic 10; .github/docs governance -> PM/GitHub/Jira governance tasks. Include a mandatory table template for agents.
Tests/validation: Markdown review, no code execution required for doc only, but run python -m ruff check docs if available.
Definition of done: doc is clear enough for future agents to follow without PM restating it.

Task A3 — Update governance docs to require Jira story mapping before PR readiness.
Jira: SCRUM-250, SCRUM-247.
Files to touch: docs/CYCLE_BRANCH_CHECKLIST.md, docs/BRANCH_PROTECTION_AND_REQUIRED_CHECKS.md, docs/PR_CHECKS_AND_CODECOV.md.
Implementation detail: Add one explicit gate to each relevant doc: the Integration/GitHub Steward must verify the PR body includes a Jira mapping section covering both governance tickets and product-story tickets. A PR is not ready if it only references governance tickets when product files changed. Do not weaken existing Codex/Codecov requirements.
Tests/validation: docs review; run ruff on docs path if accepted by current tooling.
Definition of done: docs now make Jira mapping a merge-readiness gate.

Task A4 — Produce Cycle 008 Jira correction audit table.
Jira: SCRUM-250.
Files to touch: docs/cycle_reports/CYCLE_008_AGENT_A.md.
Implementation detail: Based on the merged PR #6 file list and current cycle plan, list the Jira tickets that were corrected by PM during Cycle 008: SCRUM-154, SCRUM-156, SCRUM-149, SCRUM-164, SCRUM-163, SCRUM-212, SCRUM-213, SCRUM-228, SCRUM-247, SCRUM-248, SCRUM-249, SCRUM-250. Include “status after correction” and “why not Done” for product tickets.
Tests/validation: confirm the table is complete and does not claim Done for partial stories.
Definition of done: report prevents future ambiguity about why the board changed.

Task A5 — Keep CI/Codecov/Codex governance intact.
Jira: SCRUM-247.
Files to touch only if necessary: docs/PR_CHECKS_AND_CODECOV.md.
Implementation detail: Verify `.github/workflows/ci.yml`, `codecov.yml`, and PR template still exist and appear consistent. Do not edit workflow unless broken. Record required checks: CI / Lint, Typecheck, Tests, and Gates; codecov/project; codecov/patch. Record that merge is blocked by unresolved Codex threads.
Tests/validation: inspect files; optionally run python -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90 if environment is ready.
Definition of done: governance remains enforced.

Task A6 — Commit Agent A changes.
Commit message: docs(jira): enforce cycle story mapping protocol [Agent A].
Required final report fields: files touched, commands run, Jira keys mapped, branch SHA, blockers.
```

### Agent B Prompt — Collection Engine Continuation

```text
PROJECT CONTEXT
Project: Fiverr Research System. Work on branch cycle/008/integration after Agent A has pushed the branch. This cycle continues Phase 2 collection work and must use the new Jira mapping rule. The merged Cycle 007 work added fixture-backed dry-run coverage, corrected `records_written` stage summary behavior, and hardened nested `data-testid` extraction. You must keep all collection behavior deterministic and local-only. No live Fiverr scraping, no browser login, no account/session artifacts, and no network calls.

YOUR ROLE
You are Agent B — Collection Engineer. Your owned area is src/collection/, tests/unit/test_collection.py, tests/integration/test_collection_e2e.py, and collection docs. You must not edit analysis, dashboard, reports, exports, PM pack files, CI workflow, or unrelated docs unless needed for collection fixture documentation. Jira keys for this cycle: SCRUM-154, SCRUM-156, SCRUM-149.

GIT INSTRUCTIONS
Start after Agent A has committed and pushed cycle/008/integration. Run git checkout cycle/008/integration && git pull --ff-only origin cycle/008/integration. Do not push until your commit is complete. Do not merge. Do not touch main.

TASKS FOR THIS CYCLE

Task B1 — Strengthen S2.14 collection stage orchestration contract.
Jira: SCRUM-154.
Files: src/collection/orchestrator.py, src/collection/contracts.py, tests/unit/test_collection.py.
Implementation detail: Add explicit invariant validation for stage summaries: stage_counts total must match records_seen/records_written where applicable; stage names must be stable; warning counts must match warnings list length; failed stage summaries must include error_code and failed=True. Preserve existing public APIs. If current contract types need additional optional fields, add them in a backward-compatible way. Do not add live scraping.
Tests: unit tests for summary invariant success, undercount failure, warning-count mismatch, and failed-stage metadata.
DOD: S2.14 partial progress with stronger orchestration correctness.

Task B2 — Expand S2.16 deterministic collection smoke test.
Jira: SCRUM-156.
Files: tests/integration/test_collection_e2e.py, docs/collection_fixture_contract.md.
Implementation detail: Extend fixture smoke coverage to validate keyword expansion, search result placeholder, gig-detail placeholder, seller-profile placeholder, and external-signal placeholder stages using local fixture dictionaries. The goal is not full collection implementation; the goal is a controlled smoke harness that future live/snapshot collection can plug into.
Tests: integration test validates all required stage names exist; test validates no network/browser/session usage.
DOD: controlled fixture smoke evidence is stronger and documented.

Task B3 — Improve S2.9 gig detail fixture extraction boundaries.
Jira: SCRUM-149.
Files: src/collection/gig_detail.py if present, otherwise the current module that owns data-testid extraction; tests/unit/test_collection.py.
Implementation detail: Ensure nested markup extraction preserves text across nested elements without truncating fields and normalizes whitespace deterministically. Add tests for nested div/span/strong markup, empty nodes, duplicate data-testid values, and malformed but recoverable markup.
Tests: fixture extraction unit tests for happy path and malformed path.
DOD: gig-detail fixture extraction is robust enough for future Stage 4 work.

Task B4 — Add checkpoint/pacing evidence object.
Jira: SCRUM-154, SCRUM-156.
Files: src/collection/contracts.py, tests/unit/test_collection.py.
Implementation detail: Add a small immutable or Pydantic-compatible evidence object for checkpoint_path, pacing_decisions, cooldown_applied, retry_count, and fixture_mode. This should be serializable and safe for report/export layers. Do not persist actual browser/session artifacts.
Tests: serialization test and fixture-mode no-sensitive-fields test.
DOD: reporting can consume checkpoint/pacing evidence safely.

Task B5 — Update collection fixture contract doc.
Jira: SCRUM-154, SCRUM-156, SCRUM-149.
Files: docs/collection_fixture_contract.md.
Implementation detail: Add a section mapping fixture fields to Jira stories and source stages. Include a statement that current implementation is fixture-backed partial progress, not full live collection completion.
Tests: doc review only.
DOD: prevents future Jira overclaiming.

Task B6 — Full validation and report.
Files: docs/cycle_reports/CYCLE_008_AGENT_B.md.
Validation commands: python -m ruff check src/collection tests/unit/test_collection.py tests/integration/test_collection_e2e.py; python -m mypy src/collection; python -m pytest tests/unit/test_collection.py tests/integration/test_collection_e2e.py -q; python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90 if feasible.
Commit message: feat(collection): harden stage evidence and fixture smoke mapping [Agent B].
```

### Agent C Prompt — Analysis Engine Continuation

```text
PROJECT CONTEXT
Project: Fiverr Research System. Work on branch cycle/008/integration after Agents A and B have committed. This cycle continues Phase 2 analysis hardening and must use the new Jira mapping rule. Prior merged work fixed intent null fallback, demand readiness overstatement, partial failure metadata, and scoring-readiness snapshots. Your work must remain deterministic, fixture-backed, and local-only. No live LLM calls.

YOUR ROLE
You are Agent C — Analysis and Scoring-Readiness Engineer. Owned areas: src/analysis/, tests/unit/test_analysis.py, analysis docs if necessary. Jira keys for this cycle: SCRUM-164 and SCRUM-163. Do not edit collection, dashboard, reports, exports, CI, or governance docs except your cycle report.

GIT INSTRUCTIONS
Run git checkout cycle/008/integration && git pull --ff-only origin cycle/008/integration after Agent B commits. Do not push to main. Do not merge.

TASKS FOR THIS CYCLE

Task C1 — Strengthen S3.8 stage wiring result contract.
Jira: SCRUM-164.
Files: src/analysis/orchestrator.py, tests/unit/test_analysis.py.
Implementation detail: Add a stable AnalysisRunSummary or equivalent helper that records stage order, successful stages, failed stages, skipped stages, warning_count, missing_field_count, and scoring_readiness. Keep existing public API compatible. Ensure stage ordering is deterministic and documented in tests.
Tests: stage order test; skipped-stage test; failed-stage metadata retention test.
DOD: S3.8 partial progress toward complete analysis stage wiring.

Task C2 — Tighten S3.7 intent keyword and confidence readiness.
Jira: SCRUM-163.
Files: src/analysis/orchestrator.py, tests/unit/test_analysis.py.
Implementation detail: Expand current intent fallback helpers to return both selected keyword and selection_reason. Treat null, blank, literal `None`, literal `null`, and whitespace-only as invalid candidate values. Add confidence metadata for fallback source: explicit intent keyword > top-level keyword_text > first keywords[] entry > source_id.
Tests: all fallback reasons covered; invalid candidates never classify as literal strings.
DOD: intent fallback is explainable and future persistence-ready.

Task C3 — Add analysis-to-collection evidence linking.
Jira: SCRUM-164.
Files: src/analysis/orchestrator.py, tests/unit/test_analysis.py.
Implementation detail: Add optional collection_evidence input support that can record source stage names, fixture_mode, records_seen, records_written, and warnings into analysis run metadata. This should not depend on importing collection modules directly unless already safe. Prefer duck-typed dictionaries to avoid circular dependencies.
Tests: collection evidence accepted; malformed evidence degrades with warning; no circular import.
DOD: analysis output can trace upstream collection fixture/run context.

Task C4 — Prevent readiness overclaiming.
Jira: SCRUM-164, SCRUM-163.
Files: tests/unit/test_analysis.py.
Implementation detail: Add regression tests proving readiness booleans are false when the relevant producing stage failed or was skipped. Keep the prior Codex fix intact.
Tests: failed intent stage -> no demand readiness; failed keyword clustering -> no demand readiness unless intent succeeded; sparse payload -> expected false readiness.
DOD: no silent overclaiming.

Task C5 — Add analysis documentation note.
Files: docs/cycle_reports/CYCLE_008_AGENT_C.md.
Implementation detail: Document what is complete, what remains partial, and which Jira stories are impacted. Explicitly state that S3.7/S3.8 remain In Progress, not Done.
Validation: ruff/mypy/pytest for analysis.
Commit message: feat(analysis): harden stage readiness and intent evidence [Agent C].
```

### Agent D Prompt — Dashboard/Reporting/Export + Final GitHub Steward

```text
PROJECT CONTEXT
Project: Fiverr Research System. Work on cycle/008/integration after Agents A/B/C have committed. This cycle must enforce both GitHub governance and corrected Jira management. PR #6 is merged into develop, and there should be no open PRs at cycle start. Your final PR must target develop and must include a Jira mapping section that covers both governance tickets and product-story tickets.

YOUR ROLE
You are Agent D — Dashboard/Reporting/Export Engineer and Final GitHub Steward. Owned areas: src/dashboard/, src/reports/, src/exports/, tests/unit/test_dashboard.py, tests/unit/test_reports.py, docs/cycle_reports/, and final GitHub PR workflow. Jira keys: SCRUM-212, SCRUM-213, SCRUM-228, SCRUM-226, SCRUM-250.

GIT INSTRUCTIONS
Work only on cycle/008/integration. Pull after Agent C. Final steward actions: validate, fix local issues if in owned areas, push branch, create/update PR into develop, inspect Codex threads, post disposition replies, resolve threads only after fixes/checks, and do not merge unless explicit authorization is provided.

TASKS FOR THIS CYCLE

Task D1 — Dashboard governance/status presentation model.
Jira: SCRUM-212, SCRUM-213.
Files: src/dashboard/app.py, tests/unit/test_dashboard.py.
Implementation detail: Add or refine presentation helpers that expose status categories for local parity, GitHub Actions, Codecov project, Codecov patch, Codex disposition, Jira mapping, and merge readiness. These helpers must not import Streamlit at module import time. They should return plain data structures suitable for tests and future UI rendering.
Tests: all status categories render; missing status becomes warning/unknown; no Streamlit import side effect.
DOD: partial progress toward dashboard design/component stories.

Task D2 — Reporting placeholder for Jira mapping table.
Jira: SCRUM-213, SCRUM-228, SCRUM-250.
Files: src/reports/placeholders.py, tests/unit/test_reports.py.
Implementation detail: Add a report helper that renders a Jira mapping table from changed file groups, Jira keys, status, and DOD status. It must support Markdown and dict output. It must reject rows with missing Jira keys unless explicitly marked `not_applicable_reason`.
Tests: valid mapping renders; missing Jira key fails; not-applicable reason passes.
DOD: future PR reports cannot omit product-story mapping silently.

Task D3 — Export manifest for Jira/GitHub evidence.
Jira: SCRUM-226, SCRUM-250.
Files: src/exports/placeholders.py, tests/unit/test_reports.py or tests/unit/test_dashboard.py.
Implementation detail: Add metadata fields for jira_keys, github_pr_number, codex_threads_resolved, codecov_project_status, codecov_patch_status, and coverage_percent to export manifests. Keep export data secret-safe and deterministic.
Tests: manifest includes required fields; secret-like values are rejected/masked; coverage percent validation.
DOD: partial progress toward export system and governance evidence export.

Task D4 — Final full validation.
Validation commands: python -m ruff check .; python -m mypy src; python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90; python run.py config-check; python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle008.db; python run.py phase2-smoke. Clean generated coverage.xml and runtime DB after validation unless required as artifact outside Git.

Task D5 — GitHub PR stewardship.
Jira: SCRUM-250 plus all mapped product tickets.
Implementation detail: Push cycle/008/integration, create PR title `feat(cycle-008): enforce jira story mapping and harden phase 2 contracts`. PR body must include summary, validation, Codex disposition status, Codecov project/patch status, branch policy, and Jira mapping table with at least SCRUM-250, SCRUM-154, SCRUM-156, SCRUM-149, SCRUM-164, SCRUM-163, SCRUM-212, SCRUM-213, SCRUM-228, SCRUM-226. If Codex posts comments, review each one, decide VALID_FIXED / VALID_DEFERRED_BLOCKER / NOT_APPLICABLE_FALSE_POSITIVE / VALID_ALREADY_COVERED, reply with evidence, and resolve only after appropriate.

Task D6 — Cycle report.
Files: docs/cycle_reports/CYCLE_008_AGENT_D.md.
Commit message: feat(reporting): add jira mapping visibility and cycle 008 steward report [Agent D].
```

---

## 5. STATE UPDATE

Updated PM Pack state for Cycle 008 includes:

- New permanent Jira protocol: `04_jira_protocol/JIRA_CYCLE_STORY_MAPPING_PROTOCOL.md`
- New corrective rule: `01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_008.md`
- Updated `HYDRATION_HEADER.md` to Cycle 008
- Updated `STATE_SNAPSHOT.md` with Jira mapping correction and PR #6 merged
- Updated `EPIC_STATUS_TRACKER.md` to show active partial progress in Epic 02, Epic 03, and Epic 09
- New `10_cycle_log/CYCLE_008.md`
- Root PM response artifact: `CYCLE_008_PM_RESPONSE.md`

---

## 6. NEXT CYCLE PREVIEW

Cycle 009 should review PR #7, verify Jira mapping was included in the PR body, verify all product stories touched by Cycle 008 were updated, and continue Phase 2 implementation. If Cycle 008 agents successfully harden collection/analysis/dashboard mapping, Cycle 009 can expand into fuller Collection Stage 3/4 fixture workflows and Analysis Stage 7/8/9 persistence-ready outputs.

============================================================
END OF CYCLE 008
============================================================
