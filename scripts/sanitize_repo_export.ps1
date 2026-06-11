# sanitize_repo_export.ps1 — Safe repo export for Claude/Cursor/sharing
# NEVER upload the raw C:\Fiverr\Fiverr directory. ALWAYS use this script.
#
# Usage: .\scripts\sanitize_repo_export.ps1 [-OutputZip export.zip]
param(
    [string]$OutputZip = "C:\Temp\fiverr_repo_export_SAFE.zip"
)

$ErrorActionPreference = "Stop"
$repoRoot = "C:\Fiverr\Fiverr"
$tempDir  = "C:\Temp\fiverr_export_$(Get-Date -Format yyyyMMddHHmmss)"

Write-Host "=== Repo Export Sanitizer ===" -ForegroundColor Cyan
Write-Host "Source: $repoRoot"
Write-Host "Output: $OutputZip"
Write-Host ""

# ── Directories to EXCLUDE from export ──────────────────────────────
$excludeDirs = @(
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    ".coverage",
    "data",          # SQLite DBs (large, sensitive)
    "logs",
    "C:\Fiverr\Fiverr\PM_Pack\automation\runs",
    "C:\Fiverr\Fiverr\PM_Pack\automation\post_cycle_reviews",
    "C:\Fiverr\Fiverr\playwright-report",
    "C:\Fiverr\Fiverr\test-results",
    "htmlcov"
)

# ── Files to EXCLUDE from export ────────────────────────────────────
$excludeFiles = @(
    ".env",
    "*.env",
    "runner.env",
    "*.db",
    "*.sqlite",
    "*.lock",       # git lock files
    "*.coverage",
    "storage_state.json",
    ".credentials",
    ".credentials_rsaparams",
    ".runner",
    "*.key",
    "*.pem",
    "*.p12",
    # Ignored PM_Pack scratch scripts with token literals
    "PM_Pack/final_batch.py",
    "PM_Pack/jira_*.py",
    "setup_runner.ps1",
    "fix_secrets.ps1",
    "go_live_phase*.ps1",
    "set_secrets.ps1",
    "setup_all.ps1",
    "set_branch_protection.ps1"
)

New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
Write-Host "Copying sanitized repo to temp dir..." -ForegroundColor Yellow

# Copy repo excluding sensitive content
$robocopyArgs = @(
    $repoRoot, $tempDir,
    "/E",          # include subdirectories
    "/NFL",        # no file list
    "/NDL",        # no directory list
    "/NJH",        # no job header
    "/NJS"         # no job summary
)

# Build exclusion args
foreach ($d in $excludeDirs) {
    $robocopyArgs += "/XD"
    $robocopyArgs += $d
}
foreach ($f in $excludeFiles) {
    $robocopyArgs += "/XF"
    $robocopyArgs += $f
}

& robocopy @robocopyArgs | Out-Null

# Double-check: scan for any remaining sensitive patterns
Write-Host "Scanning export for sensitive patterns..." -ForegroundColor Yellow
$patterns = @("ANTHROPIC_API_KEY", "GH_AUTOMATION_TOKEN", "JIRA_API_TOKEN",
               "ghp_", "ATATT3x", "runner.env", "\.credentials")
$found = @()
Get-ChildItem -Path $tempDir -Recurse -File | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($pat in $patterns) {
        if ($content -match $pat) {
            $found += "$($_.FullName): matches pattern '$pat'"
        }
    }
}
if ($found.Count -gt 0) {
    Write-Error "SENSITIVE CONTENT FOUND — aborting export:`n$($found -join "`n")"
    Remove-Item $tempDir -Recurse -Force
    exit 1
}

# Create ZIP
if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
Compress-Archive -Path "$tempDir\*" -DestinationPath $OutputZip -CompressionLevel Optimal
Remove-Item $tempDir -Recurse -Force

$size = (Get-Item $OutputZip).Length / 1MB
Write-Host ""
Write-Host "=== SAFE EXPORT COMPLETE ===" -ForegroundColor Green
Write-Host "  Output : $OutputZip"
Write-Host "  Size   : $([math]::Round($size, 1)) MB"
Write-Host "  Status : No sensitive patterns found"
Write-Host ""
Write-Host "This ZIP is safe to share with Claude/Cursor/developers." -ForegroundColor Green
