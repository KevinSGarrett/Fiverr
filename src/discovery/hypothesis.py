"""Hypothesis generation helpers for discovery."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from inspect import isawaitable
from typing import Any

from src.analysis.result_set_validator import NICHE_VALIDATION_CONFIG, get_validation_config
from src.models.discovery import DiscoveryCandidate

_WEIGHTS = {
    "market_size_signal": 0.40,
    "competition_gap_signal": 0.35,
    "trend_signal": 0.25,
}

GATE1_SPECIFICITY_THRESHOLD = 0.75
_GENERIC_DELIVERABLE_TERMS = {"support", "automation", "services", "agent", "python", "help", "scraping"}
_ADJACENT_QUALIFIERS = [
    "advanced",
    "professional",
    "expert",
    "automated",
    "custom",
    "fast",
    "reliable",
    "scalable",
]
_ADJACENT_SCOPE_MODS = [
    "for startups",
    "for e-commerce",
    "for small business",
    "for agencies",
]

# S7.3: Adjacent niche relationship map - rule-based, no LLM required.
# Keep this map as a module-level constant for deterministic hypothesis generation.
# The mapping intentionally captures adjacency, not strict bidirectional symmetry.
ADJACENT_NICHE_RELATIONSHIPS: dict[str, list[str]] = {
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

# S7.4 Gap Exploit defaults. Kept as named constants for auditability.
GAP_DEMAND_THRESHOLD: float = 0.60
GAP_COMPETITION_THRESHOLD: float = 0.40
GAP_DEMAND_WEIGHT: float = 0.60
GAP_OPPORTUNITY_WEIGHT: float = 0.40


@dataclass(slots=True)
class HypothesisContract:
    hypothesis_text: str
    niche_id: str
    buyer: str | None
    deliverable: str | None
    specificity_score: float = 0.0
    accepted: bool = False
    reason: str = ""


async def generate_niche_hypotheses(
    source_niche_id: str,
    existing_keywords: list[str],
    llm_client: Any | None,
    cache: Any | None,
    *,
    enable_relevance_gates: bool = False,
) -> list[dict[str, Any]]:
    """Generate niche hypotheses, or return empty when LLM is unavailable."""
    if llm_client is None:
        return []

    del cache  # Stub path: cache wiring lands in later discovery stories.
    legacy_prompt = (
        "Generate discovery hypotheses as JSON for Fiverr niche expansion.\n"
        f"source_niche_id={source_niche_id}\n"
        f"existing_keywords={existing_keywords[:50]}"
    )
    prompt = (
        _build_gated_prompt(source_niche_id=source_niche_id, existing_keywords=existing_keywords)
        if enable_relevance_gates
        else legacy_prompt
    )

    try:
        response = llm_client.complete(
            prompt=prompt,
            model="gpt-4o-mini",
            temperature=0.4,
            response_format={"type": "json_object"},
        )
        if isawaitable(response):
            response = await response
    except Exception:
        return []

    payload = _coerce_json_payload(response)
    if payload is None:
        return []

    hypotheses_payload = payload["hypotheses"] if isinstance(payload, dict) else payload
    if not isinstance(hypotheses_payload, list):
        return []

    if not enable_relevance_gates:
        return _normalize_hypotheses_legacy(hypotheses_payload)

    contracts = parse_hypothesis_contracts(hypotheses_payload, source_niche_id=source_niche_id)
    accepted_contracts = _gate_hypotheses(contracts)
    return [
        {
            "hypothesis_text": contract.hypothesis_text,
            "hypothesis_type": "adjacent_keyword",
            "source_signal": "gated_hypothesis",
            "buyer": contract.buyer,
            "deliverable": contract.deliverable,
            "specificity_score": contract.specificity_score,
            "gate_reason": contract.reason,
        }
        for contract in accepted_contracts
    ]


def score_hypothesis_signals(
    candidate: DiscoveryCandidate,
    market_size_signal: float | None,
    competition_gap_signal: float | None,
    trend_signal: float | None,
) -> float | None:
    """Compute weighted discovery score from available market/competition/trend signals."""
    del candidate  # Candidate-aware weighting is deferred to later discovery stories.

    values = {
        "market_size_signal": market_size_signal,
        "competition_gap_signal": competition_gap_signal,
        "trend_signal": trend_signal,
    }
    present = {name: value for name, value in values.items() if value is not None}
    if not present:
        return None

    total_weight = sum(_WEIGHTS[name] for name in present)
    weighted_score = sum(value * _WEIGHTS[name] for name, value in present.items())
    return weighted_score / total_weight if total_weight else None


def _build_adjacent_candidates(
    seed: str,
    niche_id: str,
    *,
    max_per_seed: int = 5,
) -> list[str]:
    """Generate adjacent keyword candidates from a seed keyword."""
    del niche_id  # Stage 16 orchestration will apply niche-aware refinements.
    normalized_seed = seed.strip().lower()
    if not normalized_seed or max_per_seed <= 0:
        return []

    candidates: list[str] = []
    seen: set[str] = set()

    for qualifier in _ADJACENT_QUALIFIERS:
        if qualifier in normalized_seed:
            continue
        candidate = f"{qualifier} {normalized_seed}"
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)

    for modifier in _ADJACENT_SCOPE_MODS:
        candidate = f"{normalized_seed} {modifier}"
        if candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)

    filtered = [
        candidate
        for candidate in candidates
        if candidate != normalized_seed and len(candidate.split()) <= 6
    ]
    return filtered[:max_per_seed]


def _score_candidate_confidence(
    candidate: str,
    seed_keywords: list[str],
) -> float:
    """Score confidence for an adjacent keyword candidate."""
    if not seed_keywords:
        return 0.0

    candidate_terms = set(candidate.lower().split())
    if not candidate_terms:
        return 0.0

    seed_pool: set[str] = set()
    for seed_keyword in seed_keywords:
        seed_pool.update(seed_keyword.lower().split())

    overlap = len(candidate_terms & seed_pool) / max(len(candidate_terms), 1)
    generic_penalty = 0.15 * len(candidate_terms & _GENERIC_DELIVERABLE_TERMS)
    length_bonus = 0.1 if 3 <= len(candidate_terms) <= 5 else 0.0
    confidence = overlap + length_bonus - generic_penalty
    return min(1.0, max(0.0, confidence))


def generate_adjacent_keyword_hypotheses(
    source_niche_id: str,
    seed_keywords: list[str],
    existing_keywords: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
) -> list[HypothesisContract]:
    """Generate adjacent keyword hypotheses using deterministic rule expansion.

    This helper is S7.2-only and intentionally in-memory: it returns contracts
    for both accepted and rejected candidates so downstream stages can audit
    budget-gate behavior before Stage 16 persistence wiring lands.
    """
    if not seed_keywords:
        return []

    existing_lower = {keyword.lower().strip() for keyword in existing_keywords if keyword.strip()}
    seen: set[str] = set()
    results: list[HypothesisContract] = []
    accepted_count = 0

    for seed in seed_keywords:
        for candidate in _build_adjacent_candidates(seed, source_niche_id):
            normalized_candidate = candidate.lower().strip()
            if not normalized_candidate or normalized_candidate in existing_lower or normalized_candidate in seen:
                continue

            seen.add(normalized_candidate)
            confidence = _score_candidate_confidence(candidate, seed_keywords)
            accepted = confidence >= min_confidence and accepted_count < max_hypotheses
            if accepted:
                accepted_count += 1

            reason = (
                f"confidence {confidence:.2f} >= {min_confidence:.2f} (ACCEPTED)"
                if accepted
                else f"confidence {confidence:.2f} < {min_confidence:.2f} (REJECTED)"
            )
            results.append(
                HypothesisContract(
                    hypothesis_text=candidate,
                    niche_id=source_niche_id,
                    buyer=None,
                    deliverable=candidate,
                    specificity_score=confidence,
                    accepted=accepted,
                    reason=reason,
                )
            )

    return results


def _build_adjacent_niche_candidates(
    source_niche_id: str,
    seed_keywords: list[str],
    *,
    max_per_niche: int = 5,
) -> list[str]:
    """Return adjacent niche IDs from the adjacency map.

    Rule-based and deterministic: this helper does not call an LLM.
    Returns up to ``max_per_niche`` mapped adjacent niches for ``source_niche_id``.
    If ``source_niche_id`` is unknown or ``max_per_niche`` is non-positive, returns an empty list.
    """
    del seed_keywords  # Reserved for future ranking refinements.
    if max_per_niche <= 0:
        return []
    return ADJACENT_NICHE_RELATIONSHIPS.get(source_niche_id, [])[:max_per_niche]


def _score_niche_candidate_confidence(
    candidate_niche_id: str,
    seed_keywords: list[str],
    niche_validation_config: dict[str, Any] | None = None,
) -> float:
    """Score confidence for an adjacent niche candidate in ``[0.0, 1.0]``.

    Confidence factors:
    1. Keyword overlap between ``seed_keywords`` and target niche keywords.
    2. Base adjacency bonus (0.30): any niche in ``ADJACENT_NICHE_RELATIONSHIPS``
       is hand-curated as relevant, so this constant gives meaningful baseline
       relevance even for short seeds and helps overlap + adjacency reach the
       default 0.50 budget gate.
    3. Generic term penalty (same generic-term pool used in S7.2 scoring).
    """
    if not seed_keywords:
        return 0.0

    if niche_validation_config is None:
        niche_validation_config = NICHE_VALIDATION_CONFIG

    target_cfg = niche_validation_config.get(candidate_niche_id, {})
    configured_keywords = target_cfg.get("seed_keywords", [])
    if configured_keywords:
        target_terms = {
            token
            for keyword in configured_keywords
            for token in keyword.lower().split()
        }
    else:
        target_terms = set(candidate_niche_id.replace("_", " ").split())

    seed_pool = {
        token
        for keyword in seed_keywords
        for token in keyword.lower().split()
    }
    overlap = len(seed_pool & target_terms) / max(len(target_terms), 1)
    generic_penalty = 0.10 * len(seed_pool & _GENERIC_DELIVERABLE_TERMS)
    base_adjacency_bonus = 0.30
    return min(1.0, max(0.0, overlap + base_adjacency_bonus - generic_penalty))


def generate_adjacent_niche_hypotheses(
    source_niche_id: str,
    seed_keywords: list[str],
    existing_niches: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
) -> list[HypothesisContract]:
    """Generate S7.3 adjacent-niche hypotheses from source niche context.

    This mode is rule-based (no LLM), deduplicates against ``existing_niches``,
    applies a budget gate, and returns **all** contracts (accepted and rejected)
    for auditability.

    Design note: in adjacent-niche mode, ``hypothesis_text`` is the candidate
    niche ID (for example ``"ai_agent_development"``), while ``niche_id`` keeps
    the source niche ID (for example ``"python_automation"``).
    """
    if not source_niche_id:
        return []

    existing_lower = {niche.lower().strip() for niche in existing_niches if niche.strip()}
    candidates = _build_adjacent_niche_candidates(source_niche_id, seed_keywords)
    results: list[HypothesisContract] = []
    accepted_count = 0

    for candidate_niche_id in candidates:
        normalized_candidate = candidate_niche_id.lower().strip()
        if not normalized_candidate or normalized_candidate in existing_lower:
            continue

        confidence = _score_niche_candidate_confidence(candidate_niche_id, seed_keywords)
        accepted = confidence >= min_confidence and accepted_count < max_hypotheses
        if accepted:
            accepted_count += 1

        reason = (
            f"niche confidence {confidence:.2f} >= {min_confidence:.2f} (ACCEPTED)"
            if accepted
            else f"niche confidence {confidence:.2f} < {min_confidence:.2f} (REJECTED)"
        )
        results.append(
            HypothesisContract(
                hypothesis_text=candidate_niche_id,
                niche_id=source_niche_id,
                buyer=None,
                deliverable=candidate_niche_id.replace("_", " "),
                specificity_score=confidence,
                accepted=accepted,
                reason=reason,
            )
        )

    return results


def _identify_gap_keywords(
    keyword_scores: list[dict[str, Any]],
    *,
    demand_threshold: float = GAP_DEMAND_THRESHOLD,
    competition_threshold: float = GAP_COMPETITION_THRESHOLD,
) -> list[dict[str, Any]]:
    """Return keyword score rows that satisfy gap criteria."""
    gap_rows: list[dict[str, Any]] = []
    for item in keyword_scores:
        if not isinstance(item, dict):
            continue
        keyword = str(item.get("keyword", "")).strip()
        if not keyword:
            continue
        demand_score = float(item.get("demand_score") or 0.0)
        competition_score = float(item.get("competition_score") or 0.0)
        if demand_score >= demand_threshold and competition_score <= competition_threshold:
            gap_rows.append(item)
    return gap_rows


def _score_gap_hypothesis_confidence(
    kw_data: dict[str, Any],
    *,
    demand_weight: float = GAP_DEMAND_WEIGHT,
    opportunity_weight: float = GAP_OPPORTUNITY_WEIGHT,
) -> float:
    """Score S7.4 confidence from demand + opportunity components only."""
    demand_score = float(kw_data.get("demand_score") or 0.0)
    opportunity_score = float(kw_data.get("opportunity_score") or 0.0)
    confidence = (demand_weight * demand_score) + (opportunity_weight * opportunity_score)
    return max(0.0, min(1.0, confidence))


def generate_gap_exploit_hypotheses(
    source_niche_id: str,
    keyword_scores: list[dict[str, Any]],
    existing_hypotheses: list[str],
    *,
    max_hypotheses: int = 10,
    min_confidence: float = 0.50,
    demand_threshold: float = GAP_DEMAND_THRESHOLD,
    competition_threshold: float = GAP_COMPETITION_THRESHOLD,
) -> list[HypothesisContract]:
    """Generate S7.4 gap opportunity hypotheses from scored keyword rows."""
    if not source_niche_id or not keyword_scores:
        return []

    existing_lower = {item.lower().strip() for item in existing_hypotheses if item.strip()}
    seen: set[str] = set()
    contracts: list[HypothesisContract] = []
    accepted_count = 0

    for kw_data in _identify_gap_keywords(
        keyword_scores,
        demand_threshold=demand_threshold,
        competition_threshold=competition_threshold,
    ):
        hypothesis_text = str(kw_data.get("keyword", "")).strip()
        normalized = hypothesis_text.lower()
        if not normalized or normalized in existing_lower or normalized in seen:
            continue
        seen.add(normalized)

        confidence = _score_gap_hypothesis_confidence(kw_data)
        accepted = confidence >= min_confidence and accepted_count < max_hypotheses
        if accepted:
            accepted_count += 1

        reason = (
            f"gap confidence {confidence:.2f} >= {min_confidence:.2f} (ACCEPTED)"
            if accepted
            else f"gap confidence {confidence:.2f} < {min_confidence:.2f} (REJECTED)"
        )
        contracts.append(
            HypothesisContract(
                hypothesis_text=hypothesis_text,
                niche_id=source_niche_id,
                buyer=None,
                deliverable=hypothesis_text,
                specificity_score=confidence,
                accepted=accepted,
                reason=reason,
            )
        )

    return contracts


def _coerce_json_payload(response: Any) -> dict[str, Any] | list[Any] | None:
    raw_payload = getattr(response, "text", None) or getattr(response, "content", None) or response
    if isinstance(raw_payload, dict | list):
        return raw_payload
    if not isinstance(raw_payload, str):
        return None
    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict | list) else None


def parse_hypothesis_contracts(
    hypotheses_payload: list[dict[str, Any]],
    *,
    source_niche_id: str,
) -> list[HypothesisContract]:
    contracts: list[HypothesisContract] = []
    for item in hypotheses_payload:
        if not isinstance(item, dict):
            continue
        hypothesis_text = str(
            item.get("hypothesis_text")
            or item.get("suggested_keyword")
            or item.get("keyword")
            or ""
        ).strip()
        if not hypothesis_text:
            continue
        contracts.append(
            HypothesisContract(
                hypothesis_text=hypothesis_text,
                niche_id=source_niche_id,
                buyer=_normalize_optional(item.get("buyer")),
                deliverable=_normalize_optional(item.get("deliverable")),
            )
        )
    return contracts


def _normalize_hypotheses_legacy(hypotheses_payload: list[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for item in hypotheses_payload:
        if not isinstance(item, dict):
            continue
        hypothesis_text = str(
            item.get("hypothesis_text")
            or item.get("suggested_keyword")
            or item.get("keyword")
            or ""
        ).strip()
        if not hypothesis_text:
            continue
        hypothesis_type = str(item.get("hypothesis_type") or item.get("mode") or "adjacent_keyword")
        source_signal = str(item.get("source_signal") or item.get("rationale") or "").strip()
        normalized.append(
            {
                "hypothesis_text": hypothesis_text,
                "hypothesis_type": hypothesis_type,
                "source_signal": source_signal,
            }
        )
    return normalized


def _build_gated_prompt(*, source_niche_id: str, existing_keywords: list[str]) -> str:
    scope = _render_niche_scope(source_niche_id)
    return (
        "Generate discovery hypotheses as JSON for Fiverr niche expansion.\n"
        f"source_niche_id={source_niche_id}\n"
        f"existing_keywords={existing_keywords[:50]}\n"
        f"expected_service_scope={scope}\n"
        f"Keep every hypothesis strictly in the {source_niche_id} niche.\n"
        "Reject adjacent-market drift and out-of-scope services.\n"
        "Each hypothesis must explicitly include buyer and deliverable fields.\n"
        "Return JSON with a hypotheses array of objects: "
        "{hypothesis_text, buyer, deliverable}."
    )


def _render_niche_scope(niche_id: str) -> str:
    config = NICHE_VALIDATION_CONFIG.get(niche_id) or get_validation_config(niche_id)
    core_terms = [str(term).strip() for term in config.get("core_terms", []) if str(term).strip()]
    if not core_terms:
        return niche_id
    return ", ".join(core_terms[:8])


def _normalize_optional(value: Any) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _score_specificity(contract: HypothesisContract) -> float:
    score = 0.0
    if contract.buyer:
        score += 0.34
    if contract.deliverable:
        score += 0.33
    if contract.deliverable and _deliverable_in_scope(contract.deliverable, contract.niche_id):
        score += 0.33
    if _is_overbroad_single_term(contract.hypothesis_text):
        score -= 0.5
    return max(0.0, min(1.0, round(score, 4)))


def _deliverable_in_scope(deliverable: str, niche_id: str) -> bool:
    normalized_deliverable = _normalized_text(deliverable)
    if not normalized_deliverable:
        return False
    config = NICHE_VALIDATION_CONFIG.get(niche_id) or get_validation_config(niche_id)
    core_terms = [_normalized_text(str(term)) for term in config.get("core_terms", [])]
    exclusion_terms = [_normalized_text(str(term)) for term in config.get("exclusion_terms", [])]
    if any(term and term in normalized_deliverable for term in exclusion_terms):
        return False
    return any(term and term in normalized_deliverable for term in core_terms)


def _is_overbroad_single_term(text: str) -> bool:
    normalized = _normalized_text(text)
    if not normalized:
        return True
    tokens = normalized.split()
    if len(tokens) == 1:
        return True
    return len(tokens) <= 3 and all(token in _GENERIC_DELIVERABLE_TERMS for token in tokens)


def _normalized_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def _gate_hypotheses(
    contracts: list[HypothesisContract],
    threshold: float = GATE1_SPECIFICITY_THRESHOLD,
) -> list[HypothesisContract]:
    accepted: list[HypothesisContract] = []
    for contract in contracts:
        contract.specificity_score = _score_specificity(contract)
        if contract.specificity_score >= threshold:
            contract.accepted = True
            contract.reason = "passed specificity + on-niche"
            accepted.append(contract)
            continue
        contract.accepted = False
        contract.reason = f"specificity {contract.specificity_score:.2f} < {threshold:.2f}"
    return accepted
