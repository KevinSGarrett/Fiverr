# Cursor Stuck Recovery

## 1) Detection

Treat Cursor as stuck when one or more of these conditions are true for a sustained period:

- No agent output for more than 45 minutes.
- `C:\AI_Runner\state\heartbeat.json` timestamp stops advancing.
- `Runner.Listener` process is present but has near-zero CPU for an extended interval.
- stdout/stderr logs stop moving while expected work should still be active.

Use this quick check sequence:

```powershell
Get-Content C:\AI_Runner\state\heartbeat.json -Raw
Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue
Get-ChildItem C:\AI_Runner\logs | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## 2) Safe Kill Procedure

Never use broad process kills such as `taskkill /F /IM node.exe`. That can kill unrelated jobs.

Use targeted process handling:

```powershell
Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "Cursor*" -ErrorAction SilentlyContinue
```

If dependent child processes remain, inspect parent-child links before stopping them. Prefer explicit process names over wildcard mass termination.

## 3) State Capture Before Kill

Capture forensic state before any stop action:

```powershell
Set-Location C:\Fiverr\Fiverr
git status --short
git diff --stat HEAD
Copy-Item C:\AI_Runner\state\heartbeat.json C:\AI_Runner\reports\incidents\heartbeat_capture.json -Force
```

Then copy relevant logs into a timestamped incident folder:

```powershell
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$dst = "C:\AI_Runner\reports\incidents\CURSOR_STUCK_$stamp"
New-Item -ItemType Directory -Path $dst -Force | Out-Null
Copy-Item C:\AI_Runner\logs\* $dst -Recurse -Force
```

## 4) Post-Kill Validation

After process stop, validate repository and tooling health:

```powershell
Set-Location C:\Fiverr\Fiverr
git status --short
.venv\Scripts\python.exe -m ruff check automation/ .github/ --output-format=full
.venv\Scripts\python.exe -m pytest -q
```

If tree is dirty, document exactly which files changed and classify them before restart.

## 5) Resume vs Restart Decision

- If estimated lost work is less than 30 minutes, resume with a repair prompt using preserved context.
- If estimated lost work is more than one hour, restart with the original full prompt and explicit state references.
- If state capture is incomplete, prefer restart to avoid compounding unknown state.

## 6) Incident Report

Create `C:\AI_Runner\reports\incidents\CURSOR_STUCK_YYYYMMDD.md` including:

- time detected
- impacted agent
- estimated stuck duration
- kill decision rationale
- recovery action taken
- post-recovery validation results

Minimum template:

```markdown
# CURSOR STUCK INCIDENT
Detected: <timestamp>
Agent: <id>
Duration: <minutes>
Decision: <resume|restart>
Actions: <steps>
Validation: <ruff/pytest/git status>
```

## 7) Prevention

Set and enforce no-output timeout in `cursor_adapter.yaml` to 45 minutes by default. Keep heartbeat monitoring active and alert on stale timestamp drift. Add a daily verification that the timeout policy and heartbeat watcher are loaded. Include a weekly review check confirming incident counts, mean recovery time, and whether preventive controls reduced recurrence. Recovery is considered complete only when the runner is healthy, the repo is understood, and an incident record exists.

