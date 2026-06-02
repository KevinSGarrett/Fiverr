# SHA_RESOLVER_SCRIPT.ps1
# Agent A runs this via Desktop Commander at the very start of the cycle.
# It reads the prior cycle's squash SHA and replaces the placeholder in all 6 prompt files.
# This is the ONLY way SHA placeholders are resolved — no human involvement.

param(
    [string]$PromptDir = 'C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system',
    [string]$CycleNum = '056',      # The cycle whose prompts need the placeholder replaced
    [string]$PlaceholderPRNum = '64' # The PR number whose squash SHA is the placeholder value
)

Set-Location 'C:\Fiverr\Fiverr'

# Step 1: Get the squash SHA from GitHub
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = 'C:\Program Files\GitHub CLI\gh.exe'
$psi.Arguments = "api repos/KevinSGarrett/Fiverr/pulls/$PlaceholderPRNum --jq .merge_commit_sha"
$psi.WorkingDirectory = 'C:\Fiverr\Fiverr'
$psi.RedirectStandardOutput = $true; $psi.RedirectStandardError = $true
$psi.UseShellExecute = $false; $psi.CreateNoWindow = $true
$p = [System.Diagnostics.Process]::Start($psi)
$sha = $p.StandardOutput.ReadToEnd().Trim()
$err = $p.StandardError.ReadToEnd().Trim()
$p.WaitForExit()

if (-not $sha -or $sha.Length -lt 7) {
    Write-Error "Could not get squash SHA for PR #$PlaceholderPRNum. Error: $err"
    exit 1
}

Write-Host "Squash SHA for PR #$PlaceholderPRNum`: $sha"

# Step 2: Determine placeholder string
$placeholder = "[C0${CycleNum.Substring(1)}_SQUASH_SHA]"
# Construct correctly: e.g. for cycle 055 prompts: [C055_SQUASH_SHA]
$priorCycle = [int]$CycleNum - 1
$placeholder = "[C0${priorCycle}_SQUASH_SHA]"
if ($priorCycle -lt 10) { $placeholder = "[C00${priorCycle}_SQUASH_SHA]" }
if ($priorCycle -ge 10 -and $priorCycle -lt 100) { $placeholder = "[C0${priorCycle}_SQUASH_SHA]" }

Write-Host "Replacing placeholder: $placeholder"

# Step 3: Replace in all 6 prompt files for this cycle
$replaced = 0
foreach ($agent in @('A','B','C','D','E','F')) {
    $path = Join-Path $PromptDir "CYCLE_0${CycleNum}_AGENT_${agent}_PROMPT.md"
    if (Test-Path $path) {
        $content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)
        if ($content.Contains($placeholder)) {
            $updated = $content.Replace($placeholder, $sha)
            [System.IO.File]::WriteAllText($path, $updated, [System.Text.Encoding]::UTF8)
            $replaced++
            Write-Host "  Updated: CYCLE_0${CycleNum}_AGENT_${agent}_PROMPT.md"
        } else {
            Write-Host "  No placeholder in: CYCLE_0${CycleNum}_AGENT_${agent}_PROMPT.md (OK)"
        }
    } else {
        Write-Warning "  Not found: $path"
    }
}

Write-Host ""
Write-Host "SHA resolution complete. $replaced file(s) updated."
Write-Host "Placeholder '$placeholder' -> '$sha'"
