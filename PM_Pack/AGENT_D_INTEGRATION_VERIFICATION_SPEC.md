# AGENT_D_INTEGRATION_VERIFICATION_SPEC

## Zone
Agent D commits governance artifacts only:
- `PM_Pack/HYDRATION_HEADER.md`
- `docs/cycle_reports/CYCLE_074_AGENT_D.md`

## Verification Format
All 55 verifications include:
- command
- expected output
- merge-block criterion on failure

## Categories and Counts

### TierD-2 infrastructure (10)
Validate collect-live/live-validate registration, PilotLogger import, budget default, `--skip-collection`, recommendations `--live`, config guard, requirements, and gitignore live patterns.

### S8.3 scaffold (10)
Validate generator function set, 5 sections, markdown export behavior, template presence, playbook command, RecommendationOutput extension, and section builder constraints.

### Test quality (8)
Validate minimum test counts, total suite pass threshold (~5300), coverage >=90, golden parity anchor, and priority regression pack.

### Wave integrity (8)
Validate Wave 10 and 9 invariants, dashboard function presence, stage16 bounds, baseline mtime, no migrations, and no S8.1 visual module in C074.

### Governance docs (6)
Validate governance docs exist and current-state metadata is updated without stale placeholders.

### Jira closeout (5)
Validate SCRUM-1036 done, S8.3 done, SCRUM-1037 created, hydration cycle update, and E2E readiness band recorded.

### Post-merge instructions (4)
Validate D report includes live-validate command, budget ceiling, evidence path, and staged credit explanation.

### Code quality (4)
Validate no SUPERSEDED markers, no forced scrapfly true in committed config, no migrations, and no out-of-scope modules.

Total = 55 merge-gating verifications.
