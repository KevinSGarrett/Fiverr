# Codex Review Disposition Protocol

## Purpose

Codex comments are advisory guidance, not automatic merge blockers by themselves. Every Codex thread must still be reviewed, dispositioned with evidence, and either resolved or explicitly tracked as blocking work.

## Mandatory Workflow

1. Read every Codex thread on the PR.
2. Validate the claim against current branch code and tests.
3. Post one formal disposition reply per thread using the required format.
4. Resolve the thread only after the disposition conditions are satisfied.
5. Do not merge while any required-fix thread remains unresolved.

## Disposition Categories

Use exactly one of these values in each disposition reply:

- `VALID_FIXED`: Comment is correct, a fix is implemented, and regression evidence exists.
- `VALID_DEFERRED_BLOCKER`: Comment is correct, fix is not yet implemented, and PR is blocked until resolved.
- `VALID_DEFERRED_NONBLOCKING`: Comment is correct but intentionally deferred to follow-up work that is approved as non-blocking.
- `NOT_APPLICABLE`: Comment does not apply to the final changed code path in this PR.
- `FALSE_POSITIVE`: Comment is incorrect after verification with code evidence.
- `DUPLICATE`: Comment duplicates another thread or existing tracked finding.

## Required Reply Format

Use this structure for every Codex thread reply:

```text
Codex disposition: <CATEGORY>

Root cause:
<why the issue happened, or why finding is not applicable>

What changed:
- <fix detail or rationale for non-fix disposition>

Regression tests:
- <test path and test id, or N/A with reason>

Validation commands:
- <commands run and outcome summary>

Resolve thread after push/checks: <Yes|No>
```

## Resolution Rules

- Resolve immediately only for `VALID_FIXED`, `NOT_APPLICABLE`, `FALSE_POSITIVE`, or `DUPLICATE` when evidence is posted and CI/check gates are satisfied.
- Do not resolve for `VALID_DEFERRED_BLOCKER`.
- `VALID_DEFERRED_NONBLOCKING` may be resolved only if PM/operator explicitly accepts deferment and a follow-up issue is recorded.
- If account permissions prevent resolution, leave the thread open and record the exact blocker in the cycle report.

## PR Blockers

A PR is blocked when any of the following is true:

- A Codex thread has no disposition reply.
- A valid issue is not fixed and is marked `VALID_DEFERRED_BLOCKER`.
- Evidence is missing for a `VALID_FIXED` claim.
- Required checks are missing, pending, or failing.

## Evidence Expectations

- Link the fix commit SHA(s).
- Name the exact test(s) added/updated.
- Include command outputs or summarized results for lint, typecheck, tests, and coverage.
- Keep dispositions auditable so a future steward can verify without PM re-explaining policy.
