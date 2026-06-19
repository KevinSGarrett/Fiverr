# =============================================================================
# start_controller.ps1 -- Durable host-plane driver entrypoint (VERSION-CONTROLLED)
# -----------------------------------------------------------------------------
# Source of truth lives in the repo at: host/start_controller.ps1
# This file is DEPLOYED to C:\AI_Runner\scripts\ by host/deploy_host_scripts.ps1.
# Per "what runs == what's audited", edit it HERE in the repo, never edit the
# deployed copy in place. The registered Scheduled Task (host/register_driver.ps1)
# invokes the DEPLOYED copy.
#
# Responsibilities:
#   1. Fail-fast error handling.
#   2. Load secrets from C:\AI_Runner\secrets\runner.env into the process env.
#   3. Verify the repo remote is KevinSGarrett/Fiverr (fatal if not).
#   4. Branch-pin (minimal; full pin is item 5.4): fetch, ensure on `develop`,
#      pull --ff-only; REFUSE to run on `main` or a detached HEAD.
#   5. Activate the venv; force UTF-8 I/O.
#   6. Run the CONTINUOUS driver -- `start-autopilot` -- NOT single-shot `tick`.
#      Output is tee'd to a timestamped log under C:\AI_Runner\logs\controller\.
# =============================================================================

$ErrorActionPreference = "Stop"

$RepoRoot   = "C:\Fiverr\Fiverr"
$RunnerRoot = "C:\AI_Runner"
$EnvPath    = Join-Path $RunnerRoot "secrets\runner.env"
$LogDir     = Join-Path $RunnerRoot "logs\controller"

Set-Location $RepoRoot

# ---------------------------------------------------------------------------
# 1. Load secrets from runner.env (KEY=VALUE lines; skip comments/blank lines)
# ---------------------------------------------------------------------------
Write-Host "[start_controller] Loading runner.env secrets..."
if (Test-Path $EnvPath) {
    Get-Content $EnvPath | ForEach-Object {
        $line = $_
        if ($line -match '^\s*#') { return }   # skip comment lines
        if ($line -match '^\s*$') { return }   # skip blank lines
        $parts = $line -split '=', 2
        if ($parts.Count -eq 2) {
            $key = $parts[0].Trim()
            $val = $parts[1].Trim()
            if ($key) {
                [Environment]::SetEnvironmentVariable($key, $val, "Process")
            }
        }
    }
    Write-Host "[start_controller] Secrets loaded from $EnvPath"
} else {
    Write-Warning "[start_controller] runner.env not found at $EnvPath"
}

# ---------------------------------------------------------------------------
# 2. Verify repo remote == KevinSGarrett/Fiverr (fatal if not)
# ---------------------------------------------------------------------------
Write-Host "[start_controller] Verifying repo remote..."
$remote = (git -C $RepoRoot remote get-url origin 2>&1)
if ($remote -notlike "*KevinSGarrett/Fiverr*") {
    Write-Error "[start_controller] FATAL: repo remote is '$remote' -- expected KevinSGarrett/Fiverr"
    exit 1
}
Write-Host "[start_controller] Repo remote verified: $remote"

# ---------------------------------------------------------------------------
# 3. Branch-pin (minimal version; full branch-pin is item 5.4)
#    fetch -> ensure on `develop` -> pull --ff-only.
#    REFUSE to run on `main` or a detached HEAD.
# ---------------------------------------------------------------------------
Write-Host "[start_controller] Branch-pin: fetching origin..."
git -C $RepoRoot fetch origin --quiet

$branch = (git -C $RepoRoot rev-parse --abbrev-ref HEAD 2>&1).Trim()
Write-Host "[start_controller] Current branch: $branch"

if ($branch -eq "HEAD") {
    Write-Error "[start_controller] FATAL: detached HEAD -- refusing to run the continuous driver. Checkout 'develop' first."
    exit 1
}
if ($branch -eq "main") {
    Write-Error "[start_controller] FATAL: on 'main' -- refusing to run the continuous driver. The driver must run on 'develop'."
    exit 1
}
if ($branch -ne "develop") {
    Write-Host "[start_controller] Not on 'develop' (on '$branch') -- checking out develop..."
    git -C $RepoRoot checkout develop
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[start_controller] FATAL: could not checkout 'develop'."
        exit 1
    }
}

Write-Host "[start_controller] Fast-forward pull on develop..."
git -C $RepoRoot pull --ff-only
if ($LASTEXITCODE -ne 0) {
    Write-Error "[start_controller] FATAL: 'git pull --ff-only' failed -- branch is not a clean fast-forward. Resolve manually."
    exit 1
}

# ---------------------------------------------------------------------------
# 4. Activate venv; force UTF-8 so Unicode in tick output never crashes the console
# ---------------------------------------------------------------------------
Write-Host "[start_controller] Activating venv..."
& (Join-Path $RepoRoot ".venv\Scripts\Activate.ps1")

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8       = "1"

# ---------------------------------------------------------------------------
# 5. Run the CONTINUOUS driver -- start-autopilot (NOT single-shot `tick`).
#    Tee to a timestamped log under C:\AI_Runner\logs\controller\.
# ---------------------------------------------------------------------------
New-Item -ItemType Directory -Force $LogDir | Out-Null
$logFile = Join-Path $LogDir ("controller_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

Write-Host "[start_controller] Log: $logFile"
Write-Host ("[start_controller] Started: {0}" -f (Get-Date -Format "o"))
Write-Host "[start_controller] Launching CONTINUOUS driver: ai_cycle_controller.py start-autopilot"

# Continuous loop -- runs until stopped. This is the durable driver, not a tick.
python automation\ai_cycle_controller.py start-autopilot 2>&1 | Tee-Object -FilePath $logFile
