# Fiverr Research System — Master Action Items List
## Every Item to Fix, Update, Correct, or Add
**Generated:** 2026-05-17 | **Source:** Combined Pass 1 + Pass 2 Audit
**Total items: 47**

Format: `[ID] Description — Source: [section] — Owner: [who]`

---

## 🔴 CRITICAL — Must fix before Cycle 019 starts (8 items)
*These will cause AI agents to do wrong or duplicated work if not resolved first.*

---

**[C-01] Transition SCRUM-264 → Done**
- Story: `[CRITICAL C9/C10] Create all 16 Jinja2 prompt templates`
- Reason: 19 templates created, committed, merged in PR #15 (2026-05-17)
- Action: Jira status transition + add AC evidence comment + assign story points (suggest: 8)
- Source: P1.1, P1.3
- Owner: ChatGPT PM / Manual

---

**[C-02] Transition SCRUM-273 → Done**
- Story: `[CRITICAL C2/C3/C4] Create missing src/scoring/, src/pricing/, src/discovery/`
- Reason: All 3 scaffold modules created, committed, merged in PR #15
- Action: Jira status transition + add AC evidence comment + assign story points (suggest: 5)
- Source: P1.1, P1.3
- Owner: ChatGPT PM / Manual

---

**[C-03] Transition SCRUM-140 → In Review**
- Story: `[FOUNDATION] S1.7 Niche Seed Data`
- Reason: 42/42 seed tests pass; 9 YAML files + import_seeds.py merged in PR #15
- Action: Jira status transition from In Progress → In Review
- Source: P1.1
- Owner: ChatGPT PM / Manual

---

**[C-04] Re-parent SCRUM-264 away from E05 (SCRUM-20)**
- Reason: SCRUM-264 is a cross-epic gap task, NOT an E05 canonical story. Its presence inflates E05 count from 9 to 10.
- Action: Remove parent SCRUM-20; either orphan it (and close as Done) or link to a dedicated "Gap Audit" epic/task
- Source: P1.4
- Owner: ChatGPT PM / Manual

---

**[C-05] Re-parent SCRUM-273 away from E01 (SCRUM-16)**
- Reason: SCRUM-273 is a cross-epic gap task, NOT an E01 canonical story. Its presence inflates E01 count from 7 to 8.
- Action: Remove parent SCRUM-16; close as Done or link to a gap epic
- Source: P1.4
- Owner: ChatGPT PM / Manual

---

**[C-06] Create `src/recommendations/` scaffold module**
- Reason: E05 (Recommendations) is the only future epic with zero code presence. Unlike E04/E06/E07 which have stubs, E05 has no `__init__.py`, no `contracts.py`, no `orchestrator.py`. Starting E05 from zero with no scaffold is high risk for agents.
- Action: Create `src/recommendations/__init__.py`, `contracts.py` (stub Pydantic models), `orchestrator.py` (stub class) — minimum viable scaffold
- Source: P1.8, P2.18
- Owner: Cursor Agent 3

---

**[C-07] Fix Jinja2 template naming misalignment (E05 dependency)**
- Reason: E05 (Recommendation Engine) calls templates by exact filenames per spec: `gig_titles.j2`, `tag_sets.j2`, `package_structure.j2`, `description_outline.j2`, `faq_entries.j2`, `differentiation_angle.j2`, `buyer_persona.j2`, `thumbnail_direction.j2`, `upsell_structure.j2`, `red_flags.j2`, `niche_viability.j2`. The 19 existing templates all have different names. E05 will fail on `FileNotFoundError` at runtime.
- Action: Either (a) rename existing templates to match spec names + add missing ones, OR (b) formally update spec Story 5.3/5.4 to use the new names and update all LLM call sites.
- Decision required: Which approach to take must be decided before E05 work begins.
- Source: P2.15
- Owner: ChatGPT PM (decision) + Cursor Agent 3 (implementation)

---

**[C-08] Add missing `discovery-collect` CLI mode to AVAILABLE_MODES**
- Reason: Spec (Story 1.4, task 1.4.1) requires 8 modes. `AVAILABLE_MODES` in `src/orchestrator.py` has only 7 — missing `discovery-collect`.
- Action: Add `"discovery-collect"` to `AVAILABLE_MODES` tuple; add corresponding stage execution logic (can be stub initially)
- AC affected: AC-1.4.1 test for all 8 modes will fail until fixed
- Source: P2.13
- Owner: Cursor Agent 1

---

## 🟠 HIGH — Fix in Cycle 019 (12 items)
*Spec fidelity and agent usability depend on these.*

---

**[H-01] Transition SCRUM-45, 135, 136, 137, 138, 139 → Done**
- Stories: E01 Foundation Stories 1.1–1.6 (all In Review)
- Reason: AC sign-off evidence comments already posted on all stories; code merged on develop; held deliberately in In Review pending formal cycle closure
- Action: Run Jira transitions for all 6 stories once Cycle 019 opens; verify each story's evidence comment is present
- Source: P1.1
- Owner: ChatGPT PM

---

**[H-02] Transition SCRUM-18 Epic (E03 Analysis) → Done**
- Reason: All 8 E03 stories (SCRUM-157–164) are Done. Epic status still shows "To Do" — never updated.
- Action: Transition SCRUM-18 from To Do → Done
- Source: P2.21
- Owner: ChatGPT PM / Manual

---

**[H-03] Close SCRUM-196 as Duplicate of SCRUM-195**
- Reason: SCRUM-196 is an exact duplicate (no parent epic, Done, same summary `[DISCOVERY] S7.1 Discovery Engine Core Loop`) of canonical SCRUM-195
- Action: Add "Duplicate of SCRUM-195" comment; transition to Won't Do or Duplicate resolution; link issues
- Source: P1.5
- Owner: ChatGPT PM / Manual

---

**[H-04] Close SCRUM-217 as Duplicate of SCRUM-216**
- Reason: Orphan Done story, same name as canonical SCRUM-216
- Action: Add "Duplicate of SCRUM-216" comment; transition to Won't Do / Duplicate
- Source: P1.5
- Owner: ChatGPT PM / Manual

---

**[H-05] Close SCRUM-221 and SCRUM-222 as Duplicates of SCRUM-220**
- Reason: Both are orphan Done stories matching canonical SCRUM-220 `[DASHBOARD] S9.8 Page 6: LLM Costs`
- Action: Mark both as duplicates of SCRUM-220; transition to Won't Do
- Source: P1.5
- Owner: ChatGPT PM / Manual

---

**[H-06] Add `.cursorrules` file to GitHub repository root**
- Reason: Cursor agents will not follow architecture rules without this file present in the repo root. This is the single most important file for making Cursor agents comply with project standards.
- Action: Copy spec file from `PM_Pack/ref/github/10_repo_files/.cursorrules` to repo root; resolve line-length conflict first (see H-07)
- Source: P2.8, P2.11
- Owner: Cursor Agent 1

---

**[H-07] Resolve line-length conflict: `.cursorrules` says 120, `pyproject.toml` says 100**
- Reason: `.cursorrules` specifies `line-length = 120` but `pyproject.toml` has `line-length = 100`. If `.cursorrules` is added as-is, Cursor will format at 120 while CI ruff will fail at 100. This creates an unresolvable CI loop.
- Action: Decide on one value (recommend keeping 100 for CI consistency); update `.cursorrules` before deploying it to reflect the chosen value; update pyproject.toml if 120 is chosen
- Source: P2.11
- Owner: ChatGPT PM (decision) + Cursor Agent 1

---

**[H-08] Change SCRUM-440 and SCRUM-441 type from Story to Task; assign to meta epic**
- Reason: These are admin/governance documents (`AI PM Operating Protocol`, `AI PM Status Dashboard`), not product stories. Mixed with canonical stories they pollute epic metrics and confuse agents.
- Action: Change issuetype to Task; create a new "Meta/Operations" epic or link to a dedicated admin project area; they should not appear in product epic backlogs
- Source: P1.5, P2.21
- Owner: Manual (admin action)

---

**[H-09] Create `src/utils/datetime.py` with `format_duration()`, `date_stamp()`, `parse_fiverr_date()`**
- Reason: AC-1.6.1, AC-1.6.2 explicitly test `format_duration()` from `src/utils/datetime.py`. File does not exist. Story 1.6 cannot be marked Done.
- Action: Create `src/utils/datetime.py` with all 3 functions + type hints + docstrings; add unit tests to `tests/unit/test_utils.py`
- Source: P2.6, P2.16
- Owner: Cursor Agent 1

---

**[H-10] Create `src/utils/validation.py` with `validate_url()`, `validate_price()`, `sanitize_text()`**
- Reason: AC-1.6.3 tests `validate_price()` from `src/utils/validation.py`. File does not exist.
- Action: Create `src/utils/validation.py` with all 3 functions + type hints + tests
- Source: P2.6, P2.16
- Owner: Cursor Agent 1

---

**[H-11] Create `src/utils/hashing.py` with `sha256_hash()` and `jaccard_similarity()`**
- Reason: AC-1.6.4, AC-1.6.5 test these functions from `src/utils/hashing.py`. Functions exist in other modules (`src/llm/cache.py`, `src/collection/`) but the required util module does not.
- Action: Create `src/utils/hashing.py`; move/expose existing hash functions here; update imports
- Source: P2.6, P2.16
- Owner: Cursor Agent 1

---

**[H-12] Create `src/utils/export.py` with `ensure_export_dirs()` and `get_export_path()`**
- Reason: AC-1.6.6 tests `ensure_export_dirs()` from `src/utils/export.py`. File does not exist. `ensure_dir()` in `paths.py` is a partial substitute but fails AC by name.
- Action: Create `src/utils/export.py`; implement both functions; add tests
- Source: P2.6, P2.16
- Owner: Cursor Agent 1

---

## 🟡 MEDIUM — Fix in Cycle 020 / sprint planning (14 items)
*Important for completeness and long-term health.*

---

**[M-01] Add missing DB model: `KeywordGigAssociation` many-to-many table**
- Reason: AC-1.3.5 explicitly tests the Keyword ↔ Gig many-to-many relationship via this junction table. Collection engine (E02) inserts rows into it. AC will fail without it.
- Action: Create `keyword_gig_associations` junction table in `src/models/market.py` (or new `src/models/associations.py`); update Keyword and Gig models with relationship
- AC affected: AC-1.3.5
- Source: P1.7, P2.3
- Owner: Cursor Agent 1

---

**[M-02] Add discovery fields to Keyword model (`is_discovery`, `hypothesis_confidence`, `discovery_mode`)**
- Reason: AC-1.3.8 explicitly tests these fields on the Keyword model. They are absent.
- Action: Add `is_discovery: Mapped[bool]`, `hypothesis_confidence: Mapped[Optional[float]]`, `discovery_mode: Mapped[Optional[str]]` to Keyword in `src/models/market.py`; add migration
- AC affected: AC-1.3.8
- Source: P2.3
- Owner: Cursor Agent 1

---

**[M-03] Create `GigVisualAnalysis` DB model**
- Reason: AC-1.3.9 explicitly tests this model. E08 (Playbook) Story 8.1 requires it. Not implemented.
- Action: Create `GigVisualAnalysis` model per `ref/project_plan/11_playbook/GIG_VISUAL_ANALYSIS.md` spec
- AC affected: AC-1.3.9
- Source: P1.7, P2.3
- Owner: Cursor Agent 1

---

**[M-04] Create `DiscoveryCycleLog`, `AutoPromotionLog`, and `Order` DB models**
- Reason: Tasks 1.3.25, 1.3.27, 1.3.28 define these models. All three are absent. The `Order` model is needed for the Revenue Gate Tracker (E06 Story 6.5).
- Action: Create each model in appropriate model files; register in `src/models/registry.py`
- Source: P1.7
- Owner: Cursor Agent 1

---

**[M-05] Update AC-1.3.1: DOD says "exactly 28 tables" but implementation has 30**
- Reason: DOD specifies `Base.metadata.create_all()` creates exactly 28 tables. Current implementation creates 30 (7 additional runtime/report tables were added). The integration test will fail.
- Action: Update DOD_EPIC_01.md Story 1.3 AC-1.3.1 to say "at least 28 tables" or document the accepted count; update the corresponding test assertion
- Source: P2.3
- Owner: ChatGPT PM (doc update) + Cursor Agent 1 (test fix)

---

**[M-06] Create `src/collection/workflows/` subdirectory with one workflow file per class**
- Reason: `.cursorrules` rule: "Collection workflows go in `src/collection/workflows/`". The directory does not exist. All 6+ workflow classes should live here.
- Action: Create `src/collection/workflows/` directory; move or refactor workflow logic from flat modules into: `keyword_expansion.py`, `fiverr_search.py`, `gig_detail.py`, `seller_profile.py`, `google_trends.py`, `reddit_signals.py`, `autocomplete.py`, `auto_promotion.py`
- Source: P2.11
- Owner: Cursor Agent 2

---

**[M-07] Create `src/dashboard/pages/` subdirectory with one page file per dashboard page**
- Reason: `.cursorrules` rule: "Dashboard pages go in `src/dashboard/pages/`". Directory does not exist; currently uses flat `pages.py` monolith.
- Action: Create `src/dashboard/pages/` directory; split `pages.py` into 9 files: `opportunities.py`, `keywords.py`, `competitors.py`, `recommendations.py`, `run_history.py`, `llm_costs.py`, `discovery.py`, `pricing.py`, `playbook.py`
- Source: P2.11
- Owner: Cursor Agent 4

---

**[M-08] Deploy 44 GitHub labels from `labels.json` to repository**
- Reason: 0 of 44 spec labels currently deployed to GitHub. PR and issue filtering by type, agent, scope, and priority is impossible.
- Action: Use GitHub CLI `gh label create` or GitHub API to deploy all 44 labels from `ref/github/10_repo_files/.github/labels.json`
- Source: P2.10
- Owner: Manual / ChatGPT PM

---

**[M-09] Add 4 missing GitHub workflows: `pr-checks.yml`, `release.yml`, `security.yml`, `stale.yml`**
- Reason: Spec requires 5 CI/CD workflows; only `ci.yml` exists.
- Action: Copy from `ref/github/10_repo_files/.github/workflows/` to `.github/workflows/`; review and activate each
- Source: P2.8
- Owner: Cursor Agent 1

---

**[M-10] Create formal Jira sprint for Cycle 019 and assign stories**
- Reason: No stories are assigned to any Jira sprint. ChatGPT cannot track sprint velocity. Stories have no sprint scope.
- Action: Create "Cycle 019" sprint in Jira; assign all In Review and In Progress stories to it; assign upcoming To Do stories per agent
- Source: P1.10
- Owner: ChatGPT PM

---

**[M-11] Create `tests/README.md` documenting test fixtures and organization**
- Reason: AC-10.5.2 requires this file. It is missing. Agents have no documentation of `conftest.py` fixtures, test factories, or test organization patterns.
- Action: Create `tests/README.md` with: test directory structure, fixture list from `conftest.py`, factory patterns, how to run specific test groups
- Source: P2.17
- Owner: Cursor Agent 1 or 3

---

**[M-12] Add `CODEOWNERS`, `dependabot.yml`, and 5 issue templates to GitHub**
- Reason: All required per spec; all absent from actual repo.
- Action: Copy from `ref/github/10_repo_files/.github/` to `.github/`:
  - `CODEOWNERS` (defines agent ownership per directory)
  - `dependabot.yml` (automated dependency updates)
  - `ISSUE_TEMPLATE/bug_report.yml`, `epic.yml`, `feature_request.yml`, `spike.yml`, `task.yml`
- Source: P2.8
- Owner: Cursor Agent 1

---

**[M-13] Add `fixVersions` to Jira — create v0.1.0 Foundation milestone**
- Reason: Spec references v0.1.0 Foundation Release. No Jira versions exist. ChatGPT cannot track release readiness.
- Action: Create `v0.1.0 - Foundation` version in Jira project settings; assign E01 stories to this version; define release criteria
- Source: P1.10
- Owner: ChatGPT PM / Manual

---

**[M-14] Create Wave 19 Jira sub-tasks for E01 stories (current sprint)**
- Reason: 600 spec tasks exist only as description text, not as trackable Jira items. At minimum, E01's 65 tasks should be formal Jira sub-tasks so Cursor agents can mark granular progress.
- Action: Create Jira sub-tasks under SCRUM-45 through SCRUM-140 using the task tables from `ref/todo/EPIC_01_FOUNDATION.md`; at a minimum create tasks for the stories still In Review
- Source: P1.6
- Owner: ChatGPT PM

---

## 🟢 LOW — Backlog / long-term (9 items)
*Good practice; not urgent.*

---

**[L-01] Add `requirements.txt` with pinned dependency versions**
- Reason: Story 1.1 task 1.1.3 requires a `requirements.txt` for reproducible installs. Only `pyproject.toml` exists. `requirements.txt` provides a simpler install path for some deployment scenarios.
- Action: Run `pip freeze > requirements.txt` from the project venv; commit to repo root
- Source: P1.9
- Owner: Cursor Agent 1

---

**[L-02] Add CI step to verify `playwright install chromium` (AC-1.1.3)**
- Reason: AC-1.1.3 requires evidence that Playwright browser install exits 0. No CI step validates this. The foundation gate cannot be considered fully passed.
- Action: Add `playwright install chromium` to `ci.yml` after dependency install step
- Source: P2.1
- Owner: Cursor Agent 1

---

**[L-03] Add per-story DoD checklist items to DOD files E03–E10**
- Reason: DOD E01 and E02 have explicit `- [ ]` checklist items per story. E03–E10 have only AC tables. Cursor agents checking "is this story done?" have no checkbox list to verify.
- Action: Add DoD checklist blocks to each story section in `DOD_EPIC_03.md` through `DOD_EPIC_10.md` based on the epic-level DoD criteria
- Source: P2.14
- Owner: ChatGPT PM

---

**[L-04] Add `VISUAL` selector group to `src/collection/selectors.py`**
- Reason: AC-2.2.3 requires selectors organized into groups including `VISUAL`. Currently `SELECTOR_REGISTRY` has `search_results`, `gig_detail`, `seller_profile` but no `visual` group.
- Action: Add `"visual"` key to `SELECTOR_REGISTRY` with thumbnail, gallery, video indicator selectors
- Source: P2.22
- Owner: Cursor Agent 2

---

**[L-05] Rename collection class interfaces to match spec (or formally document deviation)**
- Reason: `ManagedBrowserSession` → spec says `SessionManager`; `CollectionQueue` → spec says `QueueProcessor`. Integration code and agent prompts will use spec names.
- Action: Either rename the classes (easier for future agents) or add spec-name aliases in `__init__.py`; formally document deviation in DECISION_LOG.md
- Source: P2.12
- Owner: ChatGPT PM (document decision) + Cursor Agent 2 (if aliases needed)

---

**[L-06] Update spec PR template vs actual PR template — choose one canonical version**
- Reason: Spec has a 26-line structured PR template; actual has a 91-line cycle-based template. Both exist simultaneously creating confusion about which agents should follow.
- Action: Decide on canonical PR template; if the 91-line version is kept, formally retire the spec version by updating `ref/github/05_templates/PR_TEMPLATE.md`; if spec version preferred, replace `.github/pull_request_template.md`
- Source: P2.9
- Owner: ChatGPT PM

---

**[L-07] Set up Jira-GitHub integration for automatic PR→Story linking**
- Reason: Currently PR links to Jira only appear as text comments. The Jira "Development" panel for each story shows no linked PRs. Automatic linking would give ChatGPT PM real-time PR visibility.
- Action: Configure Atlassian-GitHub integration in Jira project settings; ensure PR descriptions include `SCRUM-XXX` key for auto-linking
- Source: P1.10
- Owner: Manual (Jira admin setting)

---

**[L-08] Standardize branch naming to spec convention (or formally document deviation)**
- Reason: Spec `.cursorrules` defines `{type}/{scope}/{description}` e.g. `feature/epic01/S1.2-config-system`. Actual convention is `cycle/018/integration`. The conventions are incompatible.
- Action: Decide canonical convention; update `.cursorrules` accordingly; update ChatGPT PM operating instructions to match
- Source: P2.11
- Owner: ChatGPT PM

---

**[L-09] Standardize commit scope to epic/story references (or formally document deviation)**
- Reason: Spec commit format: `feat(scoring): description` (module scope). Actual: `feat(cycle-018): description` (cycle scope). Inconsistent scope makes `git log --grep` filtering unreliable.
- Action: Decide convention; update `.cursorrules` commit guidelines; inform all agents of chosen convention
- Source: P2.11
- Owner: ChatGPT PM

---

## ℹ️ INFORMATIONAL — Intentional deviations; document and accept (4 items)

---

**[I-01] Model consolidation: multiple models per file**
- Current state: `market.py` (3 models), `analysis.py` (6), `scoring.py` (3), `runtime.py` (6)
- Spec says: one model per file
- Assessment: This is a deliberate architectural decision made early in the project. Consolidation reduces file count and import complexity. Functionally correct.
- Action: Document this as an accepted deviation in `DECISION_LOG.md`; note in `.cursorrules` override section; ensure future models follow the established pattern (add to same group file)
- Source: P2.11

---

**[I-02] LLM template naming: 19 templates with different names than E05 spec requires**
- Current state: Templates exist and work for collection/analysis stages; E05 will need different names
- Assessment: The current 19 templates serve E02/E03/E06/E07 workflows. E05's 13 spec-named templates are a separate set that needs to be added (not replace existing ones).
- Action: Clarify in SCRUM-181 (Story 5.4 Jinja2 Templates) that existing templates are **in addition to** the 13 E05-specific ones; do not delete existing templates
- Source: P2.15

---

**[I-03] Collection module uses functional approach rather than class-based workflow pattern**
- Current state: Flat functional modules (`keyword_expansion.py`, `gig_detail.py` etc.) instead of named Workflow classes in a `workflows/` subdirectory
- Assessment: Functionally equivalent; the collection engine works. The class interface matters more for integration and testing.
- Action: Document deviation in DECISION_LOG.md; M-06 (create workflows/ directory) is the remediation but not urgent
- Source: P2.23

---

**[I-04] 0 of 600 spec sub-tasks as Jira items — by protocol design**
- Current state: All 600 task-level items live only as text in story descriptions
- Assessment: This is explicitly deferred per protocol. The risk is acknowledged.
- Action: Accept current state; create sub-tasks for the active sprint only (M-14); defer bulk sub-task creation to a dedicated wave
- Source: P1.6

---

## Quick Reference — By Owner

### ChatGPT PM
C-01, C-02, C-03, C-04, C-05, H-01, H-02, H-03, H-04, H-05, H-07(decision), H-08, M-10, M-13, M-14, L-03, L-05(doc), L-06, L-08, L-09, I-01, I-02, I-03

### Cursor Agent 1 (Infrastructure / Foundation)
C-08, H-06, H-07(impl), H-09, H-10, H-11, H-12, M-01, M-02, M-03, M-04, M-05, M-09, M-12, L-01, L-02

### Cursor Agent 2 (Collection Engine)
M-06, L-04, L-05(impl)

### Cursor Agent 3 (Analysis / Intelligence)
C-06, C-07(impl), M-11

### Cursor Agent 4 (Dashboard)
M-07

### Manual (Jira/GitHub Admin)
C-03, C-04, C-05, H-08, M-08, L-07

---

## Quick Reference — By Cycle Priority

### Before Cycle 019 Opens
C-01, C-02, C-03, C-04, C-05, C-06, C-07 (decision), C-08

### Cycle 019 Sprint
H-01, H-02, H-03, H-04, H-05, H-06, H-07, H-08, H-09, H-10, H-11, H-12

### Cycle 020 Sprint
M-01 through M-14

### Long-term Backlog
L-01 through L-09, I-01 through I-04

---

*Master Action Items List — Fiverr Research System*
*Generated 2026-05-17 by Claude AI from Pass 1 + Pass 2 combined audit*
*Total: 47 items (8 Critical, 12 High, 14 Medium, 9 Low, 4 Informational)*
