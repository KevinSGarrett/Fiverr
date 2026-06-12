# GitHub Runner Offline Playbook

## 1) Detection

Trigger this playbook if:

- GitHub Actions shows "Waiting for a runner to pick up this job" for more than 5 minutes.
- Health checks report runner stopped.

## 2) Check Interactive Process

Runner is expected as interactive `Runner.Listener` process.

```powershell
Get-Process -Name "Runner.Listener" -ErrorAction SilentlyContinue
```

If absent, runner process is down.

## 3) Restart Procedure

Primary restart path:

1. Open `C:\actions-runner`.
2. Run `run.cmd` (interactive).
3. Wait 15 seconds.
4. Validate via API:

```powershell
curl -H "Authorization: Bearer TOKEN" https://api.github.com/repos/KevinSGarrett/Fiverr/actions/runners
```

## 4) Service Restart Alternative

If admin session is available and service exists:

```powershell
Start-Service "actions.runner.*"
```

Use service mode only where permissions permit.

## 5) Confirm Online

Online confirmation criteria:

- API payload includes runner `status=online`.
- observed within ~20 seconds after startup.

## 6) Scheduled Task Recovery

If startup task failed, re-register:

```powershell
Register-ScheduledTask -Action (New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c C:\actions-runner\run.cmd") -Trigger (New-ScheduledTaskTrigger -AtStartup) -TaskName "GitHubActionsRunner" -Force
```

## 7) If Runner Cannot Come Online

1. Inspect `C:\actions-runner\_diag\` logs.
2. Verify `.credentials` and `.credentials_rsaparams` are present and valid.
3. Re-register runner if credentials expired.
4. Re-run API check to confirm online status before unblocking dispatch.

