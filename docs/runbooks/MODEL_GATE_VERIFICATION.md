# Model Gate Verification Runbook

## Purpose

This runbook describes how to verify model gate readiness before agent dispatch. The objective is to ensure the configured model, effort settings, and verification timestamps satisfy governance requirements and prevent unauthorized model drift.

## Baseline Checks

Run a dry-run agent command and capture model gate output. Confirm status is PASS, model name matches policy, effort is expected, and age is within allowed verification windows. Then inspect `cursor_model_state.json` and `claude_model_state.json` to validate stored verification metadata and expiry windows.

## Evidence Requirements

Evidence must include command output, selected model, verification status, and timestamp age. Include both cursor and claude state snapshots so reviewers can validate consistency between runtime output and persisted state.

## Drift Validation

Use a synthetic candidate state file to test drift detection behavior without touching production state files. A valid test intentionally sets an incorrect model value and verifies that drift detection returns a mismatch result. Always remove temporary drift files after testing to avoid false alerts in later checks.

## Failure Response

If model gate fails, stop dispatch and identify whether failure is due to expired verification, missing state files, or policy mismatch. Do not bypass the gate with manual state edits. Instead, re-run verification flow and update state files through approved scripts.

## Escalation

Escalate when model gate repeatedly fails after re-verification or when state files disagree with runtime outputs. Include exact command outputs and artifact paths for deterministic remediation.
