"""Deterministic rule-based keyword intent classification."""

from __future__ import annotations

from src.analysis.contracts import IntentInput, IntentLabel, IntentResult

_BUYER_READY_TERMS = {
    "hire",
    "buy",
    "order",
    "need",
    "looking for",
    "looking to hire",
    "urgent",
    "today",
}
_RESEARCH_TERMS = {
    "what is",
    "how to",
    "guide",
    "tips",
    "learn",
    "tutorial",
    "comparison",
}
_LOW_INTENT_TERMS = {
    "free",
    "example",
    "template",
    "cheap",
    "idea",
    "sample",
}
_SERVICE_PROVIDER_TERMS = {
    "i will",
    "i can",
    "offering",
    "my service",
    "we provide",
    "portfolio",
}


def classify_intent(payload: IntentInput) -> IntentResult:
    """Classify keyword intent using deterministic lexical rules."""
    keyword_text = payload.keyword_text.strip()
    combined_text = " ".join([keyword_text, *payload.title_phrases]).lower()
    matched_rules: list[str] = []

    buyer_hits = [token for token in sorted(_BUYER_READY_TERMS) if token in combined_text]
    research_hits = [token for token in sorted(_RESEARCH_TERMS) if token in combined_text]
    low_hits = [token for token in sorted(_LOW_INTENT_TERMS) if token in combined_text]
    provider_hits = [token for token in sorted(_SERVICE_PROVIDER_TERMS) if token in combined_text]

    if provider_hits:
        matched_rules.extend(f"service_provider:{token}" for token in provider_hits)
    if buyer_hits:
        matched_rules.extend(f"buyer_ready:{token}" for token in buyer_hits)
    if research_hits:
        matched_rules.extend(f"research_only:{token}" for token in research_hits)
    if low_hits:
        matched_rules.extend(f"low_intent:{token}" for token in low_hits)

    if provider_hits and not buyer_hits:
        label = IntentLabel.SERVICE_PROVIDER
        confidence = 0.82
    elif len(buyer_hits) >= 2 and not provider_hits:
        label = IntentLabel.BUYER_READY
        confidence = 0.84
    elif research_hits and not buyer_hits:
        label = IntentLabel.RESEARCH_ONLY
        confidence = 0.76
    elif low_hits and not buyer_hits:
        label = IntentLabel.LOW_INTENT
        confidence = 0.7
    elif buyer_hits and provider_hits:
        label = IntentLabel.AMBIGUOUS
        confidence = 0.42
    else:
        label = IntentLabel.AMBIGUOUS
        confidence = 0.35
        matched_rules.append("ambiguous:no_strong_signal")

    explanation = (
        "Intent label is derived from matched transactional, research, low-intent, "
        "and service-provider phrases in keyword and title context."
    )
    return IntentResult(
        source_id=payload.source_id,
        keyword_text=keyword_text,
        label=label,
        confidence=confidence,
        matched_rules=sorted(matched_rules),
        explanation=explanation,
        metadata=payload.metadata,
    )
