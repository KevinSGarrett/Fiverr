# =============================================================================
# set_branch_protection.ps1 -- Set 'develop' branch protection (OPERATOR step)
# -----------------------------------------------------------------------------
# Source of truth lives in the repo at: host/set_branch_protection.ps1
# Configures GitHub branch protection on the 'develop' branch so that a merge is
# only possible when ALL loop-critical status checks are green. This closes the
# SAFE-04 hole: protection must require the contexts produced by the workflows
# that actually exist (CI, Security, PR Checks) rather than a stale/incomplete
# set.
#
# *** GUARDED ***  By default this is a DRY-RUN: it only PRINTS the payload and
# the gh api command it WOULD run. Pass -Execute to actually apply protection.
# It is therefore safe to read/inspect and even to run without arguments -- it
# does NOT change real branch protection unless -Execute is passed.
#
# Auth: uses GH_TOKEN or GH_AUTOMATION_TOKEN (the correct automation token env
# var names; an earlier draft used a wrong GITHUB-prefixed name that gh ignores).
# gh picks up GH_TOKEN automatically; if only GH_AUTOMATION_TOKEN is set we
# promote it to GH_TOKEN for the gh call.
#
# Prerequisite: the GitHub CLI ('gh') must be installed and the token must have
# 'repo' + 'administration:write' scope on the target repository.
# =============================================================================

[CmdletBinding()]
param(
    [switch]$Execute,                       # actually apply protection; default = dry-run
    [string]$Owner  = "scentiment",         # repo owner (override if forked)
    [string]$Repo   = "Fiverr",             # repo name
    [string]$Branch = "develop"             # branch to protect
)

$DoIt = $Execute.IsPresent

# ---------------------------------------------------------------------------
# Auth: prefer GH_TOKEN; otherwise promote GH_AUTOMATION_TOKEN to GH_TOKEN.
# NOTE: we deliberately read only GH_TOKEN / GH_AUTOMATION_TOKEN -- the earlier
# GITHUB-prefixed variant was a bug (gh does not honour it).
# ---------------------------------------------------------------------------
$Token = $env:GH_TOKEN
if ([string]::IsNullOrWhiteSpace($Token)) {
    $Token = $env:GH_AUTOMATION_TOKEN
}
if (-not [string]::IsNullOrWhiteSpace($Token)) {
    # gh reads GH_TOKEN from the environment automatically.
    $env:GH_TOKEN = $Token
}

# ---------------------------------------------------------------------------
# Required status contexts -- the workflows/jobs that actually exist in this
# repo. A PR to 'develop' must have ALL of these green before it can merge.
#   CI workflow jobs (name: "CI / <job>"):
# ---------------------------------------------------------------------------
$RequiredContexts = @(
    "CI / lint",
    "CI / type-check",
    "CI / tests-coverage",
    "CI / smoke-gates",
    "CI / codex-review-gate",
    "Security",        # .github/workflows/security.yml  (name: Security)
    "PR Checks"        # .github/workflows/pr-checks.yml (name: PR Checks)
)

Write-Host "============================================================"
Write-Host " set_branch_protection.ps1  (mode: $(if ($DoIt) { 'EXECUTE' } else { 'DRY-RUN -- pass -Execute to apply' }))"
Write-Host " Target : $Owner/$Repo @ branch '$Branch'"
Write-Host "============================================================"

if ([string]::IsNullOrWhiteSpace($env:GH_TOKEN)) {
    Write-Warning "[set_branch_protection] Neither GH_TOKEN nor GH_AUTOMATION_TOKEN is set."
    Write-Warning "[set_branch_protection] gh will fall back to its stored auth (or fail if none)."
}

# ---------------------------------------------------------------------------
# Build the branch-protection payload.
#   - required_status_checks.strict = true (branch must be up to date)
#   - contexts = the required status checks above
#   - enforce_admins = true (admins are not exempt)
#   - required_pull_request_reviews = 1 approving review
#   - dismiss stale reviews on new pushes
# ---------------------------------------------------------------------------
$Payload = [ordered]@{
    required_status_checks = [ordered]@{
        strict   = $true
        contexts = $RequiredContexts
    }
    enforce_admins                = $true
    required_pull_request_reviews = [ordered]@{
        required_approving_review_count = 1
        dismiss_stale_reviews           = $true
    }
    restrictions = $null
}

$Json   = $Payload | ConvertTo-Json -Depth 6
$ApiPath = "repos/$Owner/$Repo/branches/$Branch/protection"

Write-Host ""
Write-Host "[set_branch_protection] Required status contexts:"
foreach ($ctx in $RequiredContexts) { Write-Host "    - $ctx" }
Write-Host ""
Write-Host "[set_branch_protection] PUT $ApiPath payload:"
Write-Host $Json
Write-Host ""

if (-not $DoIt) {
    Write-Host "[set_branch_protection] DRY-RUN complete. Nothing was changed."
    Write-Host "[set_branch_protection] Would run:"
    Write-Host "    gh api --method PUT $ApiPath -H 'Accept: application/vnd.github+json' --input -"
    Write-Host "[set_branch_protection] Re-run with -Execute to apply protection."
    exit 0
}

# ---------------------------------------------------------------------------
# EXECUTE: apply via gh api. The JSON payload is piped to gh's stdin (--input -).
# ---------------------------------------------------------------------------
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "[set_branch_protection] FATAL: GitHub CLI 'gh' not found on PATH."
    exit 1
}

Write-Host "[set_branch_protection][EXEC] Applying branch protection to $Owner/$Repo@$Branch ..."
$Json | gh api --method PUT $ApiPath -H "Accept: application/vnd.github+json" --input -
if ($LASTEXITCODE -ne 0) {
    Write-Error "[set_branch_protection] FATAL: gh api returned exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "[set_branch_protection][EXEC] Branch protection applied."
Write-Host "[set_branch_protection] Verify with: gh api $ApiPath | ConvertFrom-Json"
exit 0
