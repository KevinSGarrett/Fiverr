# Slack Webhook Setup For Fiverr Autonomous Runner

## Purpose

Configure the runner to deliver operational notifications through the notification router.

## Required Secret

Set `SLACK_WEBHOOK_URL` in `C:/AI_Runner/secrets/runner.env`.

Example:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/REPLACE/THIS/WITH_REAL_WEBHOOK
```

If a production URL is not available yet, keep this placeholder in documentation only:

```env
SLACK_WEBHOOK_URL=PENDING_CONFIGURATION
```

## Validation Steps

1. Confirm secret resolves:
   - `python -c "import os; from dotenv import load_dotenv; load_dotenv(r'C:/AI_Runner/secrets/runner.env'); print(bool(os.environ.get('SLACK_WEBHOOK_URL')))"`.
2. Send a router test:
   - `python -c "from automation.notification_router import notify_info; notify_info('Cycle 077 test', 'Router online')"`
3. Confirm Slack message arrives and no incident file is created for INFO severity.
4. Check local log:
   - `C:/AI_Runner/logs/notifications.log`.

## Failure Modes

- Missing webhook URL -> router silently skips Slack delivery.
- Invalid webhook URL -> HTTP failure in webhook call, router continues best-effort.
- Missing network egress -> no Slack delivery; local log still records notification.

## Operational Notes

Keep this webhook in the runner secret store only, never in tracked repository files. The expected operational pattern is: set the value in `runner.env`, restart or reload processes that use the secret loader, trigger one INFO test notification, then confirm delivery in the target Slack channel and in local logs. If the message does not appear in Slack, check three layers in sequence: first secret load, then outbound network reachability, then webhook endpoint correctness. For troubleshooting, always keep a timestamped command transcript and compare it with `notifications.log` so you can prove whether the router attempted delivery. When rotating webhook credentials, update the secret in one place and re-run the same test command immediately so stale sessions are caught early. If this system is moved to another host, include webhook setup in the host bootstrap checklist and verify after every migration, because host-level proxy or firewall policies can block outbound webhook posts even when the secret is present and syntactically valid.
