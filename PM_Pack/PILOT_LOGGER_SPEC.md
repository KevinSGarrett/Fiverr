# PILOT_LOGGER_SPEC

## Purpose
Defines the API contract for TierD-2 persistent request logging used by controlled live collection.

## Data Contract: `PilotRequestLog`
Dataclass with `slots=True` and these 10 fields:
1. `timestamp: str` (UTC ISO-8601)
2. `url: str` (truncate to <=200 chars before persistence)
3. `stage: str` (`stage03_search` | `stage04_gig_detail` | `stage05_seller_profile`)
4. `status_code: int`
5. `credits_used: int`
6. `success: bool`
7. `asp_triggered: bool`
8. `error: str | None`
9. `retry_count: int`
10. `blocked: bool`

## Class Contract: `PilotLogger`

### `__init__(log_path: str = "data/live_pilot_log.jsonl") -> None`
- Creates parent directory if missing.
- Initializes in-memory list `self._entries: list[PilotRequestLog]`.
- Does not delete existing log file.

### `log_request(...) -> None`
Required signature parameters:
- `url, stage, status_code, credits_used, success, asp_triggered=False, error=None, retry_count=0, blocked=False`

Behavior:
- Builds `PilotRequestLog` with current UTC timestamp.
- Truncates URL to 200 chars.
- Appends entry to `self._entries`.
- Appends exactly one JSON line to `log_path` for each call.
- Emits debug log with URL, stage, and credits.

### `write_evidence_bundle(output_path: str, extra: dict | None = None) -> dict`
Required output keys (8):
- `total_requests`
- `total_credits`
- `error_rate`
- `block_rate`
- `stop_conditions_triggered`
- `requests_by_stage`
- `generated_at`
- `entries`

Formulas:
- `block_rate = blocked / max(1, total_requests)`
- `error_rate = errors / max(1, total_requests)`
- `stop_conditions_triggered = (block_rate > 0.5) or (error_rate > 0.3)`

`requests_by_stage` schema:
- `{stage: {count: int, credits: int, errors: int, blocked: int}}`

File behavior:
- Writes formatted JSON to `output_path`.
- Merges `extra` into top-level bundle.
- Returns the full bundle dict.

## TierD-2 Link
Satisfies condition D (log every request) and V-2 operator auditability.

## Acceptance Criteria
- AC-1: `log_request` creates JSONL file when missing.
- AC-2: N `log_request` calls produce exactly N JSON lines.
- AC-3: `block_rate == 0.75` when 3/4 entries are blocked.
- AC-4: `stop_conditions_triggered` is `True` when `block_rate > 0.5`.
- AC-5: `write_evidence_bundle` output contains all 8 required keys.

## Test Requirement
- `TestPilotLogger` includes minimum 6 tests.
