# Incident Response And Escalation Runbook

## Purpose

This runbook defines the response model for autonomous runner incidents, including detection, triage, evidence capture, and escalation thresholds. It standardizes incident handling so cycle operations remain auditable and recoverable.

## Detection Sources

Primary signals include:
- watchdog health artifacts
- notifications log entries marked BLOCKED or CRITICAL
- maintenance task failures
- post-cycle review FAIL results

Use multiple signals before classifying incident severity.

## Triage Framework

Classify incidents as:
- informational degradation (no dispatch impact)
- operational blocker (dispatch impact)
- governance/security blocker (requires explicit human decision)

Record first-seen time, affected subsystem, and immediate impact on cycle flow.

## Immediate Response

For operational blockers, capture state and logs before making changes. Then execute least-risk remediation: rerun failing task, refresh auth context, or restore expected state files. Re-check health after each action and stop if state becomes contradictory.

## Evidence Requirements

Every incident record should include command outputs, file paths, timestamps, and final disposition. If unresolved, include best next action and external dependency owner.

## Escalation Triggers

Escalate immediately for repeated auth failures, protection-policy conflicts, persistent RED health states, missing critical artifacts after retries, or any security-sensitive inconsistency.

## Post-Incident Review

After stabilization, update cycle evidence docs with what failed, what changed, what remains open, and how recurrence risk is being managed.
