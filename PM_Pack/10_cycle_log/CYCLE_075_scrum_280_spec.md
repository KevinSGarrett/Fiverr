# CYCLE 075 EXECUTABLE SPEC - SCRUM-280

## Objective
SCRUM-280 specifies safe governance metadata extension in `config.yaml` for Cycle 077. The objective is to add non-breaking metadata that can be consumed by planning and review processes without affecting runtime configuration checks. A hard requirement is preserving `collection.scrapfly.enabled=false` unchanged.

## Component Boundaries
- In scope: `config.yaml` comments and safe optional keys under a governance namespace.
- In scope: metadata for cycle id, scope keys, snapshot date, and owner role.
- Out of scope: any key that impacts collectors, scoring, analysis, or runtime behavior.
- Out of scope: toggling live data collection features.

## Data Flow
1. Read existing config and verify protected key values.
2. Define governance metadata schema with optional fields.
3. Insert metadata in a location unlikely to affect parser logic.
4. Re-check protected key invariants and yaml readability.
5. Publish update with explicit non-breaking note in cycle log.

## Error Handling
- Protected key accidental change detected: abort update and restore baseline.
- Parser incompatibility risk for unknown keys: prefer comments-only fallback.
- Metadata field ambiguity: default to string values and documented enums.
- Duplicate governance block: update existing block in place.

## API Contract (Governance Interfaces)
```python
def assert_protected_config_values(config: dict) -> list[str]: ...
def build_cycle_governance_metadata(cycle_id: str, keys: list[str]) -> dict: ...
def inject_governance_metadata_yaml(config_text: str, metadata: dict) -> str: ...
def validate_non_breaking_metadata(config_text: str) -> list[str]: ...
```

## Validation Strategy
- Invariant check: `collection.scrapfly.enabled` remains `false`.
- Parse check: YAML structure remains valid and human-readable.
- Scope check: metadata is strictly governance-focused.
- Compatibility check: no existing required runtime fields are altered.

## Required Tests
1. `test_scrum_280_preserves_scrapfly_disabled_invariant`
2. `test_scrum_280_governance_metadata_is_optional_and_nonbreaking`
3. `test_scrum_280_yaml_structure_valid_after_update`
4. `test_scrum_280_runtime_keys_unmodified`

## AC / DoD Mapping
| AC | Implementation Signal | DoD Evidence |
|---|---|---|
| AC-1: Governance metadata added | New comments/keys in config | `config.yaml` diff |
| AC-2: Protected toggle unchanged | Value remains false | Config inspection |
| AC-3: No runtime impact | Existing sections untouched | Targeted diff |
| AC-4: Traceability improved | Cycle metadata includes key list | Governance block |

## Architecture Decision and Tradeoff Notes
Decision: add metadata via optional namespace/comments instead of new required schema fields. Tradeoff: lower strictness, significantly lower break risk. Decision: treat protected toggles as immutable invariants during governance edits. Tradeoff: limits optimization opportunities, but protects production safety posture. Decision: keep key list in metadata as compact CSV-like string for readability. Tradeoff: less structured parsing, but easier manual verification during review.
