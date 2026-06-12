# Model Drift Incident Playbook

## 1) Detection Signals

Model drift exists when runtime behavior no longer matches policy targets (Codex 5.3 medium for Cursor, Sonnet 4.6 for Claude PM review). Confirm drift with multiple signals:

1. `cursor_model_state.json` shows `observed_model` different from `Codex 5.3`.
2. `valid_until` is expired.
3. Health checks report model status as NOTVERIFIED.
4. Agent output quality shifts dramatically and no longer follows expected policy framing.
5. Agent report explicitly references the wrong model or auto-selection.

## 2) Immediate Response

Stop active dispatch if drift is confirmed. Write incident marker `BLOCKED_MODEL_DRIFT.md` in incident reports and quarantine output created under wrong model assumptions. Do not commit work generated under an invalid model policy state.

## 3) Cursor Re-Verification

In Cursor settings:

- model = Codex 5.3
- effort = medium
- Auto model selection = DISABLED
- fallback model = DISABLED

Re-check the model picker before resuming automation.

## 4) Update State File

Run:

```powershell
powershell -File C:\AI_Runner\scripts\verify_model_selection.ps1
```

This refreshes `cursor_model_state.json` and sets status to VERIFIED when checks pass.

## 5) Update Freshness

Set freshness policy to now + 7 days in state:

- `valid_until` must be updated by verification script or controlled state writer.
- If freshness cannot be extended, hold dispatch and escalate.

## 6) Resume Decision

- Drift affected less than one task: re-run that task under verified model.
- Drift affected multiple tasks: re-run the entire agent scope for deterministic recovery.

## 7) Claude Drift Handling

If Claude PM review was done under the wrong model, mark the review as ADVISORYONLY. Re-run post-cycle review with verified subscription model policy before using the result as governance evidence.

## 8) Escalation

If Cursor repeatedly reverts to the wrong model:

1. Suspend autonomous dispatch.
2. Alert Kevin with timestamped evidence.
3. Attach `cursor_model_state.json`, last verification output, and recent incident notes.
4. Resume only after explicit policy reconfirmation and fresh verification.

This decision tree is mandatory because silent drift creates non-deterministic quality and breaks governance trust.

## Operational Checklist

Use this checklist before closing a model drift incident:

- [ ] Incident file created with timestamps.
- [ ] Wrong-model work identified and quarantined.
- [ ] Cursor picker revalidated (model/effort/auto/fallback).
- [ ] Verification script rerun and status set to VERIFIED.
- [ ] `valid_until` refreshed and confirmed future-dated.
- [ ] Affected tasks rerun according to resume decision tree.
- [ ] Cycle report updated with drift event and disposition.

## Repeat Drift Mitigation

If drift repeats in the same week:

1. Increase verification cadence to every dispatch batch.
2. Require manual sign-off before Stage transitions.
3. Capture pre-dispatch model snapshot in every cycle report.
4. Audit Cursor updates/plugins changed since last stable run.

These controls reduce recurrence and provide defensible governance evidence when automation is audited.

