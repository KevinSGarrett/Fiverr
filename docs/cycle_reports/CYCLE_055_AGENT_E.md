# CYCLE 055 AGENT E — SRDI R6 Discovery Relevance Gates Validation

## One-line status

C055 R6 validation **CONCERN/BLOCKED HYBRID** — Gate 1 and Gate 2 were validated offline against realistic Appendix-D style fixtures, including candidate-level evidence and rejection-rate math, but true end-to-end Gate 3/4 validation remains blocked by missing runnable discovery orchestration + missing persisted `discovery_outcomes` table in throwaway DB.

## Scope and constraints followed

- Docs-only execution (`ZERO src/`, `ZERO tests/` edits by Agent E).
- Golden baseline remained read-only and unchanged.
- Throwaway DB used for all write-capable commands: `sqlite:///data/cycle055_discovery_validation.db`.
- No parity DB usage.
- No live ScrapFly run.

## Preflight and readiness

- Branch: `cycle/055/integration` (up to date with origin).
- B handoff for Cycle 055 is still absent at `docs/cycle_reports/HANDOFF_B.md` (latest B handoff file present is `CYCLE_054_HANDOFF_B.md`).
- `CYCLE_055_PLAN.md` Appendix-D candidate matrix used as canonical source.

Current R6 code surfaces now present on branch:

- `discovery.enable_relevance_gates` exists in config model and `config.yaml` (default false).
- `src/analysis/pre_validator.py` exists.
- `_gate_hypotheses` exists in `src/discovery/hypothesis.py`.

Remaining readiness blockers:

- `src/discovery/orchestrator.py::run_cycle` remains a stub (no end-to-end discovery gate execution path).
- `init-db` throwaway DB still does not create `discovery_outcomes` table; only `discovery_candidates`, `discovery_hypotheses`, `discovery_cycle_logs` are present.

## Baseline safety proof (required)

### Checkpoint (before validation)

Read-only query used:

`select id, scored_at, final_score, confidence_modifier, tag from keyword_scores where keyword_id=110 order by id desc limit 3`

Checkpoint rows:

- `(8590, '2026-05-30 23:19:30.996548', 62.7, 1.0, 'CONDITIONAL_GO')`
- `(8461, '2026-05-30 23:18:48.934670', 62.7, 1.0, 'CONDITIONAL_GO')`
- `(8332, '2026-05-30 22:22:32.871527', 62.7, 1.0, 'CONDITIONAL_GO')`

### Closeout re-read

Same read-only query; rows are byte-identical:

- `(8590, '2026-05-30 23:19:30.996548', 62.7, 1.0, 'CONDITIONAL_GO')`
- `(8461, '2026-05-30 23:18:48.934670', 62.7, 1.0, 'CONDITIONAL_GO')`
- `(8332, '2026-05-30 22:22:32.871527', 62.7, 1.0, 'CONDITIONAL_GO')`

Result: **baseline untouched**.

## Validation matrix

| Gate | What was tested | Toggle | Result | Evidence ref |
| ---- | --------------- | ------ | ------ | ------------ |
| G1 specificity | low-specificity / drift hypotheses rejected with reasons | ON | PASS (offline logic) | `data/cycle055_gate_eval.json` |
| G1 specificity | on-niche hypotheses kept | ON | PASS (offline logic) | `data/cycle055_gate_eval.json` |
| G2 dry-run | VALID for on-topic candidate sets | ON | PASS (offline logic) | `data/cycle055_gate_eval.json` |
| G2 dry-run | GHOST/CONTAM verdicts for off-topic sets | ON | CONCERN | Some Appendix-D ghost terms rejected at G1 before G2 |
| G2 insert semantics | VALID inserted; rejected not inserted | ON | PASS (simulated gate semantics) | `data/cycle055_gate_eval.json` |
| G3 outcomes | ghost/contam persisted as INVALID vs MISS | ON | BLOCKED | `discovery_outcomes` table unavailable on throwaway init-db |
| G4 feedback | INVALID/CONTAM excluded from learning | ON | BLOCKED | no runnable feedback gate path in discovery orchestrator |
| Parity | OFF legacy insert-all on same set | OFF | PASS (offline parity simulation) | `data/cycle055_gate_eval.json` |
| Rejection band | representative batch in 20–40% | ON | PASS | 3/12 = 0.25 |
| Baseline | kw=110 unchanged pre/post | n/a | PASS | checkpoint == closeout |

## Candidate-level evidence (Appendix-D batch)

Evidence artifact: `data/cycle055_gate_eval.json` (`appendix_d_rows` and `representative_rows`).

Highlights:

- ON-niche candidates: 9/9 evaluated as `VALID` with RSV `1.0`.
- Drift candidates: rejected at Gate 1 with reason `specificity 0.67 < 0.75`.
- Ghost candidates: mixed behavior:
  - Some passed G1 then became `GHOST` at G2 (`product strategy`, `workflow automation`, `AI agent`, `OpenAI help`, `agent development`).
  - Others were blocked at G1 (`support`, `python services`, `automation`, `scraping`), which creates a staging-concern vs expected Appendix-D flow.

## Rejection-rate calculations

### Appendix-D stress set (27 candidates, 9 niches x 3)

- Denominator: `27`
- Numerator: `18` (`Gate1=13` + `Gate2=5`)
- Rejection rate: `18/27 = 0.6667`
- Interpretation: stress-set intentionally over target (expected to be high); **not the Tier-1 representative number**.

### Representative batch (12 candidates, support_kb_readiness)

- Composition: 9 on-niche + 2 drift + 1 ghost
- Denominator: `12`
- Numerator: `3`
- Rejection rate: `3/12 = 0.25`
- Target comparison (20–40%): **in band**.

## Toggle-OFF parity contrast

Using same batches in offline parity simulation (legacy insert-all behavior):

- Appendix-D set: ON inserted `9`, OFF inserted `27`.
- Representative set: ON inserted `9`, OFF inserted `12`.

## Gate 3 / Gate 4 block details

Gate 3 and Gate 4 could not be validated end-to-end because:

1. Discovery orchestration entrypoint remains stub (`run_cycle` does not execute gate pipeline).
2. Throwaway DB created via `run.py init-db` does not include `discovery_outcomes`, preventing persistence-status verification on the isolated DB.
3. Current schema/model semantics use booleans (`is_invalid`/`is_contaminated`) and do not expose a documented `status` value split (`INVALID` vs `MISS`) as required by this cycle prompt.

## Findings for Agent B (Appendix-F format)

### FINDING E-1 (route to Agent B)

- Gate: G3/G4 integration
- Symptom: `DiscoveryOrchestrator.run_cycle` is still stubbed and does not run full discovery-gate flow.
- Expected: runnable end-to-end path for G1→G4 with persisted outcomes and feedback exclusion.
- Repro: inspect `src/discovery/orchestrator.py` and execute discovery entrypoint; no gate execution occurs.
- Suspected area: `src/discovery/orchestrator.py`.
- Severity: **blocking**.

### FINDING E-2 (route to Agent B)

- Gate: G3 outcome persistence
- Symptom: throwaway DB init lacks `discovery_outcomes` table.
- Expected: outcome persistence table queryable in throwaway DB for validation.
- Repro: query throwaway DB tables after `init-db`; only `discovery_candidates`, `discovery_hypotheses`, `discovery_cycle_logs`.
- Suspected area: model import/metadata registration + init-db bootstrap coverage.
- Severity: **blocking**.

### FINDING E-3 (route to Agent B)

- Gate: G3 semantics
- Symptom: current model shape exposes booleans, but no explicit status value split (`INVALID` vs `MISS`) in throwaway runtime path.
- Expected: explicit INVALID vs MISS outcome semantics per prompt/plan.
- Repro: inspect `src/models/discovery_outcome.py`; compare with required evidence query contract.
- Suspected area: outcome schema contract + recorder mapping.
- Severity: **blocking**.

### FINDING E-4 (route to Agent B)

- Gate: G1→G2 routing behavior
- Symptom: several Appendix-D ghost samples are rejected at G1 (`specificity 0.50 < 0.75`) before reaching G2 ghost classification.
- Expected: representative ghost path remains available to validate G2/G3 behavior.
- Repro: rows in `data/cycle055_gate_eval.json` for `support`, `python services`, `automation`, `scraping`.
- Suspected area: `src/discovery/hypothesis.py::_gate_hypotheses` threshold/rule strictness.
- Severity: **concern** (may over-block intended Gate 2 coverage).

### FINDING E-5 (route to Agent B / PM)

- Gate: Preflight comparability
- Symptom: missing `docs/cycle_reports/HANDOFF_B.md` for Cycle 055.
- Expected: B handoff present with exact toggle/entrypoint/status contracts and reference SHA.
- Repro: file lookup in `docs/cycle_reports` shows no Cycle-055 B handoff.
- Suspected area: delivery artifact gap.
- Severity: **blocking for strict comparability claims**.

## Command / isolation audit

| Command intent | DB used | Config path | Isolation status |
| ---- | ---- | ---- | ---- |
| Baseline checkpoint query | `data/cycle037_live.db` (read-only) | none | safe |
| Throwaway init | `sqlite:///data/cycle055_discovery_validation.db` | default | safe |
| Throwaway schema query | `data/cycle055_discovery_validation.db` | none | safe |
| Offline gate harness | no DB writes | none | safe |
| Baseline closeout query | `data/cycle037_live.db` (read-only) | none | safe |

No writes were executed against:

- `data/cycle037_live.db`
- `data/parity_off.db`
- `data/parity_on.db`

## ScrapFly / live policy outcome

- `SCRAPFLY_API_KEY` presence: confirmed present (value never printed).
- Live collection executed: **No**.
- Approximate credits used: **0**.
- Evidence basis:
  - G1/G2 + rejection rates + parity: offline logic validation.
  - G3/G4: blocked by missing runnable path/table on throwaway DB.

## Final verdict for D

**CONCERN/BLOCKED** — enough evidence exists to show Gate 1/2 behavior and representative rejection-rate in-band (`3/12 = 0.25`) under offline harness conditions, with baseline safety intact; however, full required end-to-end validation is still blocked until B wires orchestrator + outcome persistence + feedback path and publishes Cycle-055 `HANDOFF_B.md`.
