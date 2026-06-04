# SHA_RESOLVER_062.ps1 — run once to stamp [C062_SQUASH_SHA] in all 6 prompts
# After squash merge: replace [C062_SQUASH_SHA] with the real SHA in all 6 prompt files
# Usage: Run after D confirms squash merge SHA, then search all 6 prompts for [C062_SQUASH_SHA]
#        and replace with the real SHA string.
Write-Host "C062 SHA Resolver: search all 6 CYCLE_062 prompt files for [C062_SQUASH_SHA]"
Write-Host "Replace with actual squash SHA after PR merge."
