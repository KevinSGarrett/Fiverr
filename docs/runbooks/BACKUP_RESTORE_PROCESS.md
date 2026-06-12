# Backup and Restore Process

## Backup Strategy Overview

This system uses two backup layers:

1. **Git layer**: GitHub repository is the primary backup for code, PM_Pack, workflows, and versioned docs. Frequent push discipline protects source history.
2. **Local state layer**: `C:\AI_Runner\` stores operational state not in git (runner state, logs, config mirrors, validation artifacts).

Both layers are required for practical disaster recovery.

## Daily Snapshot Procedure

Nightly backup script:

`C:\AI_Runner\scripts\daily_snapshot.ps1`

Expected snapshot content under `C:\AI_Runner\backups\YYYY-MM-DD\`:

- `C:\AI_Runner\state\`
- `C:\AI_Runner\logs\` (retain last 7 days)
- `C:\AI_Runner\config\`
- `C:\AI_Runner\reports\validation\`

Compression and retention:

- use `Compress-Archive` to package each daily snapshot
- keep rolling 7-day snapshot window

## 7-Step Restore Procedure

1. Clone repository:
   `git clone https://github.com/KevinSGarrett/Fiverr C:\Fiverr\Fiverr`
2. Checkout main development branch:
   `git checkout develop`
3. Activate environment:
   `.\.venv\Scripts\activate`
4. Restore latest `C:\AI_Runner\` snapshot from zip to original path.
5. Update `runner.env` with current credentials.
6. Re-register GitHub runner.
7. Run health check:
   `powershell -File C:\AI_Runner\scripts\health_check.ps1`

Resume operations only if health check returns GREEN.

## Restore Without Snapshot

If no snapshot exists:

1. Restore from git clone only.
2. Recreate `C:\AI_Runner\` structure.
3. Re-run model verification:
   `powershell -File C:\AI_Runner\scripts\verify_model_selection.ps1`
4. Re-establish runner registration.
5. Regenerate fresh state files before autonomous dispatch.

This fallback is slower but still recovers core capability.

