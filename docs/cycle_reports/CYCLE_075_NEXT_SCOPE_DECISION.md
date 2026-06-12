# CYCLE 075 Next Scope Decision

## Primary objective
Unblock V-1 live collection. This yields the fastest deterministic movement (+2% Score 2 credit) and unlocks downstream V-2 and V-3 evidence.

## Agent A scope
PM_Pack state updates and V-1 collection implementation review.

## Agent B scope
Implement `collect-live` live validation evidence writing to `data/live_validation_evidence.json`; close test coverage gaps surfaced in Cycle 075.

## Agent E scope
Run V-1 live validation, capture evidence, and write/update `data/live_validation_evidence.json` and cycle evidence docs.

## Agent C scope
Verify V-1 evidence schema validity and integration-test the V-1 -> Score 2 update path.

## Agent F scope
Raise module coverage for any modules below 90% thresholds.

## Agent D scope
Handle PR lifecycle, Jira transitions, and post-cycle governance closure.

## Jira stories needed (Cycle 076)
1. Validate live Fiverr collection (V-1) with low-volume controlled run and archive artifact.
2. Implement parser validation on live-collected payload (V-2).
3. Execute full live scoring pass and compare against golden anchors (V-3).
4. Add coverage tests for automation/reporting gaps to restore >=90% gate where required.
5. Add integration harness for V-1 -> V-3 evidence ingestion into score update flow.

## Risk
Primary risk is live Fiverr rate limiting and session instability.

## Mitigation
Run `collect-live` at low volume (1-5 keywords), enforce retry/backoff, and capture explicit failure evidence on first pass.


## Jira board snapshot
Live Jira verification found 100 non-done stories; scope should prioritize explicit V-1 and V-2 stories because these were not clearly mapped in open backlog items.
