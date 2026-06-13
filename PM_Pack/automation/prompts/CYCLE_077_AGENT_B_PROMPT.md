# CYCLE 077 — AGENT B PROMPT
# Dispatched after: Agent A AGENT_COMPLETE
# Branch: cycle/077/integration
# Generated: 2026-06-12 by Claude PM post-Cycle 076 review

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight + read Agent A handoff
- Task 2 (LARGE): 60 min — Fix full-suite coverage truncation
- Task 3 (MEDIUM): 35 min — Stabilize automation-only coverage capture
- Task 4 (MEDIUM): 25 min — Raise any remaining modules below 90%
- Task 5 (SMALL): 10 min — Jira evidence + cycle report
Total estimated: ~2 hr 25 min

---

## Context

You are Cursor Agent B for the Fiverr Research System 24/7 Autonomous Runner, Cycle 077.

Agent A has completed: PM_Pack state updated for Cycle 077, ADR-014/015 written,
branch cycle/077/integration created from develop.

Combined coverage is 92.58% and CI passes. However there is a known anomaly:
when all automation tests run together (full suite, not targeted), coverage
sometimes truncates at ~54% in the runner environment due to coverage collection
interruption. This needs to be diagnosed and fixed so that the CI and runner
report accurately matches the per-module verified coverage.

Repository: C:\Fiverr\Fiverr
Jira cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
Branch: cycle/077/integration

---

## Task 1 (SMALL, ~15 min): Preflight and read handoffs

Deliverable: Confirmed on correct branch; Agent A's work verified.

Sub-steps:
1. `git checkout cycle/077/integration && git pull origin cycle/077/integration`
2. Confirm Agent A's commit is present: `git log --oneline -5`
3. Read docs/cycle_reports/CYCLE_077_AGENT_A.md — note any blockers or flags
4. Run: `python automation/ai_cycle_controller.py brain-check` — must PASS
5. Run: `python -m ruff check automation/ src/ tests/` — 0 errors
6. Run: `python -m mypy automation/ --ignore-missing-imports` — 0 errors

---

## Task 2 (LARGE, ~60 min): Diagnose and fix full-suite coverage truncation

Deliverable: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing`
reports combined coverage ≥90% without truncation; root cause documented.

Sub-steps:
1. Run the full unit suite with coverage and capture full output:
   `python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing --timeout=60 -q 2>&1 | Tee-Object coverage_full_output.txt`
2. Check if coverage truncates: look for "TOTAL" line — if it shows <90% but individual
   module runs show >90%, truncation is occurring
3. Common causes of truncation:
   a. Coverage plugin interrupted mid-run (OOM, timeout, SIGTERM)
   b. `.coverage` file written multiple times from parallel test processes
   c. `coverage.run()` not committed if tests exit early
   d. `pytest-xdist` parallel workers clobbering coverage data
4. Check if `pytest-xdist` is in use: look at conftest.py and pyproject.toml
5. Verify `[tool.coverage.run]` in pyproject.toml — check for `parallel = true` or missing settings
6. Add/verify in pyproject.toml under `[tool.coverage.run]`:
   - `branch = true`
   - `parallel = false` (or if parallel is needed, `concurrency = ["thread"]`)
   - `omit = ["tests/*", ".venv/*", "*/migrations/*"]`
7. Run targeted automation-only coverage to confirm correct values:
   `python -m pytest tests/unit/ -k "automation" --cov=automation --cov-report=term-missing --timeout=60 -q`
8. Run full suite again after pyproject.toml fix; confirm TOTAL shows ≥90%
9. If coverage is accurate, delete coverage_full_output.txt; else keep for diagnostics
10. Document root cause in cycle report

---

## Task 3 (MEDIUM, ~35 min): Stabilize coverage capture in runner environment

Deliverable: `python -m pytest tests/unit/ --cov=automation --cov-report=xml`
completes deterministically 3 times in a row; coverage.xml has correct TOTAL.

Sub-steps:
1. Run the test suite 3 times with coverage; capture TOTAL line each time:
   ```
   for i in 1..3:
     python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing -q --timeout=60
     grep TOTAL (last run output)
   ```
2. If TOTAL is consistent across 3 runs, coverage is stable — document it
3. If TOTAL varies run-to-run, there is a non-deterministic coverage issue:
   a. Check for any tests that import modules conditionally or use importlib
   b. Check for any tests marked with `@pytest.mark.coverage_skip` or similar
   c. Check for any conftest.py that modifies sys.path or monkeypatches modules
4. Add `--cov-config=pyproject.toml` explicitly to the pytest command to ensure
   coverage uses the correct config
5. Verify `coverage.xml` is generated and has a valid `line-rate` attribute ≥ 0.90
6. Confirm the CI command `python -m pytest tests/unit/ --cov=src --cov=automation
   --cov-report=xml --cov-fail-under=90 --timeout=60` would pass with this result

---

## Task 4 (MEDIUM, ~25 min): Raise any remaining automation modules below 90%

Deliverable: All automation/ modules individually report ≥90% when tested with
their corresponding test file; no module below 85% in combined run.

Sub-steps:
1. Run per-module coverage audit for all automation modules:
   ```python
   for mod in automation/*.py:
     python -m pytest tests/unit/ -k "test_{mod}" --cov=automation.{mod} --cov-report=term-missing -q
   ```
2. List any module showing <90% in the targeted run
3. For each module below 90%: read the module, identify untested branches/lines,
   write targeted test cases in the existing test file
4. Focus on branch coverage: if/else branches, error paths, empty-list paths
5. Run targeted coverage after each fix to confirm improvement
6. Do NOT lower the --cov-fail-under threshold; raise the code coverage instead
7. Run full `ruff check automation/ tests/` after any new test additions
8. Run `mypy automation/` after any production code changes

---

## Task 5 (SMALL, ~10 min): Cycle report and Jira evidence

Deliverable: CYCLE_077_AGENT_B.md written; Jira story commented; changes committed.

Sub-steps:
1. Create docs/cycle_reports/CYCLE_077_AGENT_B.md:
   - Coverage truncation diagnosis: root cause identified (yes/no) + what it was
   - Before/after TOTAL coverage (automation+src combined)
   - Modules fixed (if any) with before/after %
   - 3-run consistency test result
   - Ruff PASS | Mypy PASS | brain-check PASS
   - End with: AGENT_COMPLETE
2. Find Jira story "Stabilize automation-only full-suite coverage capture" — post comment
   with coverage TOTAL value and 3-run stability result
3. `git add -A`
4. `git commit -m "fix(coverage): stabilize full-suite coverage capture, raise remaining modules to >=90%"`
5. `git push origin cycle/077/integration`

---

## Validation (R-092 Tier 1)

```bash
python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing -q --timeout=60
python -m ruff check automation/ src/ tests/
python -m mypy automation/ --ignore-missing-imports
python automation/ai_cycle_controller.py brain-check
```

---

## Hard gates

- Do NOT reduce --cov-fail-under below 90
- Do NOT modify `data/cycle037_live.db`
- Do NOT run plan-cycle --live
- If coverage TOTAL stays below 90% after your fixes, document why and flag for Cycle 078

---

END OF PROMPT
