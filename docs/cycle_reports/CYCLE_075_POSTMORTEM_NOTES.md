# CYCLE 075 Postmortem Notes

## What went well
- Core governance checks (`brain-check`, `pm-pack-audit`) pass locally.
- TierD-2 gate language is explicit and score-credit mapping is clear.
- Daily report now includes a dedicated Model Status section.

## What could be faster
- GH/Jira evidence collection should fail fast with clearer auth diagnostics.
- Runner smoke workflow evidence currently depends on external auth state; add local fallback logging.
- Ruff command compatibility drift (`--output-format=full`) should be corrected in scripts.

## Risks for next cycle
- Live validation remains blocked by session/auth instability and no successful V-1 artifact.
- Coverage gate remains below 90% for full `automation+src` aggregate in this test mode.
- PM_Pack status contradiction (`frozen` vs `ACTIVE`) can confuse controller logic.
