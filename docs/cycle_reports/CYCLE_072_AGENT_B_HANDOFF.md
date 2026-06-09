# CYCLE 072 - AGENT B HANDOFF

## Scope

Implement S7.8 Stage 16 Orchestration in:

- CREATE: `src/discovery/stage16.py`
- UPDATE: `run.py` (add discovery CLI entrypoint)
- CREATE: `tests/unit/test_discovery_stage16.py` (>=30 tests, with F additions layered later)

Do not modify `DiscoveryOrchestrator` class behavior in `src/discovery/orchestrator.py`.

## Required Public API

```python
def run_discovery_cycle(db, run_id, config=None) -> DiscoveryCycleLog: ...
def _select_modes(config=None, run_number=None) -> list[str]: ...
```

## Stage16 Module Contract

- No LLM calls in S7.8 orchestration path.
- No new migration/table/column.
- Uses existing S7.2-S7.7 functions and existing `DiscoveryCycleLog`.
- Writes one cycle log per full run across all niches.

## Required Orchestration Sequence

1. `evaluate_discovery_results(run_id, db)`
2. `build_feedback_summary(db)`
3. `get_pending_discovery_keywords(db)`
4. `_select_modes(config, run_number)`
5. `generate_*_hypotheses()` for each selected mode
6. budget gate filter and cap
7. `process_accepted_hypotheses(filtered, run_id, db)`
8. create `DiscoveryCycleLog` and commit once
9. return `DiscoveryCycleLog`

## Mode Selection Logic (Hard Requirement)

- Base modes always:
  - `adjacent_keyword`
  - `gap_exploit`
  - `trend_chase`
- Add `adjacent_niche` when `run_number % 3 == 0`.
- If `config.discovery.enabled_modes` exists, intersect with scheduled modes.

Expected schedule:

- run `0` -> 4 modes
- run `1` -> 3 modes
- run `2` -> 3 modes
- run `3` -> 4 modes
- run `None` -> 3 modes

## Budget Gate Logic (Exact Pattern)

```python
min_confidence = (config or {}).get("discovery", {}).get("min_hypothesis_confidence", 0.50)
max_hypotheses = (config or {}).get("discovery", {}).get("max_hypotheses_per_run", 15)

confident = [
    h
    for h in all_hypotheses
    if getattr(h, "accepted", False)
    and (getattr(h, "specificity_score", 0.0) or 0.0) >= min_confidence
]
accepted = confident[:max_hypotheses]
hypotheses_gated = len(all_hypotheses) - len(confident)
```

## Niche Iteration Contract

- Iterate all 9 niches from `NICHE_VALIDATION_CONFIG`.
- Aggregate generated/accepted stats across all niches into one cycle log.
- Synchronous execution is acceptable.

## Input-Shaping Guidance for Generators

- `generate_adjacent_keyword_hypotheses`: feed seed keyword texts and existing keyword set.
- `generate_gap_exploit_hypotheses`: feed score/opportunity signal rows.
- `generate_trend_chase_hypotheses`: feed trend and velocity signal rows.
- `generate_adjacent_niche_hypotheses`: feed niche relationships/slugs.

## DiscoveryCycleLog Storage Contract

Use JSON strings for list/dict fields:

```python
modes_run=json.dumps(modes_run)
feedback_summary=json.dumps(feedback_dict)
```

Required values:

- `run_id`: input run ID
- `hypotheses_generated`: pre-gate count
- `hypotheses_gated`: filtered-out count
- `hypotheses_accepted`: `insert_result["inserted"]`
- `total_cost_usd`: `0.0`
- `cycle_at`: UTC timestamp

## CLI Wiring Contract

Update `run.py` to invoke `run_discovery_cycle` from a discovery command/mode.

Required behavior:

- accept optional `--run-id` (generate when absent)
- optional niche scoping may be supported if consistent with existing CLI patterns
- preserve dry-run sentinel behavior currently enforced in CLI pathways

## Non-Functional Gates

- Keep golden parity unchanged (`kw=110 => 62.7 / 1.0 / CONDITIONAL_GO`).
- Keep overall suite coverage >=90%.
- Add >=30 stage16 tests.
- Do not alter migration files for C072.
