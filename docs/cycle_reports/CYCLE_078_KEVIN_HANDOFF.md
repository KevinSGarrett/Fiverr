# Cycle 078 — Kevin Action Items

## REQUIRED BEFORE CYCLE 079 DISPATCH

1. Re-authenticate GitHub CLI on this machine:
   - `gh auth login -h github.com`
   - Re-run PR creation for `cycle/078/integration`.

2. Re-verify Cursor model before next dispatch window:
   - `powershell C:\AI_Runner\scripts\verify_model_selection.ps1`
   - confirm `C:\AI_Runner\state\cursor_model_state.json` remains `VERIFIED` and unexpired.

3. Confirm Jira token naming in runner secrets:
   - Must be `JIRA_API_TOKEN=...` (not `JIRA_API`, `JIRA_TOKEN`, or `JIRA_KEY`).

4. Obtain and configure `CODECOV_TOKEN`:
   - GitHub repo secrets
   - `C:\AI_Runner\secrets\runner.env` if required for local checks.

## AFTER PR CREATED/MERGED

5. Run post-merge verification:
   - `python automation/ai_cycle_controller.py merge-gate --post-merge --pr <PR_NUMBER>`

6. Run post-merge PM review path and archive artifacts.

## WHAT CYCLE 078 DELIVERED

- PM_Pack policy and catalog integration across agents A/B/E/C.
- Validated prompt generation/promotion and validated-only dispatch path.
- Agent F ops/report/export sanitizer controls and associated tests.
- Agent D merge governance enhancements:
  - pre-merge artifact writer
  - execute-merge artifact SHA guard
  - post-merge verification command path

## System Readiness Assessment (this pass)

- `status-tick`: PASS
- `brain-check`: PASS
- `pm-pack-audit`: PASS
- `compile-policy`: PASS
- `jira-inventory --dry-run`: PASS
- `plan-cycle --dry-run`: PASS
- `validate-prompts --cycle 078`: PASS
- `cursor-smoke`: PASS
- `daily-report`: PASS
- `merge-gate --pr 0 --dry-run`: expected FAIL for placeholder PR context

No unexpected failures in local command suite beyond known blockers (PR auth + full combined coverage gate).
