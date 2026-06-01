# CYCLE 055 AGENT E — SRDI R6 Discovery Relevance Gates Validation

## One-line status

C055 R6 validation **CONCERN** — full offline end-to-end validation of Gate 1/2/3/4 completed on isolated throwaway DBs, representative rejection rate is in-band (`3/12 = 0.25`), baseline is intact, and findings are limited to gate strictness/semantics and missing Cycle-055 B handoff artifact.

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

Current R6 code surfaces present on branch:

- `discovery.enable_relevance_gates` exists in config model and `config.yaml` (default false).
- `src/analysis/pre_validator.py` exists.
- `_gate_hypotheses` exists in `src/discovery/hypothesis.py`.
- `src/discovery/orchestrator.py::run_cycle` executes relevance-gated flow and feedback aggregation.
- `discovery_outcomes` table is present in throwaway DBs after re-init and was queried for Gate 3 evidence.

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
| G1 specificity | low-specificity / drift hypotheses rejected with reasons | ON | PASS (offline logic) | `artifacts/cycle055_e2e_validation.json` |
| G1 specificity | on-niche hypotheses kept | ON | PASS (offline logic) | `artifacts/cycle055_e2e_validation.json` |
| G2 dry-run | VALID for on-topic candidate sets | ON | PASS (offline logic) | `artifacts/cycle055_e2e_validation.json` |
| G2 dry-run | GHOST/CONTAM verdicts for off-topic sets | ON | CONCERN | Some Appendix-D ghost terms rejected at G1 before G2 |
| G2 insert semantics | VALID inserted; rejected not inserted | ON | PASS (offline logic + DB evidence) | `artifacts/cycle055_e2e_validation.json` |
| G3 outcomes | ghost/contam persisted as INVALID; valid paths remain MISS | ON | PASS (offline e2e) | `artifacts/cycle055_e2e_validation.json` |
| G4 feedback | INVALID/CONTAM excluded from learning | ON | PASS (offline e2e) | `artifacts/cycle055_e2e_validation.json` |
| Parity | OFF legacy insert-all on same set | OFF | PASS (offline parity simulation) | `artifacts/cycle055_e2e_validation.json` |
| Rejection band | representative batch in 20–40% | ON | PASS | 3/12 = 0.25 |
| Baseline | kw=110 unchanged pre/post | n/a | PASS | checkpoint == closeout |

## Candidate-level evidence (Appendix-D batch)

Evidence artifact: `artifacts/cycle055_e2e_validation.json` (`gate1_rows`, `appendix_d_candidate_rows_on`, `db_outcomes_on`).

Highlights:

- ON-niche candidates: 9/9 evaluated as `VALID` with RSV `1.0`.
- Drift candidates: rejected at Gate 1 with reason `specificity 0.67 < 0.75`.
- Ghost candidates: mixed behavior:
  - Some passed G1 then became `GHOST` at G2 (`product strategy`, `workflow automation`, `AI agent`, `OpenAI help`, `agent development`).
  - Others were blocked at G1 (`support`, `python services`, `automation`, `scraping`), which is recorded as a strictness concern.

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

## Gate 3 / Gate 4 evidence details

Gate 3 and Gate 4 were validated in the offline end-to-end harness:

1. Gate 3 outcome rows are persisted in `discovery_outcomes` with rejection reason and RSV (`relevance_score`), and map to `INVALID` vs `MISS` semantics via `is_invalid`.
2. Representative ON run feedback counts (`counted_valid=9`, `counted_invalid=1`, `counted_total=10`) show exclusion of invalid outcomes from learning.
3. Representative OFF run feedback counts (`counted_valid=12`, `counted_invalid=0`, `counted_total=12`) show legacy include-all behavior.

Semantic note for B/PM: current implementation stores INVALID/MISS as boolean flags rather than a string status field; report mapping was derived from those flags.

## Findings for Agent B (Appendix-F format)

### FINDING E-1 (route to Agent B)

- Gate: G1→G2 routing behavior
- Symptom: several Appendix-D ghost samples are rejected at G1 (`specificity 0.50 < 0.75`) before reaching G2 ghost classification.
- Expected: representative ghost path remains available to validate G2/G3 behavior.
- Repro: rows in `artifacts/cycle055_e2e_validation.json` for `support`, `python services`, `automation`, `scraping`.
- Suspected area: `src/discovery/hypothesis.py::_gate_hypotheses` threshold/rule strictness.
- Severity: **concern** (possible over-blocking before pre-validator).

### FINDING E-2 (route to Agent B)

- Gate: G3 semantics contract
- Symptom: implementation stores INVALID/MISS split via booleans (`is_invalid`, `is_contaminated`) instead of explicit status enum/text field.
- Expected: explicit and unambiguous INVALID vs MISS contract for downstream audit queries.
- Repro: inspect `src/models/discovery_outcome.py` + persisted rows in `artifacts/cycle055_e2e_validation.json`.
- Suspected area: discovery outcome schema contract.
- Severity: **concern** (auditing clarity, not runtime blocker).

### FINDING E-3 (route to Agent B / PM)

- Gate: Preflight comparability
- Symptom: missing `docs/cycle_reports/HANDOFF_B.md` for Cycle 055.
- Expected: B handoff present with exact toggle/entrypoint/status contracts and reference SHA.
- Repro: file lookup in `docs/cycle_reports` shows no Cycle-055 B handoff.
- Suspected area: delivery artifact gap.
- Severity: **concern** (strict comparability trace is incomplete).

## Command / isolation audit

| Command intent | DB used | Config path | Isolation status |
| ---- | ---- | ---- | ---- |
| Baseline checkpoint query | `data/cycle037_live.db` (read-only) | none | safe |
| Throwaway init | `sqlite:///data/cycle055_discovery_validation.db` | default | safe |
| Throwaway schema query | `data/cycle055_discovery_validation.db` | none | safe |
| Offline ON/OFF e2e harness | `sqlite:///data/cycle055_discovery_validation.db` + `sqlite:///data/cycle055_discovery_validation_off.db` | local in-process config | safe |
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
  - G1/G2/G3/G4 + rejection rates + parity: offline end-to-end validation on throwaway DBs.
  - Live validation: deferred (not required for this run; no credit burn approved/needed).

## Final verdict for D

**CONCERN** — full offline gate validation is complete on throwaway DBs, representative rejection-rate is in-band (`3/12 = 0.25`), OFF parity contrast is confirmed, and baseline safety is proven; remaining concerns are ghost-path strictness, boolean outcome-status semantics, and missing Cycle-055 `HANDOFF_B.md` trace artifact.
