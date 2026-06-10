# LIVE_PILOT_SPEC

## Primary API
`async def run_live_collection_pilot(niche_id: str, budget_credits: int = 500, database_url: str | None = None, config_path: str = "config.yaml", log_path: str = "data/live_pilot_log.jsonl", evidence_path: str = "data/live_validation_evidence.json") -> dict[str, Any]`

Constraints:
- One niche per run (`niche_id` required).
- Budget must be positive integer.
- Pilot DB must be isolated from baseline production DB.

## Return Schema (11 keys)
- `run_id: str`
- `niche_id: str`
- `db_url: str`
- `budget_credits: int`
- `success: bool`
- `credits_used: int`
- `gigs_collected: int`
- `search_results: int`
- `keywords_found: int`
- `errors: list[str]`
- `stop_reason: str | None`

## Seed Helper
`def _seed_pilot_niche(niche_id: str, engine) -> None`
- Idempotent niche bootstrap from config source.
- Ensures target niche row exists in pilot DB.

## TierD-2 Condition Mapping
- A one niche: filter runtime config niches to exactly `niche_id`.
- B ceiling: set `cost_budget_credits=budget_credits`.
- C logging: instantiate `PilotLogger`; record requests and evidence.
- D stop budget: `ScrapFlyRateLimitError -> stop_reason="budget_exceeded"`.
- E pilot DB: `db_url` contains `live_pilot` and niche id; never baseline path.

## Stop Conditions
1. `session_expired`
   - Trigger: `SessionManager.ensure_session()` raises.
   - Response: `success=False`, stop reason set, evidence written.
   - Recovery: relogin then retry.
2. `budget_exceeded`
   - Trigger: `ScrapFlyRateLimitError`.
   - Response: stop immediately, evidence written.
   - Recovery: review evidence and adjust budget.
3. `block_rate_exceeded`
   - Trigger: evidence bundle computes `block_rate > 0.5`.
   - Response: `stop_conditions_triggered=True` and fail-safe stop.
   - Recovery: cooldown/tune ASP settings.
4. `pipeline_error`
   - Trigger: unexpected exception from collection pipeline.
   - Response: `success=False`, record error, evidence written.
   - Recovery: inspect errors and fix root cause.

## Evidence Requirement
Evidence bundle is always written, including failure paths.

## Acceptance Criteria
- AC-1: `session_expired` path returns `success=False` with stop reason.
- AC-2: `budget_exceeded` path returns stop reason and writes evidence.
- AC-3: `block_rate_exceeded` is surfaced in evidence.
- AC-4: pilot DB is isolated and never equals baseline DB.
- AC-5: evidence file exists on success.
- AC-6: evidence file exists on failure.

## Test Requirement
- `TestRunLiveCollectionPilot` includes minimum 6 tests.

## Production Readiness
Provides V-3 enablement path for first live collection validation.
