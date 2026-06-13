# Runner Heartbeat Operations Runbook

## Purpose

This runbook defines how to verify, interpret, and recover runner heartbeat behavior for the autonomous cycle controller. A healthy heartbeat means the controller is writing fresh status updates, the watchdog can evaluate risk correctly, and downstream automation does not stall on stale state assumptions.

## Standard Validation

Start by checking `C:/AI_Runner/state/heartbeat.json` for a recent timestamp. Confirm the timestamp moves forward after a `status-tick` command. Next, inspect the newest watchdog health artifact in `C:/AI_Runner/logs/watchdog` and verify that heartbeat age is within an expected operational window. A stale heartbeat with an otherwise responsive runner can indicate controller loop interruption, scheduler suspension, or environment drift.

## Recovery Procedure

If heartbeat age exceeds expected limits, confirm scheduled task execution for the controller and watchdog tasks, then run a manual `status-tick` and observe whether heartbeat recovers. If heartbeat remains stale, inspect controller logs for dispatch errors, auth failures, or path misconfiguration. Avoid destructive actions while state is uncertain; collect evidence first, then restart affected automation components in order: controller, watchdog, then reporting tasks.

## Escalation Criteria

Escalate when heartbeat remains stale after restart attempts, when health changes to RED, or when contradictions appear between controller state and watchdog output. Capture exact timestamps, command output, and file paths in evidence notes so post-cycle reviewers can reconstruct the incident without ambiguity.
