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
