# =============================================================================
# watchdog.ps1 -- Improved host-plane watchdog (VERSION-CONTROLLED)
# -----------------------------------------------------------------------------
# Source of truth lives in the repo at: host/watchdog.ps1
# This file is DEPLOYED to C:\AI_Runner\scripts\ by host/deploy_host_scripts.ps1
# and is run on a 5-minute schedule by the task registered in host/register_driver.ps1.
#
# Improvements over the legacy watchdog:
#   * DEAD detection: heartbeat.json missing OR heartbeat age > 20 min.
#   * STUCK/SPINNING detection: same (state, cycle) for > N consecutive checks,
#     tracked via C:\AI_Runner\state\watchdog_progress.json.
#   * Relaunches the driver DIRECTLY (start_controller.ps1 / the driver task by
#     name) -- NOT the legacy logon-bound "run task" command path.
#   * Honors the pause sentinel: if C:\AI_Runner\state\autopilot_paused.json
#     exists, do NOT relaunch -- the operator paused intentionally.
#   * Preserves GitHub Actions runner-service restart behavior.
# =============================================================================

$ErrorActionPreference = "Continue"

$RunnerRoot     = "C:\AI_Runner"
$RepoRoot       = "C:\Fiverr\Fiverr"
$StateDir       = Join-Path $RunnerRoot "state"
$HeartbeatPath  = Join-Path $StateDir "heartbeat.json"
$PausePath      = Join-Path $StateDir "autopilot_paused.json"
$ProgressPath   = Join-Path $StateDir "watchdog_progress.json"
$IncidentDir    = Join-Path $RunnerRoot "reports\incidents"
$ScriptsDir     = Join-Path $RunnerRoot "scripts"
$StartController = Join-Path $ScriptsDir "start_controller.ps1"
$DriverTaskName = "FiverrAutopilotDriver"

$MaxHbMinutes   = 20      # heartbeat older than this => DEAD
$MaxStuckChecks = 4       # identical (state,cycle) for this many checks => STUCK
$now            = Get-Date

New-Item -ItemType Directory -Force $IncidentDir | Out-Null
New-Item -ItemType Directory -Force $StateDir    | Out-Null

function Write-Incident([string]$title, [string]$body) {
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $path  = Join-Path $IncidentDir "incident_${stamp}_${title}.md"
    @"
# AI Runner Incident: $title
Timestamp: $((Get-Date).ToUniversalTime().ToString("o"))
Machine  : $env:COMPUTERNAME

$body
"@ | Set-Content $path -Encoding UTF8
    Write-Host "[watchdog] INCIDENT: $title -> $path"
}

function Start-Driver([string]$reason) {
    # Relaunch the driver DIRECTLY -- prefer the registered durable task, then
    # fall back to running start_controller.ps1 directly. We deliberately do NOT
    # trigger a logon-bound task via the legacy run-task command (the old, broken
    # behavior); we use Start-ScheduledTask / Start-Process instead.
    Write-Host "[watchdog] Relaunching driver. Reason: $reason"

    $task = Get-ScheduledTask -TaskName $DriverTaskName -ErrorAction SilentlyContinue
    if ($task) {
        # The driver task is registered with -MultipleInstances IgnoreNew, so a
        # demand Start-ScheduledTask is IGNORED while a hung instance is still
        # Running. Stop the stale instance first (and kill any stale controller
        # process), then start a fresh one.
        Write-Host "[watchdog] Stopping any hung instance of '$DriverTaskName' before relaunch."
        Stop-ScheduledTask -TaskName $DriverTaskName -ErrorAction SilentlyContinue
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -like "*ai_cycle_controller.py*" } |
            ForEach-Object {
                Write-Host "[watchdog] Killing stale controller PID $($_.ProcessId)."
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
        Start-Sleep -Seconds 2
        Write-Host "[watchdog] Starting durable scheduled task '$DriverTaskName' directly."
        Start-ScheduledTask -TaskName $DriverTaskName -ErrorAction SilentlyContinue
        return
    }

    if (Test-Path $StartController) {
        Write-Host "[watchdog] Task not found -- launching start_controller.ps1 directly."
        Start-Process -FilePath "powershell.exe" `
            -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $StartController) `
            -WindowStyle Hidden
        return
    }

    Write-Warning "[watchdog] Could not relaunch: no '$DriverTaskName' task and no $StartController."
}

# ---------------------------------------------------------------------------
# 0. Honor the pause sentinel -- operator paused on purpose; do NOT relaunch.
# ---------------------------------------------------------------------------
if (Test-Path $PausePath) {
    Write-Host "[watchdog] Pause sentinel present at $PausePath -- operator paused autopilot. Not relaunching. Exiting."
    exit 0
}

# ---------------------------------------------------------------------------
# 1. DEAD detection -- heartbeat missing => (re)start the driver.
# ---------------------------------------------------------------------------
if (-not (Test-Path $HeartbeatPath)) {
    Write-Host "[watchdog] Heartbeat missing at $HeartbeatPath -- starting driver."
    Write-Incident "HeartbeatMissing" "heartbeat.json not found at $HeartbeatPath. Relaunching the durable driver."
    Start-Driver "heartbeat missing"
    exit 0
}

$hb     = Get-Content $HeartbeatPath -Raw | ConvertFrom-Json
$hbTime = [DateTime]::Parse($hb.last_seen)
$ageMin = ($now.ToUniversalTime() - $hbTime.ToUniversalTime()).TotalMinutes
$hbState = "$($hb.state)"
$hbCycle = "$($hb.cycle)"

Write-Host ("[watchdog] Heartbeat age: {0} min | state: {1} | cycle: {2}" -f [math]::Round($ageMin, 1), $hbState, $hbCycle)

# ---------------------------------------------------------------------------
# 2. STUCK/SPINNING detection -- persist last (state,cycle) + repeat count.
#    If (state,cycle) is identical across > N consecutive checks, the loop is
#    alive (writing heartbeats) but making no progress => treat as STUCK.
# ---------------------------------------------------------------------------
$repeatCount = 0
if (Test-Path $ProgressPath) {
    try {
        $prog = Get-Content $ProgressPath -Raw | ConvertFrom-Json
        if (("$($prog.state)" -eq $hbState) -and ("$($prog.cycle)" -eq $hbCycle)) {
            $repeatCount = [int]$prog.repeat_count + 1
        } else {
            $repeatCount = 0   # progress observed -- reset the stuck counter
        }
    } catch {
        $repeatCount = 0
    }
}

# Persist the updated progress snapshot for the next check.
@{
    state        = $hbState
    cycle        = $hbCycle
    repeat_count = $repeatCount
    updated      = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content $ProgressPath -Encoding UTF8

$isDead  = ($ageMin -gt $MaxHbMinutes)
$isStuck = ($repeatCount -gt $MaxStuckChecks)

if ($isDead -or $isStuck) {
    if ($isDead) {
        $diag = "DEAD: heartbeat age $([math]::Round($ageMin,1)) min exceeds threshold $MaxHbMinutes min."
    } else {
        $diag = "STUCK/SPINNING: state '$hbState' cycle '$hbCycle' unchanged across $repeatCount consecutive checks (threshold $MaxStuckChecks)."
    }
    Write-Host "[watchdog] $diag"

    $gitStatus = (git -C $RepoRoot status --short 2>&1 | Out-String).Trim()
    Write-Incident "DriverStuckOrDead" @"
$diag
Heartbeat age : $([math]::Round($ageMin,1)) minutes (threshold $MaxHbMinutes)
Last state    : $hbState
Last cycle    : $hbCycle
Repeat count  : $repeatCount (stuck threshold $MaxStuckChecks)
Git status    : $gitStatus
Action        : Relaunching the durable driver directly.
"@

    # Reset the stuck counter so we don't relaunch every single check after one relaunch.
    @{
        state        = $hbState
        cycle        = $hbCycle
        repeat_count = 0
        updated      = (Get-Date).ToUniversalTime().ToString("o")
    } | ConvertTo-Json | Set-Content $ProgressPath -Encoding UTF8

    Start-Driver $diag
} else {
    Write-Host "[watchdog] Driver healthy (alive and progressing)."
}

# ---------------------------------------------------------------------------
# 3. GitHub Actions runner service -- restart if stopped (preserve behavior).
# ---------------------------------------------------------------------------
$runnerSvc = Get-Service "actions.runner.*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($runnerSvc -and $runnerSvc.Status -ne "Running") {
    Write-Host "[watchdog] GitHub runner service is $($runnerSvc.Status) -- restarting."
    Start-Service $runnerSvc.Name -ErrorAction SilentlyContinue
    Write-Incident "GitHubRunnerDown" "GitHub runner service was $($runnerSvc.Status). Attempted restart."
} elseif (-not $runnerSvc) {
    Write-Incident "GitHubRunnerMissing" "GitHub runner service not found. Manual re-registration may be required."
}

Write-Host "[watchdog] Done."
exit 0
