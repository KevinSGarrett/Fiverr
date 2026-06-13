# Post-Cycle Review Workflow Runbook

## Purpose

This runbook documents how to execute post-cycle review checks safely and consistently. Post-cycle review controls whether subsequent dispatch should proceed and captures quality gates after agent execution.

## Mode Selection

Use post-cycle review in dry-run mode first to collect facts without writing artifacts. For compatibility with older operator prompts, the `advisory` mode alias maps to post-cycle PM review mode. Capture output showing PR merge status, CI status, baseline DB check, and report presence.

## Dry-Run Checklist

Verify that:
- cycle number is correct
- required agent reports are present
- baseline DB invariant check result is captured
- model and policy status indicators are visible

Dry-run output alone is evidence for advisory verification steps but does not unlock dispatch.

## Full Review

When running full review, store generated artifacts and confirm PASS/FAIL outcome. If FAIL, do not force next cycle dispatch. Resolve blockers first, re-run review, and preserve both failed and passing outputs for traceability.

## Frequent Failure Causes

Typical failures include unmerged PR state, failed CI checks, missing reports, or baseline invariant mismatch. Treat each as a governance blocker, not a cosmetic warning.

## Documentation Standards

Evidence files should include command used, mode used, timestamp, and key output lines. If prompt language and CLI mode names diverge, explicitly document the mapping so reviewers can reconcile requirements with implementation.

## Escalation

Escalate when review repeatedly fails after remediation or when review logic appears inconsistent with governance policy files.
