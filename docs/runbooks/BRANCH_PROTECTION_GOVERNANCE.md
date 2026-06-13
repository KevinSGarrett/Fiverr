# Branch Protection Governance Runbook

## Purpose

This runbook defines how to verify and document branch protection governance for `develop`. It ensures required checks, merge policies, and conversation-resolution settings are observable and auditable each cycle.

## Authentication Prerequisite

Before querying GitHub protection settings, validate that CLI authentication is not overridden by an invalid `GITHUB_TOKEN` environment variable. If the environment variable is invalid, clear it for the current session and rely on keyring-backed credentials.

## Verification Commands

Use:
- `gh api /repos/<owner>/<repo>/branches/develop/protection`
- `gh pr view <number> --json state,mergedAt`
- `gh run list --workflow=ci.yml --limit N --json ...`

Capture raw responses in evidence docs.

## What To Confirm

Verify required status checks list, strict mode, force-push policy, deletion policy, and conversation resolution requirement. For PR state, confirm merged/open status and merge timestamp. For CI, capture latest run conclusion and head SHA alignment with target branch.

## Failure Handling

If auth fails, record exact HTTP status and error message. If branch protection query succeeds but PR is open or CI failing, record as governance blocker rather than forcing completion claims.

## Token Scope Notes

Read-only verification generally requires repo read scope. Mutation operations (changing protections) require elevated admin permissions on the repository. Never claim a permission blocker if verification queries succeed.

## Escalation

Escalate when required checks are missing unexpectedly, PR status conflicts with git ancestry evidence, or CI conclusions disagree across interfaces.
