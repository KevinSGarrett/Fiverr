# Drift Detection Validation Runbook

## Purpose

This runbook documents the safe procedure for validating model drift detection behavior. The goal is to prove drift checks can detect mismatched model identifiers without changing production state files.

## Test Setup

Create a temporary test state file in `C:/AI_Runner/state/test_drift_state.json` with a deliberately incorrect model name and a test status flag. Use a detector implementation that compares candidate model identity against the verified cursor model state.

## Validation Steps

1. Create the temporary candidate file.
2. Execute drift detection command and capture structured output.
3. Confirm `drift_detected` is true and reason indicates model mismatch.
4. Remove temporary file immediately after capture.

The output should include expected model, candidate model, candidate status, and a deterministic reason value.

## Evidence Quality

Record the exact command used, output payload, and cleanup confirmation. Evidence is incomplete if cleanup is omitted or if result does not show both expected and candidate model values.

## Failure Modes

If detector import fails, verify module path and package resolution. If detector returns unknown values unexpectedly, inspect JSON parsing and candidate schema assumptions. Never mark drift validation complete when output fields are unresolved.

## Operational Guidance

Use drift simulation only in controlled test contexts. Do not modify verified model state files during simulation. Keep test artifacts namespaced and easy to identify for cleanup.

## Escalation

Escalate if detector repeatedly fails to import, if mismatch is not detected for known wrong models, or if cleanup cannot remove temporary files.
