# PM Pack Audit Procedure Runbook

## Purpose

This runbook defines the repeatable process for running and interpreting PM Pack audit commands. PM state consistency is critical for cycle governance because prompts, scorecards, and controller logic depend on synchronized cycle metadata.

## Required Commands

Run `compile-policy` first, then run `pm-pack-audit`. This order ensures the policy snapshot is regenerated before consistency checks. Capture full output for evidence and note any warnings even when status is PASS.

## What To Validate

Confirm cycle, branch, and status agree across hydration header, canonical state, snapshots, and controller state. Verify warnings about null or stale fields are explicitly documented; do not suppress warnings just because exit code is zero.

## Common Mismatch Patterns

Frequent mismatches include stale cycle numbers, branch labels that lag actual branch, and policy snapshots with null completion fields. Another common issue is contradictory status between controller and PM docs during active transitions.

## Corrective Workflow

When mismatches are found, update authoritative docs first, regenerate policy snapshot, then re-run audit. Keep changes scoped to PM and docs paths for Agent A operations. Re-check brain-check after significant PM updates.

## Evidence Expectations

Each cycle should store audit evidence with timestamp, command output, and final pass/fail determination. If warnings remain, evidence should explain whether they are expected carry-forward warnings or unresolved defects requiring future action.

## Escalation

Escalate when audit fails repeatedly after state correction or when required files are missing unexpectedly. Include command outputs and file paths in escalation artifacts.
