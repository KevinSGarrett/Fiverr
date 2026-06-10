# C074_COST_CONTROL_PROTOCOL

## Hard Ceiling Enforcement Path
1. `budget_credits` is passed into `run_live_collection_pilot`.
2. Runtime config sets `cost_budget_credits=budget_credits`.
3. ScrapFly stats accumulate `total_credits_used`.
4. When usage exceeds budget, `ScrapFlyRateLimitError` is raised.
5. Pilot catches error, records `stop_reason=budget_exceeded`, writes evidence, returns failure.

## Block and Error Rate Stops
- `block_rate = blocked / max(1, total)`
- `error_rate = errors / max(1, total)`
- Stop flag when `block_rate > 0.5` OR `error_rate > 0.3`.

## Budget Expectations for `python_automation`
- Search pages: ~30 x 10-15 credits = 300-450 credits.
- Gig detail pages: ~30 x 10-15 credits = 300-450 credits.
- 500-credit pilot is sufficient for controlled validation, typically partial/targeted collection.

## Recommended Budget Profiles
- 100 credits: smoke test.
- 300 credits: partial validation.
- 500 credits: full controlled pilot.

## Emergency Stop
- User can terminate process anytime.
- Pilot DB is throwaway; production baseline remains untouched.
- Financial exposure capped by configured budget.
