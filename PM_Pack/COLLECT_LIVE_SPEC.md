# COLLECT_LIVE_SPEC

## CLI Signature
`python run.py collect-live`

Required/optional options:
1. `--niche / --niche_id` (required, str, no default)
2. `--budget` (int, default 500, show_default=True)
3. `--database-url` (str | None, default None)
4. `--config-path` (str, default `config.yaml`, show_default=True)
5. `--log-path` (str, default `data/live_pilot_log.jsonl`, show_default=True)
6. `--evidence-path` (str, default `data/live_validation_evidence.json`, show_default=True)

## Docstring Requirements
Must explicitly mention:
- TierD-2 controlled pilot constraints.
- Prerequisites.
- Example command.

## Exit Contract
- Success: `SystemExit(0)`.
- Failure or stop condition: `SystemExit(1)`.
- Missing required arg from Click parser: exit code `2`.

## Output Contract
Success stdout includes:
- niche id
- gigs collected
- credits used/budget
- evidence path

Failure stderr includes:
- explicit `stop_reason`
- any surfaced error messages

## Prerequisites
1. `SCRAPFLY_API_KEY` set.
2. Valid session (`python run.py relogin`).
3. One-niche rule enforced by required `--niche`.

## Acceptance Criteria
- AC-1: missing `--niche` exits with code 2.
- AC-2: default `--budget` is 500.
- AC-3: success exits 0 and reports gigs count.
- AC-4: `budget_exceeded` exits 1 and prints stop reason.
- AC-5: `session_expired` exits 1.

## Test Requirement
- `TestCollectLiveCommand` includes minimum 4 tests.

## Production Readiness
Removes live collection CLI blocker and contributes +2% build-side E2E credit.
