# AGENT PROMPT TEMPLATE — Cycle 029+ (PERMANENT)
# Created: 2026-05-19 in response to operator feedback on Cycle 028.
# Implements Rules R-090 (task sizing), R-091 (branch hygiene), R-092 (coverage tier).

---

## Task Sizing Standard (Rule R-090)

Every agent prompt is built from 4-8 MEANINGFUL TASKS — not 16-24 micro-actions.

A "task" is a unit of work that:
- Has a clear deliverable (file created, function implemented, story advanced)
- Is labeled with a complexity tier: SMALL / MEDIUM / LARGE
- Contains its sub-steps INSIDE the task as numbered bullets
- Typically takes 15-60 minutes of agent execution time

### Complexity Tiers

**SMALL (< 15 min, < 50 LOC):**
A focused single-file change, helper function, or interface stub.
Example: "Add `parse_seller_level()` helper + 4 tests to seller_profile.py"

**MEDIUM (15-45 min, 50-200 LOC):**
A complete ORM model, a workflow module's real implementation, a calculator wiring.
Example: "Create `ExternalSignal` ORM model + write_signal helpers + 14 tests"

**LARGE (45-90 min, 200+ LOC):**
A full Playwright workflow real path, a multi-file refactor, an end-to-end integration.
Example: "Implement Workflow 4 (gig_detail) real Playwright path + DB updates + 15 tests"

### Sub-steps Format

Sub-steps go INSIDE a task. They are numbered bullets, not separate tasks.

Example of CORRECT task structure:
```
### Task 3 (MEDIUM, ~30 min): Create ExternalSignal ORM + helpers
Deliverable: src/models/external_signal.py with 4 signal type constants,
write_external_signal(), get_signal(), get_all_signals() helpers, full registration
in src/models/__init__.py, and 14 unit tests in tests/unit/test_external_signal.py.

Sub-steps:
1. Create src/models/external_signal.py with ExternalSignal class
2. Add 4 signal type constants (SIGNAL_GOOGLE_TRENDS, etc.)
3. Add UniqueConstraint and indexes per spec
4. Implement write_external_signal() upsert helper
5. Implement get_signal() and get_all_signals() query helpers
6. Register in src/models/__init__.py
7. Write 14 unit tests covering insert/update/query/constraint behavior
8. Run targeted patch coverage (R-092 Tier 1)
```

Example of WRONG task structure:
```
❌ Task 3: Create external_signal.py
❌ Task 4: Add signal constants
❌ Task 5: Register in __init__.py
❌ Task 6: Write tests
❌ Task 7: Run coverage
❌ Task 8: Commit
```

---

## Agent Time Budget (NEW)

Every prompt MUST include a TIME BUDGET BLOCK at the top:

```
## Agent Time Budget (estimated)
- Task 1 (SMALL): 10 min
- Task 2 (MEDIUM): 30 min
- Task 3 (LARGE): 60 min
- Task 4 (SMALL): 10 min
- Task 5 (MEDIUM): 25 min
Total estimated: ~2 hr 15 min
```

This sets expectations and lets the operator monitor agent pace.

---

## Validation Block Standard (Rule R-092)

### For Agents A, B, C (FAST — targeted only):

```
### Validation (R-092 Tier 1 — targeted only)
python -m pytest -q tests/unit/test_{your_new_file}.py
python -m pytest -q --cov=src.{your_module} --cov-report=term-missing tests/unit/test_{your_new_file}.py
Target: your new tests pass 100%, your module patch coverage >=90%.
```

DO NOT include in Agents A/B/C prompts:
- python -m pytest -q --cov=src --cov-fail-under=90  (this is Agent D's job)
- The 6-command "full validation block"
- Coverage XML generation
- python run.py phase2-smoke / collect-only (only Agent D needs these)

### For Agent D (COMPREHENSIVE — single end-of-cycle audit):

```
### Full validation block (R-092 Tier 2 — Agent D only)
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle{N}.db
python run.py phase2-smoke
python run.py collect-only

### Comprehensive patch coverage audit (R-092 Tier 2)
python -m pytest -q --cov=src.{module_A} --cov-report=term-missing
python -m pytest -q --cov=src.{module_B} --cov-report=term-missing
[... for every module touched this cycle]
```

---

## Branch Hygiene (Rule R-091)

Agent A prompt MUST include in their PR-merge task:

```
After successful gh pr merge {N}:
- git push origin --delete cycle/{N}/integration   # delete remote
- git branch -D cycle/{N}/integration              # delete local
- git fetch --all --prune                          # cleanup refs

If cycle ends in 0 or 5 (030, 035, 040): also run periodic full cleanup:
- git branch -r | Select-String "cycle/" | Select-Object Line
- For any cycle branch older than 3 cycles back AND verified MERGED: delete it.

Document the cleanup result in your cycle report under "Branch Hygiene".
```

---

## Standard Task Structure Per Cycle (Reference)

A typical cycle has these 4-task buckets per agent:

### Agent A (4-6 tasks):
1. PR Gate + Branch Cleanup + Cycle Branch Setup (MEDIUM)
2. Primary Implementation Task (LARGE)
3. Tests + Targeted Coverage (SMALL or MEDIUM)
4. Jira Evidence + Handoff Documentation (SMALL)

### Agent B (4-6 tasks):
1. Preflight + Spec Read + Story Read (SMALL)
2. Primary Implementation Task (LARGE)
3. Tests + Targeted Coverage (SMALL or MEDIUM)
4. Jira Evidence + Handoff (SMALL)

### Agent C (4-6 tasks):
Similar structure to Agent B.

### Agent D (5-8 tasks — additional cycle steward responsibilities):
1. Preflight + Read All Handoffs (SMALL)
2. Primary Implementation Task (MEDIUM or LARGE)
3. Tests + Comprehensive Coverage Audit (MEDIUM)
4. Board Reconciliation + Epic Progress Comments (SMALL)
5. PR Creation + CI Monitoring (MEDIUM)
6. Mandatory Codex Disposition Query (SMALL or MEDIUM)
7. Mandatory Merge Gate Checklist (SMALL)
8. Final Steward Cleanup (SMALL)

Each task is described with its tier, deliverable, and sub-steps.
A prompt should be readable as "here's what you're building" — not as
"here's a 24-item bureaucratic checklist."

---

## Anti-Patterns (What NOT to do)

1. Don't count "post Jira comment" as a task. Embed it as a sub-step in the
   task whose work the comment evidences.

2. Don't count "git add / git commit" as a task. Put the commit at the END
   of the implementation task with the exact git command.

3. Don't count "record SHA" or "update ACTIVE_STORY_DOD_LEDGER" as a task.
   These are sub-steps inside the Jira evidence / handoff task.

4. Don't have Agents A/B/C run the full pytest suite. That's Agent D's job
   under Rule R-092.

5. Don't write more than 8 tasks per agent prompt. If you have more than 8,
   you have not consolidated micro-actions. Re-group them.

6. Don't write tasks without a complexity tier label. Every task must have
   SMALL / MEDIUM / LARGE in its heading.
