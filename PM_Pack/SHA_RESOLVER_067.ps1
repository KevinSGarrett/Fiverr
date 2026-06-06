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
    $logLines = git log origin/develop --oneline -3
    if (-not $logLines -or $logLines.Count -lt 1) {
        throw "Unable to read git log origin/develop --oneline -3"
    }

    # First line should be the latest squash commit on develop.
    $first = $logLines[0].Trim()
    if ($first -notmatch "^([0-9a-f]{7,40})\s+") {
        throw "Could not parse SHA from: $first"
    }
    $squashSha = $Matches[1]

    $promptFiles = Get-ChildItem -LiteralPath $PromptDir -File -Filter "CYCLE_067_AGENT_*.md"
    if (-not $promptFiles) {
        throw "No C067 prompt files found in $PromptDir"
    }

    foreach ($file in $promptFiles) {
        $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
        $updated = $content -replace "\[C067_SQUASH_SHA\]", $squashSha
        if ($updated -ne $content) {
            Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
            Write-Host "Updated $($file.Name)"
        }
    }

    Write-Host "Resolved [C067_SQUASH_SHA] -> $squashSha"
    Write-Host "Verification command:"
    Write-Host "Select-String '\[C067_SQUASH_SHA\]' PM_Pack\03_cursor_agent_system\CYCLE_067*"
}
finally {
    Pop-Location
}
