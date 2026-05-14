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
_URGENCY_TERMS = {
    "urgent",
    "asap",
    "today",
    "now",
    "immediately",
}
_PRICE_LANGUAGE_TERMS = {
    "budget",
    "cost",
    "price",
    "$",
    "usd",
    "affordable",
    "premium",
    "under ",
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
_SERVICE_VERBS = {
    "build",
    "develop",
    "design",
    "create",
    "automate",
    "integrate",
    "write",
    "set up",
}


def classify_intent(payload: IntentInput) -> IntentResult:
    """Classify keyword intent using deterministic lexical rules."""
    keyword_text = payload.keyword_text.strip()
    combined_text = " ".join([keyword_text, *payload.title_phrases]).lower()
    matched_rules: list[str] = []

    buyer_hits = [token for token in sorted(_BUYER_READY_TERMS) if token in combined_text]
    urgency_hits = [token for token in sorted(_URGENCY_TERMS) if token in combined_text]
    price_hits = [token for token in sorted(_PRICE_LANGUAGE_TERMS) if token in combined_text]
    research_hits = [token for token in sorted(_RESEARCH_TERMS) if token in combined_text]
    low_hits = [token for token in sorted(_LOW_INTENT_TERMS) if token in combined_text]
    provider_hits = [token for token in sorted(_SERVICE_PROVIDER_TERMS) if token in combined_text]
    service_verb_hits = [token for token in sorted(_SERVICE_VERBS) if token in combined_text]

    if provider_hits:
        matched_rules.extend(f"service_provider:{token}" for token in provider_hits)
    if buyer_hits:
        matched_rules.extend(f"buyer_ready:{token}" for token in buyer_hits)
    if urgency_hits:
        matched_rules.extend(f"urgency:{token}" for token in urgency_hits)
    if price_hits:
        matched_rules.extend(f"price_language:{token}" for token in price_hits)
    if research_hits:
        matched_rules.extend(f"research_only:{token}" for token in research_hits)
    if low_hits:
        matched_rules.extend(f"low_intent:{token}" for token in low_hits)
    if service_verb_hits:
        matched_rules.extend(f"service_verb:{token}" for token in service_verb_hits)

    buyer_signal = len(buyer_hits) + len(urgency_hits) + len(price_hits)
    provider_signal = len(provider_hits) + len(service_verb_hits)
    research_signal = len(research_hits)
    low_signal = len(low_hits)

    if provider_signal >= 2 and buyer_signal == 0:
        label = IntentLabel.SERVICE_PROVIDER
        confidence = 0.82
    elif buyer_signal >= 3 and provider_signal == 0:
        label = IntentLabel.BUYER_READY
        confidence = 0.86
    elif research_signal > 0 and buyer_signal == 0:
        label = IntentLabel.RESEARCH_ONLY
        confidence = 0.76
    elif low_signal > 0 and buyer_signal == 0:
        label = IntentLabel.LOW_INTENT
        confidence = 0.7
    elif buyer_signal > 0 and provider_signal > 0:
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
