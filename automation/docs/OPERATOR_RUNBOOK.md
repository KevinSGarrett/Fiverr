# Operator Runbook — Fiverr Research System Autonomous Runner

**Repo:** `KevinSGarrett/Fiverr` | **Runner:** `FIVERR-AI-RUNNER` | **Updated:** 2026-06-11

---

## Quick Reference

| What | Where |
|---|---|
| Repo | `C:\Fiverr\Fiverr` |
| Runner scripts | `C:\AI_Runner\scripts\` |
| Secrets | `C:\AI_Runner\secrets\runner.env` |
| State / heartbeat | `C:\AI_Runner\state\` |
| Logs | `C:\AI_Runner\logs\` |
| Incidents | `C:\AI_Runner\reports\incidents\` |
| Snapshots | `C:\AI_Runner\backups\state_snapshots\` |
| Policy snapshot | `PM_Pack/automation/current_policy_snapshot.json` |

---

## Daily Health Check

```powershell
powershell -File C:\AI_Runner\scripts\health_check.ps1
# Expected: health_level = GREEN
```

---

## Controller Commands

```powershell
cd C:\Fiverr\Fiverr
.venv\Scripts\python.exe automation\ai_cycle_controller.py brain-check
.venv\Scripts\python.exe automation\ai_cycle_controller.py compile-policy
.venv\Scripts\python.exe automation\ai_cycle_controller.py status
.venv\Scripts\python.exe automation\ai_cycle_controller.py plan-cycle --dry-run
.venv\Scripts\python.exe automation\ai_cycle_controller.py jira-inventory --dry-run
.venv\Scripts\python.exe automation\ai_cycle_controller.py run-agent --agent A --cycle 38 --dry-run
.venv\Scripts\python.exe automation\ai_cycle_controller.py validate-prompts --cycle 38
.venv\Scripts\python.exe automation\ai_cycle_controller.py merge-gate --pr 85
.venv\Scripts\python.exe automation\ai_cycle_controller.py recover
```

---

## GitHub Runner Service

```powershell
Get-Service "actions.runner.*"          # check
Stop-Service "actions.runner.*"         # stop
Start-Service "actions.runner.*"        # start
```

---

## Scheduled Tasks (Admin required once)

```powershell
# Register all 4 tasks
powershell -File C:\AI_Runner\scripts\register_tasks.ps1

# Task status
schtasks /Query /FO LIST | Select-String "AI Runner" -Context 0,4
```

Four tasks: AI Runner Controller, AI Runner Watchdog (5 min), AI Runner Health Report (30 min), AI Runner Daily Snapshot (02:00).

---

## Recovery from Stale State

```powershell
cd C:\Fiverr\Fiverr
.venv\Scripts\python.exe automation\ai_cycle_controller.py recover
.venv\Scripts\python.exe automation\ai_cycle_controller.py brain-check
.venv\Scripts\python.exe automation\ai_cycle_controller.py compile-policy
powershell -File C:\AI_Runner\scripts\snapshot_state.ps1
```

---

## Cursor Model Re-verification

```powershell
# Open Cursor Desktop, confirm Codex 5.3 / medium / Auto off
# Then update state:
powershell -File C:\AI_Runner\scripts\verify_model_selection.ps1
# Or re-run brain-check to confirm VERIFIED
```

---

## Incident Quick Reference

| Condition | Action |
|---|---|
| health_level = ORANGE | Check heartbeat; watchdog auto-restarts in ≤5 min |
| health_level = RED | Check repo / runner / PM_Pack; run `recover` |
| health_level = BLACK | Tailscale → RDP; see EC2_FAILOVER.md |
| MODEL_GATE blocked | Re-verify Cursor model; update cursor_model_state.json |
| CI failing | `gh pr checks <N>`; repair prompt; push fix |
| Jira 401 | Replace JIRA_API_TOKEN in runner.env |
| GitHub auth expired | `gh auth login` on runner |

---

## Secrets

Store only in `C:\AI_Runner\secrets\runner.env` and GitHub Actions secrets. Never commit.

```text
GITHUB_AUTOMATION_TOKEN=...
JIRA_BASE_URL=https://yourdomain.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=...
CODECOV_TOKEN=...
```
