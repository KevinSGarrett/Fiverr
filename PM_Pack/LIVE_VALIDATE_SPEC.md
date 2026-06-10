# LIVE_VALIDATE_SPEC

## Command
`python run.py live-validate`

## CLI Options (7)
1. `--niche` (default `python_automation`)
2. `--budget` (int, default 500)
3. `--database-url` (optional)
4. `--config-path` (default `config.yaml`)
5. `--skip-collection` (flag, default False)
6. `--evidence-path` (default `data/live_validation_evidence.json`)
7. `--log-path` (default `data/live_pilot_log.jsonl`)

## Stage Contract (8 stages)
1. Pre-flight: validate credentials/session prerequisites.
2. Collection: run live pilot unless skip flag.
3. DB validation: `_validate_pilot_db_state` returns counts dict.
4. Scoring: call `run_pipeline(mode="full")`, capture failures in evidence.
5. Recommendations: `_run_live_recommendations` returns `{count, dry_run}`.
6. Export: create `data/exports/live_pilot/`, record file count.
7. Playbook: `_generate_playbook_from_live_data` returns `{success, has_full_data, sections_count}`.
8. Evidence: always write evidence JSON.

## Helper Functions
- `_validate_pilot_db_state(db_url: str) -> dict[str, int]`
- `_run_live_recommendations(config_path: str, db_url: str) -> dict[str, object]`
- `_generate_playbook_from_live_data(niche_id: str, db_url: str) -> dict[str, object]`
- `_resolve_pilot_db_url(database_url: str | None, niche_id: str) -> str`

## Evidence Success Logic
`evidence.success = (db_validation.gigs > 0) and (scoring.success is True)`

## Acceptance Criteria
- AC-1: `--skip-collection` bypasses stage 2 cleanly.
- AC-2: evidence is written even when stage 4 or 5 fails.
- AC-3: `evidence.success` is false when gigs count is zero.
- AC-4: evidence includes all stage keys.
- AC-5: command exit code reflects success state.

## Test Requirement
- `TestLiveValidateCommand` includes minimum 3 tests.

## Production Readiness
Enables V-5 and V-6 staging credits after real execution evidence.
