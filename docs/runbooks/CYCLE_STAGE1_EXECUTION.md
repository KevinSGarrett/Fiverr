# Cycle Stage 1 Execution Runbook

## Purpose

This runbook defines the execution order for Cycle Stage 1 setup: branch readiness, brain and PM audits, prompt generation, prompt validation, and task-floor enforcement.

## Stage 1 Sequence

1. Confirm correct base branch and cycle branch setup.
2. Run `brain-check` and resolve all FAIL conditions before continuing.
3. Run `pm-pack-audit` and reconcile state mismatches.
4. Run `plan-cycle --live` for target cycle.
5. Run `validate-prompts --cycle <id>`.
6. Enforce mandatory task-floor regex check across all six agent prompts.

Do not authorize downstream agents before all six prompts pass floor and validation checks.

## Prompt Quality Controls

Ensure every generated prompt includes end marker text and avoids stub placeholders. If validation reports stub patterns, patch prompts and re-run validation until PASS.

## Evidence Requirements

Capture command outputs and write dedicated evidence files for OPS-030 and DOD-007. Include timestamp, validation summary, and per-agent task counts.

## Failure Handling

If `plan-cycle --live` has insufficient Jira input stories, query board state and resolve shortfall according to governance instructions before rerunning. If validation still fails, inspect prompt sections directly for unresolved placeholders or format mismatches.

## Completion Criteria

Stage 1 is complete only when:
- brain-check PASS
- pm-pack-audit PASS
- plan-cycle PASS
- validate-prompts PASS
- task floor PASS for all six agents
- evidence files written and traceable

## Escalation

Escalate when required dependencies (Jira, auth, policy files) block Stage 1 from achieving deterministic PASS outcomes.
