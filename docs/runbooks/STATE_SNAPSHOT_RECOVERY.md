# State Snapshot Recovery Runbook

## Purpose

This runbook explains how to validate and recover state snapshot generation used by the autonomous runner. Snapshot integrity is essential because daily and weekly governance evidence relies on consistent artifacts under `C:/AI_Runner/backups/state_snapshots`.

## Expected Behavior

A successful snapshot run creates a timestamped directory containing manifest and state files such as `controller_state.json`, `heartbeat.json`, branch metadata, and summary files. Snapshot tasks should complete with a zero result code and produce a coherent `snapshot_manifest.json` that references generated files.

## Validation Steps

First, trigger the snapshot task manually and capture the scheduler response. Then check the newest snapshot directory and verify file creation times align with the trigger time. Read the manifest and confirm key files exist, including state, branch, and policy snapshot artifacts. If files are missing, inspect task command configuration and script path correctness.

## Recovery Steps

If the task launches but produces incomplete output, inspect backup path permissions and available disk space. Confirm the task account can read repository and runner state files. If failures persist, run the snapshot script directly and compare direct execution output with scheduler output. Record both for evidence because scheduler context differs from shell context.

## Escalation

Escalate when snapshot directories are not created after manual and scheduled runs, or when manifests are repeatedly incomplete. Include task metadata, command output, and path listings in the escalation note to avoid repeated blind retries during cycle execution.
