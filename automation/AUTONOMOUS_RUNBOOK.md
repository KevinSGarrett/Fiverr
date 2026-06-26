# Autonomous Runner — 24/7 Operation Runbook

How to run the Fiverr build runner fully autonomously, hands-free, around the clock.

## Architecture (three resilience layers)

```
Windows Scheduled Task  ──launches at boot, restarts if it dies──►  Supervisor
        │                                                               │
        │ (survives logoff/reboot; ExecutionTimeLimit 0)                │ restart-on-death,
        ▼                                                               ▼ storm-protected,
  autopilot_supervisor.py  ──restarts when the process exits──►  start-autopilot (the loop)
                                                                        │
                                                                        ▼ per-tick resilience:
                                                  circuit breaker · bounded recoveries ·
                                                  tick hard-timeout · orphan reaping ·
                                                  gh keyring auth · UTF-8 io
```

- **Autopilot** (`ai_cycle_controller.py start-autopilot`) runs the cycle state machine: plan → dispatch 6 Cursor agents → review → PR → CI → Codex resolve → merge → advance. It has an in-loop circuit breaker, bounded recoveries, a state-aware tick hard-timeout, claude process-tree reaping, gh keyring auth, and forced UTF-8 (PRs #150–#154).
- **Supervisor** (`autopilot_supervisor.py`) owns *process* liveness: when the autopilot process exits or dies for any reason, it restarts it — singleton-guarded, storm-protected (exponential backoff on rapid failures, capped), and freeze-aware (auto-recovers from a circuit-breaker freeze after a cooldown; respects a deliberate human kill-switch freeze).
- **Scheduled Task** owns *boot/OS* persistence: launches the supervisor at startup, survives logoff and reboot, restarts the supervisor itself if it ever dies.

## One-time setup (the only human action)

```powershell
# Dedicated runner box that stays logged in (simplest — no password):
powershell -ExecutionPolicy Bypass -File automation\setup_autopilot_task.ps1 -StartNow

# OR truly headless (runs at boot even when logged off — prompts for the account password):
powershell -ExecutionPolicy Bypass -File automation\setup_autopilot_task.ps1 -RunWhetherLoggedOn -StartNow
```

After this, the runner builds the Fiverr project cycle-to-cycle with **zero** ongoing intervention.

## CRITICAL operating constraint — dedicate the box

The runner's PM prompt-generation calls the **Claude subscription** via the `claude` CLI.
An interactive Claude Code session on the *same machine* shares that subscription and
**starves** the runner (its `plan-cycle` stalls). Run the autopilot on a **dedicated box**
with no concurrent interactive Claude Code session. Unattended, the runner has the
subscription to itself and prompt-gen completes (~16–28 min/agent, historically observed).

## Preconditions (verify once)

- `python automation/ai_cycle_controller.py brain-check` → Cursor VERIFIED (Codex 5.3), Claude subscription reachable.
- Model gate fresh (`model_gate` VERIFIED; auto-refreshes after each successful run — PR #149).
- `gh auth status` → logged in (keyring); the runner uses it via the keyring fallback (PR #153).
- Cursor CLI present (`agent.cmd`).

## Manage it

| Action | Command |
|--------|---------|
| Start  | `Start-ScheduledTask -TaskName FiverrAutopilot` |
| Graceful stop | `python automation\autopilot_supervisor.py --stop` (supervisor reaps the autopilot tree and exits) |
| Hard stop | `Stop-ScheduledTask -TaskName FiverrAutopilot` |
| Status | `Get-ScheduledTask -TaskName FiverrAutopilot \| Get-ScheduledTaskInfo` |
| Kill-switch (stay down) | set `frozen: true` in `PM_Pack/automation/policies/autonomy_freeze.yml` — the supervisor RESPECTS a manual freeze (only auto-clears its own circuit-breaker freezes) |
| Remove | `Unregister-ScheduledTask -TaskName FiverrAutopilot -Confirm:$false` |

## Tunables (env vars)

| Var | Default | Meaning |
|-----|---------|---------|
| `AUTOPILOT_INTERVAL` | 60 | seconds between ticks |
| `SUPERVISOR_BASE_BACKOFF` | 30 | seconds between autopilot restarts |
| `SUPERVISOR_BREAKER_COOLDOWN` | 1800 | cooldown before auto-clearing a circuit-breaker freeze |
| `AUTOPILOT_TICK_TIMEOUT_SEC` | 3600 | hard-timeout for non-dispatch ticks |
| `AUTOPILOT_DISPATCH_TICK_TIMEOUT_SEC` | 12600 | hard-timeout for a Cursor-dispatch tick (~210 min) |
| `AUTOPILOT_MAX_CONSECUTIVE_TICK_FAILURES` | 10 | circuit-breaker trip threshold |
| `POST_CYCLE_PYTEST_TIMEOUT` | 1800 | post-cycle review local-suite timeout |

## Health check (any time, subscription-free)

```powershell
python -c "import json; from automation import runner_paths; print(json.loads((runner_paths.state_dir()/'controller_state.json').read_text()))"
Get-Content C:\Fiverr\Fiverr\autopilot_detached.log -Tail 40   # if launched via the task's redirect
```
