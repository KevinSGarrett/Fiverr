# =============================================================================
# register_driver.ps1 -- Register ONE durable driver + ONE watchdog (OPERATOR step)
# -----------------------------------------------------------------------------
# Source of truth lives in the repo at: host/register_driver.ps1
# Registers exactly ONE canonical driver Scheduled Task and ONE watchdog task,
# configured to run NON-INTERACTIVELY (whether logged on or not), restart on
# failure, start at boot, and survive on battery. It also deletes duplicate /
# legacy tasks and configures power so the box never sleeps.
#
# *** GUARDED ***  By default this is a DRY-RUN: it only PRINTS what it would do.
# Pass -Execute (or -Confirm) to actually register tasks and change power config.
# It is therefore safe to read/inspect and even to run without arguments.
#
# Prerequisite: run host/deploy_host_scripts.ps1 -Execute FIRST so the scripts
# exist under C:\AI_Runner\scripts\.
# =============================================================================

[CmdletBinding()]
param(
    [switch]$Execute,   # actually perform registration + power config
    [switch]$Confirm    # alias for -Execute (operator ergonomics)
)

$DoIt = $Execute.IsPresent -or $Confirm.IsPresent

$RunnerRoot      = "C:\AI_Runner"
$ScriptsDir      = Join-Path $RunnerRoot "scripts"
$StartController  = Join-Path $ScriptsDir "start_controller.ps1"
$Watchdog        = Join-Path $ScriptsDir "watchdog.ps1"

$DriverTaskName   = "FiverrAutopilotDriver"
$WatchdogTaskName = "FiverrAutopilotWatchdog"

# Duplicate / legacy tasks to remove so exactly ONE driver + ONE watchdog remain.
$DuplicateTasks = @(
    "AI Runner Controller",   # legacy logon-bound single-shot driver
    "WatchdogRunner",         # duplicate watchdog
    "DailySnapshot",          # duplicate snapshot variants
    "WeeklyMaintenance"       # duplicate maintenance variants
)

function Write-Plan([string]$msg) { Write-Host "[register_driver][PLAN] $msg" }
function Write-Act ([string]$msg) { Write-Host "[register_driver][EXEC] $msg" }

Write-Host "============================================================"
Write-Host " register_driver.ps1  (mode: $(if ($DoIt) { 'EXECUTE' } else { 'DRY-RUN -- pass -Execute to apply' }))"
Write-Host "============================================================"

# ---------------------------------------------------------------------------
# 0. Sanity: deployed scripts must exist (operator runs deploy first).
# ---------------------------------------------------------------------------
if ($DoIt) {
    if (-not (Test-Path $StartController)) {
        Write-Error "[register_driver] FATAL: $StartController not found. Run host/deploy_host_scripts.ps1 -Execute first."
        exit 1
    }
    if (-not (Test-Path $Watchdog)) {
        Write-Error "[register_driver] FATAL: $Watchdog not found. Run host/deploy_host_scripts.ps1 -Execute first."
        exit 1
    }
}

# ---------------------------------------------------------------------------
# 1. Delete duplicate / legacy tasks (keep ONE driver + ONE watchdog canonical).
# ---------------------------------------------------------------------------
foreach ($dup in $DuplicateTasks) {
    if ($DoIt) {
        $existing = Get-ScheduledTask -TaskName $dup -ErrorAction SilentlyContinue
        if ($existing) {
            Write-Act "Deleting duplicate/legacy task: $dup"
            Unregister-ScheduledTask -TaskName $dup -Confirm:$false -ErrorAction SilentlyContinue
        }
    } else {
        Write-Plan "Would delete duplicate/legacy task if present: $dup"
    }
}

# ---------------------------------------------------------------------------
# 2. Register the ONE durable DRIVER task.
#    - Triggers: at startup (primary) + at logon (backup).
#    - Principal: S4U LogonType, RunLevel Highest, "run whether logged on or not"
#      (non-interactive).
#    - Settings: RestartCount 999, RestartInterval 1 min, ExecutionTimeLimit 0
#      (unlimited), StartWhenAvailable, do NOT stop/skip on batteries.
# ---------------------------------------------------------------------------
Write-Plan "Driver task '$DriverTaskName' -> run NON-INTERACTIVELY (whether logged on or not),"
Write-Plan "  LogonType S4U, RunLevel Highest, triggers AtStartup + AtLogon,"
Write-Plan "  RestartCount 999 / RestartInterval 1 min, ExecutionTimeLimit 0 (unlimited),"
Write-Plan "  StartWhenAvailable, DisallowStartIfOnBatteries=`$false, StopIfGoingOnBatteries=`$false,"
Write-Plan "  Action: powershell -NoProfile -ExecutionPolicy Bypass -File $StartController"

if ($DoIt) {
    Write-Act "Registering driver task '$DriverTaskName'"

    $driverAction = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartController`""

    $driverTriggerStartup = New-ScheduledTaskTrigger -AtStartup
    $driverTriggerLogon   = New-ScheduledTaskTrigger -AtLogOn   # backup trigger

    # Non-interactive: "run whether logged on or not" == S4U logon type.
    $driverPrincipal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest

    $driverSettings = New-ScheduledTaskSettingsSet `
        -RestartCount 999 `
        -RestartInterval (New-TimeSpan -Minutes 1) `
        -StartWhenAvailable `
        -DisallowStartIfOnBatteries:$false `
        -StopIfGoingOnBatteries:$false `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -MultipleInstances IgnoreNew

    Register-ScheduledTask `
        -TaskName $DriverTaskName `
        -Action $driverAction `
        -Trigger @($driverTriggerStartup, $driverTriggerLogon) `
        -Principal $driverPrincipal `
        -Settings $driverSettings `
        -Force | Out-Null

    Write-Act "Driver task '$DriverTaskName' registered."
}

# ---------------------------------------------------------------------------
# 3. Register the ONE WATCHDOG task -- runs every 5 minutes, non-interactive.
# ---------------------------------------------------------------------------
Write-Plan "Watchdog task '$WatchdogTaskName' -> every 5 minutes, NON-INTERACTIVE (whether logged on or not),"
Write-Plan "  LogonType S4U, RunLevel Highest, StartWhenAvailable, runs on battery,"
Write-Plan "  Action: powershell -NoProfile -ExecutionPolicy Bypass -File $Watchdog"

if ($DoIt) {
    Write-Act "Registering watchdog task '$WatchdogTaskName'"

    $wdAction = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Watchdog`""

    $wdTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 5) `
        -RepetitionDuration ([TimeSpan]::MaxValue)

    $wdPrincipal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType S4U `
        -RunLevel Highest

    $wdSettings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -DisallowStartIfOnBatteries:$false `
        -StopIfGoingOnBatteries:$false `
        -MultipleInstances IgnoreNew

    Register-ScheduledTask `
        -TaskName $WatchdogTaskName `
        -Action $wdAction `
        -Trigger $wdTrigger `
        -Principal $wdPrincipal `
        -Settings $wdSettings `
        -Force | Out-Null

    Write-Act "Watchdog task '$WatchdogTaskName' registered."
}

# ---------------------------------------------------------------------------
# 4. Power configuration -- never sleep/hibernate; High Performance; USB awake.
#    Wrapped in try/catch; failures are logged, not fatal.
# ---------------------------------------------------------------------------
Write-Plan "Power: standby-timeout-ac 0, hibernate-timeout-ac 0, High Performance plan, USB selective suspend OFF."

if ($DoIt) {
    try {
        Write-Act "powercfg /change standby-timeout-ac 0"
        powercfg /change standby-timeout-ac 0 | Out-Null
    } catch { Write-Warning "[register_driver] standby-timeout-ac failed: $_" }

    try {
        Write-Act "powercfg /change hibernate-timeout-ac 0"
        powercfg /change hibernate-timeout-ac 0 | Out-Null
    } catch { Write-Warning "[register_driver] hibernate-timeout-ac failed: $_" }

    try {
        # High Performance plan GUID is fixed across Windows installs.
        Write-Act "powercfg /setactive High Performance (8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c)"
        powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c | Out-Null
    } catch { Write-Warning "[register_driver] set High Performance plan failed: $_" }

    try {
        # USB selective suspend OFF (AC). 2a737441-1930-4402-8d77-b2bebba308a3 = USB settings subgroup,
        # 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 = selective suspend setting.
        Write-Act "powercfg /setacvalueindex SCHEME_CURRENT USB selective-suspend OFF"
        powercfg /setacvalueindex SCHEME_CURRENT 2a737441-1930-4402-8d77-b2bebba308a3 48e6b7a6-50f5-4782-a5d4-53bb8f07e226 0 | Out-Null
        powercfg /setactive SCHEME_CURRENT | Out-Null
    } catch { Write-Warning "[register_driver] USB selective suspend off failed: $_" }
}

# ---------------------------------------------------------------------------
# 5. Windows Update active-hours guidance (operator-side; best-effort note only).
#    Full deferral is an operator step -- documented in items/0.5/DOD_RW.md.
#    We do NOT force registry changes here; we only print guidance.
# ---------------------------------------------------------------------------
Write-Plan "Windows Update: set wide Active Hours (e.g. 00:00-23:00) and defer feature updates"
Write-Plan "  to avoid auto-reboots during a run. Full deferral is operator-side -- see items/0.5/DOD_RW.md."
# Best-effort guidance only (commented; not executed):
#   Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' ActiveHoursStart 0
#   Set-ItemProperty 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings' ActiveHoursEnd   23

if (-not $DoIt) {
    Write-Host ""
    Write-Host "[register_driver] DRY-RUN complete. Nothing was changed."
    Write-Host "[register_driver] Re-run with -Execute (or -Confirm) to register tasks and apply power config."
} else {
    Write-Host ""
    Write-Host "[register_driver] EXECUTE complete. Verify with: schtasks /query /TN $DriverTaskName /V /FO LIST"
}
