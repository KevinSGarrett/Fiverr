# Notification Routing Operations Runbook

## Purpose

This runbook covers setup, validation, and troubleshooting for the runner notification router. It applies to INFO, WARNING, BLOCKED, and CRITICAL flows routed to logs, Slack, and optionally GitHub issues.

## Setup Requirements

Ensure notification secrets are loaded from the runner secret store. Slack routing requires `SLACK_WEBHOOK_URL` in `C:/AI_Runner/secrets/runner.env`. Without this value, Slack delivery is intentionally skipped while local logs still record events.

## Validation Workflow

1. Confirm secret presence through a non-printing boolean check.
2. Send an INFO-level notification test.
3. Verify local log append in `C:/AI_Runner/logs/notifications.log`.
4. If webhook exists, verify Slack receipt and HTTP behavior.

For BLOCKED/CRITICAL tests, verify incident file creation and optional GitHub issue behavior where configured.

## Evidence Standards

Evidence should include command output, timestamp, local log line proof, and Slack/GitHub outcomes. If webhook is missing, classify status as `NEEDSWEBHOOKURL` with explicit missing dependency details.

## Troubleshooting

Common issues:
- secret missing or stale session environment
- webhook URL invalid or revoked
- outbound network restrictions
- auth failures for GitHub issue creation

Test each layer separately to avoid ambiguous failure reports.

## Security Notes

Never print raw webhook values in logs or reports. Keep sensitive values out of committed files. Use placeholders in documentation and real values only in secret stores.

## Escalation

Escalate when notifications fail despite valid secrets and network connectivity, or when incident paths are not created for critical events.
