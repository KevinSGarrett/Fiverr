# CYCLE 062 — AGENT D HANDOFF

## Execution Order

D runs after all agents complete:
- A
- B
- E
- C
- F

## D Core Responsibility

Final governance, attribution, CI/risk adjudication, and squash merge closeout.

## G1 Comprehensive Attribution Audit

Enumerate every commit in `base_sha..HEAD` and validate zone compliance:

- B: only `src/` + `tests/` + B report
- E: only E report (no `src/`)
- C: only C report
- F: only `tests/` + F report
- A: PM/docs governance artifacts only

Any out-of-zone commit requires explicit NO-GO or documented governance override.

## §12.3 Operational Playbook (Mandatory)

- If PR size is large (expected for Wave 9), apply `override:large-pr`.
- Run Codex/Review query pass twice; include both raw JSON payloads in D report.
- Resolve all unresolved review threads (hard gate).
- Treat `codecov/patch` as advisory; `codecov/project` and coverage floor remain blocking.
- Handle `mergeable_state`:
  - `clean` => proceed
  - `unstable` => proceed with documentation
  - `blocked` => stop

## Independent Gate Re-Checks

D independently revalidates before merge:

- PRAGMA/schema checks for `price_analysis`, `niche_price_analysis`, `pricing_snapshots`
- Dashboard demo-data reference check (`build_dashboard_demo_data` must be absent)
- Golden parity anchor check
- Coverage floor check

## Jira and Merge Closeout

After successful squash merge:

- Transition `SCRUM-1021` to Done (`id: 41`)
- Transition `SCRUM-1022` to Done (`id: 41`)
- Post closeout comments with PR number and squash SHA

## Hydration Header Update

Record:
- `CYCLE_CURRENT=063`
- C062 squash SHA
- Updated G-D progress note

## D Report Deliverable

`docs/cycle_reports/CYCLE_062_AGENT_D.md` must include:
- full attribution table
- dual codex query evidence
- CI gate summary
- independent gate evidence
- merge record and Jira completion evidence
- final GO/NO-GO statement
