# CYCLE 004 — 2026-05-13
Focus: Cycle 003 PR Gate + Epic 02 Collection Expansion + Epic 03 Analysis Expansion
Branch: `cycle/004/integration` after Cycle 003 PR is merged into `develop`
Primary PR Dependency: latest PR from `cycle/003/integration` → `develop`
Main Policy: `main` remains untouched. No direct pushes or PRs to `main`.

---

## 1. REVIEW OF PRIOR AGENT WORK

### Source Evidence Reviewed

- Uploaded PM pack: `PM_Pack_Cycle_003_READY (1).zip`.
- Uploaded repository archive: `Fiverr_003.zip`.
- Live GitHub fetch attempt for `https://github.com/KevinSGarrett/Fiverr` failed from the ChatGPT environment with a cache/fetch error, and direct `git ls-remote` in the local review container could not resolve `github.com`. Cycle 004 therefore assigns live GitHub verification to Agent A and final PR stewardship to Agent D.

### Repository Archive Findings

| Item | Finding |
|---|---|
| Current archive branch | `cycle/003/integration` |
| Archive head | `af43539 docs(reporting): add cycle status reports and steward workflow [Agent D]` |
| Remote ref in archive | `origin/cycle/003/integration` at `af43539` |
| Develop ref in archive | `develop` and `origin/develop` at `7e3be60` |
| Cycle 003 commits present | Agent A/B/C/D commits present |
| Dirty working tree in archive | 77 files show local modifications from line-ending conversion only |
| Diff ignoring EOL | Empty |
| Runtime DB artifacts in archive | `data/fiverr_research_cycle003.db`, `data/fiverr_research_cycle003_a.db`, `data/foundation_gate_cycle003.db` present as ignored runtime artifacts |
| Local dependency validation | Could not run full tests in ChatGPT container because SQLAlchemy is not installed there |

### Cycle 003 Commit Review

| Commit | Scope | Owner |
|---|---|---|
| `d69a8ee` | Foundation release gate and registry hardening | Agent A |
| `359d198` | Foundation registry/loader follow-up fixes | Agent A |
| `d7ae21e` | Dry-run collection planning pipeline | Agent B |
| `aa4dced` | Dry-run clustering and quality analysis | Agent C |
| `e283cdd` | Remaining Epic 03 contract and signal gaps | Agent C |
| `af43539` | Cycle status reports and steward workflow docs | Agent D |

### Review Scores

| Agent | Score | Status | Notes |
|---|---:|---|---|
| A | 90 | In Review | Foundation gate and model registry appear committed; live PR/merge state still requires agent verification. |
| B | 89 | In Review | Collection dry-run pipeline is present; next cycle should move into fixture-backed detail/seller/review workflows without live scraping. |
| C | 90 | In Review | Analysis dry-run engines are present; next cycle should expand seller strength, saturation, reviews, and intent classification. |
| D | 91 | In Review | Reporting/steward docs present; next cycle must enforce line-ending hygiene and final PR discipline. |

### Blocking / Caution Items

1. Cycle 003 should not be marked Done until the live GitHub PR state is verified and merged or intentionally held.
2. Runtime SQLite DB files are ignored but present in the uploaded archive. Steward agents must clean/avoid packaging runtime artifacts in future handoffs.
3. The local archive shows line-ending-only changes across many files. Agent A must normalize `.gitattributes` / repo settings or explicitly report why the live repo is clean.
4. Jira tool calls returned intermittent 502 errors during this PM cycle. The Jira action queue below must be applied on the next successful Jira connection.

---

## 2. JIRA BOARD UPDATE

### Jira Tool Status

Jira write attempts during this cycle returned `502 Bad Gateway`. No successful Jira status transitions were confirmed in this pass. The following queue is recorded for the next successful Jira tool pass.

### Jira Action Queue

| Ticket | Intended Status | Reason |
|---|---|---|
| `SCRUM-246` | In Review | PM process correction remains open until two clean cycles include all required artifacts. |
| `SCRUM-147` | In Review / In Progress based on live PR | Cycle 003 keyword expansion/search planning work present in repo archive. |
| `SCRUM-148` | In Review / In Progress based on live PR | Cycle 003 search planning work present in repo archive. |
| `SCRUM-154` | In Review / In Progress based on live PR | Cycle 003 collection dry-run orchestration present. |
| `SCRUM-157` | In Review / In Progress based on live PR | Cycle 003 keyword clustering present. |
| `SCRUM-158` | In Review / In Progress based on live PR | Cycle 003 gig quality analysis present. |
| `SCRUM-159` | In Review / In Progress based on live PR | Cycle 003 competitor profiling present. |
| `SCRUM-149` | In Progress for Cycle 004 | Begin fixture-backed gig detail collection. |
| `SCRUM-150` | In Progress for Cycle 004 | Begin fixture-backed seller profile collection. |
| `SCRUM-151` | In Progress for Cycle 004 | Add safe external trend signal connector abstraction. |
| `SCRUM-152` | In Progress for Cycle 004 | Add safe Reddit/community signal connector abstraction. |
| `SCRUM-153` | In Progress for Cycle 004 | Add autocomplete collection planning/fixture support. |
| `SCRUM-160` | In Progress for Cycle 004 | Expand seller strength model. |
| `SCRUM-161` | In Progress for Cycle 004 | Expand saturation model. |
| `SCRUM-162` | In Progress for Cycle 004 | Expand review analysis. |
| `SCRUM-163` | In Progress for Cycle 004 | Add intent classification. |
| `SCRUM-164` | In Progress for Cycle 004 | Wire analysis orchestration outputs. |

---

## 3. CYCLE 004 PLAN

Cycle 004 is a controlled Phase 2 expansion cycle. It must first close the Cycle 003 GitHub gate, then expand Epic 02 and Epic 03 using safe local/fixture-backed workflows. No live scraping or direct main work is allowed.

| Agent | Primary Focus | Task Count | GitHub Responsibility |
|---|---|---:|---|
| Agent A | GitHub gate, repo hygiene, shared model/config/CLI support for Phase 2 | 6 | Verify/merge Cycle 003 PR if authorized and green; create `cycle/004/integration` from updated `develop` |
| Agent B | Collection workflow expansion: gig detail, seller profile, autocomplete, external signals, fixtures | 6 | Commit only collection-owned files; no push |
| Agent C | Analysis expansion: seller strength, saturation, reviews, intent, persistence DTOs | 6 | Commit only analysis-owned files; no push |
| Agent D | Dashboard/report/export updates plus final GitHub steward duties | 6 | Final validation, hygiene cleanup, push, PR create/update into `develop` |

### Branch Rules

- `cycle/003/integration` must be merged or explicitly reported as blocked before new Cycle 004 product work proceeds.
- `cycle/004/integration` must be created from updated `develop`.
- Agents must not push directly to `main`.
- Cycle PR target is `develop`.
- `main` is release-only after approved Foundation/Phase gates.

---

## 4. AGENT PROMPTS

### Agent A Prompt — Integration Gate, Repo Hygiene, Phase 2 Foundation Support

```text
PROJECT CONTEXT
Project: Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local repo root: C:\Fiverr\Fiverr. Current PM cycle: Cycle 004. Current intended branch: cycle/004/integration, created only after Cycle 003 PR from cycle/003/integration into develop is verified and merged or explicitly reported as blocked. Tech stack: Python 3.11+, Click, Pydantic v2, SQLAlchemy 2.0, pytest, Ruff, Mypy, local-first execution. Active phase: Phase 2 expansion with Epic 02 Collection and Epic 03 Analysis, while preserving Foundation release readiness.

YOUR ROLE
You are Agent A — Infrastructure/Foundation/Git Gate Engineer. You own repo gate verification at the start of Cycle 004, shared foundation support, CLI/orchestrator boundaries, config/model compatibility, repo hygiene helpers, and tests for those files. You may modify only: root repo hygiene files when necessary (`.gitattributes`, `.gitignore`, `pyproject.toml`, `requirements.txt`), `run.py`, `src/config/`, `src/models/`, `src/utils/`, `src/scripts/`, `src/orchestrator.py`, `tests/conftest.py`, `tests/unit/test_config.py`, `tests/unit/test_models.py`, `tests/unit/test_utils.py`, `tests/unit/test_cli.py`, and `tests/integration/test_database_init.py`. Do not modify `src/collection/`, `src/analysis/`, `src/llm/`, `src/dashboard/`, `src/reports/`, `src/exports/`, or their tests unless you are only resolving a mechanical line-ending/hygiene issue before branch creation.

GIT INSTRUCTIONS
First verify live repository state. Run `git fetch --all --prune`, inspect PR/branch status using `gh pr list --head cycle/003/integration --base develop` or equivalent GitHub CLI command, and verify whether Cycle 003 PR is merged. If the PR is open and all checks are green and your token is authorized, merge it into `develop` using squash merge. If not authorized or checks are not green, stop and report the blocker. After Cycle 003 is confirmed merged, run `git checkout develop && git pull origin develop && git checkout -b cycle/004/integration`. Do not touch `main`. Do not push until Agent D final steward step unless you must push only to resolve a GitHub PR gate and that action is explicitly part of the PR merge verification.

TASKS FOR THIS CYCLE

Task A1 — Live GitHub Gate and Branch Creation
Story/Epic: PM GitHub governance / Cycle 004 entry gate. Jira: SCRUM-246 process enforcement plus active Epic 02/03 gates. Spec References: `05_github_protocol/BRANCH_WORKFLOW.md`, `05_github_protocol/MERGE_PROTOCOL.md`, `ref/github/02_pr_policy/PR_POLICY.md`. Files to modify: none unless documenting a blocker in `docs/CYCLE_BRANCH_CHECKLIST.md`. Implementation details: Verify the live GitHub state that ChatGPT could not fetch. Confirm whether the Cycle 003 PR exists, whether it targets `develop`, whether checks passed, whether review requirements are satisfied, and whether it is merged. If it is not merged but safe/authorized to merge, complete the merge into `develop`. If it cannot be merged, stop before product work and create a concise blocker report. After merge, create `cycle/004/integration` from updated `develop`. Required tests/validation: `git branch --show-current`, `git log --oneline -8`, `git merge-base --is-ancestor origin/develop HEAD` after branch creation, and `git status --short`. Definition of Done: Cycle 004 starts from current `develop`, not stale Cycle 003.

Task A2 — Repo Line-Ending and Artifact Hygiene Hardening
Story/Epic: Foundation hygiene / PM corrective follow-up. Jira: SCRUM-246. Spec References: `ref/github/08_hygiene/HYGIENE_CHECKLIST.md`, `ref/github/09_security/SECRETS_MANAGEMENT.md`. Files to create/modify: `.gitattributes`, `.gitignore`, `src/scripts/repo_hygiene.py`, `tests/unit/test_utils.py`. Implementation details: The uploaded Cycle 003 archive showed line-ending-only changes across many files and ignored runtime DB artifacts in `data/`. Add or harden `.gitattributes` with explicit text normalization such as `*.py text eol=lf`, `*.md text eol=lf`, `*.yaml text eol=lf`, `*.yml text eol=lf`, `*.toml text eol=lf`, `*.html text eol=lf`, while keeping binary patterns for db/png/jpg/pdf/xlsx. Extend repo hygiene checks to detect runtime SQLite DB files under `data/`, pycache, pytest/mypy/ruff caches, and accidental browser/session artifacts. Do not mass-rewrite files in this task unless the steward approves. Required tests: hygiene detects runtime DB paths; hygiene accepts allowed docs/source files; `.gitattributes` exists and contains Python/Markdown/YAML rules. Definition of Done: future zip artifacts are less likely to produce misleading dirty trees.

Task A3 — Phase 2 Model Registry Compatibility
Story/Epic: S1.3 follow-up supporting Epics 02/03. Jira: SCRUM-136, SCRUM-160–SCRUM-164. Spec References: `ref/project_plan/03_data/SCHEMA.md`, `ref/project_plan/03_data/FIELD_CATALOG.md`, `ref/dod/DOD_EPIC_01.md`, `ref/dod/DOD_EPIC_03.md`. Files: `src/models/registry.py`, `src/models/analysis.py`, `src/models/market.py`, `tests/unit/test_models.py`, `tests/integration/test_database_init.py`. Implementation details: Add model-registry helpers needed by Agent C’s analysis persistence work without implementing Agent C logic. Ensure analysis-related tables expose stable names and minimal fields for analysis runs/results, competitor snapshots, and signal records. Add `get_registered_table_names()`, `verify_required_phase2_tables()`, and deterministic table classification by domain. Required tests: registry names are unique; phase 2 required analysis/collection support tables are present; database init creates all registered tables; missing-table verifier returns deterministic sorted results. Definition of Done: Agent C can persist or map analysis outputs without adding model infrastructure in its own owned files.

Task A4 — CLI Phase 2 Dry-Run Command Surfaces
Story/Epic: S1.4 CLI support for Phase 2. Jira: SCRUM-137, SCRUM-154, SCRUM-164. Spec References: `ref/project_plan/02_architecture/API_SURFACE.md`, `ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md`, `ref/project_plan/06_analysis/KEYWORD_CLUSTERING.md`. Files: `run.py`, `src/orchestrator.py`, `tests/unit/test_cli.py`. Implementation details: Add or harden CLI commands for `collection-dry-run`, `analysis-dry-run`, and `phase2-smoke` without crossing into collection/analysis implementation details. Commands should call already-exposed orchestrator functions through import-safe wrappers and return clear exit codes. Add options for fixture path, output path, and sample size where safe. Do not perform live scraping or require credentials. Required tests: help lists new commands; invalid fixture path returns nonzero; dry-run command can be monkeypatched to return success; phase2-smoke reports collection+analysis import status. Definition of Done: Phase 2 work can be validated from CLI without manual Python snippets.

Task A5 — Config Support for Phase 2 Safe Limits
Story/Epic: S1.2 follow-up for collection/analysis configuration. Jira: SCRUM-135, SCRUM-141–SCRUM-164. Spec References: `ref/project_plan/02_architecture/CONFIG_SCHEMA.md`, `ref/project_plan/04_collection/PACING_MODEL.md`, `ref/project_plan/06_analysis/LLM_PROMPT_TEMPLATES.md`. Files: `src/config/models.py`, `src/config/loader.py`, `config.yaml`, `tests/unit/test_config.py`. Implementation details: Add explicit config sections for phase2 collection dry-run limits, fixture-only mode, external signal connectors disabled by default, analysis confidence thresholds, and max input sizes. Ensure live connector flags default false. Add validation that no external connector runs without explicit opt-in config. Required tests: config defaults disable live connectors; fixture-only mode loads; invalid negative limits fail; analysis thresholds are 0–1 or 0–100 consistently. Definition of Done: Agent B/C can read safe limits without inventing constants.

Task A6 — Agent A Report and Commit
Story/Epic: PM governance. Jira: SCRUM-246. Files: `docs/cycle_reports/CYCLE_004_AGENT_A.md`. Implementation details: Create a concise report with branch state, PR # status, merge result, files changed, tests run, blockers, and whether `main` was untouched. Required validation: run `python -m pytest tests/unit/test_config.py tests/unit/test_models.py tests/unit/test_cli.py tests/unit/test_utils.py tests/integration/test_database_init.py -q`, `python -m ruff check .`, and `python -m mypy src` if dependencies are available. If dependencies are missing, report exact error and do not claim pass. Commit message: `chore(foundation): prepare cycle 004 phase2 gate and hygiene [Agent A]`. Definition of Done: branch is ready for Agent B or clearly blocked.
```

### Agent B Prompt — Collection Workflow Expansion

```text
PROJECT CONTEXT
Project: Fiverr Research System. Local repo root: C:\Fiverr\Fiverr. Cycle: 004. Branch: cycle/004/integration after Agent A confirms Cycle 003 merge and branch creation. Active focus: Epic 02 Collection Engine expansion using fixture-backed and dry-run-only workflows. No live Fiverr scraping, no account mutation, no unauthorized automation, and no direct GitHub push by Agent B.

YOUR ROLE
You are Agent B — Collection Engineer. You own `src/collection/`, `tests/unit/test_collection.py`, `tests/integration/test_collection_e2e.py`, and collection fixtures under `tests/fixtures/collection/`. You must not modify config/models/analysis/llm/dashboard/report/export files. If you need a shared config/model change, document it in your report for Agent A or a later cycle.

GIT INSTRUCTIONS
Start after Agent A commit. Confirm `git branch --show-current` is `cycle/004/integration`. Run `git status --short` and stop if uncommitted files outside collection/test fixture ownership exist. Commit only your files. Do not push. Commit message: `feat(collection): add fixture-backed detail seller and signal workflows [Agent B]`.

TASKS FOR THIS CYCLE

Task B1 — Gig Detail Fixture Parser
Story/Epic: S2.9 / Epic 02 Collection. Jira: SCRUM-149. Spec References: `ref/todo/EPIC_02_COLLECTION.md` Story 2.9; `ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md` Stage 4. Files: `src/collection/gig_detail.py`, `tests/fixtures/collection/gig_detail.html`, `tests/unit/test_collection.py`. Implementation details: Implement fixture-backed parsing for gig detail data from static HTML strings. Extract or gracefully miss title, seller name, package names, package prices, delivery days, description, FAQ presence, rating, review count, image count, and metadata fields. Use selector registry from Cycle 003. The parser must not fetch pages or launch a browser. Required tests: complete fixture parses expected title/packages; missing optional fields create warnings not crashes; malformed HTML returns controlled warning/error; prices normalize to numeric cents or Decimal-safe strings. Definition of Done: Stage 4 parser exists behind a safe local boundary.

Task B2 — Seller Profile Fixture Parser
Story/Epic: S2.10 / Epic 02 Collection. Jira: SCRUM-150. Spec References: `ref/todo/EPIC_02_COLLECTION.md` Story 2.10; `ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md` Stage 5. Files: `src/collection/seller_profile.py`, `tests/fixtures/collection/seller_profile.html`, `tests/unit/test_collection.py`. Implementation details: Implement fixture-backed seller profile parsing for seller username/display name, level, rating, review count, country, languages, member-since, response time, last delivery if available, active gig count if available, and warning list. Do not collect sensitive/private account data. Required tests: complete fixture parses stable fields; missing rating/review count returns warnings; parser redacts suspicious email/API-key-like strings; no browser/network imports. Definition of Done: seller profile records can feed analysis without live source calls.

Task B3 — Autocomplete Fixture and Planning Workflow
Story/Epic: S2.13 / Epic 02 Collection. Jira: SCRUM-153. Spec References: `ref/todo/EPIC_02_COLLECTION.md` Story 2.13; `ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md` Stage 2b. Files: `src/collection/autocomplete.py`, `tests/fixtures/collection/autocomplete_suggestions.json`, `tests/unit/test_collection.py`. Implementation details: Add autocomplete suggestion ingestion from local JSON fixture and query planning object for future live autocomplete. Normalize suggestions, remove duplicates, preserve source keyword lineage, and tag collection mode as fixture/dry_run. Required tests: duplicate suggestions collapse; suggestions preserve seed keyword; empty fixture creates warning; invalid JSON raises controlled error. Definition of Done: autocomplete can be simulated safely before live browser support.

Task B4 — External Trend Signal Connector Contract
Story/Epic: S2.11 / Epic 02 Collection. Jira: SCRUM-151. Spec References: `ref/project_plan/03_data/SOURCE_CONNECTORS.md`, `ref/project_plan/03_data/FRESHNESS_MODEL.md`, `ref/todo/EPIC_02_COLLECTION.md` Story 2.11. Files: `src/collection/external_signals.py`, `tests/unit/test_collection.py`. Implementation details: Create connector contract and fixture-based trend signal ingestion. Define `ExternalSignal`, `SignalSource`, `SignalFreshness`, and a fixture reader for local trend data. Live network calls must be impossible by default and require explicit future connector implementation. Required tests: fixture records validate; stale signal is marked stale; disabled live connector raises clear error; source names are constrained. Definition of Done: trend-signal data shape is ready for analysis/scoring.

Task B5 — Reddit/Community Signal Fixture Contract
Story/Epic: S2.12 / Epic 02 Collection. Jira: SCRUM-152. Spec References: `ref/todo/EPIC_02_COLLECTION.md` Story 2.12; `ref/project_plan/03_data/SOURCE_CONNECTORS.md`. Files: `src/collection/community_signals.py`, `tests/fixtures/collection/community_signals.json`, `tests/unit/test_collection.py`. Implementation details: Add fixture-based community signal ingestion for aggregate/non-personal signals only: keyword, mention_count, sentiment_hint, sample_theme, source, captured_at, confidence. Do not store usernames, URLs to personal profiles, or private data. Required tests: aggregate fixture loads; missing confidence defaults safely; personal-data-like fields are rejected or ignored; records preserve keyword lineage. Definition of Done: community signal stage can run locally and safely.

Task B6 — Collection Orchestrator Stage 4–6 Dry Run
Story/Epic: S2.14 / Epic 02 Collection. Jira: SCRUM-154. Spec References: `ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md`, `ref/dod/DOD_EPIC_02.md`. Files: `src/collection/orchestrator.py`, `tests/integration/test_collection_e2e.py`. Implementation details: Extend dry-run orchestrator so it can optionally read local fixtures for gig detail, seller profile, autocomplete, trend signals, and community signals after keyword expansion/search planning. Return stage counts and warnings in `CollectionStageResult.metadata`. Required tests: dry run with fixtures reports each stage count; missing fixture path returns failed result without traceback; no network/browser calls occur; checkpoint includes stage summary. Definition of Done: Epic 02 can demonstrate a safe end-to-end local collection dry-run through Stage 6b.

Task B7 — Agent B Report
Story/Epic: PM governance. Files: `docs/cycle_reports/CYCLE_004_AGENT_B.md`. Implementation details: Report changed files, fixture coverage, tests run, skipped live behaviors, and any Agent A/C dependencies. Run `python -m pytest tests/unit/test_collection.py tests/integration/test_collection_e2e.py -q`, `python -m ruff check src/collection tests/unit/test_collection.py tests/integration/test_collection_e2e.py`, and `python -m mypy src/collection`. Commit only after validation or clear dependency failure report.
```

### Agent C Prompt — Analysis Workflow Expansion

```text
PROJECT CONTEXT
Project: Fiverr Research System. Local repo root: C:\Fiverr\Fiverr. Cycle: 004. Branch: cycle/004/integration. Active focus: Epic 03 Analysis Engine expansion. Cycle 003 added dry-run keyword clustering, gig quality, and competitor profiling. Cycle 004 expands seller strength, saturation, review analysis, intent classification, and stage orchestration. No live LLM calls unless explicitly mocked; no collection files; no GitHub push.

YOUR ROLE
You are Agent C — Analysis/Scoring/LLM Engineer. You own `src/analysis/` and `tests/unit/test_analysis.py`. You may touch `src/llm/` only for compatibility bug fixes directly required by analysis validation, and those must be documented. Do not edit models/config/collection/dashboard/report/export files.

GIT INSTRUCTIONS
Start after Agent B commit. Confirm branch is `cycle/004/integration`. Stop if files outside your owned areas are dirty. Commit message: `feat(analysis): add seller saturation review and intent analysis [Agent C]`. Do not push.

TASKS FOR THIS CYCLE

Task C1 — Seller Strength Model
Story/Epic: S3.4 / Epic 03 Analysis. Jira: SCRUM-160. Spec References: `ref/todo/EPIC_03_ANALYSIS.md` Story 3.4; `ref/project_plan/06_analysis/SELLER_STRENGTH_MODEL.md`. Files: `src/analysis/seller_strength.py`, `src/analysis/contracts.py`, `tests/unit/test_analysis.py`. Implementation details: Implement deterministic seller strength scoring from fixture/collected seller fields: level, rating, review count, response time, delivery consistency if available, active gig count, language breadth, and account tenure. Output must include score 0–100, confidence, components, warnings, and explanation. Required tests: strong seller scores higher than weak seller; missing fields reduce confidence not crash; output serializes deterministically; score remains bounds-safe. Definition of Done: seller strength signal is usable by scoring later.

Task C2 — Saturation Model
Story/Epic: S3.5 / Epic 03 Analysis. Jira: SCRUM-161. Spec References: `ref/project_plan/06_analysis/SATURATION_MODEL.md`, `ref/project_plan/05_scoring/SATURATION_SCORE.md`. Files: `src/analysis/saturation.py`, `src/analysis/contracts.py`, `tests/unit/test_analysis.py`. Implementation details: Build saturation metrics using keyword count, search result count, competitor density, seller strength concentration, price crowding, and gig quality similarity. Return saturation_level enum low/medium/high/unknown, score 0–100 where higher means more saturated, confidence, and component breakdown. Required tests: high competitor density yields high saturation; sparse data returns unknown/low confidence; price crowding affects score; ties are deterministic. Definition of Done: saturation model feeds future scoring system.

Task C3 — Review Analysis
Story/Epic: S3.6 / Epic 03 Analysis. Jira: SCRUM-162. Spec References: `ref/project_plan/06_analysis/REVIEW_ANALYSIS.md`, `ref/todo/EPIC_03_ANALYSIS.md` Story 3.6. Files: `src/analysis/reviews.py`, `src/analysis/contracts.py`, `tests/unit/test_analysis.py`. Implementation details: Add local review-theme analysis over sanitized review snippets. Extract aggregate themes, sentiment hints, complaint frequency, praise frequency, opportunity gaps, and confidence. Do not preserve personal reviewer data. Required tests: repeated complaint themes surface as weaknesses; positive reviews surface strengths; empty reviews return low confidence warning; secret-like strings are redacted. Definition of Done: review analysis provides aggregate opportunity/weakness signals.

Task C4 — Intent Classification
Story/Epic: S3.7 / Epic 03 Analysis. Jira: SCRUM-163. Spec References: `ref/project_plan/06_analysis/GO_NOGO_LOGIC.md`, `ref/project_plan/06_analysis/LLM_PROMPT_TEMPLATES.md`, `ref/todo/EPIC_03_ANALYSIS.md` Story 3.7. Files: `src/analysis/intent.py`, `src/analysis/contracts.py`, `tests/unit/test_analysis.py`. Implementation details: Implement deterministic rule-based intent classification as a baseline before LLM integration. Categories: buyer_ready, research_only, low_intent, service_provider, ambiguous. Use keyword text, title phrases, price language, urgency markers, and service verbs. Return label, confidence, matched_rules, and explanation. Required tests: buyer-ready examples classify correctly; ambiguous queries return ambiguous with low confidence; service-provider phrases do not overstate buyer demand; serialization is deterministic. Definition of Done: intent classification exists and can be replaced/augmented by LLM later.

Task C5 — Analysis Stage Wiring Expansion
Story/Epic: S3.8 / Epic 03 Analysis. Jira: SCRUM-164. Spec References: `ref/todo/EPIC_03_ANALYSIS.md` Story 3.8; `ref/project_plan/06_analysis/RECOMMENDATION_OUTPUT_FORMAT.md`. Files: `src/analysis/orchestrator.py`, `tests/unit/test_analysis.py`. Implementation details: Extend `run_analysis_dry_run` to run seller strength, saturation, review analysis, and intent classification in addition to existing stages when payload sections are present. Preserve partial-failure behavior. The output run summary must list each stage, status, warnings, result type, and metadata counts. Required tests: complete fixture runs all stages successfully; missing reviews do not fail other stages; invalid seller input yields one failed stage only; summary status is success/partial/failed using clear logic. Definition of Done: Epic 03 dry-run can show full multi-stage analysis without external calls.

Task C6 — Analysis Fixtures and Golden Examples
Story/Epic: Epic 03 test quality. Jira: SCRUM-157–SCRUM-164. Files: `tests/fixtures/analysis/complete_payload.json`, `tests/fixtures/analysis/sparse_payload.json`, `tests/unit/test_analysis.py`. Implementation details: Add stable fixtures for a complete market sample and sparse market sample. Use them in tests to prevent hardcoded one-off cases scattered across tests. Required tests: complete fixture expected stage count; sparse fixture warnings count; fixture schema validation; golden score ordering for strong vs weak examples. Definition of Done: analysis tests are realistic enough for downstream scoring development.

Task C7 — Agent C Report
Story/Epic: PM governance. Files: `docs/cycle_reports/CYCLE_004_AGENT_C.md`. Implementation details: Summarize model decisions, assumptions, tests run, payload fixtures added, and known scoring dependencies. Run `python -m pytest tests/unit/test_analysis.py -q`, `python -m ruff check src/analysis tests/unit/test_analysis.py`, and `python -m mypy src/analysis`. Commit after validation or documented dependency failure.
```

### Agent D Prompt — Dashboard/Reporting + Final GitHub Steward

```text
PROJECT CONTEXT
Project: Fiverr Research System. Local repo root: C:\Fiverr\Fiverr. Cycle: 004. Branch: cycle/004/integration. Active focus: Phase 2 visibility and final integration stewardship. Cycle 004 must end with a clean branch, validation report, push to origin, and PR into develop. Main remains untouched.

YOUR ROLE
You are Agent D — Dashboard/Presentation Engineer and Final Integration/GitHub Steward. You own `src/dashboard/`, `src/reports/`, `src/exports/`, `src/playbook/`, `docs/`, `tests/unit/test_dashboard.py`, `tests/unit/test_reports.py`, and `tests/unit/test_playbook.py`. You also own final integration checks, cleanup of ignored runtime artifacts from the working tree/package, branch push, and PR creation/update. You may not modify Agent A/B/C owned source files except to run hygiene cleanup that does not alter tracked content.

GIT INSTRUCTIONS
Start after Agents A, B, and C commit. Confirm branch is `cycle/004/integration`. Do not touch main. At the end, run full validation and push only `cycle/004/integration` to origin. Open or update a PR from `cycle/004/integration` into `develop`. If a PR already exists, update it rather than creating a duplicate. Include final report in `docs/cycle_reports/CYCLE_004_AGENT_D.md`.

TASKS FOR THIS CYCLE

Task D1 — Dashboard Phase 2 State Panels
Story/Epic: Epic 09 prep supporting Epics 02/03. Jira: SCRUM-154, SCRUM-164, SCRUM-246. Spec References: `ref/project_plan/07_reporting/DASHBOARD_PLAN.md`, `ref/project_plan/12_dashboard_ux/DESIGN_SYSTEM.md`. Files: `src/dashboard/state.py`, `src/dashboard/navigation.py`, `src/dashboard/app.py`, `tests/unit/test_dashboard.py`. Implementation details: Add import-safe dashboard state models for collection dry-run status, analysis dry-run status, fixture coverage, gate status, and pending blockers. Do not launch Streamlit on import. Required tests: state serializes; dashboard imports without streamlit; navigation includes Phase 2 pages as disabled/preview; missing metrics render pending placeholders. DoD: PM and agents can inspect Phase 2 readiness through structured state.

Task D2 — Collection/Analysis Report Templates
Story/Epic: Reporting support. Jira: SCRUM-154, SCRUM-164. Spec References: `ref/project_plan/07_reporting/REPORT_TEMPLATES.md`, `ref/project_plan/07_reporting/RUN_LOG_DESIGN.md`. Files: `src/reports/templates.py`, `src/reports/run_summary.py`, `tests/unit/test_reports.py`. Implementation details: Add report models for collection fixture run, gig detail parser coverage, seller profile parser coverage, analysis multi-stage run, and Phase 2 PR readiness. Include severity enum validation and markdown rendering. Required tests: complete report renders markdown; missing sections are detected; invalid severity fails; report dict is JSON serializable. DoD: final PR body can include reliable generated summary content.

Task D3 — Export Manifest for Fixture/Dry-Run Outputs
Story/Epic: Reporting/export prep. Jira: SCRUM-149–SCRUM-164. Spec References: `ref/project_plan/07_reporting/EXPORT_FORMATS.md`. Files: `src/exports/manifest.py`, `src/exports/formats.py`, `tests/unit/test_reports.py`. Implementation details: Add export manifest support for fixture outputs and dry-run summaries with checksum placeholder validation, format normalization, and path safety. Do not write files outside allowed artifact directories. Required tests: manifest accepts supported formats; rejects traversal; requires checksum or explicit pending checksum state; serializes to dict. DoD: dry-run outputs can later be exported safely.

Task D4 — Operator Documentation Refresh
Story/Epic: PM/GitHub governance. Jira: SCRUM-246. Spec References: `ref/github/07_ai_workflow/AGENT_COORDINATION.md`, `ref/github/08_hygiene/HYGIENE_CHECKLIST.md`. Files: `docs/OPERATOR_QUICKSTART.md`, `docs/CYCLE_BRANCH_CHECKLIST.md`, `README.md`, `docs/SEED_DATA_GUIDE.md` if needed. Implementation details: Update docs to state that Cursor agents handle branch verification, push, and PR stewardship when authenticated. Human role is oversight/approval, not default executor. Add explicit warning that runtime DB files should not be included in handoff zips unless intentionally archived outside repo package. Required tests: docs mention no direct main push; docs mention cycle branch to develop; docs mention runtime DB hygiene. DoD: no operator-command ambiguity remains.

Task D5 — Final Validation and Hygiene Cleanup
Story/Epic: Cycle 004 steward. Jira: SCRUM-246. Files: tracked files only if adding final report; cleanup ignored runtime files locally. Implementation details: Remove ignored runtime DBs from the handoff working tree before creating zip/report if they are not needed. Run `git diff --ignore-space-at-eol --stat` and report if EOL-only changes remain. Run full validation: `python -m pytest -q`, `python -m ruff check .`, `python -m mypy src`, `python run.py config-check`, `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle004.db`, `python run.py phase2-smoke` if Agent A added it. Do not claim pass unless commands pass. DoD: branch has clean tracked state or documented blockers.

Task D6 — GitHub Push and PR Stewardship
Story/Epic: GitHub workflow. Jira: SCRUM-246. Spec References: `05_github_protocol/PR_CYCLE_BATCH.md`, `05_github_protocol/MERGE_PROTOCOL.md`. Files: `docs/cycle_reports/CYCLE_004_AGENT_D.md`. Implementation details: Push `cycle/004/integration` to origin. Create/update PR into `develop` with title `feat(cycle-004): expand collection and analysis dry-run workflows`. PR body must include summary, validation commands/results, changed areas, Jira list, branch policy, and main untouched confirmation. If GitHub credentials are missing or PR creation fails, report the exact failure and leave branch pushed if possible. Required validation: `git status --short`, `git log --oneline -10`, `git branch --show-current`, `git remote -v`, and PR URL. DoD: PR is open/updated or blocker report is complete.

Task D7 — Agent D Report and Commit
Story/Epic: PM governance. Files: `docs/cycle_reports/CYCLE_004_AGENT_D.md`. Implementation details: Include final commit list, validation results, PR URL, line-ending/artifact hygiene notes, main policy confirmation, and blockers. Commit message: `docs(reporting): add cycle 004 dashboard reports and steward handoff [Agent D]`.
```

---

## 5. STATE UPDATE

- Current cycle advanced to 004.
- Active phase remains Phase 2 entry, with Cycle 004 expanding Collection and Analysis while preserving Foundation release gate discipline.
- `SCRUM-246` remains open/In Review due Jira 502 and because PM process requires two clean cycles before closure.
- Cycle 004 pack includes four detailed prompts and this updated PM Pack zip per hard requirement.

---

## 6. NEXT CYCLE PREVIEW

Cycle 005 should review Cycle 004 PR results. If Cycle 004 validates and merges into `develop`, the next focus should be either:

1. Continue Epic 02 live-safe collection implementation with browser/session integration behind explicit config gates, or
2. Move into Epic 04 Scoring if Epic 03 reaches sufficient completeness and required analysis outputs are stable.

No direct work on `main` should occur until a formal release cycle.
