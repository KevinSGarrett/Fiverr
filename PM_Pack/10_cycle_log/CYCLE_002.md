# CYCLE 002 — 2026-05-13

**Focus:** Epic 01 Foundation completion + safe preparatory infrastructure for Collection/LLM/Dashboard layers  
**Branch:** `cycle/002/integration`  
**Source branch:** `develop` after Cycle 001 PR has been merged  
**Target PR:** `cycle/002/integration` → `develop`  
**Main rule:** No Cursor agent pushes to `main`. `main` is release-only after approved release gates.

---

## 0. CORRECTIVE PM NOTE

The prior corrective response correctly diagnosed the Cycle 001 prompt-depth and GitHub workflow problem, but it failed to include the next-cycle Cursor prompts. That was a PM process failure. Cycle 002 corrects that omission by providing a full actionable handoff: review summary, branch/PR strategy, cycle plan, and four detailed Cursor prompts with 5–8 substantive tasks per agent.

Permanent rule going forward: a process-correction response does not replace the cycle handoff. Every PM cycle reply must still contain four Cursor prompts unless the human explicitly says not to generate prompts.

---

## 1. REVIEW OF CYCLE 001 REPO STATE

### Evidence reviewed

Repository archive inspected: `Fiverr_000(1).zip`.

Observed Cycle 001 branch state:

```text
Branch: cycle/001/integration
Commits observed:
fe7b90d docs(foundation): add onboarding docs and presentation scaffolds [Agent D]
8d5bad8 feat(llm): add mocked client cache and renderer [Agent C]
3e6f5d2 chore(collection): add safe collection scaffolding [Agent B]
a185349 test(foundation): close remaining epic 01 config acceptance gaps
5ff7af2 feat(foundation): scaffold config and model base [Agent A]
```

Observed files created in Cycle 001:

```text
pyproject.toml
requirements.txt
.env.example
.gitignore
README.md
config.yaml
src/config/models.py
src/config/loader.py
src/models/base.py
src/models/database.py
src/models/niche.py
src/collection/contracts.py
src/collection/playwright_check.py
src/collection/safety.py
src/llm/client.py
src/llm/cache.py
src/llm/template_renderer.py
src/dashboard/app.py
src/reports/placeholders.py
src/exports/placeholders.py
src/playbook/seed_guidance.py
unit tests for config/models/collection/llm/dashboard/reports/playbook
```

### Validation caveat

I inspected the repository contents and commit history from the uploaded archive. I did **not** confirm a full passing test suite in this sandbox because this environment did not have the repo dependencies installed; attempting to run pytest stopped on missing `sqlalchemy`. The Cycle 002 prompts require each agent to run their assigned validation locally after dependencies are installed.

### Cycle 001 confidence assessment

| Agent | Observed work | Confidence | Notes |
|---|---|---:|---|
| A | Config, base model, initial database helpers, package setup | 82 | Good foundation, but S1.3 still incomplete because only initial model layer exists. |
| B | Collection contracts, safety, Playwright availability checker | 84 | Safe preparatory work; no active collection yet. |
| C | Mocked LLM client, cache, renderer | 82 | Good start; needs provider abstraction, robust retries, durable usage logging, structured output validation. |
| D | README, dashboard/report/export stubs, seed guidance | 80 | Useful scaffolds; needs documentation hardening and real export/report interfaces later. |

### Rework needed

No product-code failure is confirmed from inspection alone, but Cycle 002 must harden the foundation and add missing production-grade details. The PM process failure is tracked under `SCRUM-246`.

---

## 2. GITHUB WORKFLOW — MANDATORY FOR CYCLE 002

### Step A — Finish Cycle 001 first

Do not start Cycle 002 from the old Cycle 001 branch until Cycle 001 is pushed and merged into `develop`.

```bash
cd C:\Fiverr
git status
git checkout cycle/001/integration
git push -u origin cycle/001/integration
```

Open PR:

```text
Source: cycle/001/integration
Target: develop
Title: feat(cycle-001): establish foundation scaffolding and safe package contracts
```

After review and passing CI, squash-merge into `develop`.

### Step B — Create Cycle 002 branch from updated develop

```bash
cd C:\Fiverr
git checkout develop
git pull origin develop
git checkout -b cycle/002/integration
```

### Step C — Run agents sequentially on the same branch

```text
Agent A runs first -> commit
Agent B runs second -> commit
Agent C runs third -> commit
Agent D runs fourth -> commit
```

### Step D — Push only after all four agents commit

```bash
git status
git log --oneline -8
git push -u origin cycle/002/integration
```

### Step E — Open one PR into develop

```text
Source: cycle/002/integration
Target: develop
Title: feat(cycle-002): complete foundation database CLI and harden core service contracts
```

### Step F — Main branch policy

No Cursor agent should push to `main`. No cycle branch should be merged directly to `main`. `main` receives code only through a later release PR after Epic 01 release gates pass.

Expected future release path:

```text
cycle branches -> develop -> release/v0.1.0-foundation -> main
```

---

## 3. JIRA UPDATE PLAN

### Completed Jira update

| Issue | Status |
|---|---|
| SCRUM-246 — PM process bug | In Review after corrective follow-up |

### Cycle 002 scope tickets to update during execution

| Jira issue | Intended Cycle 002 status |
|---|---|
| SCRUM-136 — S1.3 Database Models | In Progress / In Review after Agent A |
| SCRUM-137 — S1.4 CLI Entry Point | In Progress |
| SCRUM-138 — S1.5 LLM Client and Cache | In Review if Agent C passes validation |
| SCRUM-139 — S1.6 Utility Modules | In Progress / In Review after Agent A/C support |
| SCRUM-141 — S2.1 Playwright Session Manager | In Progress, preparatory only |
| SCRUM-142 — S2.2 Fiverr Selectors | In Progress, registry only |
| SCRUM-143 — S2.3 Pacing Manager | In Progress |
| SCRUM-144 — S2.4 Queue Processor | In Progress |
| SCRUM-145 — S2.5 Checkpoint System | In Progress |

No tickets should be marked Done until the human provides validation evidence from the local repo.

---

## 4. CYCLE 002 PLAN

| Agent | Task count | Primary scope | File ownership |
|---|---:|---|---|
| Agent A | 7 | Expand database models, add CLI, init-db, utility foundation | `src/models/`, `src/scripts/`, `src/utils/`, `run.py`, model/CLI tests |
| Agent B | 7 | Collection infrastructure foundations without live scraping | `src/collection/`, collection tests |
| Agent C | 7 | LLM hardening, output validation, retry/cost/provider layers | `src/llm/`, `src/analysis/` interfaces, LLM/analysis tests |
| Agent D | 6 | Docs, dashboard/report/export scaffolding hardening | `README.md`, `docs/`, `src/dashboard/`, `src/reports/`, `src/exports/`, D tests |

### File overlap check

No agent may modify another agent's owned files. If an agent discovers that a change requires another agent's file, they must add a note in their completion report instead of editing it.

---

# 5. CURSOR AGENT PROMPTS

## Agent A Prompt — Infrastructure / Foundation Lead

```text
PROJECT CONTEXT
You are working on the Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local path: C:\Fiverr. Active branch for this cycle: cycle/002/integration. This branch must be created from the updated develop branch after Cycle 001 has been merged into develop. Tech stack: Python 3.11+, SQLAlchemy 2.0, Pydantic v2, Click, SQLite now with PostgreSQL-ready design, pytest, Ruff, Mypy.

YOUR ROLE
You are Agent A — Infrastructure Engineer and Epic 01 Foundation lead. Your job in Cycle 002 is to turn the Cycle 001 skeleton into a stronger foundation: expanded ORM model layer, database initialization, CLI entry point, reusable utilities, and integration tests. You own only these areas for this cycle: run.py, src/orchestrator.py, src/models/, src/scripts/, src/utils/, tests/conftest.py only if needed, tests/unit/test_models.py, tests/unit/test_config.py only if needed for existing config compatibility, tests/unit/test_utils.py, and tests/integration/test_database_init.py. Do not modify src/collection/, src/llm/, src/analysis/, src/dashboard/, src/reports/, src/exports/, src/playbook/, README.md, or tests owned by Agents B/C/D.

GIT INSTRUCTIONS
Before starting, confirm you are on cycle/002/integration. Do not push. Do not merge. Do not touch main. Commit only your assigned files.

Required start commands:
cd C:\Fiverr
git status
git checkout cycle/002/integration

Commit message:
feat(foundation): expand database cli and utilities [Agent A]

TASK A1 — Expand SQLAlchemy model foundation and naming conventions
Story/Epic: S1.3 / Epic 01 Foundation. Jira: SCRUM-136. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md Story 1.3; ref/dod/DOD_EPIC_01.md AC-1.3.1 through AC-1.3.30; ref/project_plan/03_data/SCHEMA.md; ref/project_plan/03_data/FIELD_CATALOG.md; ref/project_plan/03_data/VALIDATION_RULES.md. Files to create/modify: src/models/base.py, src/models/__init__.py, tests/unit/test_models.py.
Implementation Details: Upgrade the model base layer to be production-oriented without breaking Cycle 001 tests. Keep SQLAlchemy 2.0 typed declarative style. Add reusable mixins for integer primary key, created_at, updated_at, external_source, source_url, source_collected_at, metadata_json, and soft status where appropriate. Establish naming conventions for indexes and constraints so later migrations are stable. Add a Base.metadata naming convention dictionary if appropriate. Include helper functions for utc_now and safe_json_default if needed. Avoid global database connection creation at import time.
Required Tests: Verify model metadata can be imported without creating a DB connection. Verify the timestamp mixin creates non-null timestamps after insert. Verify metadata naming conventions are present. Verify no accidental duplicate table names exist in Base.metadata.
Definition of Done: Base layer supports all later model expansion, import remains side-effect free, and existing Cycle 001 tests still pass.

TASK A2 — Add core market/research models
Story/Epic: S1.3 / Epic 01 Foundation. Jira: SCRUM-136. Spec Reference: ref/project_plan/03_data/SCHEMA.md keyword/niche/search/gig/seller/review sections; ref/todo/EPIC_01_FOUNDATION.md tasks 1.3.4 through 1.3.14. Files to create/modify: src/models/market.py, src/models/niche.py, src/models/__init__.py, tests/unit/test_models.py.
Implementation Details: Add models for Keyword, SearchResult, Gig, Seller, Review, and ExternalSignal. Keep relationships explicit but not overly complex. Required fields should include stable identifiers, source fields, normalized text fields, and status fields. Keyword must relate to niche. SearchResult must relate to keyword. Gig should support seller relationship. Review should support gig relationship where possible. ExternalSignal should support source_name, signal_type, keyword_id nullable, raw_value_json, normalized_value, collected_at. Use JSON columns compatible with SQLite and PostgreSQL. Do not build collection logic here; only persistent structures.
Required Tests: Create temporary SQLite database, create all tables, insert a niche, keyword, search result, seller, gig, review, and external signal, then query them back. Verify unique constraints where clearly required, such as niche_id and possibly keyword+niche combination. Verify nullable fields allow sparse early data.
Definition of Done: Core market entities exist and are usable by collection/analysis layers without live scraping.

TASK A3 — Add analysis, scoring, pricing, recommendation, discovery, and run-log models
Story/Epic: S1.3 / Epic 01 Foundation. Jira: SCRUM-136. Spec Reference: ref/project_plan/03_data/SCHEMA.md analysis/scoring/recommendation/run sections; ref/project_plan/07_reporting/RUN_LOG_DESIGN.md; ref/project_plan/05_scoring/SCORING_SYSTEM.md. Files to create/modify: src/models/analysis.py, src/models/scoring.py, src/models/runtime.py, src/models/__init__.py, tests/unit/test_models.py.
Implementation Details: Add enough models to move toward the required 28-table foundation while staying maintainable. Include AnalysisRun, AnalysisResult, ScoreComponent, FinalScore, Recommendation, PricingSnapshot, DiscoveryHypothesis, RunLog, JobStatus, AlertEvent, ExportArtifact, LLMUsageLog, and LLMCacheRecord if the existing LLM layer does not own persistent schema. Use simple fields now: foreign keys, score_name, score_value, explanation, confidence, status, error_message, raw_json, created_at. Avoid tying business formulas to the models; that belongs in scoring later. Include indexes on run_id, keyword_id, gig_id, seller_id, score_name, and status where useful.
Required Tests: Verify all model modules import. Verify Base.metadata contains at least the expected tables from Cycle 001 plus the new model tables. Verify insert/query works for a RunLog, AnalysisResult, ScoreComponent, FinalScore, and Recommendation. Verify JSON fields store dict values in SQLite.
Definition of Done: Model layer is broad enough that later epics do not need to invent their own tables ad hoc.

TASK A4 — Harden database initialization and session helpers
Story/Epic: S1.3 / Epic 01 Foundation. Jira: SCRUM-136. Spec Reference: ref/dod/DOD_EPIC_01.md database initialization gate; ref/project_plan/02_architecture/SYSTEM_ARCHITECTURE.md persistence layer. Files to create/modify: src/models/database.py, src/scripts/init_db.py, tests/integration/test_database_init.py.
Implementation Details: Expand database.py with robust helpers: normalize_database_url, build_engine, create_session_factory, get_session context manager, initialize_database, drop_database_for_tests only gated for tests, list_tables, and verify_required_tables. Ensure default database path is data/fiverr_research.db and parent directories are created only when explicitly initializing, not on import. src/scripts/init_db.py should expose a callable main(database_url=None) that initializes all metadata and prints a concise table count. It must be usable from CLI later.
Required Tests: Temporary SQLite init creates all expected tables. verify_required_tables reports missing tables clearly. get_session commits on success and rolls back on failure. Parent data path creation works in a temp directory.
Definition of Done: `python -m src.scripts.init_db` or equivalent can initialize the database after dependencies are installed.

TASK A5 — Implement CLI entry point for init-db, config-check, and smoke
Story/Epic: S1.4 / Epic 01 Foundation. Jira: SCRUM-137. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md Story 1.4; ref/dod/DOD_EPIC_01.md CLI acceptance criteria; ref/project_plan/02_architecture/API_SURFACE.md. Files to create/modify: run.py, src/orchestrator.py, tests/unit/test_cli.py if you create it.
Implementation Details: Create a Click-based CLI if one does not exist. Commands/modes required now: init-db, config-check, smoke, and run with --mode choices full, collect-only, score-only, analyze-only, recommendations-only, discovery-only, resume. The `run` command should not pretend the pipeline is complete; it should load config, initialize logging, print/return a clear stage availability message, and exit cleanly for unavailable downstream stages. `init-db` should call database initialization. `config-check` should load config.yaml and report niches/profiles. `smoke` should run import smoke checks for config, models, collection contracts, llm client, dashboard placeholder, exports placeholder.
Required Tests: Use Click CliRunner to verify config-check exits 0, invalid config path exits nonzero, init-db creates temp database, smoke exits 0. Do not require network or OpenAI credentials.
Definition of Done: CLI exists, is safe, and does not overclaim unbuilt features.

TASK A6 — Add shared utility modules
Story/Epic: S1.6 / Epic 01 Foundation. Jira: SCRUM-139. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md Story 1.6; ref/dod/DOD_EPIC_01.md utility acceptance criteria; ref/project_plan/03_data/VALIDATION_RULES.md. Files to create/modify: src/utils/__init__.py, src/utils/logging.py, src/utils/paths.py, src/utils/retry.py, src/utils/json.py, tests/unit/test_utils.py.
Implementation Details: Implement generic utilities only. logging.py should provide configure_logging(log_level="INFO", redact_secrets=True) and a simple RedactingFilter that redacts strings matching API key-like patterns. paths.py should provide ensure_dir, project_root, resolve_data_path. retry.py should provide a simple retry decorator with bounded attempts, exponential delay parameters, and exception filters, but tests must avoid real sleeping by allowing injected sleep function. json.py should provide safe_json_dumps and safe_json_loads with clear error messages.
Required Tests: Verify logging redacts fake keys. Verify ensure_dir creates nested temp directory. Verify retry succeeds after transient failure and stops after max attempts. Verify safe_json_loads raises clear error on malformed JSON.
Definition of Done: Utilities are reusable and do not contain product-specific collection/scoring/dashboard logic.

TASK A7 — Agent A validation and completion report
Story/Epic: Cycle QA / Epic 01. Jira: SCRUM-136, SCRUM-137, SCRUM-139. Files to create/modify: do not create a report file unless there is an existing reports directory for agent reports; otherwise provide completion output in Cursor response.
Implementation Details: Run targeted validation and report exact results. Fix failures in your owned files before committing. Do not modify other agents' files to fix cross-agent issues; report them.
Required Validation Commands:
python -m pip install -e .
python -m ruff check run.py src/models src/scripts src/utils tests/unit/test_models.py tests/unit/test_utils.py tests/integration/test_database_init.py
python -m mypy src/models src/scripts src/utils
python -m pytest tests/unit/test_models.py tests/unit/test_utils.py tests/integration/test_database_init.py -q
python run.py config-check
python run.py init-db --database-url sqlite:///data/fiverr_research_cycle002.db
python run.py smoke
Definition of Done: Commit is made only after owned validation passes or a precise blocker is documented.

FILES YOU MAY CREATE OR MODIFY
run.py
src/orchestrator.py
src/models/base.py
src/models/database.py
src/models/niche.py
src/models/market.py
src/models/analysis.py
src/models/scoring.py
src/models/runtime.py
src/models/__init__.py
src/scripts/init_db.py
src/scripts/__init__.py
src/utils/__init__.py
src/utils/logging.py
src/utils/paths.py
src/utils/retry.py
src/utils/json.py
tests/unit/test_models.py
tests/unit/test_utils.py
tests/unit/test_cli.py
tests/integration/test_database_init.py

COMMIT INSTRUCTIONS
git add run.py src/orchestrator.py src/models src/scripts src/utils tests/unit/test_models.py tests/unit/test_utils.py tests/unit/test_cli.py tests/integration/test_database_init.py && git commit -m "feat(foundation): expand database cli and utilities [Agent A]"
```

---

## Agent B Prompt — Collection Infrastructure Engineer

```text
PROJECT CONTEXT
You are working on the Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local path: C:\Fiverr. Active branch: cycle/002/integration. This branch is shared by all four agents for Cycle 002 and must later be pushed as one PR into develop. You are not allowed to push or merge.

YOUR ROLE
You are Agent B — Collection Engineer. Your job in Cycle 002 is to build safe, testable, read-only collection infrastructure foundations. This does not mean live scraping. Do not make network calls in tests. Do not automate login. Do not collect real Fiverr data. Build selector registries, pacing, queue, checkpoint, session abstractions, proxy config, and orchestration skeletons that future Epic 02 work can use. You own only src/collection/ and tests/unit/test_collection.py plus tests/integration/test_collection_e2e.py if needed. Do not edit root packaging, src/models, src/config, src/llm, src/utils, dashboard/report/export/playbook files, or their tests.

GIT INSTRUCTIONS
Confirm branch:
cd C:\Fiverr
git status
git checkout cycle/002/integration
Do not push. Do not merge. Commit only your files.
Commit message:
feat(collection): add queue pacing checkpoint and selector foundations [Agent B]

TASK B1 — Central selector registry foundation
Story/Epic: S2.2 preparatory / Epic 02, allowed as Phase 1 support because it is no-network scaffolding. Jira: SCRUM-142. Spec Reference: ref/todo/EPIC_02_COLLECTION.md Story 2.2; ref/dod/DOD_EPIC_02.md selectors criteria; ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md; ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md. Files to create/modify: src/collection/selectors.py, src/collection/__init__.py, tests/unit/test_collection.py.
Implementation Details: Create a central selector registry with typed selector groups for search results, gig detail pages, seller profiles, autocomplete, and generic navigation. Do not hard-code brittle one-selector-only logic. Each selector entry should include name, css candidates, xpath candidates optional, description, required boolean, and fallback priority. Add functions get_selector_group(group_name), list_selector_groups(), validate_selector_registry(), and explain_missing_required_selectors(). Include safe placeholder selectors where exact values are not confirmed but mark them as unverified. Do not make Playwright calls in this module.
Required Tests: Verify all required selector groups exist. Verify registry validation passes with current definitions. Verify missing required selector detection works with a test registry. Verify no selector group is empty.
Definition of Done: Future collection code can reference selectors centrally and tests prove registry structure.

TASK B2 — Pacing manager with source-specific limits
Story/Epic: S2.3 preparatory / Epic 02. Jira: SCRUM-143. Spec Reference: ref/project_plan/04_collection/PACING_MODEL.md; ref/todo/EPIC_02_COLLECTION.md Story 2.3; ref/dod/DOD_EPIC_02.md pacing criteria. Files to create/modify: src/collection/pacing.py, tests/unit/test_collection.py.
Implementation Details: Implement PacingManager with configuration dataclass/Pydantic model fields: base_delay_seconds, jitter_min_seconds, jitter_max_seconds, max_requests_per_minute, cooldown_after_error_seconds, cooldown_after_429_seconds, adaptive_backoff_multiplier, max_backoff_seconds. Provide methods next_delay(source="fiverr"), record_success(source), record_error(source, status_code=None), should_cooldown(source), and get_state(source). Use injected random provider and clock for deterministic tests. Do not sleep inside next_delay; return the delay for callers to apply. Safety requirement: repeated 429 or block-like errors must increase cooldown, not decrease it.
Required Tests: Deterministic delay with injected random. Repeated error increases cooldown. 429 applies stronger cooldown. Success reduces or resets backoff safely. No unbounded negative delay is possible.
Definition of Done: Pacing logic is safe, deterministic under test, and never bypasses cooldown.

TASK B3 — Queue processor skeleton with bounded retries
Story/Epic: S2.4 preparatory / Epic 02. Jira: SCRUM-144. Spec Reference: ref/project_plan/04_collection/QUEUE_DESIGN.md; ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md; ref/todo/EPIC_02_COLLECTION.md Story 2.4. Files to create/modify: src/collection/queue.py, tests/unit/test_collection.py.
Implementation Details: Create queue models for CollectionJob, JobPriority, JobStatus, RetryPolicy, and QueueProcessor. Keep implementation in-memory for now but design it so later persistence can attach. QueueProcessor should support enqueue(job), dequeue(), mark_running(job_id), mark_success(job_id), mark_failed(job_id, error), retry_or_dead_letter(job_id, error), and snapshot(). Enforce bounded retries and move exhausted jobs to dead_letter status. Preserve error messages and attempt counts. No concurrency in this cycle; keep it deterministic.
Required Tests: Higher-priority jobs dequeue first. Failed job retries until max attempts then dead letters. Successful job records status and timestamps. Queue snapshot includes waiting/running/succeeded/failed/dead_letter counts.
Definition of Done: Queue behavior is deterministic, retry-bounded, and ready for checkpoint integration.

TASK B4 — Checkpoint manager with atomic writes
Story/Epic: S2.5 preparatory / Epic 02. Jira: SCRUM-145. Spec Reference: ref/project_plan/04_collection/RETRY_AND_CHECKPOINT.md; ref/todo/EPIC_02_COLLECTION.md Story 2.5. Files to create/modify: src/collection/checkpoint.py, tests/unit/test_collection.py.
Implementation Details: Implement CheckpointManager with JSON checkpoint files. Methods: save_checkpoint(run_id, payload), load_checkpoint(run_id), checkpoint_exists(run_id), list_checkpoints(), mark_complete(run_id), and delete_checkpoint(run_id, allow_delete=False). Save must be atomic: write to temporary file then replace. Include schema version, run_id, stage_name, cursor/offset, record counts, updated_at, and payload. If a checkpoint is corrupted, load_checkpoint should raise a clear CheckpointCorruptionError and preserve the original file.
Required Tests: Save/load round trip. Atomic write leaves final file. Corrupted JSON raises custom error. Delete requires allow_delete=True. list_checkpoints returns known run IDs.
Definition of Done: Checkpoint/resume foundation exists without data loss or silent corruption.

TASK B5 — Playwright session manager abstraction without live login
Story/Epic: S2.1 preparatory / Epic 02. Jira: SCRUM-141. Spec Reference: ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md; ref/todo/EPIC_02_COLLECTION.md Story 2.1; security references from PM pack. Files to create/modify: src/collection/session.py, tests/unit/test_collection.py.
Implementation Details: Create abstractions only: BrowserMode enum, SessionState dataclass, SessionManagerConfig, and PlaywrightSessionManager with methods describe_required_manual_setup(), session_state_path(), validate_session_state_file(), and build_launch_options(). Do not launch a browser unless a test explicitly mocks Playwright. Do not store cookies or browser state in the repo. The session manager should clearly distinguish unauthenticated_read_only and authenticated_read_only modes. Add guardrails so missing session files return a structured validation result rather than crashing.
Required Tests: Missing session file returns valid=False with clear message. Launch options do not include credentials. Authenticated mode requires external session path. Unauthenticated mode can proceed without session file. Browser state file paths under repo are rejected unless ignored/safe.
Definition of Done: Session behavior is explicit and safe, but not active scraping.

TASK B6 — Optional proxy configuration abstraction
Story/Epic: S2.6 preparatory / Epic 02. Jira: SCRUM-146. Spec Reference: ref/project_plan/04_collection/PROXY_LAYER.md; ref/todo/EPIC_02_COLLECTION.md Story 2.6. Files to create/modify: src/collection/proxy.py, tests/unit/test_collection.py.
Implementation Details: Implement ProxyConfig and ProxyProvider. Proxy support must be optional. Config should include enabled, server, username_env_var, password_env_var, country, provider_name, and redact() method. The provider should build Playwright-compatible proxy settings only when enabled and env vars exist. Never return raw secrets in repr, logs, exceptions, or tests. Missing credentials should produce a safe ProxyConfigurationError with redacted context.
Required Tests: Disabled proxy returns None. Enabled proxy with env credentials returns expected dict. repr/redact hides fake password. Missing env var raises safe error without secret leakage.
Definition of Done: Proxy layer is secure and pluggable.

TASK B7 — Collection orchestration skeleton and validation report
Story/Epic: S2.14 preparatory / Epic 02. Jira: SCRUM-154 as future reference, not Done this cycle. Spec Reference: ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md; ref/todo/EPIC_02_COLLECTION.md stage orchestration overview. Files to create/modify: src/collection/orchestrator.py, tests/integration/test_collection_e2e.py or tests/unit/test_collection.py.
Implementation Details: Create a no-network CollectionOrchestrator that can accept staged callables and execute them in configured order using the queue, pacing manager, checkpoint manager, and contracts from Cycle 001. Include dry_run=True default. It should return CollectionStageResult objects and never call real Playwright/Fiverr code. This is a skeleton to prove stage composition, not a scraper.
Required Tests: Dry-run orchestrator runs two fake stages in order. Failure in one fake stage records failure without losing prior stage result. Checkpoint is saved after a fake stage. Pacing manager is consulted but no sleep occurs.
Definition of Done: Future collection stages have a safe orchestrator foundation.

VALIDATION STEPS
python -m ruff check src/collection tests/unit/test_collection.py tests/integration/test_collection_e2e.py
python -m mypy src/collection
python -m pytest tests/unit/test_collection.py tests/integration/test_collection_e2e.py -q
python -c "from src.collection.pacing import PacingManager; from src.collection.queue import QueueProcessor; from src.collection.checkpoint import CheckpointManager"

FILES YOU MAY CREATE OR MODIFY
src/collection/__init__.py
src/collection/selectors.py
src/collection/pacing.py
src/collection/queue.py
src/collection/checkpoint.py
src/collection/session.py
src/collection/proxy.py
src/collection/orchestrator.py
tests/unit/test_collection.py
tests/integration/test_collection_e2e.py

COMMIT INSTRUCTIONS
git add src/collection tests/unit/test_collection.py tests/integration/test_collection_e2e.py && git commit -m "feat(collection): add queue pacing checkpoint and selector foundations [Agent B]"
```

---

## Agent C Prompt — LLM / Analysis Foundations Engineer

```text
PROJECT CONTEXT
You are working on the Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local path: C:\Fiverr. Active branch: cycle/002/integration. Cycle 002 runs on a shared branch after Agent A and Agent B have committed. You must not push or merge.

YOUR ROLE
You are Agent C — Analysis, Scoring, Recommendations, Pricing, Discovery, and LLM Engineer. In this cycle your primary work is to harden the LLM foundation from Story S1.5 and add safe analysis-facing interfaces without implementing full market analysis yet. You may touch only src/llm/, src/analysis/ interface-only files, tests/unit/test_llm.py, and tests/unit/test_analysis.py. Do not modify src/models, src/config, src/collection, src/utils, run.py, dashboard/report/export/playbook, or their tests.

GIT INSTRUCTIONS
Confirm branch:
cd C:\Fiverr
git status
git checkout cycle/002/integration
Do not push. Do not merge. Commit only your assigned files.
Commit message:
feat(llm): harden provider validation retry and analysis interfaces [Agent C]

TASK C1 — Add provider abstraction and OpenAI adapter shell
Story/Epic: S1.5 / Epic 01 Foundation. Jira: SCRUM-138. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md Story 1.5; ref/dod/DOD_EPIC_01.md AC-1.5.1; ref/project_plan/02_architecture/SYSTEM_ARCHITECTURE.md LLM layer. Files to create/modify: src/llm/provider.py, src/llm/client.py, src/llm/__init__.py, tests/unit/test_llm.py.
Implementation Details: Split provider concerns from LLMClient. Define a protocol/interface for chat completion and embeddings. Provide MockLLMProvider for tests and OpenAIProvider shell that reads API key from env at runtime only, never import time. OpenAIProvider should not be used in unit tests. LLMClient should accept provider injection and should never instantiate a network provider unless explicitly requested. Keep prompt text out of logs by default.
Required Tests: Mock provider completion works. LLMClient does not require OPENAI_API_KEY when a mock provider is injected. OpenAIProvider initialization with missing key raises a clear error only when constructed. Prompt text is not included in repr/log metadata.
Definition of Done: LLM provider boundary is testable and no live credentials are needed for local unit tests.

TASK C2 — Durable cache upgrade and cache policy controls
Story/Epic: S1.5 / Epic 01 Foundation. Jira: SCRUM-138. Spec Reference: ref/dod/DOD_EPIC_01.md cache criteria; ref/project_plan/03_data/FRESHNESS_MODEL.md. Files to create/modify: src/llm/cache.py, tests/unit/test_llm.py.
Implementation Details: Upgrade the existing cache so it supports deterministic SHA-256 keys, TTL, model/prompt metadata, response payload, created_at, expires_at, cache_version, and invalidation. SQLite-backed cache is preferred if already started; otherwise implement it now with sqlite3 from the standard library to avoid ORM coupling. Do not create cache DB on import. Include CachePolicy with ttl_hours, enabled, cache_namespace, and max_prompt_chars_for_keying metadata. For safety, keys should hash prompt content and not store full prompt unless explicitly requested; default should store prompt_hash only.
Required Tests: Cache write/read round trip. Expired record misses. Disabled policy bypasses get/set. Same inputs produce same key; changed model/temperature changes key. No raw fake API key is stored in the cache file or record dict.
Definition of Done: Cache can be reused by analysis/recommendation calls without accidental secret or prompt leakage.

TASK C3 — Structured output schemas and validation error handling
Story/Epic: S1.5 foundation supporting later Epics 03/05. Jira: SCRUM-138. Spec Reference: ref/project_plan/06_analysis/RECOMMENDATION_OUTPUT_FORMAT.md; ref/project_plan/06_analysis/LLM_PROMPT_TEMPLATES.md; ref/dod/DOD_EPIC_01.md validation retry criteria. Files to create/modify: src/llm/schemas.py, src/llm/validation.py, tests/unit/test_llm.py.
Implementation Details: Create generic Pydantic schemas for LLMTaskResult, ValidationIssue, RetryDecision, TokenUsage, and CostEstimate. Add parse_json_response(model_cls, raw_text) that returns typed output or raises LLMValidationError with sanitized details. Include truncate_for_error_message and redact_sensitive_text helpers local to LLM validation if needed. Do not implement Fiverr-specific recommendation prompts yet; keep this generic and reusable.
Required Tests: Valid JSON parses into schema. Malformed JSON raises LLMValidationError. Missing required field raises sanitized validation error. Fake secret values are redacted from errors.
Definition of Done: Later analysis/recommendation code has a safe validation boundary.

TASK C4 — Retry, backoff, and self-correction prompt builder
Story/Epic: S1.5 / Epic 01. Jira: SCRUM-138. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md tasks 1.5.5–1.5.6; ref/project_plan/06_analysis/LLM_PROMPT_TEMPLATES.md. Files to create/modify: src/llm/retry.py, src/llm/template_renderer.py, tests/unit/test_llm.py.
Implementation Details: Implement LLMRetryPolicy with max_attempts, retry_on_validation_error, retry_on_rate_limit, retry_on_transient_error, base_delay_seconds, max_delay_seconds. Provide compute_delay(attempt, jitter_provider=None) without sleeping. Add build_self_correction_prompt(original_task_name, schema_hint, validation_error) that instructs the model to return corrected structured output only. It must not include raw secrets or full original prompt by default; include prompt_hash or task_name instead.
Required Tests: Delay increases with attempts and caps. Validation error returns retry decision when enabled. Prompt builder includes schema hint and sanitized validation detail. Prompt builder does not include fake API key strings.
Definition of Done: Retry/self-correction behavior is deterministic and safe.

TASK C5 — Cost tracking and usage event objects
Story/Epic: S1.5 / Epic 01. Jira: SCRUM-138. Spec Reference: ref/project_plan/07_reporting/RUN_LOG_DESIGN.md; ref/dod/DOD_EPIC_01.md cost logging requirement. Files to create/modify: src/llm/costs.py, src/llm/client.py, tests/unit/test_llm.py.
Implementation Details: Create centralized price table and estimate_llm_cost(model, input_tokens, output_tokens). Include known models from Cycle 001 and allow unknown models to return CostEstimate with confidence="unknown" or raise depending on strict flag. LLMClient completion metadata should include usage event: model, task_name optional, input_tokens, output_tokens, total_tokens, estimated_cost_usd, cache_hit, provider_name, created_at. Do not persist to DB in this agent; Agent A owns model persistence.
Required Tests: Known model cost calculation exact for sample tokens. Unknown model behavior is safe and documented. LLMClient returns usage metadata for mock completion. Cache hit has zero or marked avoided cost depending on policy.
Definition of Done: Cost tracking exists and can feed reporting later.

TASK C6 — Analysis interface contracts without full implementation
Story/Epic: Epic 03 preparation only. Jira: SCRUM-157 future reference, not Done. Spec Reference: ref/project_plan/06_analysis/KEYWORD_CLUSTERING.md; ref/project_plan/06_analysis/GIG_QUALITY_RUBRIC.md; ref/project_plan/06_analysis/COMPETITOR_PROFILING.md. Files to create/modify: src/analysis/__init__.py, src/analysis/contracts.py, tests/unit/test_analysis.py.
Implementation Details: Create analysis-facing contracts so later analysis modules can consume collected data and LLM outputs. Include AnalysisInput, AnalysisOutput, AnalysisStatus, AnalysisError, and AnalysisTaskType enum values: keyword_clustering, gig_quality, competitor_profile, seller_strength, saturation, review_analysis, intent_classification. Keep this as interface only. Do not implement clustering/scoring logic yet.
Required Tests: Contracts instantiate and serialize. All expected AnalysisTaskType values exist. Failure output includes sanitized error message. No dependency on database or LLM provider during import.
Definition of Done: Analysis package is importable and ready for Epic 03 without premature implementation.

TASK C7 — Agent C validation and completion report
Story/Epic: Cycle QA. Jira: SCRUM-138. Implementation Details: Run validation for all owned files. Fix failures in owned files only. Do not change Agent A/B/D files.
Validation Commands:
python -m ruff check src/llm src/analysis tests/unit/test_llm.py tests/unit/test_analysis.py
python -m mypy src/llm src/analysis
python -m pytest tests/unit/test_llm.py tests/unit/test_analysis.py -q
python -c "from src.llm import LLMClient; from src.analysis.contracts import AnalysisTaskType"
Definition of Done: Owned tests pass, no live API key required, and completion report includes all files changed.

FILES YOU MAY CREATE OR MODIFY
src/llm/__init__.py
src/llm/client.py
src/llm/cache.py
src/llm/provider.py
src/llm/schemas.py
src/llm/validation.py
src/llm/retry.py
src/llm/template_renderer.py
src/llm/costs.py
src/analysis/__init__.py
src/analysis/contracts.py
tests/unit/test_llm.py
tests/unit/test_analysis.py

COMMIT INSTRUCTIONS
git add src/llm src/analysis tests/unit/test_llm.py tests/unit/test_analysis.py && git commit -m "feat(llm): harden provider validation retry and analysis interfaces [Agent C]"
```

---

## Agent D Prompt — Dashboard / Reporting / Documentation Engineer

```text
PROJECT CONTEXT
You are working on the Fiverr Research System. GitHub repository: https://github.com/KevinSGarrett/Fiverr. Local path: C:\Fiverr. Active branch: cycle/002/integration. This is a shared cycle branch and will be pushed once after all four agents commit. You must not push, merge, or edit main.

YOUR ROLE
You are Agent D — Dashboard, Playbook, Reporting, and Presentation Engineer. In Cycle 002 your job is to harden user-facing documentation and presentation/report/export package scaffolding so the system remains understandable, safe, and ready for later Epic 08/09 work. You may touch README.md, docs/, src/dashboard/, src/reports/, src/exports/, src/playbook/ if needed for documentation-facing guidance, tests/unit/test_dashboard.py, tests/unit/test_reports.py, tests/unit/test_playbook.py. Do not edit pyproject.toml, config.yaml, src/models, src/config, src/collection, src/llm, src/analysis, run.py, or tests owned by other agents.

GIT INSTRUCTIONS
Confirm branch:
cd C:\Fiverr
git status
git checkout cycle/002/integration
Do not push. Do not merge. Commit only your files.
Commit message:
docs(reporting): harden operator docs exports and dashboard scaffolds [Agent D]

TASK D1 — README correction and Cycle 002 operator workflow
Story/Epic: S1.1 / Epic 01 Foundation. Jira: SCRUM-45. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md task 1.1.7; ref/dod/DOD_EPIC_01.md documentation criteria; ref/github/02_pr_policy/PR_POLICY.md; ref/github/08_hygiene/RELEASE_PROCESS.md. Files to create/modify: README.md.
Implementation Details: Update README so it accurately reflects Cycle 001 plus Cycle 002 status. It must not overclaim that scraping, scoring, recommendations, or dashboard pages are complete. Add a “Branching and Release Workflow” section that explains: agents commit locally to cycle branches, human pushes one cycle branch, PR targets develop, main is release-only, no direct main pushes. Add “Current Foundation Commands” with config-check, init-db, smoke, pytest, ruff, mypy. Add “Known Current Limitations” that says collection is currently safe scaffolding only.
Required Tests: Manual grep or test helper can confirm headings exist: Installation, Configuration, Running, Testing, Branching and Release Workflow, Known Current Limitations. Verify no phrase says full pipeline is production complete.
Definition of Done: README is honest, operator-friendly, and matches the real workflow.

TASK D2 — Add docs/ operator quickstart and branch checklist
Story/Epic: Foundation documentation. Jira: SCRUM-45 / SCRUM-246 process prevention. Spec Reference: ref/github/07_ai_workflow/AGENT_COORDINATION.md; ref/github/01_branching/BRANCHING_STRATEGY.md. Files to create/modify: docs/OPERATOR_QUICKSTART.md, docs/CYCLE_BRANCH_CHECKLIST.md.
Implementation Details: Create an operator quickstart for Kevin/human operator. It should be copy-paste friendly and include exact PowerShell/Git commands for: checking current branch, creating cycle branch from develop, running agents in order, committing after each agent, pushing branch, opening PR into develop, and not touching main. The checklist should be short enough to use every cycle but detailed enough to prevent the missing-push/PR ambiguity from Cycle 001.
Required Tests: Documentation must include branch names with placeholders like cycle/002/integration and commands for git status, git log --oneline -8, git push -u origin cycle/002/integration. Verify it explicitly says “Do not push to main.”
Definition of Done: Human operator can follow docs without guessing.

TASK D3 — Dashboard app shell hardening
Story/Epic: Epic 09 preparation only, no full dashboard. Jira: SCRUM-unknown future dashboard, not Done. Spec Reference: ref/project_plan/07_reporting/DASHBOARD_PLAN.md; ref/project_plan/12_dashboard_ux/DESIGN_SYSTEM.md. Files to create/modify: src/dashboard/app.py, src/dashboard/navigation.py, src/dashboard/state.py, tests/unit/test_dashboard.py.
Implementation Details: Create a non-launching dashboard shell. app.py must remain import-safe and should expose build_page_title(), get_available_pages(), and main(). navigation.py should define page metadata for Overview, Niches, Keywords, Collection Runs, Scores, Recommendations, Reports, Settings, but mark unavailable pages as disabled/not_implemented. state.py should define DashboardState dataclass with selected_page, filters, active_run_id, and safe defaults. Do not call streamlit functions at import time; if streamlit is imported, do it inside main or guard it.
Required Tests: Importing dashboard modules does not launch Streamlit. get_available_pages returns expected page IDs. Disabled pages are clearly marked. DashboardState default is serializable or dataclass-asdict compatible.
Definition of Done: Dashboard foundation is ready without fake features.

TASK D4 — Export interface foundation
Story/Epic: Epic 09 export preparation. Jira future export, not Done. Spec Reference: ref/project_plan/07_reporting/EXPORT_FORMATS.md; ref/dod/DOD_EPIC_09.md export criteria for later reference. Files to create/modify: src/exports/placeholders.py or src/exports/formats.py, src/exports/manifest.py, tests/unit/test_reports.py.
Implementation Details: Upgrade export stubs into safe interfaces. Define ExportFormat enum or constants for csv, xlsx, json, html, pdf. Define ExportRequest with format, output_path, include_metadata, redaction_level, created_by optional. Define ExportManifest with artifact_path, format, row_count optional, created_at, source_run_id optional, checksum optional. Add validate_export_request that rejects unsupported formats and unsafe output paths such as parent directory traversal. Do not generate real PDF/XLSX yet unless existing code already supports it safely.
Required Tests: Supported formats validate. Unsupported format fails. Output path with ../ fails. Manifest can be created and serialized.
Definition of Done: Export layer has safe contracts for later implementation.

TASK D5 — Report template and run summary foundation
Story/Epic: Epic 09 reporting preparation. Spec Reference: ref/project_plan/07_reporting/REPORT_TEMPLATES.md; ref/project_plan/07_reporting/RUN_LOG_DESIGN.md. Files to create/modify: src/reports/placeholders.py or src/reports/templates.py, src/reports/run_summary.py, tests/unit/test_reports.py.
Implementation Details: Create report-facing structures for RunSummary, ReportSection, ReportSeverity, and ReportTemplate. Include sections for Executive Summary, Niche Overview, Demand Signals, Competition Signals, Scoring Summary, Recommendations, Risks/Limitations, and Data Freshness. This is not a generator yet; it is a typed structure and validation layer. Include render_plain_text_summary(summary) for a minimal safe text preview that can be tested without WeasyPrint.
Required Tests: RunSummary with minimal data validates. Plain text summary includes run ID and status. Missing required section can be detected. Severity values are constrained.
Definition of Done: Reporting layer has reusable contracts and does not overclaim final PDF/report generation.

TASK D6 — Playbook seed guidance hardening and docs linkage
Story/Epic: S1.7 / Epic 01 Foundation. Jira: SCRUM-140. Spec Reference: ref/todo/EPIC_01_FOUNDATION.md Story 1.7; ref/project_plan/01_vision/NICHE_CONFIG_DESIGN.md; ref/project_plan/11_playbook/SELLER_SETUP_PLAYBOOK.md. Files to create/modify: src/playbook/seed_guidance.py, docs/SEED_DATA_GUIDE.md, tests/unit/test_playbook.py.
Implementation Details: Expand the existing seed guidance module so it explains expected seed payload shape, minimum keyword count, duplicate keyword detection, niche_id naming rules, and how seed data relates to config.yaml. Do not edit config.yaml; do not implement database import; Agent A owns DB. Add docs/SEED_DATA_GUIDE.md with examples for one valid niche seed payload and common invalid payloads.
Required Tests: Duplicate keywords fail validation. Invalid niche_id characters fail. Valid payload passes. Documentation examples are syntactically valid YAML if PyYAML is available; if not, keep a simple string/heading test.
Definition of Done: Seed guidance supports future import work and avoids source-of-truth drift.

VALIDATION STEPS
python -m ruff check src/dashboard src/reports src/exports src/playbook tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py
python -m mypy src/dashboard src/reports src/exports src/playbook
python -m pytest tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py -q
python -c "from src.dashboard.navigation import get_available_pages; from src.exports.manifest import ExportManifest"

FILES YOU MAY CREATE OR MODIFY
README.md
docs/OPERATOR_QUICKSTART.md
docs/CYCLE_BRANCH_CHECKLIST.md
docs/SEED_DATA_GUIDE.md
src/dashboard/app.py
src/dashboard/navigation.py
src/dashboard/state.py
src/reports/placeholders.py
src/reports/templates.py
src/reports/run_summary.py
src/exports/placeholders.py
src/exports/formats.py
src/exports/manifest.py
src/playbook/seed_guidance.py
tests/unit/test_dashboard.py
tests/unit/test_reports.py
tests/unit/test_playbook.py

COMMIT INSTRUCTIONS
git add README.md docs src/dashboard src/reports src/exports src/playbook tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py && git commit -m "docs(reporting): harden operator docs exports and dashboard scaffolds [Agent D]"
```

---

## 6. POST-AGENT OPERATOR COMMANDS

After all four agents finish and commit:

```bash
cd C:\Fiverr
git status
git log --oneline -8
python -m pytest -q
python -m ruff check .
python -m mypy src
git push -u origin cycle/002/integration
```

Open PR:

```text
Title: feat(cycle-002): complete foundation database CLI and harden core service contracts
Source: cycle/002/integration
Target: develop
```

Suggested PR body:

```markdown
## Summary
- Expands Foundation model layer, database initialization, CLI, and utilities.
- Adds safe collection infrastructure for selectors, pacing, queue, checkpoints, sessions, and proxy config.
- Hardens LLM provider/cache/validation/retry/cost interfaces.
- Hardens documentation, dashboard shell, export/report contracts, and seed guidance.

## Validation
- [ ] python -m pytest -q
- [ ] python -m ruff check .
- [ ] python -m mypy src
- [ ] python run.py config-check
- [ ] python run.py init-db
- [ ] python run.py smoke

## Branch Policy
- Source branch: cycle/002/integration
- Target branch: develop
- No direct main changes.

## Jira
- SCRUM-136
- SCRUM-137
- SCRUM-138
- SCRUM-139
- SCRUM-140
- SCRUM-141
- SCRUM-142
- SCRUM-143
- SCRUM-144
- SCRUM-145
- SCRUM-146
- SCRUM-246
```

---

## 7. STATE UPDATE

- Cycle 002 is now the next active PM cycle.
- Cycle 002 branch is `cycle/002/integration`.
- Cycle 002 should not begin until Cycle 001 is merged into `develop`.
- Epic 01 remains active and should move materially closer to completion after Agent A finishes S1.3/S1.4/S1.6.
- Epic 02 work in Agent B is preparatory and must not be marked Done for collection workflow stories until later live-safe implementation and validation are complete.
- `SCRUM-246` tracks the PM-process correction and should remain visible until two clean cycles complete with full prompts and full GitHub workflow included.

---

## 8. NEXT CYCLE PREVIEW

Cycle 003 should review Cycle 002 outputs and then either:

1. Finish remaining Epic 01 gaps if model/CLI/config/test gates are not complete, or
2. Start true Phase 2 with Agent B leading Epic 02 Collection Engine and Agent C leading Epic 03 Analysis Engine, if Epic 01 reaches at least 80% completion with tests passing.

Main branch should still not be touched in Cycle 003 unless a formal Foundation release PR is created after Epic 01 release gates pass.
