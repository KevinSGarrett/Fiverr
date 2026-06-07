param(
    [string]$RepoRoot = "C:\Fiverr\Fiverr",
    [string]$PromptDir = "C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $RepoRoot)) {
    throw "Repo root not found: $RepoRoot"
}

if (-not (Test-Path -LiteralPath $PromptDir)) {
    throw "Prompt directory not found: $PromptDir"
}

Push-Location $RepoRoot
try {
    $logLine = git log origin/develop --oneline -1
    if (-not $logLine) {
        throw "Unable to read git log origin/develop --oneline -1"
    }

    $first = "$logLine".Trim()
    if ($first -notmatch "^([0-9a-f]{7,40})\s+") {
        throw "Could not parse SHA from: $first"
    }
    $squashSha = $Matches[1]

    $promptFiles = Get-ChildItem -LiteralPath $PromptDir -File -Filter "CYCLE_068*.md"
    if (-not $promptFiles) {
        throw "No C068 prompt files found in $PromptDir"
    }

    foreach ($file in $promptFiles) {
        $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
        $updated = $content -replace "\[C068_SQUASH_SHA\]", $squashSha
        if ($updated -ne $content) {
            Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
            Write-Host "Updated $($file.Name)"
        }
    }

    Write-Host "Resolved [C068_SQUASH_SHA] -> $squashSha"
    Write-Host "Verification command:"
    Write-Host "Select-String '\[C068_SQUASH_SHA\]' PM_Pack\03_cursor_agent_system\CYCLE_068*"
}
finally {
    Pop-Location
}
