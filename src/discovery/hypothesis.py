"""Hypothesis generation and scoring stubs for discovery."""

from __future__ import annotations

import json
from typing import Any

from src.models.discovery import DiscoveryCandidate

_WEIGHTS = {
    "market_size_signal": 0.40,
    "competition_gap_signal": 0.35,
    "trend_signal": 0.25,
}


async def generate_niche_hypotheses(
    source_niche_id: str,
    existing_keywords: list[str],
    llm_client: Any | None,
    cache: Any | None,
) -> list[dict[str, str]]:
    """Generate niche hypotheses, or return empty when LLM is unavailable."""
    if llm_client is None:
        return []

    del cache  # Stub path: cache wiring lands in later discovery stories.
    prompt = (
        "Generate discovery hypotheses as JSON for Fiverr niche expansion.\n"
        f"source_niche_id={source_niche_id}\n"
        f"existing_keywords={existing_keywords[:50]}"
    )

    try:
        response = await llm_client.complete(
            prompt=prompt,
            model="gpt-4o-mini",
            temperature=0.4,
            response_format={"type": "json_object"},
        )
    except Exception:
        return []

    payload = _coerce_json_payload(response)
    if payload is None:
        return []

    hypotheses_payload = payload["hypotheses"] if isinstance(payload, dict) else payload
    if not isinstance(hypotheses_payload, list):
        return []

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
