<#
.SYNOPSIS
  Install the Fiverr autonomous runner as a Windows Scheduled Task (24/7, hands-free).

.DESCRIPTION
  Registers a task that launches automation/autopilot_supervisor.py at system startup.
  The supervisor keeps start-autopilot alive (restart-on-death, storm-protected,
  freeze-aware); the autopilot runs the build cycles. Together they give true unattended
  operation: the only human action is running THIS installer once.

  Layers of resilience:
    * Task-level   : RestartCount on failure + StartWhenAvailable + ExecutionTimeLimit 0
                     (unlimited) + "do not start a new instance if already running".
    * Supervisor   : restarts the autopilot process when it exits/dies (PR: supervisor).
    * Autopilot    : in-loop circuit breaker, bounded recoveries, tick hard-timeout,
                     orphan reaping, gh keyring auth, UTF-8 (PRs #150-154).

.PARAMETER RepoPath          Repo root (default C:\Fiverr\Fiverr).
.PARAMETER PythonExe         Python to use (default: 'python' on PATH).
.PARAMETER Interval          Autopilot tick interval seconds (default 60).
.PARAMETER RunWhetherLoggedOn  Run even when no user is logged on (needs the account
                               password; otherwise the task runs only while logged on —
                               fine for an always-logged-in dedicated runner box).
.PARAMETER StartNow          Start the task immediately after registering.

.EXAMPLE
  # Always-logged-in runner box (simplest, no password):
  powershell -ExecutionPolicy Bypass -File automation\setup_autopilot_task.ps1 -StartNow

.EXAMPLE
  # True headless (runs at boot, logged off) — will prompt for the account password:
  powershell -ExecutionPolicy Bypass -File automation\setup_autopilot_task.ps1 -RunWhetherLoggedOn -StartNow
#>
[CmdletBinding()]
param(
  [string]$RepoPath = "C:\Fiverr\Fiverr",
  [string]$PythonExe = "python",
  [int]$Interval = 60,
  [switch]$RunWhetherLoggedOn,
  [switch]$StartNow
)

$ErrorActionPreference = "Stop"
$TaskName = "FiverrAutopilot"

if (-not (Test-Path $RepoPath)) { throw "RepoPath not found: $RepoPath" }
$supervisor = Join-Path $RepoPath "automation\autopilot_supervisor.py"
if (-not (Test-Path $supervisor)) { throw "supervisor not found: $supervisor" }

# Action: run the supervisor (which keeps the autopilot alive). PYTHONIOENCODING via env
# of the action is set by the supervisor itself; here we just launch it.
$argLine = "automation\autopilot_supervisor.py --interval $Interval"
$action = New-ScheduledTaskAction -Execute $PythonExe -Argument $argLine -WorkingDirectory $RepoPath

# Trigger: at system startup (survives reboot). StartWhenAvailable catches a missed start.
$trigger = New-ScheduledTaskTrigger -AtStartup

# Settings: never time out (runs forever); restart the TASK if the supervisor process dies
# unexpectedly (defence-in-depth atop the supervisor's own restart loop); singleton.
$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -ExecutionTimeLimit ([TimeSpan]::Zero) `
  -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) `
  -MultipleInstances IgnoreNew

if ($RunWhetherLoggedOn) {
  # S4U / password principal — Register-ScheduledTask will prompt for the password.
  $cred = Get-Credential -Message "Account to run the autopilot (run whether logged on or not)"
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -User $cred.UserName -Password $cred.GetNetworkCredential().Password -RunLevel Highest -Force | Out-Null
  Write-Host "Registered '$TaskName' to run whether logged on or not." -ForegroundColor Green
} else {
  $principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive -RunLevel Highest
  Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Principal $principal -Force | Out-Null
  Write-Host "Registered '$TaskName' (runs while you are logged on)." -ForegroundColor Green
}

Write-Host ""
Write-Host "Manage it:" -ForegroundColor Cyan
Write-Host "  Start : Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Stop  : python automation\autopilot_supervisor.py --stop   (graceful)  OR  Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Status: Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
Write-Host "  Remove: Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
Write-Host ""
Write-Host "IMPORTANT: do NOT run an interactive Claude Code session on this box while the" -ForegroundColor Yellow
Write-Host "runner is active — both share the Claude subscription and an interactive session" -ForegroundColor Yellow
Write-Host "starves the runner's PM prompt-generation. Use a dedicated runner machine." -ForegroundColor Yellow

if ($StartNow) {
  Start-ScheduledTask -TaskName $TaskName
  Write-Host "`nStarted '$TaskName' now." -ForegroundColor Green
}
