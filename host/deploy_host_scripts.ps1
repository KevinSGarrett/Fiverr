# =============================================================================
# deploy_host_scripts.ps1 -- Copy version-controlled host/*.ps1 to the host (OPERATOR step)
# -----------------------------------------------------------------------------
# Source of truth lives in the repo at: host/deploy_host_scripts.ps1
# Copies the version-controlled host scripts (host/*.ps1) into the live host
# scripts directory C:\AI_Runner\scripts\ so that "what runs == what's audited".
# Existing files are backed up (timestamped) before being overwritten, so the
# operation is idempotent and reversible.
#
# *** GUARDED ***  By default this is a DRY-RUN: it only PRINTS what it would do.
# Pass -Execute to actually back up + copy.
# =============================================================================

[CmdletBinding()]
param(
    [switch]$Execute   # actually back up + copy; default = dry-run (print only)
)

$DoIt = $Execute.IsPresent

# Repo host/ dir = directory this script lives in.
$HostDir    = $PSScriptRoot
$DestDir    = "C:\AI_Runner\scripts"
$BackupDir  = Join-Path $DestDir ("_backup_{0}" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

# The canonical set of scripts this deploy manages.
$Scripts = @("start_controller.ps1", "watchdog.ps1", "register_driver.ps1", "deploy_host_scripts.ps1")

Write-Host "============================================================"
Write-Host " deploy_host_scripts.ps1  (mode: $(if ($DoIt) { 'EXECUTE' } else { 'DRY-RUN -- pass -Execute to copy' }))"
Write-Host " Source : $HostDir"
Write-Host " Dest   : $DestDir"
Write-Host "============================================================"

if ($DoIt) {
    New-Item -ItemType Directory -Force $DestDir | Out-Null
}

foreach ($name in $Scripts) {
    $src = Join-Path $HostDir $name
    $dst = Join-Path $DestDir $name

    if (-not (Test-Path $src)) {
        Write-Warning "[deploy] Source missing, skipping: $src"
        continue
    }

    if (Test-Path $dst) {
        if ($DoIt) {
            New-Item -ItemType Directory -Force $BackupDir | Out-Null
            $bak = Join-Path $BackupDir $name
            Write-Host "[deploy][EXEC] Backing up existing $name -> $bak"
            Copy-Item $dst $bak -Force
        } else {
            Write-Host "[deploy][PLAN] Would back up existing $name -> $BackupDir\$name"
        }
    }

    if ($DoIt) {
        Write-Host "[deploy][EXEC] Copying $name -> $dst"
        Copy-Item $src $dst -Force
    } else {
        Write-Host "[deploy][PLAN] Would copy $src -> $dst"
    }
}

if (-not $DoIt) {
    Write-Host ""
    Write-Host "[deploy] DRY-RUN complete. Nothing was copied. Re-run with -Execute to deploy."
} else {
    Write-Host ""
    Write-Host "[deploy] EXECUTE complete. Backups (if any) under: $BackupDir"
}
