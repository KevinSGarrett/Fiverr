# CYCLE 066 - AGENT B HANDOFF

Date: 2026-06-05  
Branch: `cycle/066/integration`

## Scope

Wave 10 S7.2 adjacent keyword hypothesis mode implementation only.

In-scope:

- adjacent keyword candidate generation from seed/cluster context
- filtering + dedupe against existing keywords/prior candidates
- confidence scoring + budget gate (`min_confidence=0.50`)
- persistence context for `DiscoveryCandidate`
- tests for generation, dedupe, empty input, and confidence boundary

Out-of-scope this cycle:

- S7.3+ modes
- Stage 16 full loop wiring
- Test/Evaluate/Feedback implementation
- DB schema expansion

## Files

### Modify

- `src/discovery/hypothesis.py`

### Create

- `tests/unit/test_adjacent_keyword_hypotheses.py` (target: >= 20 tests)

### Possibly Modify (minor carry-forward)

- `run.py` or `src/cli.py` for coherent `pricing-export` surface wiring

## Required Function Signatures

- `generate_adjacent_keyword_hypotheses(source_niche_id, seed_keywords, existing_keywords, *, max_hypotheses=10, min_confidence=0.50) -> list[HypothesisContract]`
- `_build_adjacent_candidates(seed: str, niche_id: str) -> list[str]`
- `_score_candidate_confidence(candidate: str, seed_keywords: list[str]) -> float`

## Behavior Contract for `generate_adjacent_keyword_hypotheses`

Output type: `list[HypothesisContract]`

Populate per item:

- `hypothesis_text`: proposed adjacent keyword
- `niche_id`: equals `source_niche_id`
- `specificity_score`: structural specificity score
- `confidence`: estimated confidence from overlap + term quality
- `accepted`: `True` only when `confidence >= min_confidence`
- `reason`: accept/reject rationale

Rules:

- no LLM dependency
- deterministic/rule-based expansion path
- dedupe against `existing_keywords` and generated duplicates
- cap to `max_hypotheses`

## Spec Anchors Reviewed by A

`HYPOTHESIS_GENERATION_PROMPTS.md`:

- adjacent = same buyer intent, alternate phrasing, narrower specialization, or related deliverable
- confidence should reflect likely score success and rationale lineage

`DISCOVERY_ENGINE_ARCHITECTURE.md`:

- S7.2 maps to `HYPOTHESIZE`
- budget gate is explicitly `hypothesis_confidence >= 0.50`

`DISCOVERY_SCORING_AND_FEEDBACK.md` + existing code context:

- preserve score context and lineage for later evaluate/feedback phases
- existing weighted signal context in discovery helpers: market size `0.40`, competition gap `0.35`, trend `0.25`

## DiscoveryCandidate Persistence Guidance

Model fields available:

- identity/context: `candidate_id`, `hypothesis_text`, `hypothesis_type`, `source_signal`, `source_niche_id`, `run_id`, `status`
- score lineage: `discovery_score`, `market_size_signal`, `competition_gap_signal`, `trend_signal`, `llm_hypothesis_text`, `llm_reasoning`

Minimum expected S7.2 write context:

- `hypothesis_text`
- `hypothesis_type='adjacent_keyword'`
- `source_niche_id`
- confidence/rationale lineage in score/reasoning-compatible fields

## Existing Discovery Baseline Tests

Current discovery suite collects 66 tests including:

- scaffold and candidate model/persistence tests
- relevance gate behavior tests
- orchestrator/session none-safety tests
- cycle alias regression `test_discovery_core_loop_budget_gate`

B must add dedicated S7.2 coverage without breaking existing baseline.

## Carry-Forward Advisory (Pricing Export)

- `src/cli.py` already includes a `pricing-export` command
- `run.py` does not expose `pricing-export` string path directly
- treat this as minor carry-forward only if project runtime contract requires top-level wiring

## Acceptance Checklist for B

- [ ] `generate_adjacent_keyword_hypotheses` implemented in `src/discovery/hypothesis.py`
- [ ] helper functions implemented and unit-tested
- [ ] no LLM dependency introduced
- [ ] budget gate threshold `0.50` enforced
- [ ] dedupe against existing keywords and generated duplicates
- [ ] >=20 S7.2 tests added and passing
- [ ] no new DB tables/migrations
- [ ] golden parity unaffected
