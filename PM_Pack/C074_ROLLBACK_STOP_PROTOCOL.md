# C074_ROLLBACK_STOP_PROTOCOL

## Stop Condition 1: `budget_exceeded`
- Trigger: `ScrapFlyRateLimitError` from collection pipeline.
- Response: `success=False`, `stop_reason=budget_exceeded`, evidence written.
- Recovery: inspect credits used, optionally retry with larger budget.

## Stop Condition 2: `session_expired`
- Trigger: session ensure/login check raises.
- Response: `success=False`, `stop_reason=session_expired`, evidence written.
- Recovery: `python run.py relogin`, then retry.

## Stop Condition 3: `block_rate_exceeded`
- Trigger: evidence computes `block_rate > 0.5`.
- Response: `stop_conditions_triggered=True` in evidence and fail-safe stop.
- Recovery: adjust timing/ASP strategy, retry later.

## Stop Condition 4: `pipeline_error`
- Trigger: unexpected collection exception.
- Response: `success=False`, `stop_reason=pipeline_error`, errors list populated.
- Recovery: debug from evidence `errors` and JSONL entries.

## Data Safety
- Pilot DB: `data/live_pilot_*.db` is throwaway and can be deleted.
- Production baseline: `data/cycle037_live.db` is never touched by pilot flow.
- JSONL log excludes credentials and stores request metadata only.

## Rollback Procedure
1. Stop process.
2. Preserve evidence and logs for forensic review.
3. Optionally delete `data/live_pilot_*.db` to reset pilot state.
4. Keep baseline DB untouched.
