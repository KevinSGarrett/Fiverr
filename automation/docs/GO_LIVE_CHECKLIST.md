# Go-Live Checklist — Fiverr Research System Autonomous Runner

Complete every item before enabling `dev_auto` 24/7 mode.

---

## Phase 1 — Manual Dry Run

Run these in sequence on the runner machine. All must pass before Phase 2.

```powershell
cd C:\Fiverr\Fiverr

# Brain check
.venv\Scripts\python.exe automation\ai_cycle_controller.py brain-check
# Expected: BRAIN CHECK PASS, all 33 files loaded, Cursor VERIFIED

# Policy compile
.venv\Scripts\python.exe automation\ai_cycle_controller.py compile-policy
# Expected: policy snapshot written, cycle/wave/E2E detected

# Plan cycle dry-run
.venv\Scripts\python.exe automation\ai_cycle_controller.py plan-cycle --dry-run
# Expected: manifest + 6 prompt stubs generated, no git changes

# Status check
.venv\Scripts\python.exe automation\ai_cycle_controller.py status
# Expected: GitHub runner Running, Cursor VERIFIED

# Health check
powershell -File C:\AI_Runner\scripts\health_check.ps1
# Expected: health_level = GREEN
```

---

## Phase 2 — Assisted Single Agent

Run one agent with `--safe-docs-only --dry-run` first.

```powershell
.venv\Scripts\python.exe automation\ai_cycle_controller.py run-agent `
  --agent D --cycle 38 --safe-docs-only --dry-run
# Expected: MODEL_GATE PASS, prompt located, dry-run complete
```

Then without dry-run (still --safe-docs-only):
```powershell
.venv\Scripts\python.exe automation\ai_cycle_controller.py run-agent `
  --agent D --cycle 38 --safe-docs-only
# Expected: Cursor executes, post-agent validation runs
```

---

## Phase 3 — Full Cycle No Auto-Merge

Run a full cycle without merge enabled. Confirm:

```text
[ ] 6 agents complete (A, B, E, C, F, D in order)
[ ] Each agent has a commit on the cycle branch
[ ] Local validation passes: ruff, mypy, pytest, coverage
[ ] PR created on GitHub
[ ] CI workflow triggers
[ ] Jira comments posted
[ ] PM_Pack run summary written
[ ] No secrets staged
[ ] Branch targets develop (not main)
```

---

## Phase 4 — Repair Loop Test

Force a test failure to confirm repair loop works:

```powershell
# Introduce a known ruff error and see if repair loop fixes it
# Then run a targeted repair:
.venv\Scripts\python.exe automation\ai_cycle_controller.py run-agent `
  --agent F --cycle 38 --safe-docs-only
```

Confirm:
```text
[ ] Failure classified correctly
[ ] Repair prompt generated
[ ] Repair agent dispatched
[ ] Validation passes after repair
[ ] Repair record written
```

---

## Phase 5 — Merge Gate Test

```powershell
.venv\Scripts\python.exe automation\ai_cycle_controller.py merge-gate --pr <N>
# Expected: gate checks run, dry-run summary printed
```

Confirm:
```text
[ ] PR target = develop (not main)
[ ] CI checks visible
[ ] Codecov statuses visible (or MISSING/non-blocking until token is set)
[ ] No secrets in staged files
[ ] Model evidence present
```

---

## Phase 6 — 24-Hour Observation

Enable `dev_auto` for 24 hours. Monitor:

```text
[ ] Controller completes at least 1 full cycle overnight
[ ] Watchdog fires and restarts controller if needed
[ ] Health check stays GREEN or YELLOW (never RED)
[ ] No force-push or main-push attempts
[ ] Jira updates appear with evidence comments
[ ] PRs open with correct template content
[ ] At least 1 merge to develop succeeds
[ ] Incident reports are written (not zero is OK — zero is also OK)
[ ] Daily snapshot runs at 02:00
```

---

## Phase 7 — 7-Day Trial

After 24h is clean, run for 7 days. Review weekly:

```text
[ ] Cycle count per day (target: 2-4)
[ ] Repair loop usage (< 40% of cycles should need repair)
[ ] CI pass rate (target: > 85%)
[ ] Jira transitions correct
[ ] No unresolved MODEL_GATE blocks
[ ] No main-branch risks
[ ] EC2 failover tested (optional during this window)
```

---

## Pre-Go-Live Blockers

These must be resolved before 24/7 mode:

```text
[ ] GitHub Secrets set: GITHUB_AUTOMATION_TOKEN, JIRA_BASE_URL, JIRA_EMAIL,
    JIRA_API_TOKEN, CODECOV_TOKEN
[ ] runner.env filled with same values
[ ] Branch protection on develop and main configured
[ ] Cursor model verified: Codex 5.3 / medium / Auto disabled
[ ] cursor_model_state.json fresh (age < 7 days)
[ ] PM_Pack HYDRATION_HEADER current
[ ] No uncommitted work on develop that would conflict
[ ] Scheduled tasks registered (Admin): run register_tasks.ps1 as Admin
[ ] Tailscale or other remote access confirmed working
```

---

## Autonomy Mode Reference

| Mode | What runs automatically | Merge? |
|---|---|---|
| `manual` | Plan + generate prompts only | No |
| `assisted` | Run agents + validate locally | No |
| `dev_auto` | Full cycle + PR + Jira + repair | Yes (develop only) |
| `release_guarded` | Same + prepare release PR | No (main) |
| `full_auto_experimental` | Everything | Yes (main if gates pass) |

**Recommended start:** `dev_auto`
