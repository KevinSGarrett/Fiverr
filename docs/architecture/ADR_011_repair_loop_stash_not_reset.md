# ADR-011: Repair Loop Uses git stash for Quarantine, Not git reset

## Status
Accepted

## Context
When a Cursor agent produces work that fails validation (ruff, mypy, pytest, coverage),
the controller must quarantine the bad work safely. Two options exist: git reset (destructive,
permanently discards work) or git stash (non-destructive, preserves work for inspection).

## Decision
The repair loop quarantines failing agent work using `git stash push --include-untracked`
with a timestamp message. It NEVER uses `git reset --hard` or `git reset --mixed` to
discard agent work. Rollback of accepted (committed) work uses `git revert --no-edit`
rather than force-push or reset.

## Consequences
- All quarantined work is recoverable from the stash list for post-mortem inspection.
- `git stash list` provides a full audit trail of quarantine events.
- No permanent data loss occurs during normal repair operations.
- The stash list must be pruned periodically to avoid accumulation.
- Force-push and reset are permanently blocked by autonomy_policy.yml.
