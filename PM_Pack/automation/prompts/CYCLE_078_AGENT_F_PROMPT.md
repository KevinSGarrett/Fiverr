====================================================================
AGENT F -- CYCLE 078 PROMPT
====================================================================

## PROJECT CONTEXT

- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch: `cycle/078/integration`
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit
- Cycle: 078 | Run ID: 20260613T224936

## MODEL POLICY (MANDATORY â€” do not override)

- **Model:** Codex 5.3
- **Effort:** medium
- **Auto model selection:** DISABLED â€” use only Codex 5.3
- **Fallback model:** DISABLED
- **Billing:** Claude subscription only for PM review; no API key

## YOUR ROLE

**Agent F** â€” Test coverage gaps, regression tests, coverage enforcement
**Role type:** `test_coverage_regression`

**You own these file paths (you may create/modify only these):**
- `tests/**`

## GIT INSTRUCTIONS

1. Confirm you are on branch: `cycle/078/integration`
   ```
   git branch --show-current
   # Expected: cycle/078/integration
   ```
2. Pull latest: `git pull origin cycle/078/integration`
3. ALL work on `cycle/078/integration` only â€” do NOT create other branches
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
| SCRUM-287 | [LOW L1] Sweep 23 stale In-Review issues — verify DoD e | To Do | Low |
| SCRUM-288 | [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate fil | To Do | Low |
| SCRUM-211 | [PLAYBOOK] S8.7 Playbook Dashboard Data Layer | To Do | Medium |
| SCRUM-229 | [DASHBOARD] S9.15 Mobile Optimization | To Do | Medium |
| SCRUM-230 | [DASHBOARD] S9.16 Pricing Dashboard Widgets | To Do | Medium |
| SCRUM-246 | [PM PROCESS] Cycle 001 prompts lacked required depth an | In Review | Medium |
| SCRUM-250 | [PM/JIRA] Correct cycle-to-story Jira mapping and preve | In Review | Medium |
| SCRUM-252 | [PM/CURSOR] Grant Cursor-agent Jira operations authorit | In Review | Medium |
| SCRUM-253 | [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard bl | In Review | Medium |
| SCRUM-254 | [PM/JIRA] Enforce full-board AC/DoD-first planning and  | In Review | Medium |
| SCRUM-255 | [CYCLE 012] Close AC/DoD audit gaps from Agent D integr | To Do | Medium |
| SCRUM-256 | [CYCLE 013] Resolve PR #10 Codex blockers and continue  | In Progress | Medium |
| SCRUM-257 | [CYCLE 013] Audit recent Done dashboard stories for pre | To Do | Medium |
| SCRUM-258 | [CYCLE 014] Resume product development and enforce same | In Progress | Medium |

## TASKS FOR THIS CYCLE

> **Floor:** 55 LARGE/XLARGE/XXLARGE tasks (AGENT_TASK_FLOOR_ENFORCEMENT.md hard rule).
> Each task must have: Story/Jira key, Epic, Spec, Files, Implementation details
> (>=100 words), >=3 tests, Definition of Done.

### Task 1: Test coverage gap analysis for [LOW L1] Sweep 23 stale In-Review i

- **Jira:** SCRUM-287 â€” [LOW L1] Sweep 23 stale In-Review issues — verify 
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-287 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-287 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_low_l1__sweep_23_stale_i.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-287 '[LOW L1] Sweep 23 stale In-Review issues — verify DoD evidence and transition to correct status'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-287 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 2: Regression test expansion for [LOW L1] Sweep 23 stale In-Review i

- **Jira:** SCRUM-287 â€” [LOW L1] Sweep 23 stale In-Review issues — verify 
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-287 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-287 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_low_l1__sweep_23_stale_i_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-287 '[LOW L1] Sweep 23 stale In-Review issues — verify DoD evidence and transition to correct status'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-287 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-287 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 3: Edge case and error path tests for [LOW L1] Sweep 23 stale In-Review i

- **Jira:** SCRUM-287 â€” [LOW L1] Sweep 23 stale In-Review issues — verify 
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-287 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-287 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_low_l1__sweep_23_stale_i.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-287 '[LOW L1] Sweep 23 stale In-Review issues — verify DoD evidence and transition to correct status'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-287 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 4: Test fixture and conftest improvements for [LOW L1] Sweep 23 stale In-Review i

- **Jira:** SCRUM-287 â€” [LOW L1] Sweep 23 stale In-Review issues — verify 
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-287 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-287 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_low_l1__sweep_23_stale_i.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-287 '[LOW L1] Sweep 23 stale In-Review issues — verify DoD evidence and transition to correct status'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-287 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 5: Test coverage gap analysis for [LOW L7/L9/L10] Minor cleanup — Cyc

- **Jira:** SCRUM-288 â€” [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicat
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-288 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-288 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_low_l7_l9_l10__minor_cle.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-288 '[LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIES.md ID mapping, CHANGE_LOG missing cycles 013-017'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-288 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 6: Regression test expansion for [LOW L7/L9/L10] Minor cleanup — Cyc

- **Jira:** SCRUM-288 â€” [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicat
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-288 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-288 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_low_l7_l9_l10__minor_cle_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-288 '[LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIES.md ID mapping, CHANGE_LOG missing cycles 013-017'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-288 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-288 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 7: Edge case and error path tests for [LOW L7/L9/L10] Minor cleanup — Cyc

- **Jira:** SCRUM-288 â€” [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicat
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-288 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-288 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_low_l7_l9_l10__minor_cle.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-288 '[LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIES.md ID mapping, CHANGE_LOG missing cycles 013-017'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-288 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 8: Test fixture and conftest improvements for [LOW L7/L9/L10] Minor cleanup — Cyc

- **Jira:** SCRUM-288 â€” [LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicat
- **Status:** To Do | **Priority:** Low
- **Epic:** See SCRUM-288 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-288 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_low_l7_l9_l10__minor_cle.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-288 '[LOW L7/L9/L10] Minor cleanup — Cycle 016 duplicate files, USER_STORIES.md ID mapping, CHANGE_LOG missing cycles 013-017'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-288 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 9: Test coverage gap analysis for [PLAYBOOK] S8.7 Playbook Dashboard 

- **Jira:** SCRUM-211 â€” [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-211 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-211 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_playbook__s8_7_playbook.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-211 '[PLAYBOOK] S8.7 Playbook Dashboard Data Layer'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-211 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 10: Regression test expansion for [PLAYBOOK] S8.7 Playbook Dashboard 

- **Jira:** SCRUM-211 â€” [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-211 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-211 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_playbook__s8_7_playbook_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-211 '[PLAYBOOK] S8.7 Playbook Dashboard Data Layer'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-211 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-211 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 11: Edge case and error path tests for [PLAYBOOK] S8.7 Playbook Dashboard 

- **Jira:** SCRUM-211 â€” [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-211 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-211 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_playbook__s8_7_playbook.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-211 '[PLAYBOOK] S8.7 Playbook Dashboard Data Layer'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-211 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 12: Test fixture and conftest improvements for [PLAYBOOK] S8.7 Playbook Dashboard 

- **Jira:** SCRUM-211 â€” [PLAYBOOK] S8.7 Playbook Dashboard Data Layer
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-211 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-211 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_playbook__s8_7_playbook.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-211 '[PLAYBOOK] S8.7 Playbook Dashboard Data Layer'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-211 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 13: Test coverage gap analysis for [DASHBOARD] S9.15 Mobile Optimizati

- **Jira:** SCRUM-229 â€” [DASHBOARD] S9.15 Mobile Optimization
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-229 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-229 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_dashboard__s9_15_mobile.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-229 '[DASHBOARD] S9.15 Mobile Optimization'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-229 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 14: Regression test expansion for [DASHBOARD] S9.15 Mobile Optimizati

- **Jira:** SCRUM-229 â€” [DASHBOARD] S9.15 Mobile Optimization
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-229 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-229 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_dashboard__s9_15_mobile_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-229 '[DASHBOARD] S9.15 Mobile Optimization'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-229 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-229 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 15: Edge case and error path tests for [DASHBOARD] S9.15 Mobile Optimizati

- **Jira:** SCRUM-229 â€” [DASHBOARD] S9.15 Mobile Optimization
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-229 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-229 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_dashboard__s9_15_mobile.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-229 '[DASHBOARD] S9.15 Mobile Optimization'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-229 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 16: Test fixture and conftest improvements for [DASHBOARD] S9.15 Mobile Optimizati

- **Jira:** SCRUM-229 â€” [DASHBOARD] S9.15 Mobile Optimization
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-229 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-229 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_dashboard__s9_15_mobile.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-229 '[DASHBOARD] S9.15 Mobile Optimization'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-229 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 17: Test coverage gap analysis for [DASHBOARD] S9.16 Pricing Dashboard

- **Jira:** SCRUM-230 â€” [DASHBOARD] S9.16 Pricing Dashboard Widgets
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-230 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-230 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_dashboard__s9_16_pricing.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-230 '[DASHBOARD] S9.16 Pricing Dashboard Widgets'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-230 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 18: Regression test expansion for [DASHBOARD] S9.16 Pricing Dashboard

- **Jira:** SCRUM-230 â€” [DASHBOARD] S9.16 Pricing Dashboard Widgets
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-230 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-230 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_dashboard__s9_16_pricing_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-230 '[DASHBOARD] S9.16 Pricing Dashboard Widgets'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-230 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-230 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 19: Edge case and error path tests for [DASHBOARD] S9.16 Pricing Dashboard

- **Jira:** SCRUM-230 â€” [DASHBOARD] S9.16 Pricing Dashboard Widgets
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-230 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-230 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_dashboard__s9_16_pricing.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-230 '[DASHBOARD] S9.16 Pricing Dashboard Widgets'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-230 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 20: Test fixture and conftest improvements for [DASHBOARD] S9.16 Pricing Dashboard

- **Jira:** SCRUM-230 â€” [DASHBOARD] S9.16 Pricing Dashboard Widgets
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-230 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-230 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_dashboard__s9_16_pricing.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-230 '[DASHBOARD] S9.16 Pricing Dashboard Widgets'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-230 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 21: Test coverage gap analysis for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 â€” [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_process__cycle_001_pr.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 22: Regression test expansion for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 â€” [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_pm_process__cycle_001_pr_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-246 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 23: Edge case and error path tests for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 â€” [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_process__cycle_001_pr.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 24: Test fixture and conftest improvements for [PM PROCESS] Cycle 001 prompts lack

- **Jira:** SCRUM-246 â€” [PM PROCESS] Cycle 001 prompts lacked required dep
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-246 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-246 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_pm_process__cycle_001_pr.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-246 '[PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-246 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 25: Test coverage gap analysis for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 â€” [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_jira__correct_cycle_t.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 26: Regression test expansion for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 â€” [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_pm_jira__correct_cycle_t_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-250 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 27: Edge case and error path tests for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 â€” [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_jira__correct_cycle_t.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 28: Test fixture and conftest improvements for [PM/JIRA] Correct cycle-to-story Ji

- **Jira:** SCRUM-250 â€” [PM/JIRA] Correct cycle-to-story Jira mapping and 
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-250 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-250 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_pm_jira__correct_cycle_t.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-250 '[PM/JIRA] Correct cycle-to-story Jira mapping and prevent governance-only updates'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-250 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 29: Test coverage gap analysis for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 â€” [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_cursor__grant_cursor.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 30: Regression test expansion for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 â€” [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_pm_cursor__grant_cursor_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-252 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 31: Edge case and error path tests for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 â€” [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_cursor__grant_cursor.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 32: Test fixture and conftest improvements for [PM/CURSOR] Grant Cursor-agent Jira

- **Jira:** SCRUM-252 â€” [PM/CURSOR] Grant Cursor-agent Jira operations aut
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-252 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-252 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_pm_cursor__grant_cursor.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-252 '[PM/CURSOR] Grant Cursor-agent Jira operations authority and double agent task limits'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-252 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 33: Test coverage gap analysis for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 â€” [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_011__resolve_pr__8.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 34: Regression test expansion for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 â€” [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_cycle_011__resolve_pr__8_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-253 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 35: Edge case and error path tests for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 â€” [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_011__resolve_pr__8.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 36: Test fixture and conftest improvements for [CYCLE 011] Resolve PR #8 Codex che

- **Jira:** SCRUM-253 â€” [CYCLE 011] Resolve PR #8 Codex checkpoint/dashboa
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-253 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-253 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_cycle_011__resolve_pr__8.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-253 '[CYCLE 011] Resolve PR #8 Codex checkpoint/dashboard blockers and continue Jira-operated Phase 2 work'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-253 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 37: Test coverage gap analysis for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 â€” [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_jira__enforce_full_bo.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 38: Regression test expansion for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 â€” [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_pm_jira__enforce_full_bo_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-254 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 39: Edge case and error path tests for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 â€” [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_pm_jira__enforce_full_bo.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 40: Test fixture and conftest improvements for [PM/JIRA] Enforce full-board AC/DoD

- **Jira:** SCRUM-254 â€” [PM/JIRA] Enforce full-board AC/DoD-first planning
- **Status:** In Review | **Priority:** Medium
- **Epic:** See SCRUM-254 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-254 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_pm_jira__enforce_full_bo.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-254 '[PM/JIRA] Enforce full-board AC/DoD-first planning and double Cursor prompt depth again'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-254 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 41: Test coverage gap analysis for [CYCLE 012] Close AC/DoD audit gaps

- **Jira:** SCRUM-255 â€” [CYCLE 012] Close AC/DoD audit gaps from Agent D i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-255 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-255 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_012__close_ac_dod.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-255 '[CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-255 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 42: Regression test expansion for [CYCLE 012] Close AC/DoD audit gaps

- **Jira:** SCRUM-255 â€” [CYCLE 012] Close AC/DoD audit gaps from Agent D i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-255 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-255 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_cycle_012__close_ac_dod_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-255 '[CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-255 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-255 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 43: Edge case and error path tests for [CYCLE 012] Close AC/DoD audit gaps

- **Jira:** SCRUM-255 â€” [CYCLE 012] Close AC/DoD audit gaps from Agent D i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-255 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-255 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_012__close_ac_dod.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-255 '[CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-255 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 44: Test fixture and conftest improvements for [CYCLE 012] Close AC/DoD audit gaps

- **Jira:** SCRUM-255 â€” [CYCLE 012] Close AC/DoD audit gaps from Agent D i
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-255 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-255 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_cycle_012__close_ac_dod.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-255 '[CYCLE 012] Close AC/DoD audit gaps from Agent D integration handoff'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-255 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 45: Test coverage gap analysis for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 â€” [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_013__resolve_pr__1.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 46: Regression test expansion for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 â€” [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_cycle_013__resolve_pr__1_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-256 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 47: Edge case and error path tests for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 â€” [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_013__resolve_pr__1.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 48: Test fixture and conftest improvements for [CYCLE 013] Resolve PR #10 Codex bl

- **Jira:** SCRUM-256 â€” [CYCLE 013] Resolve PR #10 Codex blockers and cont
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-256 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-256 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_cycle_013__resolve_pr__1.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-256 '[CYCLE 013] Resolve PR #10 Codex blockers and continue board-first development'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-256 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 49: Test coverage gap analysis for [CYCLE 013] Audit recent Done dashb

- **Jira:** SCRUM-257 â€” [CYCLE 013] Audit recent Done dashboard stories fo
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-257 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-257 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_013__audit_recent.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-257 '[CYCLE 013] Audit recent Done dashboard stories for premature closure signals'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-257 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 50: Regression test expansion for [CYCLE 013] Audit recent Done dashb

- **Jira:** SCRUM-257 â€” [CYCLE 013] Audit recent Done dashboard stories fo
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-257 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-257 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_cycle_013__audit_recent_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-257 '[CYCLE 013] Audit recent Done dashboard stories for premature closure signals'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-257 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-257 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 51: Edge case and error path tests for [CYCLE 013] Audit recent Done dashb

- **Jira:** SCRUM-257 â€” [CYCLE 013] Audit recent Done dashboard stories fo
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-257 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-257 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_013__audit_recent.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-257 '[CYCLE 013] Audit recent Done dashboard stories for premature closure signals'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-257 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 52: Test fixture and conftest improvements for [CYCLE 013] Audit recent Done dashb

- **Jira:** SCRUM-257 â€” [CYCLE 013] Audit recent Done dashboard stories fo
- **Status:** To Do | **Priority:** Medium
- **Epic:** See SCRUM-257 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-257 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_cycle_013__audit_recent.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-257 '[CYCLE 013] Audit recent Done dashboard stories for premature closure signals'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-257 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 53: Test coverage gap analysis for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 â€” [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_014__resume_produc.py (add coverage tests)
- - MODIFY: tests/conftest.py (add fixtures if needed)

**Implementation Details:**

Analyze test coverage gaps for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution'. Run pytest --cov on the files changed in this story. Identify all uncovered lines and branches. For each gap, determine if the gap represents a real risk (untested error path, untested edge case) or is acceptable (boilerplate, logging). Write tests for all high-risk coverage gaps. Target 90%+ coverage on changed files. Document the coverage analysis in the cycle report.

**Required Tests:**
- Coverage report shows >= 90% on changed files
- All high-risk uncovered paths have tests
- Coverage gap analysis documented

**Definition of Done:**
- [ ] Coverage floor (90%) met for all changed files
- [ ] High-risk gaps have test coverage
- [ ] Coverage report committed
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 54: Regression test expansion for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 â€” [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - CREATE: tests/unit/test_cycle_014__resume_produc_regression.py
- - MODIFY: docs/AGENT_EXECUTION_STRATEGY.md (add to permanent pack)

**Implementation Details:**

Add regression tests for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution'. Review the permanent regression pack in AGENT_EXECUTION_STRATEGY.md. Verify that all 20+ existing regression tests still pass after changes in this cycle. Add new regression tests for any production failure modes discovered during this cycle. Each new regression test must be substantive: it must run actual code, produce a measurable result, have acceptance criteria, and be added to the permanent pack documentation.

**Required Tests:**
- All existing regression tests still pass
- New regression test added for SCRUM-258 failure mode
- New test added to permanent pack documentation

**Definition of Done:**
- [ ] Regression pack integrity maintained
- [ ] New regression tests documented in AGENT_EXECUTION_STRATEGY.md
- [ ] No existing regression tests broken
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 55: Edge case and error path tests for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 â€” [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/unit/test_cycle_014__resume_produc.py (add edge case tests)

**Implementation Details:**

Write edge case and error path tests for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution'. Identify the most likely real-world failure modes: empty database, malformed API response, rate limit hit, concurrent access, very large or very small numeric values. For each edge case, write a test that: sets up the specific failure condition, calls the code under test, and verifies the correct error behavior. Tests must be deterministic and not require live API access.

**Required Tests:**
- Edge case test covers empty/null input correctly
- Error path test verifies exception type and message
- Concurrent access test (if applicable) passes under load

**Definition of Done:**
- [ ] All edge cases identified in spec have tests
- [ ] Error paths produce specific, testable exceptions
- [ ] Tests are deterministic (no flakiness)
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

### Task 56: Test fixture and conftest improvements for [CYCLE 014] Resume product developm

- **Jira:** SCRUM-258 â€” [CYCLE 014] Resume product development and enforce
- **Status:** In Progress | **Priority:** Medium
- **Epic:** See SCRUM-258 parent epic in Jira board
- **Spec:** `ref/project_plan/` (see SCRUM-258 description for referenced spec files)
- **AC:** AC placeholder: define acceptance criteria in Jira.
- **DoD:** Definition of done should be confirmed in Jira.

**Files to Create/Modify:**
- - MODIFY: tests/conftest.py (extract fixtures)
- - MODIFY: tests/unit/test_cycle_014__resume_produc.py (use fixtures)

**Implementation Details:**

Improve test fixtures and conftest.py for SCRUM-258 '[CYCLE 014] Resume product development and enforce same-cycle Codex resolution'. If tests for this story require complex setup, extract it into reusable pytest fixtures in the appropriate conftest.py. Ensure fixtures are properly scoped (function/class/module/session). Add parameterized test cases where the same logic needs to be tested with multiple inputs. Verify that fixture teardown is clean and does not leave test artifacts that could affect other tests.

**Required Tests:**
- Fixtures extracted and reusable across multiple tests
- Parametrized tests cover all required input variants
- Fixture teardown is clean (verified by running tests in isolation)

**Definition of Done:**
- [ ] No fixture pollution between tests
- [ ] Complex setup is in fixtures, not inline
- [ ] Parametrized cases cover the full AC matrix
- [ ] All AC items for SCRUM-258 addressed by this task
- [ ] Ruff: 0 errors on changed files
- [ ] Mypy: 0 errors on changed files

## VALIDATION STEPS

Run these commands in order. Fix any failures before writing your report.

```bash
# 1. Ruff lint
python -m ruff check src/ tests/ automation/ --output-format=full

# 2. Mypy type check
python -m mypy src/ --ignore-missing-imports

# 3. Pytest â€” run tests relevant to your changed files
python -m pytest tests/ -q --no-header --tb=short -x

# 4. Config check
python run.py config-check
```

**Do not mark your report complete if any check fails.**

## FINAL REPORT REQUIREMENTS

Write your report to: `docs/cycle_reports/CYCLE_078_AGENT_F.md`

Your report MUST contain:
- Header: `# CYCLE_078_AGENT_F REPORT`
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
| (provided by agent evidence) | (provided by agent evidence) |

====================================================================
END OF PROMPT -- AGENT F CYCLE 078
====================================================================

<!-- Generated by prompt_generator.py -->
<!-- Run ID: 20260613T224936 | Generated: 2026-06-13T22:49:39.084531+00:00 -->