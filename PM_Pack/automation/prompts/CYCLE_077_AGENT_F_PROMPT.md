# CYCLE 077 — AGENT F PROMPT
# Dispatched after: Agent C AGENT_COMPLETE
# Branch: cycle/077/integration
# Generated: 2026-06-12 by Claude PM post-Cycle 076 review

## Agent Time Budget (estimated)
- Task 1 (SMALL): 10 min — Preflight + read Agent C handoff
- Task 2 (LARGE): 60 min — Raise src/ module coverage gaps
- Task 3 (MEDIUM): 30 min — Full regression suite + mutation safety check
- Task 4 (SMALL): 15 min — Coverage report + cycle report + commit
Total estimated: ~1 hr 55 min

---

## Context

You are Cursor Agent F for the Fiverr Research System 24/7 Autonomous Runner, Cycle 077.

Agent C has verified V-1 evidence and confirmed CI simulation PASS.
Your job is to improve src/ module coverage, run the full regression suite,
and confirm the codebase is in the best possible state before Agent D closes the cycle.

Current combined coverage: ≥90% (per Agent C verification).
Focus areas: any src/ module below 85%, any automation/ module that regressed.

Repository: C:\Fiverr\Fiverr
Jira cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
Branch: cycle/077/integration

---

## Task 1 (SMALL, ~10 min): Preflight and read handoff

Sub-steps:
1. `git checkout cycle/077/integration && git pull origin cycle/077/integration`
2. `git log --oneline -10` — confirm all A/B/E/C commits present
3. Read docs/cycle_reports/CYCLE_077_AGENT_C.md — note coverage TOTAL and any flags
4. Run: `python automation/ai_cycle_controller.py brain-check` — must PASS
5. Run: `python -m ruff check automation/ src/ tests/` — 0 errors

---

## Task 2 (LARGE, ~60 min): Raise src/ module coverage gaps

Deliverable: All src/ modules that were below 85% are now at ≥85%;
at least 3 previously low-coverage src/ modules improved.

Sub-steps:
1. Run per-module coverage scan across all src/ modules:
   `python -m pytest tests/unit/ --cov=src --cov-report=term-missing -q --timeout=60 2>&1 | grep -E "^src/"`
2. Identify all src/ modules below 85%; sort by coverage ascending
3. For each of the top 3 lowest-coverage modules:
   a. Read the module in full — understand its interface and purpose
   b. Run existing tests: `python -m pytest tests/unit/ -k "test_{module_name}" -v --tb=short`
   c. Identify the lowest-coverage lines/branches (look at "miss" column in term-missing)
   d. Write targeted test cases for uncovered branches:
      - Error paths (exception handling)
      - Edge cases (empty input, None values, boundary conditions)
      - Conditional branches (if/elif/else)
   e. Add tests to the existing test file (do not create new files unless none exists)
   f. Run module-targeted coverage: `python -m pytest tests/unit/ -k "test_{module}" --cov=src.{module} --cov-report=term-missing -q`
   g. Confirm improvement; document before/after %
4. Do not reduce existing tests or remove assertions to improve coverage artificially
5. After all improvements, run `python -m ruff check tests/` — 0 errors
6. Run `python -m mypy automation/ --ignore-missing-imports` — 0 errors

---

## Task 3 (MEDIUM, ~30 min): Full regression suite + safety check

Deliverable: Full unit test suite passes; combined coverage ≥90% confirmed;
no regressions introduced by any Cycle 077 agent.

Sub-steps:
1. Run the full unit suite:
   `python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing -q --timeout=60`
2. Record: N passed, N failed (expected: 0 failures, ≤5 xfail/xpass)
3. Record: TOTAL coverage % (must be ≥90%)
4. If any unexpected failures:
   - Run failing test individually with `--tb=long`
   - If caused by your Task 2 changes: fix your code
   - If pre-existing: mark with `@pytest.mark.xfail(strict=False, reason="pre-existing: <description>")`
5. Quick safety check — confirm baseline DB untouched:
   `git diff data/cycle037_live.db` — must show no changes
6. Quick safety check — confirm no new secrets:
   `python automation/ai_cycle_controller.py secret-guard` — must PASS (or use equivalent)
7. Run brain-check one final time before writing cycle report

---

## Task 4 (SMALL, ~15 min): Coverage report + cycle report + commit

Deliverable: CYCLE_077_AGENT_F.md written; changes committed and pushed.

Sub-steps:
1. Create docs/cycle_reports/CYCLE_077_AGENT_F.md:
   - Modules improved (list with before/after %)
   - Full suite results: N passed, N xfail, coverage TOTAL %
   - Ruff PASS | Mypy PASS | brain-check PASS
   - Baseline DB unchanged: YES
   - Secret guard: PASS
   - End with: AGENT_COMPLETE
2. Find Jira story "Raise combined automation+src coverage to >=90%" — add comment:
   "Agent F Cycle 077: full regression PASS. Coverage TOTAL: N%. Modules improved: [list]"
3. `git add -A`
4. `git commit -m "test(c077): raise src/ coverage gaps, full regression suite PASS"`
5. `git push origin cycle/077/integration`

---

## Validation (R-092 Tier 1)

```bash
python -m pytest tests/unit/ --cov=automation --cov=src -q --timeout=60 | tail -3
python -m ruff check automation/ src/ tests/
python automation/ai_cycle_controller.py brain-check
```

---

## Hard gates

- Coverage TOTAL must be ≥90% after your changes
- No regressions: 0 unexpected test failures
- Do NOT modify data/cycle037_live.db
- Do NOT add tests that mock real behavior to inflate coverage numbers

---

END OF PROMPT
