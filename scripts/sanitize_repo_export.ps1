param(
    [string]$OutputZip = "",
    [switch]$SelfTest
)

$ErrorActionPreference = "Stop"
$repoRoot = "C:\Fiverr\Fiverr"
if ($OutputZip -eq "") { $OutputZip = "C:\Temp\fiverr_repo_export_SAFE.zip" }
$tempDir = "C:\Temp\fiverr_export_work"

$excludeDirs = @(
    ".git", ".venv", ".mypy_cache", ".pytest_cache", "__pycache__",
    "node_modules", "htmlcov", "playwright-report", "test-results", "data", "logs",
    "PM_Pack\automation\runs", "PM_Pack\automation\post_cycle_reviews",
    "PM_Pack\automation\prompts\drafts"
)
$excludeFiles = @(
    ".env", "*.env", "runner.env", "*.db", "*.sqlite", "*.lock",
    "storage_state.json", ".credentials", ".credentials_rsaparams", ".runner",
    "*.key", "*.pem", "*.p12", "Fiverr.zip", "Fiverr*.zip",
    "setup_runner.ps1", "setup_all.ps1", "set_secrets.ps1",
    "fix_secrets.ps1", "set_branch_protection.ps1"
)

# Patterns that match SECRET VALUES (assignments), not policy text mentioning key names
$secretValuePatterns = @(
    'GH_AUTOMATION_TOKEN\s*=\s*\S+',
    'JIRA_API_TOKEN\s*=\s*\S+',
    'CODECOV_TOKEN\s*=\s*\S+',
    'ANTHROPIC_API_KEY\s*=\s*sk-',
    'ghp_[A-Za-z0-9]{20,}',
    'ATATT3x[A-Za-z0-9]{10,}',
    'sk-ant-[A-Za-z0-9]{10,}'
)

function Test-FileHasSecretValue {
    param([string]$FilePath)
    try {
        $ext = [System.IO.Path]::GetExtension($FilePath).ToLower()
        $skip = @('.exe','.dll','.pyc','.db','.sqlite','.zip','.png','.jpg','.ico','.bin','.whl')
        if ($ext -in $skip) { return $false }
        $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
        if (-not $content) { return $false }
        foreach ($pat in $secretValuePatterns) {
            if ($content -match $pat) { return $true }
        }
    } catch {}
    return $false
}

if ($SelfTest) {
    Write-Host "=== SANITIZER SELF-TEST ===" -ForegroundColor Cyan
    $pass = $true

    $t1 = New-TemporaryFile
    Set-Content $t1.FullName "# Do not use GH_AUTOMATION_TOKEN in this file"
    if (Test-FileHasSecretValue $t1.FullName) {
        Write-Host "FAIL: False positive on policy mention" -ForegroundColor Red; $pass = $false
    } else {
        Write-Host "PASS: Policy mention ignored (no assignment value)" -ForegroundColor Green
    }

    $t2 = New-TemporaryFile
    Set-Content $t2.FullName "GH_AUTOMATION_TOKEN=ghp_realtoken123456789abcdef"
    if (Test-FileHasSecretValue $t2.FullName) {
        Write-Host "PASS: Token assignment detected" -ForegroundColor Green
    } else {
        Write-Host "FAIL: Token assignment not detected" -ForegroundColor Red; $pass = $false
    }

    $t3 = New-TemporaryFile
    Set-Content $t3.FullName "x = ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ01234"
    if (Test-FileHasSecretValue $t3.FullName) {
        Write-Host "PASS: Token literal detected" -ForegroundColor Green
    } else {
        Write-Host "FAIL: Token literal not detected" -ForegroundColor Red; $pass = $false
    }

    $t4 = New-TemporaryFile
    Set-Content $t4.FullName "model: Codex 5.3`neffort: medium"
    if (Test-FileHasSecretValue $t4.FullName) {
        Write-Host "FAIL: False positive on config file" -ForegroundColor Red; $pass = $false
    } else {
        Write-Host "PASS: Config file clean" -ForegroundColor Green
    }

    # Test 5: ANTHROPIC_API_KEY mention only (policy doc) should NOT trigger
    $t5 = New-TemporaryFile
    Set-Content $t5.FullName "# Never set ANTHROPIC_API_KEY on this runner"
    if (Test-FileHasSecretValue $t5.FullName) {
        Write-Host "FAIL: False positive on ANTHROPIC_API_KEY mention" -ForegroundColor Red; $pass = $false
    } else {
        Write-Host "PASS: ANTHROPIC_API_KEY mention without value ignored" -ForegroundColor Green
    }

    Remove-Item $t1.FullName, $t2.FullName, $t3.FullName, $t4.FullName, $t5.FullName -Force -ErrorAction SilentlyContinue

    if ($pass) { Write-Host "`nSelf-test: PASS" -ForegroundColor Green; exit 0 }
    else { Write-Host "`nSelf-test: FAIL" -ForegroundColor Red; exit 1 }
}

# Export mode
Write-Host "Source: $repoRoot"
Write-Host "Output: $OutputZip"

if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

$rcArgs = @($repoRoot, $tempDir, "/E", "/NFL", "/NDL", "/NJH", "/NJS")
foreach ($d in $excludeDirs) { $rcArgs += "/XD"; $rcArgs += (Join-Path $repoRoot $d) }
foreach ($f in $excludeFiles) { $rcArgs += "/XF"; $rcArgs += $f }
& robocopy @rcArgs | Out-Null

$found = @()
Get-ChildItem -Path $tempDir -Recurse -File | ForEach-Object {
    if (Test-FileHasSecretValue $_.FullName) {
        $found += $_.FullName.Replace($tempDir, "[EXPORT]")
    }
}
if ($found.Count -gt 0) {
    Remove-Item $tempDir -Recurse -Force
    Write-Error ("SECRET VALUES found in export - aborting: " + ($found -join ", "))
    exit 1
}

if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
Compress-Archive -Path "$tempDir\*" -DestinationPath $OutputZip -CompressionLevel Optimal
Remove-Item $tempDir -Recurse -Force
$size = [math]::Round((Get-Item $OutputZip).Length / 1MB, 1)
Write-Host "=== SAFE EXPORT COMPLETE ==="
Write-Host ("Output: " + $OutputZip + " (" + $size + " MB) - No secrets detected")
