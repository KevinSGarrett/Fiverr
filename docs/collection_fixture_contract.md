# Collection Fixture Contract (Dry-Run Only)

This contract defines the fixture schema and safety rules for `src/collection` dry-run workflows.

## Scope

- Applies to `run_collection_dry_run` and collection parsers/loaders.
- Fixtures must be local files committed under `tests/fixtures/collection/` or created in test temp directories.
- Dry-runs must remain deterministic and side-effect free except writing the requested checkpoint file.

## Required Core Inputs

- **Seed keywords**: at least one non-empty keyword string is required for a successful run.
- **Checkpoint path**: must be writable to persist queue/stage summary output.
- **Stage summary**: output must include `stage_counts` with:
  - `stage_1_keyword_expansion`
  - `stage_2b_autocomplete`
  - `stage_2_search_plan`
  - `stage_4_gig_detail`
  - `stage_5_seller_profile`
  - `stage_7_checkpoint_metadata`
  - `stage_8_pacing_decisions`

## Optional Fixture Inputs

- `autocomplete_fixture_path` JSON object with `suggestions` list.
- `gig_detail_fixture_path` HTML payload for gig detail extraction.
- `seller_profile_fixture_path` HTML payload for seller profile parsing.
- `external_signal_fixture_path` JSON array of aggregate external signal records.
- `community_signal_fixture_path` JSON array of aggregate community signal records.

## Missing-Data Behavior (Allowed and Expected)

- Missing optional fixture paths may fail with a controlled `fixture_unavailable` error.
- Empty optional fixture payloads must **not** fabricate records.
- Empty signal arrays must emit deterministic warnings and keep stage counts at `0`.
- Malformed HTML must return parsed objects with warnings/errors instead of raising uncontrolled exceptions.
- Non-positive candidate caps must be normalized to a safe positive deterministic cap and emit a warning.

## Forbidden Live Behaviors

- No browser automation in collection dry-run tests.
- No login/session state usage.
- No external HTTP/network calls from collection dry-run path.
- No runtime DB writes for fixture-only collection smoke tests.

## Adding New Fixtures Safely

- Keep fixtures minimal and deterministic; avoid timestamps that vary at runtime.
- Use aggregate/sanitized text only; never include personal handles, emails, or account IDs.
- For any new fixture type:
  - add parser/loader validation,
  - add at least one warning-path test,
  - add one happy-path test,
  - ensure `stage_counts` representation is updated if a new required stage is introduced.
- Prefer local relative fixture paths and temporary files in tests; do not fetch fixture data from the web.
