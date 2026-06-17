====================================================================
AGENT E -- CYCLE 083 PROMPT
====================================================================

## PROJECT CONTEXT

- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch: `cycle/083/integration`
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit
- Cycle: 083 | Run ID: 20260616T164232

## MODEL POLICY (MANDATORY — do not override)

- **Model:** Codex 5.3
- **Effort:** medium
- **Auto model selection:** DISABLED — use only Codex 5.3
- **Fallback model:** DISABLED
- **Billing:** Claude subscription only for PM review; no API key

## YOUR ROLE

**Agent E** — Live data validation, external signal collection, evidence files
**Role type:** `live_validation_external_signals`

**You own these file paths (you may create/modify only these):**
- `docs/cycle_reports/**`
- `data/evidence/**`
- `scripts/validation/**`

**You must NOT modify these paths:**
- `src/**`
- `tests/**`
- `config.yaml`

**IMPORTANT:** You must wait for Agent B's first commit before starting your work.

## GIT INSTRUCTIONS

1. Confirm you are on branch: `cycle/083/integration`
   ```
   git branch --show-current
   # Expected: cycle/083/integration
   ```
2. Pull latest: `git pull origin cycle/083/integration`
3. ALL work on `cycle/083/integration` only — do NOT create other branches
4. **DO NOT run git add, git commit, git push.** The controller owns all git operations.
5. **DO NOT run gh pr commands.** The controller manages PRs.
6. Complete your tasks, write your report, and exit.

## AUTONOMY RULE

- Proceed autonomously through all tasks without pausing for confirmation.
- If a task cannot be completed due to a missing dependency, document the blocker
  in your report and continue to the next task.
- If a test fails, fix the bug causing the failure. Do NOT use `pytest.mark.skip`
  as a workaround. If you cannot fix it in 3 attempts, document it as a blocker.
- Do NOT commit files. The controller validates and commits after you finish.

## JIRA SCOPE FOR THIS CYCLE

| Jira Key | Summary | Status | Priority |
|---|---|---|---|
| SCRUM-986 | [SRDI][R10.3.3] Per-gig relevance rendering in Data Int | To Do | Medium |
| SCRUM-978 | [SRDI][R6.8.5] Integration test_discovery_orchestrator_ | To Do | Medium |
| SCRUM-974 | [SRDI][R6.5.3] Contaminated discovery outcome: is_conta | To Do | Medium |
| SCRUM-973 | [SRDI][R6.3.5] Minimal collector dependency for pre-val | To Do | Medium |
| SCRUM-972 | [SRDI][R6.3.4] Ghost and low-relevance rejection in Dis | To Do | Medium |
| SCRUM-971 | [SRDI][R6.3.3] TRC sanity check vs potential_trc_range  | To Do | Medium |
| SCRUM-969 | [SRDI][R7.4.3] process_reddit_collection storage of qua | To Do | Medium |
| SCRUM-959 | [SRDI][R4.2.5] Defer to R7 stored qualifier when Extern | To Do | Medium |
| SCRUM-948 | [SRDI][R2.4.4] Return run stats dict from run_stage_3_5 | To Do | Medium |
| SCRUM-947 | [SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version stam | To Do | Medium |
| SCRUM-946 | [SRDI][R2.3.3] Per-niche ghost_market_threshold in NICH | To Do | Medium |
| SCRUM-945 | [SRDI][R2.2.5] Confidence deduction tiers in validate_r | To Do | Medium |
| SCRUM-944 | [SRDI][R2.2.4] Ghost and contamination flag logic in va | To Do | Medium |
| SCRUM-941 | [SRDI][R2.1.5] Signal 4: over-generic gig penalty (-0.1 | To Do | Medium |
| SCRUM-928 | [SRDI][R1.4.5] Store pages_collected on SearchResult | To Do | Medium |

## TASKS FOR THIS CYCLE

> **Floor:** 55 LARGE/XLARGE/XXLARGE tasks (AGENT_TASK_FLOOR_ENFORCEMENT.md hard rule).
> Each task must have: Story/Jira key, Epic, Spec, Files, Implementation details
> (>=100 words), >=3 tests, Definition of Done.

### Task 1: Live validation probe for [SRDI][R10.3.3] Per-gig relevance r

- **Jira:** SCRUM-986 — [SRDI][R10.3.3] Per-gig relevance rendering in Dat
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-986 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-986 description for referenced spec files)
- **DOD:** See SCRUM-986 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-986)

**Implementation Details:**

Implement a production validation probe for SCRUM-986 '[SRDI][R10.3.3] Per-gig relevance rendering in Data Integrity tab'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-986 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 2: External signal validation for [SRDI][R10.3.3] Per-gig relevance r

- **Jira:** SCRUM-986 — [SRDI][R10.3.3] Per-gig relevance rendering in Dat
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-986 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-986 description for referenced spec files)
- **DOD:** See SCRUM-986 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-986 '[SRDI][R10.3.3] Per-gig relevance rendering in Data Integrity tab'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-986 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 3: Scoring pipeline validation for [SRDI][R10.3.3] Per-gig relevance r

- **Jira:** SCRUM-986 — [SRDI][R10.3.3] Per-gig relevance rendering in Dat
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-986 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-986 description for referenced spec files)
- **DOD:** See SCRUM-986 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-986 '[SRDI][R10.3.3] Per-gig relevance rendering in Data Integrity tab'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-986 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 4: Integration evidence collection for [SRDI][R10.3.3] Per-gig relevance r

- **Jira:** SCRUM-986 — [SRDI][R10.3.3] Per-gig relevance rendering in Dat
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-986 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-986 description for referenced spec files)
- **DOD:** See SCRUM-986 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-986 '[SRDI][R10.3.3] Per-gig relevance rendering in Data Integrity tab'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-986 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 5: Live validation probe for [SRDI][R6.8.5] Integration test_dis

- **Jira:** SCRUM-978 — [SRDI][R6.8.5] Integration test_discovery_orchestr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-978 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-978 description for referenced spec files)
- **DOD:** See SCRUM-978 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-978)

**Implementation Details:**

Implement a production validation probe for SCRUM-978 '[SRDI][R6.8.5] Integration test_discovery_orchestrator_validated_only.py'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-978 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 6: External signal validation for [SRDI][R6.8.5] Integration test_dis

- **Jira:** SCRUM-978 — [SRDI][R6.8.5] Integration test_discovery_orchestr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-978 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-978 description for referenced spec files)
- **DOD:** See SCRUM-978 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-978 '[SRDI][R6.8.5] Integration test_discovery_orchestrator_validated_only.py'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-978 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 7: Scoring pipeline validation for [SRDI][R6.8.5] Integration test_dis

- **Jira:** SCRUM-978 — [SRDI][R6.8.5] Integration test_discovery_orchestr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-978 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-978 description for referenced spec files)
- **DOD:** See SCRUM-978 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-978 '[SRDI][R6.8.5] Integration test_discovery_orchestrator_validated_only.py'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-978 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 8: Integration evidence collection for [SRDI][R6.8.5] Integration test_dis

- **Jira:** SCRUM-978 — [SRDI][R6.8.5] Integration test_discovery_orchestr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-978 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-978 description for referenced spec files)
- **DOD:** See SCRUM-978 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-978 '[SRDI][R6.8.5] Integration test_discovery_orchestrator_validated_only.py'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-978 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 9: Live validation probe for [SRDI][R6.5.3] Contaminated discove

- **Jira:** SCRUM-974 — [SRDI][R6.5.3] Contaminated discovery outcome: is_
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-974 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-974 description for referenced spec files)
- **DOD:** See SCRUM-974 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-974)

**Implementation Details:**

Implement a production validation probe for SCRUM-974 '[SRDI][R6.5.3] Contaminated discovery outcome: is_contaminated + discovery_needs_recollection'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-974 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 10: External signal validation for [SRDI][R6.5.3] Contaminated discove

- **Jira:** SCRUM-974 — [SRDI][R6.5.3] Contaminated discovery outcome: is_
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-974 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-974 description for referenced spec files)
- **DOD:** See SCRUM-974 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-974 '[SRDI][R6.5.3] Contaminated discovery outcome: is_contaminated + discovery_needs_recollection'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-974 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 11: Scoring pipeline validation for [SRDI][R6.5.3] Contaminated discove

- **Jira:** SCRUM-974 — [SRDI][R6.5.3] Contaminated discovery outcome: is_
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-974 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-974 description for referenced spec files)
- **DOD:** See SCRUM-974 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-974 '[SRDI][R6.5.3] Contaminated discovery outcome: is_contaminated + discovery_needs_recollection'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-974 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 12: Integration evidence collection for [SRDI][R6.5.3] Contaminated discove

- **Jira:** SCRUM-974 — [SRDI][R6.5.3] Contaminated discovery outcome: is_
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-974 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-974 description for referenced spec files)
- **DOD:** See SCRUM-974 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-974 '[SRDI][R6.5.3] Contaminated discovery outcome: is_contaminated + discovery_needs_recollection'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-974 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 13: Live validation probe for [SRDI][R6.3.5] Minimal collector de

- **Jira:** SCRUM-973 — [SRDI][R6.3.5] Minimal collector dependency for pr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-973 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-973 description for referenced spec files)
- **DOD:** See SCRUM-973 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-973)

**Implementation Details:**

Implement a production validation probe for SCRUM-973 '[SRDI][R6.3.5] Minimal collector dependency for pre-validation dry-run'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-973 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 14: External signal validation for [SRDI][R6.3.5] Minimal collector de

- **Jira:** SCRUM-973 — [SRDI][R6.3.5] Minimal collector dependency for pr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-973 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-973 description for referenced spec files)
- **DOD:** See SCRUM-973 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-973 '[SRDI][R6.3.5] Minimal collector dependency for pre-validation dry-run'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-973 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 15: Scoring pipeline validation for [SRDI][R6.3.5] Minimal collector de

- **Jira:** SCRUM-973 — [SRDI][R6.3.5] Minimal collector dependency for pr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-973 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-973 description for referenced spec files)
- **DOD:** See SCRUM-973 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-973 '[SRDI][R6.3.5] Minimal collector dependency for pre-validation dry-run'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-973 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 16: Integration evidence collection for [SRDI][R6.3.5] Minimal collector de

- **Jira:** SCRUM-973 — [SRDI][R6.3.5] Minimal collector dependency for pr
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-973 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-973 description for referenced spec files)
- **DOD:** See SCRUM-973 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-973 '[SRDI][R6.3.5] Minimal collector dependency for pre-validation dry-run'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-973 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 17: Live validation probe for [SRDI][R6.3.4] Ghost and low-releva

- **Jira:** SCRUM-972 — [SRDI][R6.3.4] Ghost and low-relevance rejection i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-972 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-972 description for referenced spec files)
- **DOD:** See SCRUM-972 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-972)

**Implementation Details:**

Implement a production validation probe for SCRUM-972 '[SRDI][R6.3.4] Ghost and low-relevance rejection in DiscoveryPreValidator'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-972 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 18: External signal validation for [SRDI][R6.3.4] Ghost and low-releva

- **Jira:** SCRUM-972 — [SRDI][R6.3.4] Ghost and low-relevance rejection i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-972 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-972 description for referenced spec files)
- **DOD:** See SCRUM-972 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-972 '[SRDI][R6.3.4] Ghost and low-relevance rejection in DiscoveryPreValidator'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-972 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 19: Scoring pipeline validation for [SRDI][R6.3.4] Ghost and low-releva

- **Jira:** SCRUM-972 — [SRDI][R6.3.4] Ghost and low-relevance rejection i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-972 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-972 description for referenced spec files)
- **DOD:** See SCRUM-972 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-972 '[SRDI][R6.3.4] Ghost and low-relevance rejection in DiscoveryPreValidator'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-972 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 20: Integration evidence collection for [SRDI][R6.3.4] Ghost and low-releva

- **Jira:** SCRUM-972 — [SRDI][R6.3.4] Ghost and low-relevance rejection i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-972 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-972 description for referenced spec files)
- **DOD:** See SCRUM-972 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-972 '[SRDI][R6.3.4] Ghost and low-relevance rejection in DiscoveryPreValidator'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-972 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 21: Live validation probe for [SRDI][R6.3.3] TRC sanity check vs 

- **Jira:** SCRUM-971 — [SRDI][R6.3.3] TRC sanity check vs potential_trc_r
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-971 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-971 description for referenced spec files)
- **DOD:** See SCRUM-971 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-971)

**Implementation Details:**

Implement a production validation probe for SCRUM-971 '[SRDI][R6.3.3] TRC sanity check vs potential_trc_range in DiscoveryPreValidator'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-971 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 22: External signal validation for [SRDI][R6.3.3] TRC sanity check vs 

- **Jira:** SCRUM-971 — [SRDI][R6.3.3] TRC sanity check vs potential_trc_r
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-971 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-971 description for referenced spec files)
- **DOD:** See SCRUM-971 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-971 '[SRDI][R6.3.3] TRC sanity check vs potential_trc_range in DiscoveryPreValidator'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-971 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 23: Scoring pipeline validation for [SRDI][R6.3.3] TRC sanity check vs 

- **Jira:** SCRUM-971 — [SRDI][R6.3.3] TRC sanity check vs potential_trc_r
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-971 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-971 description for referenced spec files)
- **DOD:** See SCRUM-971 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-971 '[SRDI][R6.3.3] TRC sanity check vs potential_trc_range in DiscoveryPreValidator'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-971 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 24: Integration evidence collection for [SRDI][R6.3.3] TRC sanity check vs 

- **Jira:** SCRUM-971 — [SRDI][R6.3.3] TRC sanity check vs potential_trc_r
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-971 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-971 description for referenced spec files)
- **DOD:** See SCRUM-971 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-971 '[SRDI][R6.3.3] TRC sanity check vs potential_trc_range in DiscoveryPreValidator'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-971 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 25: Live validation probe for [SRDI][R7.4.3] process_reddit_colle

- **Jira:** SCRUM-969 — [SRDI][R7.4.3] process_reddit_collection storage o
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-969 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-969 description for referenced spec files)
- **DOD:** See SCRUM-969 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-969)

**Implementation Details:**

Implement a production validation probe for SCRUM-969 '[SRDI][R7.4.3] process_reddit_collection storage of qualified score'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-969 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 26: External signal validation for [SRDI][R7.4.3] process_reddit_colle

- **Jira:** SCRUM-969 — [SRDI][R7.4.3] process_reddit_collection storage o
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-969 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-969 description for referenced spec files)
- **DOD:** See SCRUM-969 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-969 '[SRDI][R7.4.3] process_reddit_collection storage of qualified score'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-969 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 27: Scoring pipeline validation for [SRDI][R7.4.3] process_reddit_colle

- **Jira:** SCRUM-969 — [SRDI][R7.4.3] process_reddit_collection storage o
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-969 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-969 description for referenced spec files)
- **DOD:** See SCRUM-969 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-969 '[SRDI][R7.4.3] process_reddit_collection storage of qualified score'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-969 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 28: Integration evidence collection for [SRDI][R7.4.3] process_reddit_colle

- **Jira:** SCRUM-969 — [SRDI][R7.4.3] process_reddit_collection storage o
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-969 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-969 description for referenced spec files)
- **DOD:** See SCRUM-969 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-969 '[SRDI][R7.4.3] process_reddit_collection storage of qualified score'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-969 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 29: Live validation probe for [SRDI][R4.2.5] Defer to R7 stored q

- **Jira:** SCRUM-959 — [SRDI][R4.2.5] Defer to R7 stored qualifier when E
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-959 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-959 description for referenced spec files)
- **DOD:** See SCRUM-959 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-959)

**Implementation Details:**

Implement a production validation probe for SCRUM-959 '[SRDI][R4.2.5] Defer to R7 stored qualifier when ExternalSignal present'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-959 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 30: External signal validation for [SRDI][R4.2.5] Defer to R7 stored q

- **Jira:** SCRUM-959 — [SRDI][R4.2.5] Defer to R7 stored qualifier when E
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-959 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-959 description for referenced spec files)
- **DOD:** See SCRUM-959 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-959 '[SRDI][R4.2.5] Defer to R7 stored qualifier when ExternalSignal present'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-959 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 31: Scoring pipeline validation for [SRDI][R4.2.5] Defer to R7 stored q

- **Jira:** SCRUM-959 — [SRDI][R4.2.5] Defer to R7 stored qualifier when E
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-959 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-959 description for referenced spec files)
- **DOD:** See SCRUM-959 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-959 '[SRDI][R4.2.5] Defer to R7 stored qualifier when ExternalSignal present'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-959 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 32: Integration evidence collection for [SRDI][R4.2.5] Defer to R7 stored q

- **Jira:** SCRUM-959 — [SRDI][R4.2.5] Defer to R7 stored qualifier when E
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-959 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-959 description for referenced spec files)
- **DOD:** See SCRUM-959 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-959 '[SRDI][R4.2.5] Defer to R7 stored qualifier when ExternalSignal present'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-959 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 33: Live validation probe for [SRDI][R2.4.4] Return run stats dic

- **Jira:** SCRUM-948 — [SRDI][R2.4.4] Return run stats dict from run_stag
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-948 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-948 description for referenced spec files)
- **DOD:** See SCRUM-948 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-948)

**Implementation Details:**

Implement a production validation probe for SCRUM-948 '[SRDI][R2.4.4] Return run stats dict from run_stage_3_5_validation'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-948 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 34: External signal validation for [SRDI][R2.4.4] Return run stats dic

- **Jira:** SCRUM-948 — [SRDI][R2.4.4] Return run stats dict from run_stag
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-948 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-948 description for referenced spec files)
- **DOD:** See SCRUM-948 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-948 '[SRDI][R2.4.4] Return run stats dict from run_stage_3_5_validation'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-948 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 35: Scoring pipeline validation for [SRDI][R2.4.4] Return run stats dic

- **Jira:** SCRUM-948 — [SRDI][R2.4.4] Return run stats dict from run_stag
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-948 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-948 description for referenced spec files)
- **DOD:** See SCRUM-948 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-948 '[SRDI][R2.4.4] Return run stats dict from run_stage_3_5_validation'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-948 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 36: Integration evidence collection for [SRDI][R2.4.4] Return run stats dic

- **Jira:** SCRUM-948 — [SRDI][R2.4.4] Return run stats dict from run_stag
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-948 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-948 description for referenced spec files)
- **DOD:** See SCRUM-948 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-948 '[SRDI][R2.4.4] Return run stats dict from run_stage_3_5_validation'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-948 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 37: Live validation probe for [SRDI][R2.3.4] DEFAULT_VALIDATION_C

- **Jira:** SCRUM-947 — [SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-947 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-947 description for referenced spec files)
- **DOD:** See SCRUM-947 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-947)

**Implementation Details:**

Implement a production validation probe for SCRUM-947 '[SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version stamps in result_set_validator.py'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-947 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 38: External signal validation for [SRDI][R2.3.4] DEFAULT_VALIDATION_C

- **Jira:** SCRUM-947 — [SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-947 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-947 description for referenced spec files)
- **DOD:** See SCRUM-947 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-947 '[SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version stamps in result_set_validator.py'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-947 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 39: Scoring pipeline validation for [SRDI][R2.3.4] DEFAULT_VALIDATION_C

- **Jira:** SCRUM-947 — [SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-947 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-947 description for referenced spec files)
- **DOD:** See SCRUM-947 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-947 '[SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version stamps in result_set_validator.py'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-947 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 40: Integration evidence collection for [SRDI][R2.3.4] DEFAULT_VALIDATION_C

- **Jira:** SCRUM-947 — [SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-947 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-947 description for referenced spec files)
- **DOD:** See SCRUM-947 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-947 '[SRDI][R2.3.4] DEFAULT_VALIDATION_CONFIG + version stamps in result_set_validator.py'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-947 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 41: Live validation probe for [SRDI][R2.3.3] Per-niche ghost_mark

- **Jira:** SCRUM-946 — [SRDI][R2.3.3] Per-niche ghost_market_threshold in
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-946 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-946 description for referenced spec files)
- **DOD:** See SCRUM-946 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-946)

**Implementation Details:**

Implement a production validation probe for SCRUM-946 '[SRDI][R2.3.3] Per-niche ghost_market_threshold in NICHE_VALIDATION_CONFIG'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-946 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 42: External signal validation for [SRDI][R2.3.3] Per-niche ghost_mark

- **Jira:** SCRUM-946 — [SRDI][R2.3.3] Per-niche ghost_market_threshold in
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-946 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-946 description for referenced spec files)
- **DOD:** See SCRUM-946 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-946 '[SRDI][R2.3.3] Per-niche ghost_market_threshold in NICHE_VALIDATION_CONFIG'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-946 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 43: Scoring pipeline validation for [SRDI][R2.3.3] Per-niche ghost_mark

- **Jira:** SCRUM-946 — [SRDI][R2.3.3] Per-niche ghost_market_threshold in
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-946 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-946 description for referenced spec files)
- **DOD:** See SCRUM-946 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-946 '[SRDI][R2.3.3] Per-niche ghost_market_threshold in NICHE_VALIDATION_CONFIG'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-946 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 44: Integration evidence collection for [SRDI][R2.3.3] Per-niche ghost_mark

- **Jira:** SCRUM-946 — [SRDI][R2.3.3] Per-niche ghost_market_threshold in
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-946 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-946 description for referenced spec files)
- **DOD:** See SCRUM-946 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-946 '[SRDI][R2.3.3] Per-niche ghost_market_threshold in NICHE_VALIDATION_CONFIG'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-946 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 45: Live validation probe for [SRDI][R2.2.5] Confidence deduction

- **Jira:** SCRUM-945 — [SRDI][R2.2.5] Confidence deduction tiers in valid
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-945 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-945 description for referenced spec files)
- **DOD:** See SCRUM-945 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-945)

**Implementation Details:**

Implement a production validation probe for SCRUM-945 '[SRDI][R2.2.5] Confidence deduction tiers in validate_result_set'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-945 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 46: External signal validation for [SRDI][R2.2.5] Confidence deduction

- **Jira:** SCRUM-945 — [SRDI][R2.2.5] Confidence deduction tiers in valid
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-945 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-945 description for referenced spec files)
- **DOD:** See SCRUM-945 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-945 '[SRDI][R2.2.5] Confidence deduction tiers in validate_result_set'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-945 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 47: Scoring pipeline validation for [SRDI][R2.2.5] Confidence deduction

- **Jira:** SCRUM-945 — [SRDI][R2.2.5] Confidence deduction tiers in valid
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-945 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-945 description for referenced spec files)
- **DOD:** See SCRUM-945 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-945 '[SRDI][R2.2.5] Confidence deduction tiers in validate_result_set'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-945 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 48: Integration evidence collection for [SRDI][R2.2.5] Confidence deduction

- **Jira:** SCRUM-945 — [SRDI][R2.2.5] Confidence deduction tiers in valid
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-945 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-945 description for referenced spec files)
- **DOD:** See SCRUM-945 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-945 '[SRDI][R2.2.5] Confidence deduction tiers in validate_result_set'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-945 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 49: Live validation probe for [SRDI][R2.2.4] Ghost and contaminat

- **Jira:** SCRUM-944 — [SRDI][R2.2.4] Ghost and contamination flag logic 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-944 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-944 description for referenced spec files)
- **DOD:** See SCRUM-944 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-944)

**Implementation Details:**

Implement a production validation probe for SCRUM-944 '[SRDI][R2.2.4] Ghost and contamination flag logic in validate_result_set'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-944 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 50: External signal validation for [SRDI][R2.2.4] Ghost and contaminat

- **Jira:** SCRUM-944 — [SRDI][R2.2.4] Ghost and contamination flag logic 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-944 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-944 description for referenced spec files)
- **DOD:** See SCRUM-944 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-944 '[SRDI][R2.2.4] Ghost and contamination flag logic in validate_result_set'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-944 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 51: Scoring pipeline validation for [SRDI][R2.2.4] Ghost and contaminat

- **Jira:** SCRUM-944 — [SRDI][R2.2.4] Ghost and contamination flag logic 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-944 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-944 description for referenced spec files)
- **DOD:** See SCRUM-944 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-944 '[SRDI][R2.2.4] Ghost and contamination flag logic in validate_result_set'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-944 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 52: Integration evidence collection for [SRDI][R2.2.4] Ghost and contaminat

- **Jira:** SCRUM-944 — [SRDI][R2.2.4] Ghost and contamination flag logic 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-944 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-944 description for referenced spec files)
- **DOD:** See SCRUM-944 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-944 '[SRDI][R2.2.4] Ghost and contamination flag logic in validate_result_set'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-944 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 53: Live validation probe for [SRDI][R2.1.5] Signal 4: over-gener

- **Jira:** SCRUM-941 — [SRDI][R2.1.5] Signal 4: over-generic gig penalty 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-941 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-941 description for referenced spec files)
- **DOD:** See SCRUM-941 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-941)

**Implementation Details:**

Implement a production validation probe for SCRUM-941 '[SRDI][R2.1.5] Signal 4: over-generic gig penalty (-0.15) in compute_gig_relevance'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-941 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 54: External signal validation for [SRDI][R2.1.5] Signal 4: over-gener

- **Jira:** SCRUM-941 — [SRDI][R2.1.5] Signal 4: over-generic gig penalty 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-941 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-941 description for referenced spec files)
- **DOD:** See SCRUM-941 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-941 '[SRDI][R2.1.5] Signal 4: over-generic gig penalty (-0.15) in compute_gig_relevance'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-941 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 55: Scoring pipeline validation for [SRDI][R2.1.5] Signal 4: over-gener

- **Jira:** SCRUM-941 — [SRDI][R2.1.5] Signal 4: over-generic gig penalty 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-941 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-941 description for referenced spec files)
- **DOD:** See SCRUM-941 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-941 '[SRDI][R2.1.5] Signal 4: over-generic gig penalty (-0.15) in compute_gig_relevance'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-941 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 56: Integration evidence collection for [SRDI][R2.1.5] Signal 4: over-gener

- **Jira:** SCRUM-941 — [SRDI][R2.1.5] Signal 4: over-generic gig penalty 
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-941 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-941 description for referenced spec files)
- **DOD:** See SCRUM-941 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-941 '[SRDI][R2.1.5] Signal 4: over-generic gig penalty (-0.15) in compute_gig_relevance'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-941 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 57: Live validation probe for [SRDI][R1.4.5] Store pages_collecte

- **Jira:** SCRUM-928 — [SRDI][R1.4.5] Store pages_collected on SearchResu
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-928 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-928 description for referenced spec files)
- **DOD:** See SCRUM-928 acceptance criteria in Jira

**Files to Create/Modify:**
- - CREATE: docs/cycle_reports/CYCLE_075_AGENT_E.md (section for SCRUM-928)

**Implementation Details:**

Implement a production validation probe for SCRUM-928 '[SRDI][R1.4.5] Store pages_collected on SearchResult'. A LARGE validation probe must: run actual code against live data or the development database, record specific measured values (not just pass/fail), have explicit acceptance criteria, and write results to the evidence file at docs/cycle_reports/CYCLE_083_AGENT_E.md. Design the probe to catch real production failure modes such as: wrong data types returned, unexpected null values, performance regression vs baseline, or incorrect scoring calculations. Run the probe against the current data/cycle037_live.db golden anchor and verify consistency. Record the exact measured value and the accepted range.

**Required Tests:**
- Probe runs without errors against development database
- Measured value recorded in evidence file
- Acceptance criterion verified and documented

**Definition of Done:**
- [ ] Evidence file contains specific measured values (not just PASS)
- [ ] Probe covers real production failure mode
- [ ] Baseline DB integrity confirmed
- [ ] All AC items for SCRUM-928 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 58: External signal validation for [SRDI][R1.4.5] Store pages_collecte

- **Jira:** SCRUM-928 — [SRDI][R1.4.5] Store pages_collected on SearchResu
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-928 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-928 description for referenced spec files)
- **DOD:** See SCRUM-928 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Validate external signal collection for SCRUM-928 '[SRDI][R1.4.5] Store pages_collected on SearchResult'. Run a controlled check of the external data sources used by this feature (Google Trends, Reddit signals, competitive data). Verify that the data collection does not exceed cost limits. Confirm that scrapfly.enabled remains false in config.yaml. If using mock data, verify mock matches the real API schema. Record the signal validation results with timestamps in the evidence file. Document any API rate limit usage observed.

**Required Tests:**
- Signal collection runs within budget limits
- scrapfly.enabled=false confirmed
- Mock data matches real API schema

**Definition of Done:**
- [ ] Cost guard respected
- [ ] Evidence file has timestamped signal data
- [ ] No live API calls without budget approval
- [ ] All AC items for SCRUM-928 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 59: Scoring pipeline validation for [SRDI][R1.4.5] Store pages_collecte

- **Jira:** SCRUM-928 — [SRDI][R1.4.5] Store pages_collected on SearchResu
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-928 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-928 description for referenced spec files)
- **DOD:** See SCRUM-928 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Run validation checks on the scoring pipeline output for SCRUM-928 '[SRDI][R1.4.5] Store pages_collected on SearchResult'. Verify that the scoring components produce consistent results across multiple runs. Check for any floating-point instability or non-deterministic behavior. Confirm that the golden anchor keyword (kw=110) still scores within the expected range after any changes in this cycle. Record the exact score values and compare against the cycle037_live.db baseline. Flag any regression of more than 0.5 points. Document findings with before/after comparison in the evidence file.

**Required Tests:**
- Golden anchor (kw=110) scores within expected range
- Scores are deterministic across 3 runs
- No regression vs baseline DB

**Definition of Done:**
- [ ] Score consistency verified
- [ ] Baseline DB mtime unchanged
- [ ] Evidence file records exact score values
- [ ] All AC items for SCRUM-928 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 60: Integration evidence collection for [SRDI][R1.4.5] Store pages_collecte

- **Jira:** SCRUM-928 — [SRDI][R1.4.5] Store pages_collected on SearchResu
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-928 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-928 description for referenced spec files)
- **DOD:** See SCRUM-928 acceptance criteria in Jira

**Files to Create/Modify:**
- - MODIFY: docs/cycle_reports/CYCLE_075_AGENT_E.md

**Implementation Details:**

Collect integration evidence for SCRUM-928 '[SRDI][R1.4.5] Store pages_collected on SearchResult'. Run the full integration suite against the development database. Record which integration tests pass and which fail. For any failing integration tests, identify whether the failure is pre-existing or introduced by cycle 083 changes. Document the findings with full test output in the evidence file. If integration failures are pre-existing and tracked in Jira, reference the Jira key. New integration failures must be escalated as blockers.

**Required Tests:**
- Integration test suite runs without environment errors
- All new integration failures documented
- Pre-existing failures traced to Jira keys

**Definition of Done:**
- [ ] Integration evidence collected and recorded
- [ ] No new integration failures from cycle 083 changes
- [ ] Evidence file references specific test names and results
- [ ] All AC items for SCRUM-928 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

## VALIDATION STEPS

Run these commands in order. Fix any failures before writing your report.

```bash
# 1. Ruff lint
python -m ruff check src/ tests/ automation/ --output-format=text

# 2. Mypy type check
python -m mypy src/ --ignore-missing-imports

# 3. Pytest — run tests relevant to your changed files
python -m pytest tests/ -q --no-header --tb=short -x

# 4. Config check
python run.py config-check
```

**Do not mark your report complete if any check fails.**

## FINAL REPORT REQUIREMENTS

Write your report to: `docs/cycle_reports/CYCLE_083_AGENT_E.md`

Your report MUST contain:
- Header: `# CYCLE_083_AGENT_E REPORT`
- Summary of all work completed
- List of all files created or modified (with full paths)
- Validation results (ruff/mypy/pytest command output)
- Jira evidence (which AC/DoD items were addressed and how)
- Blockers encountered (if any, with details)
- `AGENT_COMPLETE` as the final line

**IMPORTANT:** Do NOT run git add, git commit, or git push.
Write your report and exit. The controller handles all commits.

## FILES CREATED/MODIFIED THIS CYCLE (Summary)

Fill in after completing all tasks:

| Action | File Path |
|---|---|
| (fill in) | (fill in) |

====================================================================
END OF PROMPT -- AGENT E CYCLE 083
====================================================================

<!-- Generated by prompt_generator.py -->
<!-- Run ID: 20260616T164232 | Generated: 2026-06-16T16:42:34.417339+00:00 -->