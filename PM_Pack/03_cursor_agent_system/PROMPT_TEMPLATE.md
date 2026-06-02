# CURSOR AGENT PROMPT TEMPLATE
# The PM MUST use this exact structure for EVERY agent prompt. No exceptions.

---

```
====================================================================
AGENT {A|B|C|D} — CYCLE {NNN} PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr
- Branch: cycle/{NNN}/integration
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | Playwright | OpenAI | Streamlit

## YOUR ROLE
{Agent role and epic ownership from AGENT_ROSTER.md}
MANDATORY (Agent D, Draft PRs): Start §15.1 Codex wait from `ready_for_review` timestamp (after `gh pr ready <PR>`), not CI completion.

## GIT INSTRUCTIONS
1. Ensure you are on branch: cycle/{NNN}/integration
2. Pull latest: git pull origin cycle/{NNN}/integration
3. All work goes on this branch — do NOT create other branches
4. Commit message format: {type}({scope}): {description}
5. Do NOT push — the human operator will push after all agents complete

## TASKS FOR THIS CYCLE

### Task {N}.{N}.{N}: {Task Title}
- **Story:** S{N}.{N} — {Story Title}
- **Epic:** Epic {NN} — {Epic Name}
- **Spec Reference:** ref/project_plan/{folder}/{FILE}.md
- **DOD Reference:** ref/dod/DOD_EPIC_{NN}.md -> AC-{ID}
- **Files to Create/Modify:**
  - CREATE: src/{path}/{filename}.py
  - MODIFY: src/{path}/{existing_file}.py (add {what exactly})
- **Implementation Details:**
  {Detailed description — class names, method signatures, field types,
  logic flow, edge cases, error handling. >=100 words per task.
  This threshold is strict for every substantive task unless a
  documented PROMPT-DETAIL WAIVER is included in the cycle plan.
  Be exhaustive — the agent should not need to guess anything.}
- **Required Tests:**
  - tests/unit/test_{module}.py::test_{function_name}
  - Test: {describe what the test validates and expected behavior}
  - Test: {describe edge case test}
  - Test: {describe error handling test}
- **Definition of Done:**
  - [ ] {DOD criterion from DOD file}
  - [ ] All tests pass: pytest tests/unit/test_{module}.py -v
  - [ ] No Ruff lint errors
  - [ ] Mypy type check passes

{REPEAT FOR EACH ADDITIONAL TASK — minimum 20 substantive tasks; target 24-32 tasks; maximum 40 tasks. Any exception requires BOTH a TASK-COUNT WAIVER and a PROMPT-DETAIL WAIVER in the cycle plan, including risk rationale and backfill plan.}

## VALIDATION STEPS (Run before declaring done)
1. Path preflight command proving each required file/directory exists (or is intentionally created by this cycle)
2. ruff check {exact existing directories/files} --output-format=text
3. mypy {exact existing directories/files} --ignore-missing-imports
4. pytest {exact existing test files/node IDs} -v
5. If any path is missing and not created by this cycle, use nearest existing suite with explicit rationale instead of blind-failing commands
6. Verify all __init__.py files export new classes/functions when applicable

## FILES CREATED THIS CYCLE (Summary)
| Action | File Path |
|---|---|
| CREATE | src/... |
| CREATE | tests/... |
| MODIFY | src/... |

## COMMIT INSTRUCTIONS
git add .
git commit -m "{type}({scope}): {description} [Agent {A|B|C|D}]"

====================================================================
END OF AGENT {A|B|C|D} PROMPT
====================================================================
```

---

## Template Validation Rules (15 mandatory checks)

| # | Rule | Fail Condition |
|---|---|---|
| 1 | PROJECT CONTEXT section present | Missing = reject |
| 2 | YOUR ROLE section present with specific text | Missing or generic = reject |
| 3 | GIT INSTRUCTIONS with exact branch name | Missing or wrong branch = reject |
| 4 | At least 20 substantive tasks listed | <20 tasks = reject unless both waivers are present with reason, risk, and next-cycle backfill |
| 5 | Each task has Story + Epic reference | Any task missing = reject |
| 6 | Each task has Spec Reference with full path | Any task missing = reject |
| 7 | Each task has DOD Reference with AC ID | Any task missing = reject |
| 8 | Each task lists files to create/modify with full paths | Any task missing = reject |
| 9 | Each task has Implementation Details >=100 words | Any task <100 words = reject |
| 10 | Each task has >=3 Required Tests with descriptions | Any task <3 tests = reject unless the task is explicitly non-code documentation with a validation checklist |
| 11 | Each task has Definition of Done checklist | Any task missing = reject |
| 12 | VALIDATION STEPS section present with commands | Missing = reject |
| 13 | FILES CREATED THIS CYCLE table present | Missing = reject |
| 14 | COMMIT INSTRUCTIONS present | Missing = reject |
| 15 | Total prompt >=6,000 words and preferably 8,000-12,000 words | <6,000 words = reject unless both waivers are present |

## Prompt Template Self-Check (Required)

Before issuing any agent prompt, the PM must include and validate this checklist:

- [ ] Substantive task count is 20-40 (target 24-32), or both waivers are explicitly documented.
- [ ] Every substantive task contains at least 100 words of implementation detail, or a cycle-specific prompt-detail waiver is documented.
- [ ] Each task lists exact Jira key(s), AC bullets, and DoD bullets.
- [ ] Every referenced path exists in the current repository, or the task explicitly creates it this cycle.
- [ ] Validation commands are exact and runnable against current repo layout; no guaranteed-fail mandatory path assumptions remain.
- [ ] Obsolete path assumptions (for example future architecture paths not yet present) are either conditionalized or removed.


## Cycle 012 Corrective Addendum — Depth Standard

The old 500-word / 3-task and 3,000-word / 10-20-task floors are not sufficient for this project. They are preserved only as historical context where explicitly labeled. The binding rule is:

- Every active Cursor agent prompt must contain **20-40 substantive tasks** (target **24-32**).
- Every prompt must be **>=6,000 words**, target **8,000-12,000 words**.
- Every implementation task must include exact files, exact method/class/function names where applicable, edge cases, validation behavior, data-shape expectations, and test names.
- Every cycle reply must include a separate **GitHub Operator Workflow** section with branch creation, per-agent commit order, push command, PR target, PR title/body, CI expectations, merge rule, and main-promotion rule.
- Agents do **not** push directly to `main`. Agents do not push at all unless explicitly instructed. The human operator pushes `cycle/{NNN}/integration`; PR targets `develop`; `main` is updated only by an approved release PR from `develop` after release gates pass.
