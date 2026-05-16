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
$dirtyEntries = @($statusShort | Where-Object { $_ -and -not $_.StartsWith("##") })
$worktreePaths = @()
foreach ($line in $worktreeList) {
    $parts = $line -split "\s+"
    if ($parts.Count -gt 0 -and $parts[0]) {
        $worktreePaths += ($parts[0] -replace "/", "\")
    }
}
$unauthorizedWorktrees = @($worktreePaths | Where-Object { $_ -and $_ -ne $expectedRoot })
$rootLockStatus = if ($normalizedGitRoot -eq $expectedRoot) { "ready" } else { "blocked" }
$worktreeStatus = if ($unauthorizedWorktrees.Count -gt 0) { "blocked" } else { "ready" }
$dirtyTreeStatus = if ($dirtyEntries.Count -gt 0) { "warning" } else { "ready" }
$runtimeStatus = "ready"
if ($rootLockStatus -eq "blocked" -or $worktreeStatus -eq "blocked") {
    $runtimeStatus = "blocked"
}
elseif ($dirtyTreeStatus -eq "warning") {
    $runtimeStatus = "warning"
}

Write-Section "Execution Context"
Write-Output "Location: $locationPath"
Write-Output "Git root: $gitRoot"
Write-Output "Branch: $branch"

Write-Section "Git Status"
$statusShort | ForEach-Object { Write-Output $_ }

Write-Section "Git Worktrees"
$worktreeList | ForEach-Object { Write-Output $_ }

Write-Section "Integration Run Context"
$runContext = [ordered]@{
    status = $runtimeStatus
    expected_root = $expectedRoot
    git_root = $normalizedGitRoot
    branch = $branch
    root_lock = $rootLockStatus
    worktree_control = $worktreeStatus
    dirty_tree = $dirtyTreeStatus
    worktree_count = $worktreePaths.Count
    unauthorized_worktrees = @($unauthorizedWorktrees)
    dirty_entries = @($dirtyEntries)
}
$runContext | ConvertTo-Json -Depth 4

if ($normalizedGitRoot -ne $expectedRoot) {
    Write-Error "Preflight failed: git root must be '$expectedRoot' but was '$gitRoot'."
    exit 1
}

if ($unauthorizedWorktrees.Count -gt 0) {
    Write-Error "Preflight failed: unauthorized worktrees detected."
    exit 1
}

Write-Output ""
Write-Output "Preflight root-lock/worktree check: PASS"
