# CYCLE 003 — 2026-05-13
Focus: Cycle 002 PR Review Gate + Foundation Release Readiness + Phase 2 Entry Prep
Branch: `cycle/003/integration` after PR #1 is merged into `develop`
Primary PR Dependency: Existing PR #1 — `cycle/002/integration` → `develop`
Main Policy: `main` remains untouched. No direct pushes to `main`.

---

## 1. REVIEW OF PRIOR AGENT WORK

### Source Evidence Reviewed

- User final handoff report for `cycle/002/integration`.
- Uploaded repository archive: `Fiverr_002.zip`.
- Uploaded PM Pack archive: `PM_Pack_Cycle_002_READY(1).zip`.
- Jira process issue: `SCRUM-246`.

### Cycle 002 Handoff Evidence

The Cycle 002 handoff reports the following verified results:

| Validation / GitHub Item | Reported Result |
|---|---|
| Branch | `cycle/002/integration` |
| Commit range | `fe7b90d..5ec326a` |
| Remote visibility | Passed for `origin/develop` and `origin/cycle/002/integration` |
| Ancestry | Passed: `origin/develop` is an ancestor of `HEAD` |
| Runtime DB artifact | Removed before push |
| Working tree | Clean before push |
| `python -m pytest -q` | 113 passed |
| `python -m ruff check .` | All checks passed |
| `python -m mypy src` | No issues in 56 files |
| `python run.py config-check` | Passed |
| `python run.py init-db --database-url sqlite:///data/fiverr_research_cycle002.db` | Passed |
| `python run.py smoke` | Passed |
| Push | Succeeded / everything up-to-date |
| PR | Existing PR #1 already open |
| `main` | Untouched |

### Local Archive Review Notes

The uploaded archive shows `cycle/002/integration` at commit `5ec326a` with the expected Agent A/B/C/D commits. The archive also shows local line-ending changes in three `__init__.py` files, but the user’s final handoff explicitly reports the working tree was clean before push. Treat the pushed branch and final handoff report as authoritative, while requiring Agent A/D in Cycle 003 to verify live repository cleanliness before making any new commits.

### Agent Confidence Scores

| Agent | Cycle 002 Scope | Evidence | Confidence | Status |
|---|---|---|---:|---|
| A | Database, CLI, utilities, Foundation integration | Tests, Ruff, Mypy, config-check, init-db, smoke all reported passing | 94 | In Review pending PR merge |
| B | Collection queue/pacing/checkpoint/selectors/session/proxy foundations | Tests and full validation suite reported passing | 92 | In Review pending PR merge |
| C | LLM provider/cache/validation/retry/cost/analysis contracts | Tests and full validation suite reported passing | 93 | In Review pending PR merge |
| D | Dashboard/docs/export/reporting and GitHub steward cleanup | Final handoff reports cleanup, push, PR status, main untouched | 95 | In Review pending PR merge |

### PM Process Review

A hard process failure occurred in prior PM outputs: updated PM Pack zip was not included in every PM reply. `SCRUM-246` remains In Review and must not be closed until at least two consecutive clean PM cycles include all required elements: review, Jira update, state update, four detailed Cursor prompts, GitHub steward instructions, and updated PM Pack zip.

---

## 2. JIRA BOARD UPDATE

### Jira Actions Taken / Required

| Jira | Status Direction | Reason |
|---|---|---|
| `SCRUM-246` | Remain In Review | Corrective PM process item is active until two clean cycles complete |
| `SCRUM-136` | In Review | Cycle 002 validated database/model expansion; PR merge pending |
| `SCRUM-137` | In Review | Cycle 002 validated CLI commands; PR merge pending |
| `SCRUM-138` | In Review | Cycle 002 validated LLM hardening; PR merge pending |
| `SCRUM-139` | In Review | Cycle 002 validated utility expansion; PR merge pending |
| `SCRUM-140` | In Review | Cycle 002 validated seed guidance / docs support; PR merge pending |
| `SCRUM-141`–`SCRUM-146` | In Review | Cycle 002 collection foundation work validated; PR merge pending |
| `SCRUM-147`–`SCRUM-154` | To Do / In Progress for Cycle 003 if PR #1 merges | Begin real Collection Phase 2 work after develop sync |
| `SCRUM-157`–`SCRUM-164` | To Do / In Progress for Cycle 003 if PR #1 merges | Begin Analysis Phase 2 scaffolding after develop sync |

### PM Rule Correction Added to Cycle 003

Every cycle response must include:

1. Full cycle review.
2. Jira update summary.
3. Four detailed Cursor prompts.
4. GitHub steward instructions assigned to an agent, not defaulted to the human operator.
5. Updated PM Pack zip.
6. Clear `main` policy.

---

## 3. CYCLE 003 PLAN

Cycle 003 is a controlled gate-and-advance cycle. It should not blindly start new product work until PR #1 is reviewed and merged into `develop` or until the GitHub steward confirms why it cannot be merged.

### Cycle 003 Execution Strategy

| Phase | Owner | Action |
|---|---|---|
| 003-A | Agent A | Verify PR #1 / branch state, merge PR #1 if authorized and green, create `cycle/003/integration` from updated `develop`, run Foundation release gate, close remaining Foundation gaps |
| 003-B | Agent B | Begin Epic 02 collection workflow implementation from updated foundation contracts |
| 003-C | Agent C | Begin Epic 03 analysis workflow implementation using validated LLM/contracts/model layer |
| 003-D | Agent D | Dashboard/reporting/docs support plus final Integration/GitHub Steward duties: validation, push, PR creation/update |

### Branch Policy

| Branch | Purpose | Who handles |
|---|---|---|
| `cycle/002/integration` | Completed Cycle 002 branch, already pushed | Agent A/D verify and close PR #1 |
| `develop` | Integration branch | PR #1 target; Cycle 003 must branch from updated `develop` |
| `cycle/003/integration` | New working branch | Agent A creates; all agents commit here |
| `main` | Stable release only | No agent pushes; release PR only after approved gate |

---

## 4. AGENT PROMPTS

## Agent A Prompt — Foundation Release Gate + Branch Steward Start

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local working repo path: C:\Fiverr\Fiverr. IMPORTANT: the parent C:\Fiverr is not the Git repository. The active repository root is C:\Fiverr\Fiverr. Current cycle: Cycle 003. Prior completed branch: cycle/002/integration. Existing PR: #1 from cycle/002/integration into develop. Target Cycle 003 branch: cycle/003/integration, created only after PR #1 is verified and merged into develop or after you clearly report that it cannot be merged due to authorization, CI, or GitHub state.

YOUR ROLE
You are Agent A — Infrastructure Engineer and Cycle 003 opening GitHub steward. Your ownership areas are root packaging/config/CLI/orchestrator, src/config/, src/models/, src/utils/, src/scripts/, tests/conftest.py, tests/unit/test_config.py, tests/unit/test_models.py, tests/unit/test_cli.py, tests/unit/test_utils.py, and tests/integration/test_database_init.py. You also own the opening branch-control step for this cycle because no new work should start from stale develop. You must not modify src/collection/, src/llm/, src/dashboard/, src/reports/, src/exports/, src/playbook/, or Agent B/C/D tests unless you are only resolving a merge conflict caused by PR #1 merge and you document that conflict clearly.

GIT / GITHUB INSTRUCTIONS
Do not push to main. Do not commit directly to main. Do not create work on top of a stale branch. Start by running live GitHub/remote checks from C:\Fiverr\Fiverr:

1. git status --short
2. git branch --show-current
3. git fetch origin --prune
4. git ls-remote --heads origin develop cycle/002/integration cycle/003/integration main
5. gh pr view 1 --json number,state,headRefName,baseRefName,mergeable,reviewDecision,statusCheckRollup,url || echo "GH CLI PR view unavailable"

If PR #1 is open, mergeable, targets develop, and checks are green, merge it using the repository-approved method. Prefer squash merge unless the repo policy says otherwise:

- gh pr merge 1 --squash --delete-branch=false

If you cannot merge due to auth or checks, stop new branch creation and report the blocker. If PR #1 is already merged, continue. Then create Cycle 003 branch from updated develop:

- git checkout develop
- git pull origin develop
- git checkout -b cycle/003/integration

If cycle/003/integration already exists remotely, stop and report; do not overwrite it.

TASKS FOR THIS CYCLE

Task A1 — PR #1 Closure Gate / GitHub Branch Truth
Story/Epic: Cycle Integration Gate / Epic 01. Jira: SCRUM-246 plus SCRUM-136/SCRUM-137 supporting review. Spec References: 05_github_protocol/BRANCH_WORKFLOW.md, 05_github_protocol/MERGE_PROTOCOL.md, 02_cycle_protocol/PR_BATCH_STRATEGY.md, 01_pm_instructions/PM_CORRECTIVE_RULES_CYCLE_002.md. Files to modify: none unless merge conflicts require resolution; if no conflicts, this is a verification/merge task only. Implementation details: Verify the live state of PR #1 and branch ancestry. Confirm PR #1 source is cycle/002/integration and target is develop. Confirm main remains untouched. Confirm current local develop matches origin/develop after PR merge. Produce a clear report in your Cursor final response with the exact commit hashes for origin/develop before merge, the PR #1 merge commit/squash commit after merge, and the new starting commit for cycle/003/integration. Required tests/validations: git merge-base --is-ancestor origin/develop HEAD after branch creation; git branch --show-current returns cycle/003/integration; git status --short is clean before code edits. DoD: no stale branch work begins; PR #1 is either merged or a blocker is reported with exact reason.

Task A2 — Foundation Release Gate Script
Story/Epic: S1.4 / Epic 01 Foundation. Jira: SCRUM-137. Spec References: ref/todo/EPIC_01_FOUNDATION.md Story 1.4; ref/dod/DOD_EPIC_01.md final Foundation DoD; ref/project_plan/08_roadmap/DEVELOPMENT_ROADMAP.md Phase 1 exit criteria. Files to create/modify: src/scripts/foundation_gate.py, src/scripts/__init__.py, run.py, src/orchestrator.py, tests/unit/test_cli.py, tests/integration/test_database_init.py. Implementation details: Add a deterministic Foundation release-gate command that executes only local checks and reports PASS/FAIL without accessing external services. It should verify config loads, database initializes with all currently declared models, smoke imports pass, no runtime DB artifact is tracked, and key packages import. Add CLI command `python run.py foundation-gate --database-url sqlite:///data/foundation_gate.db`. The command should return exit code 0 only when all checks pass. It should print a compact summary with check names and statuses. Required tests: Click CliRunner test for command success with a temp SQLite DB; failure test for invalid config path or malformed database URL. DoD: Foundation release gate provides one command for PM/agents to determine if Epic 01 is release-ready.

Task A3 — ORM Table Registry and Table Count Reconciliation
Story/Epic: S1.3 / Epic 01 Foundation. Jira: SCRUM-136. Spec References: ref/project_plan/03_data/SCHEMA.md, ref/project_plan/03_data/FIELD_CATALOG.md, ref/dod/DOD_EPIC_01.md database acceptance criteria. Files to modify/create: src/models/__init__.py, src/models/database.py, src/models/registry.py, tests/unit/test_models.py, tests/integration/test_database_init.py. Implementation details: Create an explicit model registry that lists every SQLAlchemy model class currently implemented and every source-required model not yet implemented. Do not silently claim that the project has all 28 source tables unless the code truly does. Add `get_registered_model_classes()`, `get_registered_table_names()`, and `get_missing_source_tables()` or equivalent. The registry must be used by database initialization tests to assert current coverage and by the foundation gate to print table counts. Required tests: registry returns no duplicate table names; database initialization creates every registered table; missing-source-table list is deterministic and documented. DoD: PM can inspect the code and know exactly which source tables are complete versus pending.

Task A4 — Config Validation Hardening
Story/Epic: S1.2 / Epic 01 Foundation. Jira: SCRUM-135. Spec References: ref/project_plan/02_architecture/CONFIG_SCHEMA.md, ref/project_plan/01_vision/NICHE_CONFIG_DESIGN.md, ref/dod/DOD_EPIC_01.md config criteria. Files to modify: src/config/models.py, src/config/loader.py, tests/unit/test_config.py. Implementation details: Harden the config models so they validate all nine required niches, required scoring profiles, weight sums, positive pacing values, export formats, and safe default paths. Add clear error messages for missing scoring profile, duplicate niche IDs, empty keyword seed lists, invalid collection pacing values, and unsupported export formats. Required tests: invalid weight sum fails; duplicate niche ID fails; missing required profile fails; valid config still passes. DoD: config-check is not only a load test; it enforces source-critical constraints.

Task A5 — CLI Export/Dashboard Command Stubs Without Cross-Agent Ownership Drift
Story/Epic: S1.4 / Epic 01 Foundation. Jira: SCRUM-137. Spec References: ref/todo/EPIC_01_FOUNDATION.md tasks 1.4.3 and 1.4.4; ref/dod/DOD_EPIC_01.md CLI requirements. Files to modify: run.py, src/orchestrator.py, tests/unit/test_cli.py. Implementation details: Add CLI commands for `export` and `dashboard` as safe stubs that do not implement Agent D’s export/dashboard internals. The commands should validate arguments and print a clear message that full implementation is in Epic 09. They should return 0 for `--help` and predictable exit codes for invalid formats or missing inputs. Required tests: help output includes export and dashboard; invalid export format returns nonzero; dashboard command does not launch Streamlit in tests. DoD: CLI surface matches expected project modes without crossing into dashboard/report implementation.

Task A6 — Repository Hygiene Guard
Story/Epic: Foundation QA / Epic 01. Jira: SCRUM-246 supporting. Spec References: ref/github/08_hygiene/RELEASE_PROCESS.md, 05_github_protocol/GITHUB_RULES.md. Files to create/modify: src/scripts/repo_hygiene.py, tests/unit/test_cli.py or tests/unit/test_utils.py. Implementation details: Add a lightweight local script/helper that checks for untracked runtime DB files, tracked `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`, and session/browser artifacts. The helper should be callable from foundation gate or CLI and should not require GitHub access. Required tests: temp file paths for forbidden patterns are detected; safe files pass. DoD: future agents have a deterministic local hygiene check before push.

VALIDATION STEPS
Run before commit: python -m pytest tests/unit/test_config.py tests/unit/test_models.py tests/unit/test_cli.py tests/unit/test_utils.py tests/integration/test_database_init.py -q; python -m ruff check src/config src/models src/scripts src/utils run.py tests; python -m mypy src; python run.py config-check; python run.py init-db --database-url sqlite:///data/fiverr_research_cycle003_a.db; python run.py smoke; python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle003.db; git status --short.

COMMIT INSTRUCTIONS
Commit only after validations pass. Commit message: feat(foundation): add release gate and registry hardening [Agent A]. Do not push unless you are explicitly completing GitHub steward fallback. Agent D is final GitHub steward for this cycle.
```

## Agent B Prompt — Epic 02 Collection Workflow Start

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local repo root: C:\Fiverr\Fiverr. Current cycle: Cycle 003. Work branch: cycle/003/integration. This branch must be created from updated develop after PR #1 is merged or confirmed already merged. Do not start work on cycle/002/integration. Tech stack: Python 3.11+, Playwright, Pydantic v2, SQLAlchemy model layer, pytest, Ruff, Mypy. This cycle begins real Epic 02 Collection Engine work, but all code must remain safe, read-only, paced, testable, and fixture-driven.

YOUR ROLE
You are Agent B — Collection Engineer. Your owned directories are src/collection/ and tests/unit/test_collection.py plus tests/integration/test_collection_e2e.py. You may also add collection fixtures under tests/fixtures/collection/ if needed. Do not edit src/config, src/models, src/llm, src/dashboard, src/reports, src/exports, src/playbook, run.py, or root packaging files. If Agent A’s Foundation release gate exposes an interface you need, use it as imported public API only; do not modify it.

GIT INSTRUCTIONS
Work on branch cycle/003/integration after Agent A commits. Do not push. Do not merge. Do not touch main. Before editing, run git status --short and verify the current branch is cycle/003/integration. If not, stop and report.

TASKS FOR THIS CYCLE

Task B1 — Playwright Session Manager Implementation
Story/Epic: S2.1 / Epic 02 Collection. Jira: SCRUM-141. Spec References: ref/todo/EPIC_02_COLLECTION.md Story 2.1; ref/dod/DOD_EPIC_02.md session criteria; ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md. Files to modify/create: src/collection/session.py, tests/unit/test_collection.py. Implementation details: Upgrade the session manager from scaffold to a real safe abstraction. Implement a `BrowserSessionConfig` model/dataclass with headless, storage_state_path, user_agent, timeout_ms, and authenticated_mode fields. Implement `build_browser_launch_options(config)` and `validate_storage_state_path(path)` without launching a browser during unit tests. Implement an async context manager skeleton `ManagedBrowserSession` that can accept injected Playwright/browser objects for tests. Do not store cookies or session files in Git. Required tests: validates missing storage state for authenticated mode; build launch options respects headless/timeout/user_agent; injected fake browser closes cleanly. DoD: session manager is ready for E2E collection but unit tests remain no-network.

Task B2 — Selector Registry and Fixture-Based Parsing
Story/Epic: S2.2 / Epic 02 Collection. Jira: SCRUM-142. Spec References: ref/todo/EPIC_02_COLLECTION.md Story 2.2; ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md search/gig/seller sections. Files to modify/create: src/collection/selectors.py, tests/fixtures/collection/search_results.html, tests/unit/test_collection.py. Implementation details: Expand selector registry with typed selectors for search result cards, gig title, gig URL, seller name, price, rating, review count, pagination next, gig detail title, package cards, seller profile fields, and unavailable/blocked page indicators. Add helper `get_selector(group, name)` and `validate_selector_registry()`. Add fixture-based parse helper functions only for static HTML strings; do not launch browser. Required tests: registry contains required groups and selectors; missing selector raises clear KeyError; fixture search page extracts two or more result card candidates. DoD: selectors are centralized, testable, and can be used by future browser collection.

Task B3 — Keyword Expansion Workflow
Story/Epic: S2.7 / Epic 02 Collection. Jira: SCRUM-147. Spec References: ref/todo/EPIC_02_COLLECTION.md Story 2.7; ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md Stage 2. Files to modify/create: src/collection/keyword_expansion.py, tests/unit/test_collection.py. Implementation details: Implement deterministic keyword expansion that takes seed keywords and niche metadata and returns normalized candidate keywords with lineage. Include normalization, lowercasing, whitespace cleanup, duplicate removal, source tagging, and maximum candidate cap. Use no external network calls. Add `ExpandedKeyword` and `KeywordExpansionResult` structures with source_seed and expansion_method. Required tests: duplicate seeds collapse deterministically; lineage is preserved; max candidate cap is enforced; empty seed list returns warning result rather than crashing. DoD: Stage 2 can produce controlled candidate keywords for later collection.

Task B4 — Search Collection Planner Without Live Scraping
Story/Epic: S2.8 / Epic 02 Collection. Jira: SCRUM-148. Spec References: ref/todo/EPIC_02_COLLECTION.md Story 2.8; ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md Stage 3. Files to modify/create: src/collection/search_plan.py, tests/unit/test_collection.py. Implementation details: Implement a search planning layer that builds read-only Fiverr search URLs or query objects from expanded keywords, region/language/sort parameters, and depth controls. It must not perform HTTP requests or launch Playwright. Add structures for SearchPlanItem and SearchPlan, including keyword_id, query, url, page_number, max_pages, source, and estimated_priority. Required tests: URL encoding is correct; page range respects max_pages; invalid max_pages fails; generated plan preserves keyword lineage. DoD: future browser automation can consume a safe search plan.

Task B5 — Queue/Checkpoint Integration for Planned Jobs
Story/Epic: S2.4/S2.5 / Epic 02 Collection. Jira: SCRUM-144, SCRUM-145. Spec References: ref/project_plan/04_collection/QUEUE_DESIGN.md; ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md. Files to modify/create: src/collection/queue.py, src/collection/checkpoint.py, tests/unit/test_collection.py. Implementation details: Connect search plan items to queue job objects and checkpoint snapshots. Implement queue job statuses for pending, running, succeeded, failed, skipped, dead_letter. Add `enqueue_search_plan(plan)` and `checkpoint_queue_state(queue, path)` using atomic write. Ensure JSON output is deterministic and safe for resume. Required tests: enqueue creates expected number of jobs; checkpoint writes valid JSON atomically; corrupted checkpoint returns a controlled error; job ordering is deterministic. DoD: Stage 3 planning can become resumable before live collection.

Task B6 — Collection E2E Dry Run
Story/Epic: S2.14 preparatory / Epic 02 Collection. Jira: SCRUM-154 future story, not Done this cycle. Spec References: ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md stage orchestration; ref/dod/DOD_EPIC_02.md orchestration requirements. Files to modify/create: src/collection/orchestrator.py, tests/integration/test_collection_e2e.py. Implementation details: Implement a dry-run collection orchestrator that runs seed keywords through keyword expansion, search planning, queue creation, and checkpoint write without opening a browser or contacting Fiverr. Return a CollectionStageResult with counts and warnings. Required tests: dry run from two seed keywords creates expanded keywords, plan items, queue jobs, and checkpoint; invalid input returns failed result with error; no network/browser dependencies are used. DoD: PM can run an Epic 02 dry-run test safely.

VALIDATION STEPS
Run before commit: python -m pytest tests/unit/test_collection.py tests/integration/test_collection_e2e.py -q; python -m ruff check src/collection tests/unit/test_collection.py tests/integration/test_collection_e2e.py; python -m mypy src/collection; python -c "from src.collection.orchestrator import run_collection_dry_run"; git status --short.

COMMIT INSTRUCTIONS
Commit message: feat(collection): implement dry-run collection planning pipeline [Agent B]. Do not push. Agent D handles final push/PR duties.
```

## Agent C Prompt — Epic 03 Analysis Engine Start

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local repo root: C:\Fiverr\Fiverr. Current cycle: Cycle 003. Work branch: cycle/003/integration. The prior Cycle 002 branch must already be merged into develop before Cycle 003 begins. Tech stack: Python 3.11+, Pydantic v2, scikit-learn/numpy where available, LLM client/cache/validation from src/llm, SQLAlchemy model layer from src/models, pytest, Ruff, Mypy.

YOUR ROLE
You are Agent C — Analysis, Scoring & LLM Engineer. For Cycle 003 you begin Epic 03 Analysis Engine implementation while preserving LLM safety and not modifying Agent A/B/D files. You may edit src/analysis/, tests/unit/test_analysis.py, and if absolutely necessary src/llm/ only for compatibility fixes caused by your analysis contracts. Do not edit src/collection, src/models, src/config, src/dashboard, src/reports, src/exports, src/playbook, run.py, or root files.

GIT INSTRUCTIONS
Work on cycle/003/integration after Agents A and B have committed. Do not push. Do not merge. Do not touch main. Run git status --short before editing and stop if there are uncommitted files outside your owned directories.

TASKS FOR THIS CYCLE

Task C1 — Analysis Domain Contracts
Story/Epic: S3.1/S3.2/S3.3 / Epic 03 Analysis. Jira: SCRUM-157, SCRUM-158, SCRUM-159. Spec References: ref/todo/EPIC_03_ANALYSIS.md; ref/dod/DOD_EPIC_03.md; ref/project_plan/06_analysis/KEYWORD_CLUSTERING.md; ref/project_plan/06_analysis/GIG_QUALITY_RUBRIC.md; ref/project_plan/06_analysis/COMPETITOR_PROFILING.md. Files to create/modify: src/analysis/contracts.py, src/analysis/__init__.py, tests/unit/test_analysis.py. Implementation details: Define Pydantic or dataclass contracts for KeywordClusterInput, KeywordClusterResult, GigQualityInput, GigQualityResult, CompetitorProfileInput, CompetitorProfileResult, AnalysisWarning, and AnalysisRunSummary. Include source IDs, confidence, explanation, missing_data_fields, and metadata. Required tests: valid objects serialize deterministically; invalid confidence outside 0-1 or 0-100 range fails; missing required source ID fails. DoD: later analysis modules share consistent, validated contracts.

Task C2 — Keyword Normalization and Feature Builder
Story/Epic: S3.1 / Epic 03 Analysis. Jira: SCRUM-157. Spec References: ref/project_plan/06_analysis/KEYWORD_CLUSTERING.md. Files to create/modify: src/analysis/keyword_features.py, tests/unit/test_analysis.py. Implementation details: Implement keyword text normalization, token extraction, simple lexical features, and optional numeric feature vectors using numpy only if available from project dependencies. Do not require live embeddings in this cycle. Include deterministic fallback vectorization for tests. Required tests: normalization removes extra whitespace/case variance; vector output is deterministic; empty keyword returns controlled error/warning. DoD: clustering can run using deterministic local features.

Task C3 — Keyword Clustering Engine
Story/Epic: S3.1 / Epic 03 Analysis. Jira: SCRUM-157. Spec References: ref/todo/EPIC_03_ANALYSIS.md Story 3.1; ref/dod/DOD_EPIC_03.md clustering criteria. Files to create/modify: src/analysis/clustering.py, tests/unit/test_analysis.py. Implementation details: Implement local clustering for small keyword sets using deterministic grouping by normalized token overlap or scikit-learn if available. The system must degrade safely when there are too few keywords. Output cluster_id, label, keywords, size, cohesion_score, and explanation. Required tests: related keywords group together in a deterministic fixture; too few keywords returns one low-confidence cluster or a warning; cluster labels are stable. DoD: Stage 9 keyword clustering has a first working local implementation.

Task C4 — Gig Quality Rubric Engine
Story/Epic: S3.2 / Epic 03 Analysis. Jira: SCRUM-158. Spec References: ref/project_plan/06_analysis/GIG_QUALITY_RUBRIC.md; ref/todo/EPIC_03_ANALYSIS.md Story 3.2. Files to create/modify: src/analysis/gig_quality.py, tests/unit/test_analysis.py. Implementation details: Implement heuristic gig quality scoring from title, description length, package completeness, rating, review count, image_count if present, FAQ presence, and metadata completeness. Return 0-100 score, component scores, weaknesses, strengths, explanation, and confidence. Required tests: complete high-quality gig scores higher than sparse gig; missing fields produce warnings not crashes; scores stay within 0-100. DoD: scoring engine has usable gig-quality weakness signals.

Task C5 — Competitor Profile and Seller Strength Pre-Model
Story/Epic: S3.3/S3.4 / Epic 03 Analysis. Jira: SCRUM-159, SCRUM-160. Spec References: ref/project_plan/06_analysis/COMPETITOR_PROFILING.md; ref/todo/EPIC_03_ANALYSIS.md Stories 3.3 and 3.4. Files to create/modify: src/analysis/competitors.py, tests/unit/test_analysis.py. Implementation details: Implement competitor summary analysis from a list of gigs/sellers. Identify dominant seller levels, pricing bands, review/rating concentration, high-authority sellers, weak competitors, and new-seller feasibility hints. Required tests: fixture with strong incumbents returns high competition warning; fixture with weak/sparse competitors returns opportunity signals; empty list returns low-confidence result. DoD: analysis engine can produce early competitor signals without LLM calls.

Task C6 — Analysis Stage Orchestrator
Story/Epic: S3.8 / Epic 03 Analysis. Jira: SCRUM-164. Spec References: ref/todo/EPIC_03_ANALYSIS.md Story 3.8; ref/project_plan/06_analysis/ANALYSIS_STAGE_FLOW.md if present, otherwise TOPIC_MAP analysis entries. Files to create/modify: src/analysis/orchestrator.py, tests/unit/test_analysis.py. Implementation details: Implement an analysis dry-run orchestrator that accepts fixture keyword/gig/seller payloads, runs clustering, gig quality, and competitor profiling, and returns AnalysisRunSummary. It must not require database writes or live LLM calls in Cycle 003. Required tests: complete fixture returns all stages succeeded; sparse fixture returns warnings; invalid payload returns failed stage summary. DoD: Epic 03 has a no-network dry-run that can be connected to collection outputs later.

Task C7 — Cycle Validation
Story/Epic: Cycle QA / Epic 03. Jira: SCRUM-157 through SCRUM-164. Files to modify: owned files only. Implementation details: Run all owned tests and fix issues only in src/analysis or tests/unit/test_analysis.py. Do not patch other agents’ work. Required tests: python -m pytest tests/unit/test_analysis.py -q; mypy src/analysis; ruff for src/analysis. DoD: Agent C reports exact validation output and limitations.

VALIDATION STEPS
Run before commit: python -m pytest tests/unit/test_analysis.py -q; python -m ruff check src/analysis tests/unit/test_analysis.py; python -m mypy src/analysis; python -c "from src.analysis.orchestrator import run_analysis_dry_run"; git status --short.

COMMIT INSTRUCTIONS
Commit message: feat(analysis): add dry-run clustering and quality analysis [Agent C]. Do not push. Agent D handles final GitHub steward duties.
```

## Agent D Prompt — Dashboard/Docs + Final GitHub Steward

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local repo root: C:\Fiverr\Fiverr. Current cycle: Cycle 003. Work branch: cycle/003/integration. PR #1 for Cycle 002 must be merged into develop before this branch starts. Main is release-only and must remain untouched. You are both Dashboard/Presentation Engineer and final Integration/GitHub Steward for this cycle.

YOUR ROLE
You are Agent D — Dashboard, Playbook & Presentation Engineer plus final GitHub Steward. Your owned directories are src/dashboard/, src/playbook/, src/reports/, src/exports/, docs/, tests/unit/test_dashboard.py, tests/unit/test_playbook.py, tests/unit/test_reports.py. For GitHub steward tasks, you may run repo-wide validation commands, inspect git status/log/branch state, push the cycle branch, and create/update the PR. Do not edit Agent A/B/C source files unless final validation exposes a trivial documentation-only reference error in your owned docs. Do not push to main.

GIT INSTRUCTIONS
Work after Agents A/B/C have committed. Verify you are on cycle/003/integration. You are responsible for final validation, branch push, and PR creation/update for Cycle 003. Do not merge your own PR unless explicitly instructed by PM in a later cycle. Do not push to main.

TASKS FOR THIS CYCLE

Task D1 — Cycle 003 Dashboard Shell for Foundation/Collection/Analysis Status
Story/Epic: Epic 09 preparation / Dashboard. Jira: future Epic 09 reference, not Done. Spec References: ref/project_plan/07_reporting/DASHBOARD_PLAN.md; ref/project_plan/12_dashboard_ux/DESIGN_SYSTEM.md. Files to modify/create: src/dashboard/app.py, src/dashboard/navigation.py, src/dashboard/state.py, tests/unit/test_dashboard.py. Implementation details: Add non-launching dashboard state builders that can display Foundation, Collection Dry Run, and Analysis Dry Run status. Do not require Streamlit at import time unless already safely optional. Provide functions that return plain dict/list data structures suitable for UI rendering. Required tests: importing dashboard modules does not launch UI; state builder includes Foundation/Collection/Analysis sections; missing metrics render as pending not crashes. DoD: dashboard shell can represent Cycle 003 progress without full UI implementation.

Task D2 — Report Templates for Release Gate and Dry Runs
Story/Epic: Reporting prep / Epic 09. Jira: future Epic 09 reference. Spec References: ref/project_plan/07_reporting/REPORT_GENERATION.md; ref/project_plan/07_reporting/EXPORT_FORMATS.md. Files to modify/create: src/reports/run_summary.py, src/reports/templates.py, tests/unit/test_reports.py. Implementation details: Add report structures for FoundationGateReport, CollectionDryRunReport, AnalysisDryRunReport, and CycleValidationReport. Keep outputs as markdown/plain dict; do not generate PDFs yet unless already supported. Include severity contract from Cycle 002 and enforce valid severities. Required tests: valid reports render markdown; invalid severity fails; missing optional sections render placeholders. DoD: agents and PM can produce consistent review reports.

Task D3 — Export Manifest Hardening
Story/Epic: Export prep / Epic 09. Jira: future Epic 09 reference. Spec References: ref/project_plan/07_reporting/EXPORT_FORMATS.md. Files to modify/create: src/exports/manifest.py, src/exports/formats.py, tests/unit/test_reports.py. Implementation details: Expand export manifest to include artifact_type, format, source_cycle, generated_at, path, checksum placeholder, and included_sections. Add validation for supported formats csv, xlsx, json, html, pdf, md. Do not write actual export files unless tests use temporary paths. Required tests: valid manifest serializes; unsupported format fails; checksum placeholder rules are deterministic. DoD: export layer can track PM/dry-run artifacts.

Task D4 — Documentation Update: GitHub Steward Ownership
Story/Epic: PM process + docs. Jira: SCRUM-246. Spec References: 05_github_protocol/BRANCH_WORKFLOW.md, 05_github_protocol/GITHUB_RULES.md, docs/CYCLE_BRANCH_CHECKLIST.md. Files to modify/create: docs/CYCLE_BRANCH_CHECKLIST.md, docs/OPERATOR_QUICKSTART.md, README.md if needed. Implementation details: Remove any language implying the human operator is the default GitHub executor. Document that Cursor agents handle branch checks, push, and PR preparation when authenticated, with Agent D as final steward unless PM assigns otherwise. Keep the human role as approval/oversight only. Required tests: documentation references cycle branch → develop, not main; direct main push prohibition is explicit; PR target is develop. DoD: docs align with Kevin’s required AI/agent-managed GitHub workflow.

Task D5 — Seed and Playbook Guidance Alignment
Story/Epic: S1.7 / Epic 01 Foundation; Epic 08 prep. Jira: SCRUM-140. Spec References: ref/todo/EPIC_01_FOUNDATION.md Story 1.7; ref/project_plan/11_playbook/SELLER_SETUP_PLAYBOOK.md. Files to modify/create: src/playbook/seed_guidance.py, docs/SEED_DATA_GUIDE.md, tests/unit/test_playbook.py. Implementation details: Align seed guidance with Agent A config hardening and model registry. Ensure seed guidance explains source-of-truth relationship: config.yaml stores niche config, seed payloads provide keyword lineage, database stores imported records. Required tests: guidance validator accepts valid 6+ keyword payload; fails missing source lineage; docs mention all nine niches if appropriate. DoD: seed docs are clear enough for future import implementation.

Task D6 — Final Repository Validation
Story/Epic: Cycle QA / all active Cycle 003 scope. Jira: SCRUM-246 plus active tickets. Files to modify: none unless validation fixes are strictly in your owned files. Implementation details: Run full validation after all agents commit. Required commands: python -m pytest -q; python -m ruff check .; python -m mypy src; python run.py config-check; python run.py init-db --database-url sqlite:///data/fiverr_research_cycle003.db; python run.py smoke; python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle003.db if Agent A added it. Remove untracked runtime DB artifacts after validation. Required report: include exact pass/fail output, number of tests passed, branch name, commit range, dirty tree status, and any blockers. DoD: final branch is clean except intentional committed changes.

Task D7 — Push and PR Creation/Update
Story/Epic: GitHub Steward / Cycle 003. Jira: SCRUM-246. Spec References: 05_github_protocol/PR_CYCLE_BATCH.md; 05_github_protocol/MERGE_PROTOCOL.md. Files to modify: none. Implementation details: After validation passes and working tree is clean, push cycle/003/integration to origin. Then create PR into develop using GitHub CLI if available. If a PR already exists, update/report it. Suggested title: `feat(cycle-003): advance foundation gate and start collection analysis dry runs`. Suggested PR body must include summary, validation checklist with actual results, Jira references, main policy, and branch policy. Do not merge the PR. Do not push to main. Required commands: git push -u origin cycle/003/integration; gh pr create --base develop --head cycle/003/integration --title "feat(cycle-003): advance foundation gate and start collection analysis dry runs" --body-file <temp-pr-body.md> OR report exact auth limitation. DoD: PR is open or blocker is reported with exact reason.

VALIDATION STEPS
Run before final commit and before push: python -m pytest tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py -q; python -m ruff check src/dashboard src/reports src/exports src/playbook docs tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py; python -m mypy src/dashboard src/reports src/exports src/playbook; then final repo-wide validation after all agents commit as described above.

COMMIT INSTRUCTIONS
Commit your code/docs first: git add README.md docs src/dashboard src/reports src/exports src/playbook tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py && git commit -m "docs(reporting): add cycle status reports and steward workflow [Agent D]". Then perform final validation, cleanup, push, and PR creation/update. Final report must confirm main untouched.
```

---

## 5. GITHUB STEWARD WORKFLOW FOR CYCLE 003

This workflow is assigned to Cursor agents, not the human operator as a default.

### Opening Steward: Agent A

Agent A must verify and close PR #1 if authorized, then create `cycle/003/integration` from updated `develop`.

### Final Steward: Agent D

Agent D must validate, clean, push, and create/update the PR.

### Main Branch Policy

`main` is untouched in Cycle 003. It should only receive a release PR later after Foundation and Phase 2 entry gates are reviewed and approved.

---

## 6. STATE UPDATE

### Updated State

| Field | Value |
|---|---|
| Current Cycle | 003 |
| Current Phase | Phase 1 closure / Phase 2 entry |
| Current branch | `cycle/003/integration` after PR #1 merge |
| Prior PR | PR #1: `cycle/002/integration` → `develop` |
| Validation evidence | Cycle 002 handoff reports 113 tests passing, Ruff clean, Mypy clean, config/init/smoke passing |
| PM corrective issue | `SCRUM-246` remains In Review |

### Next Cycle Preview

Cycle 004 should review PR for Cycle 003, then continue Epic 02 collection implementation and Epic 03 analysis implementation. If Foundation gates are fully green and Cycle 003 PR is merged into `develop`, Cycle 004 can become the first normal Phase 2 build cycle.

---

## 7. REQUIRED ARTIFACTS

This cycle reply must include:

- `Cycle_003_Fiverr_PM_Response.md`
- `PM_Pack_Cycle_003_READY.zip`

No PM response is complete without the updated PM Pack zip.
