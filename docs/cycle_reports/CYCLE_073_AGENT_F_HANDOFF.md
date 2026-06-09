# CYCLE 073 - AGENT F HANDOFF

## Scope

F scope is constrained to:

- `tests/` changes only
- `docs/cycle_reports/CYCLE_073_AGENT_F.md`

No `src/`, `config.yaml`, or migration edits from F.

## Required Test Classes

`tests/unit/test_discovery_dashboard.py` must include:

- `TestGetDiscoveryStats`
- `TestGetGoldDiscoveries`
- `TestGetModePerformance`
- `TestRenderDiscoveryPage`
- `TestS79Integration`

## Minimum Test Coverage Targets

- `TestGetDiscoveryStats`: >=5 tests
- `TestGetGoldDiscoveries`: >=6 tests
- `TestGetModePerformance`: >=5 tests
- `TestRenderDiscoveryPage`: >=3 tests
- `TestS79Integration`: >=4 tests
- Total minimum: >=23 tests
- Cycle target: >=30 tests

## Required Edge/Behavior Cases

- stats helper empty DB returns all zeros/None shape
- stats helper real DB values map correctly
- gold helper empty DB returns `[]`
- gold helper field mapping and limit behavior
- gold helper error path returns `[]`
- mode helper groups multiple modes correctly
- mode helper `None` mode normalized to `"unknown"`
- mode helper avg rounding to 3 decimals
- mode helper error path returns `{}`
- render page empty path uses `st.info`
- render page data path uses `st.metric` and `st.dataframe`

## Integration Assertions

- S7.9 helpers coexist with S7.8 stage16 module unchanged.
- No migration introduced.
- Golden parity unchanged.
- Coverage remains >=90%.
