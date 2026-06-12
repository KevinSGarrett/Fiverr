# Jira Auth Expiry Recovery

## Symptoms

- Jira API calls fail with unauthorized or forbidden responses.
- Issue sync tasks cannot comment, transition, or query issue state.
- Controller reports missing Jira updates despite expected operations.

## Recovery Steps

1. Confirm Jira auth failure using configured Jira command or integration check.
2. Refresh Jira credentials/token from approved credential source.
3. Re-run Jira connectivity test command from runner integration.
4. Retry one read operation and one write-safe operation (comment on a test issue if permitted).

## Suggested Verification Sequence

```powershell
# example placeholders, adapt to integration wrapper
python automation/ai_cycle_controller.py jira-health
python automation/ai_cycle_controller.py jira-list --cycle 075
```

## Security Considerations

- Never paste Jira tokens in reports or commit history.
- Keep tokens in secure local state or environment configuration excluded from git.
- Rotate token if compromise is suspected.

## Post-Recovery Checks

- Jira issue search works
- issue comment operation works
- status transitions (where allowed) work
- cycle sync summary can be generated

## Incident Note

Document expiry event, downtime window, and whether any cycle completion gates were delayed.

## Operational Checks

After token refresh, run these checks:

1. Query open issues for active cycle board/filter.
2. Add one non-destructive comment to a designated test or control issue.
3. Verify transition metadata loads for expected workflow states.

If any check fails, do not mark Jira connectivity recovered.

## Minimum Incident Fields

Include in report:

- Jira project key(s) impacted
- first failing timestamp
- restored timestamp
- commands used for recovery
- any stories that were delayed by outage

This level of detail supports PM review and root-cause trending.

