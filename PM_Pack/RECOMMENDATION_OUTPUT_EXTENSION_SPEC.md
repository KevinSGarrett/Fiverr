# RECOMMENDATION_OUTPUT_EXTENSION_SPEC

## Current State
`RecommendationOutput` contains existing recommendation payload fields for prior waves.

## C074 Extension
Add two optional fields:
- `profile_optimization: Optional[dict] = None` (Wave 11 S8.2 / C076)
- `visual_recommendations: Optional[dict] = None` (Wave 11 S8.1 / C075)

## Backward Compatibility
- Both default to `None`.
- Existing callers remain valid without payload changes.
- No DB migration required (application-layer model extension only).

## Completeness Ratio Impact
- Denominator expands from `N` to `N+2`; existing scoring logic must treat missing new fields as optional.

## Why `Optional[dict]`
- Preserves schema flexibility for future per-wave nested structures.
- Avoids premature rigid typing during staged delivery.

## Required Tests
- `test_profile_optimization_defaults_none`
- `test_visual_recommendations_defaults_none`

## Production Readiness
Connects C074 foundations to planned S8.1 and S8.2 implementations.
