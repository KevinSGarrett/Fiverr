# CYCLE 067 - AGENT B HANDOFF (S7.3 Adjacent Niche)

## Scope (Exact)

Files to MODIFY:

- `src/discovery/hypothesis.py`
- `src/discovery/contracts.py` (only if enum value missing; at C067 start it is already present)

Files to CREATE:

- `tests/unit/test_adjacent_niche_hypotheses.py` (base test file, minimum 30 tests)

No migrations, no new DB tables, no Stage 16 persistence wiring, no dashboard work.

## Required Function Signatures

Implement in `src/discovery/hypothesis.py`:

```python
def generate_adjacent_niche_hypotheses(
    source_niche_id: str,
    seed_keywords: list[str],
    existing_niches: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
) -> list[HypothesisContract]:
    ...

def _build_adjacent_niche_candidates(
    source_niche_id: str,
    seed_keywords: list[str],
    *,
    max_per_niche: int = 5,
) -> list[str]:
    ...

def _score_niche_candidate_confidence(
    candidate_niche_id: str,
    seed_keywords: list[str],
    target_niche_keywords: list[str] | None = None,
) -> float:
    ...
```

Budget gate is mandatory: `min_confidence=0.50`.

## Adjacent Niche Relationships (Rule-Based)

```python
ADJACENT_NICHE_RELATIONSHIPS = {
    "python_automation": ["ai_agent_development", "workflow_automation", "gumloop_lindy_workflow"],
    "ai_agent_development": ["python_automation", "mcp_ai_agent", "ai_tool_llm_integration"],
    "workflow_automation": ["python_automation", "gumloop_lindy_workflow", "ai_agent_development"],
    "gumloop_lindy_workflow": ["workflow_automation", "ai_agent_development", "python_automation"],
    "prd_ai_saas": ["mcp_ai_agent", "ai_tool_llm_integration", "ai_agent_development"],
    "mcp_ai_agent": ["prd_ai_saas", "ai_tool_llm_integration", "ai_agent_development"],
    "ai_tool_llm_integration": ["mcp_ai_agent", "prd_ai_saas", "ai_agent_development"],
    "python_web_scraping": ["python_automation", "workflow_automation"],
    "support_kb_readiness": ["ai_tool_llm_integration", "prd_ai_saas"],
}
```

## Implementation Pattern Requirement

S7.3 must mirror S7.2 structure:

- public generator (`generate_adjacent_niche_hypotheses`)
- candidate builder helper (`_build_adjacent_niche_candidates`)
- confidence helper (`_score_niche_candidate_confidence`)

Use `HypothesisContract` outputs, preserving:

- lineage: `niche_id=source_niche_id`
- confidence: `specificity_score`
- acceptance: budget gate
- reason: accepted/rejected rationale text

## Acceptance Criteria (Verbatim from SCRUM-198)

- Adjacent niche hypotheses are generated from source-backed niche/cluster context.
- Hypotheses preserve rationale, lineage, confidence, and budget context.
- Child tasks are created in later native task import waves or formally waived.
- Tests cover candidate generation, duplicates, sparse inputs, and empty outputs.

## Test Plan Baseline for B

Create `tests/unit/test_adjacent_niche_hypotheses.py` with at least 30 tests:

- `TestAdjacentNicheRelationshipsMap` (3 tests)
- `TestBuildAdjacentNicheCandidates` (6 tests)
- `TestScoreNicheCandidateConfidence` (4-5 tests)
- `TestGenerateAdjacentNicheHypotheses` (17+ tests)

Mandatory coverage points:

- all 9 niches as `source_niche_id`
- dedup against `existing_niches`
- no self-reference in output
- unknown source niche returns empty
- empty seed keywords behavior
- min confidence boundary around `0.50`

## C067 Boundaries (Do Not Expand)

In-scope:

- S7.3 adjacent niche hypothesis generation and tests

Out-of-scope:

- S7.8 persistence/orchestration wiring
- S7.9 dashboard widgets
- S7.4/S7.5 modes (gap exploit, trend chase)

## Current Baseline Facts

- `HypothesisMode` already includes `ADJACENT_NICHE="adjacent_niche"` at C067 start.
- Existing adjacent keyword pattern file: `tests/unit/test_adjacent_keyword_hypotheses.py` (77 tests, class-based pattern available for reuse).
- Golden parity currently PASS (`kw=110 -> 62.7 / 1.0 / CONDITIONAL_GO`).
