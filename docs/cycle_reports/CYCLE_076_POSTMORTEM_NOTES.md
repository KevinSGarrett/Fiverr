# Cycle 076 Postmortem Notes

## What Went Well
- Agent B and follow-up fixes closed all critical low-coverage modules and restored >=90% per-target module coverage.
- V-1 evidence infrastructure is complete and ready for Cycle 077 execution.
- Jira token loading was diagnosed and fixed with explicit credential validation.
- All 13 ADRs are now written and tracked.
- Combined coverage improved from 86.75% -> 92.58%.

## Issues Encountered
- `gh` CLI initially failed due invalid `GITHUB_TOKEN` overriding keyring auth; resolved by clearing env var for PR commands.
- Required labels (`cycle/076`, `runner-infra`, `tests`) were missing in the repository, so PR was created without labels.
- `merge-gate --dry-run` currently reports unknown PR metadata/checks pre-CI and fails expected gate checks.
- Jira inventory summary field still reports `total=0` while listing active rows (known non-blocking inconsistency).
- `status-tick` shows `BLOCKED_DIRTY_REPO` while Agent D artifacts are in progress and uncommitted.

## Process Improvements for Cycle 077
- Agent prompts must specify --output-format=full (not text) - fixed in this cycle.
- Agent prompts should specify exact Jira token load path and expected env override behavior.
- Ensure repo labels are bootstrapped (`create-labels`) before PR creation steps.

## Lessons Learned
- Keep CLI auth deterministic by avoiding conflicting environment tokens during GitHub operations.
- Run merge-gate with explicit PR context and interpret pre-CI failures as expected unless policy gates fail.
- Capture board inventory rows and totals separately when Jira summary fields are known to be inconsistent.
