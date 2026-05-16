$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Output ""
    Write-Output "=== $Title ==="
}

$expectedRoot = "C:\Fiverr\Fiverr"
$locationPath = (Get-Location).Path
$gitRoot = (git rev-parse --show-toplevel).Trim()
$normalizedGitRoot = $gitRoot -replace "/", "\"
$branch = (git branch --show-current).Trim()
$statusShort = git status --short --branch
$worktreeList = git worktree list

Write-Section "Execution Context"
Write-Output "Location: $locationPath"
Write-Output "Git root: $gitRoot"
Write-Output "Branch: $branch"

Write-Section "Git Status"
$statusShort | ForEach-Object { Write-Output $_ }

Write-Section "Git Worktrees"
$worktreeList | ForEach-Object { Write-Output $_ }

if ($normalizedGitRoot -ne $expectedRoot) {
    Write-Error "Preflight failed: git root must be '$expectedRoot' but was '$gitRoot'."
    exit 1
}

Write-Output ""
Write-Output "Preflight root-lock check: PASS"
