# AGENT_F_EDGE_CASE_SPEC

## Zone
Agent F commits only:
- `tests/unit/test_live_pilot_edge.py`
- `docs/cycle_reports/CYCLE_074_AGENT_F.md`

## Required Test Inventory: 55 tests total

### 1) `TestPilotLoggerEdgeCases` (10)
- error rate stop threshold behavior
- sequential request integrity
- zero-request bundle validity
- parent directory creation
- stage breakdown aggregation
- multi-instance continuity
- extra key merge behavior
- credit summation accuracy
- JSONL validity
- URL truncation at 200 chars

### 2) `TestRunLivePilotEdgeCases` (10)
- baseline DB isolation
- session expired stop behavior
- budget exceeded stop behavior
- evidence always on failure
- seed idempotency
- run id present
- single-niche scoping
- evidence path returned
- no credentials in logs
- baseline mtime unchanged

### 3) `TestCollectLiveEdgeCases` (8)
- exit=1 budget exceeded
- exit=1 session expired
- exit=0 success
- required niche enforcement
- error list display
- gig count output
- credit count output
- evidence path output

### 4) `TestLiveValidateEdgeCases` (8)
- skip collection behavior
- evidence on scoring failure
- stage keys required
- success false when gigs=0
- all 8 stages represented
- scoring failure recorded not hidden
- playbook stage runs on partial failures
- configurable evidence path

### 5) `TestRecommendationsEdgeCases` (5)
- `--live` sets `dry_run=False`
- default remains `dry_run=True`
- live without API key falls back safely
- output includes dry_run mode
- live flag accepted by CLI

### 6) `TestPlaybookEdgeCases` (9)
- no input mutation
- markdown handles all section types
- `has_full_data=True` with recommendation
- handles `None` recommendation
- uses display names
- markdown heading exists
- estimated time in sections
- gig creation has 8 steps
- first orders has 4 strategies primary type

### 7) `TestConfigEdgeCases` (5)
- committed `scrapfly.enabled=False`
- runtime override only in pilot path
- logs contain no API keys
- pilot DB name includes niche id
- pilot DB separated from production path

Every test maps to a TierD-2 condition or failure mode.
