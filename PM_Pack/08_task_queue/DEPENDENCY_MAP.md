# DEPENDENCY MAP
# Which stories and epics depend on which other work being complete

---

## Epic-Level Dependencies

```
Epic 01 (Foundation)
  -> Epic 02 (Collection) — needs models, config, CLI
  -> Epic 03 (Analysis) — needs models, config, LLM client
  -> Epic 04 (Scoring) — needs models, config
  -> Epic 08 (Playbook) — needs models
  -> Epic 09 (Dashboard) — needs models, config

Epic 02 (Collection)
  -> Epic 03 (Analysis) — needs collected data
  -> Epic 07 (Discovery) — needs collection workflows

Epic 03 (Analysis)
  -> Epic 04 (Scoring) — needs analysis models/results
  -> Epic 05 (Recommendations) — needs analysis output

Epic 04 (Scoring)
  -> Epic 05 (Recommendations) — needs scores
  -> Epic 06 (Pricing) — needs scores
  -> Epic 09 (Dashboard) — needs scores for display

Epic 05 (Recommendations)
  -> Epic 08 (Playbook) — needs recommendation output
  -> Epic 09 (Dashboard) — needs recommendation display

Epic 10 (Integration) — depends on ALL other epics
```

---

## Story-Level Dependencies (Epic 01 — Foundation)

| Story | Depends On | Why |
|---|---|---|
| S1.1 (Scaffolding) | Nothing | First work to do |
| S1.2 (Config) | S1.1 | Needs directory structure |
| S1.3 (Models) | S1.1, S1.2 | Needs config for DB URL |
| S1.4 (CLI) | S1.1, S1.2, S1.3 | CLI orchestrates models/config |
| S1.5 (Logging) | S1.1 | Needs directory structure |
| S1.6 (Utilities) | S1.1, S1.2 | Utils use config |
| S1.7 (Test Infra) | S1.1, S1.3 | Test fixtures need models |

## Safe Parallel Work (can run simultaneously)

| Agent A (Infra) | Agent B (Collection) | Agent C (Analysis) | Agent D (Dashboard) |
|---|---|---|---|
| Phase 1: Epic 01 core | Phase 1: Epic 01 support | Phase 1: Epic 01 support | Phase 1: Epic 01 support |
| Phase 2: Epic 01 finish | Phase 2: Epic 02 start | Phase 2: Epic 03 start | Phase 2: Epic 09 design |
| Phase 3: Support/utils | Phase 3: Epic 02 main | Phase 3: Epic 04 scoring | Phase 3: Epic 09 shell |
| Phase 4: Epic 06 pricing | Phase 4: Epic 02 finish | Phase 4: Epic 05 recs | Phase 4: Epic 08 playbook |
| Phase 5: Epic 10 integ | Phase 5: Epic 07 support | Phase 5: Epic 07 discovery | Phase 5: Epic 09 widgets |
