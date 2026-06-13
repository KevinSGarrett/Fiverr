# Scheduled Task Operations Runbook

## Purpose

This runbook defines how to validate and operate production scheduled tasks used by the runner platform. It focuses on task discovery, manual trigger validation, and evidence capture for watchdog, snapshot, and maintenance jobs.

## Task Discovery

Do not assume task names; query all tasks and locate entries by function and script path. In this environment, task names may be `AI Runner ...` even when prompts reference legacy `Fiverr...` names. Treat script path and behavior as authoritative when name aliases differ.

## Manual Trigger Validation

For each task, capture query output fields: status, last run time, next run time, last result, and command path. Trigger tasks manually with `schtasks /run` and then verify resulting artifacts:
- watchdog: health JSON updates
- daily snapshot: new snapshot directory and manifest
- weekly maintenance: maintenance log with git operations

## Evidence Quality

Evidence files should include raw command output plus artifact paths and timestamps. When partial failures occur inside a task script, record both successful and failed substeps. This prevents false binary labeling and gives reviewers actionable context.

## Recovery Guidance

If a task reports failures, check script syntax, runtime dependencies, and execution context. Scheduler context often differs from interactive shells, especially for Python module availability and environment variables. Validate from both contexts before concluding root cause.

## Escalation

Escalate when tasks fail repeatedly across both manual and scheduled runs, or when expected artifacts are absent despite success codes. Include task metadata and log excerpts in escalation documentation.
