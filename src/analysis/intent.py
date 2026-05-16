"""Deterministic rule-based keyword intent classification."""

from __future__ import annotations

from src.analysis.contracts import (
    AnalysisEvidence,
    AnalysisReadinessStatus,
    AnalysisWarning,
    IntentInput,
    IntentLabel,
    IntentResult,
)

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


def _coerce_confidence(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None
        try:
            return float(normalized)
        except ValueError:
            return None
    return None


def _normalize_mock_label(value: object) -> IntentLabel | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    try:
        return IntentLabel(normalized)
    except ValueError:
        return None


def classify_intent(payload: IntentInput) -> IntentResult:
    """Classify keyword intent using deterministic lexical rules."""
    keyword_text = payload.keyword_text.strip()
    warnings: list[AnalysisWarning] = []
    metadata = dict(payload.metadata)
    normalized_keyword = keyword_text.lower()
    if normalized_keyword in {"none", "null"}:
        warnings.append(
            AnalysisWarning(
                code="intent_keyword_nullish",
                message="Keyword text was null-like; intent degraded to low-confidence ambiguous.",
                source_id=payload.source_id,
                missing_data_fields=["keyword_text"],
            )
        )
        keyword_text = "unknown"
        normalized_keyword = keyword_text

    mock_label = _normalize_mock_label(metadata.get("mock_label"))
    if "mock_label" in metadata and mock_label is None:
        warnings.append(
            AnalysisWarning(
                code="intent_mock_label_invalid",
                message="Mock intent label was malformed or out of taxonomy; fallback intent applied.",
                source_id=payload.source_id,
                metadata={"raw_mock_label": metadata.get("mock_label")},
            )
        )

    llm_response = metadata.get("llm_response")
    if llm_response is not None:
        parsed_from_llm = _parse_llm_like_intent_response(
            llm_response,
            source_id=payload.source_id,
        )
        if parsed_from_llm is not None:
            label, confidence, explanation, llm_warnings = parsed_from_llm
            warnings.extend(llm_warnings)
            matched_rules = ["llm_contract:parsed_response"]
            readiness_status = (
                AnalysisReadinessStatus.READY
                if confidence >= 0.75
                else AnalysisReadinessStatus.PARTIAL
                if confidence >= 0.45
                else AnalysisReadinessStatus.BLOCKED
            )
            return IntentResult(
                source_id=payload.source_id,
                keyword_text=keyword_text,
                label=label,
                confidence=confidence,
                matched_rules=matched_rules,
                explanation=explanation,
                warnings=warnings,
                metadata=metadata,
                status=readiness_status,
                source_context={
                    "keyword_text": keyword_text,
                    "title_phrase_count": len(payload.title_phrases),
                    "llm_response_used": True,
                },
                evidence=[
                    AnalysisEvidence(
                        code="llm_intent_confidence",
                        message="Structured llm-like intent response confidence.",
                        metric=confidence,
                        source_ref="intent.metadata.llm_response",
                    )
                ],
                downstream_readiness={
                    "status": readiness_status.value,
                    "reasons": [] if confidence >= 0.45 else ["llm_low_confidence"],
                },
            )
        warnings.append(
            AnalysisWarning(
                code="intent_llm_response_malformed",
                message="Malformed llm-like response ignored; lexical fallback used.",
                source_id=payload.source_id,
                metadata={"raw_type": type(llm_response).__name__},
            )
        )

    if mock_label is not None:
        label = mock_label
        confidence = 0.65
        matched_rules = [f"mock_label:{mock_label.value}"]
        explanation = (
            "Intent label came from validated mocked label metadata for deterministic test execution."
        )
        return IntentResult(
            source_id=payload.source_id,
            keyword_text=keyword_text,
            label=label,
            confidence=confidence,
            matched_rules=matched_rules,
            explanation=explanation,
            warnings=warnings,
            metadata=metadata,
            status=AnalysisReadinessStatus.PARTIAL,
            source_context={"keyword_text": keyword_text, "title_phrase_count": len(payload.title_phrases)},
            evidence=[
                AnalysisEvidence(
                    code="mock_label_override",
                    message="Intent derived from validated mocked label.",
                    source_ref="intent.metadata.mock_label",
                )
            ],
            downstream_readiness={
                "status": "partial",
                "reasons": ["mock_label_override"],
            },
        )

    combined_text = " ".join([keyword_text, *payload.title_phrases]).lower()
    lexical_matched_rules: list[str] = []

    buyer_hits = [token for token in sorted(_BUYER_READY_TERMS) if token in combined_text]
    urgency_hits = [token for token in sorted(_URGENCY_TERMS) if token in combined_text]
    price_hits = [token for token in sorted(_PRICE_LANGUAGE_TERMS) if token in combined_text]
    research_hits = [token for token in sorted(_RESEARCH_TERMS) if token in combined_text]
    low_hits = [token for token in sorted(_LOW_INTENT_TERMS) if token in combined_text]
    provider_hits = [token for token in sorted(_SERVICE_PROVIDER_TERMS) if token in combined_text]
    service_verb_hits = [token for token in sorted(_SERVICE_VERBS) if token in combined_text]

    if provider_hits:
        lexical_matched_rules.extend(f"service_provider:{token}" for token in provider_hits)
    if buyer_hits:
        lexical_matched_rules.extend(f"buyer_ready:{token}" for token in buyer_hits)
    if urgency_hits:
        lexical_matched_rules.extend(f"urgency:{token}" for token in urgency_hits)
    if price_hits:
        lexical_matched_rules.extend(f"price_language:{token}" for token in price_hits)
    if research_hits:
        lexical_matched_rules.extend(f"research_only:{token}" for token in research_hits)
    if low_hits:
        lexical_matched_rules.extend(f"low_intent:{token}" for token in low_hits)
    if service_verb_hits:
        lexical_matched_rules.extend(f"service_verb:{token}" for token in service_verb_hits)

    buyer_signal = len(buyer_hits) + len(urgency_hits) + len(price_hits)
    provider_signal = len(provider_hits) + len(service_verb_hits)
    research_signal = len(research_hits)
    low_signal = len(low_hits)

    if keyword_text == "unknown":
        label = IntentLabel.UNKNOWN
        confidence = 0.2
        lexical_matched_rules.append("unknown:missing_keyword_context")
    elif provider_signal >= 2 and buyer_signal == 0:
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
        lexical_matched_rules.append("ambiguous:no_strong_signal")

    explanation = (
        "Intent label is derived from matched transactional, research, low-intent, "
        "and service-provider phrases in keyword and title context."
    )
    readiness_status = (
        AnalysisReadinessStatus.READY
        if confidence >= 0.75
        else AnalysisReadinessStatus.PARTIAL
        if confidence >= 0.45
        else AnalysisReadinessStatus.BLOCKED
    )
    readiness_reasons: list[str] = []
    if warnings:
        readiness_reasons.append("input_warnings_present")
    if label in {IntentLabel.AMBIGUOUS, IntentLabel.UNKNOWN} and confidence <= 0.4:
        readiness_reasons.append("low_signal_or_unknown")
    return IntentResult(
        source_id=payload.source_id,
        keyword_text=keyword_text,
        label=label,
        confidence=confidence,
        matched_rules=sorted(lexical_matched_rules),
        explanation=explanation,
        warnings=warnings,
        metadata=metadata,
        status=readiness_status,
        source_context={"keyword_text": keyword_text, "title_phrase_count": len(payload.title_phrases)},
        evidence=[
            AnalysisEvidence(
                code="intent_confidence",
                message="Deterministic lexical intent confidence score.",
                metric=confidence,
                source_ref="intent",
            ),
            AnalysisEvidence(
                code="matched_rule_count",
                message="Count of lexical rules matched while classifying intent.",
                metric=float(len(lexical_matched_rules)),
                source_ref="intent",
            ),
        ],
        downstream_readiness={
            "status": readiness_status.value,
            "reasons": readiness_reasons,
        },
    )


def _parse_llm_like_intent_response(
    response: object, *, source_id: str
) -> tuple[IntentLabel, float, str, list[AnalysisWarning]] | None:
    if not isinstance(response, dict):
        return None
    raw_label = response.get("category")
    label = _normalize_mock_label(raw_label)
    confidence = _coerce_confidence(response.get("confidence"))
    explanation_raw = response.get("explanation")
    explanation = explanation_raw.strip() if isinstance(explanation_raw, str) else ""
    if label is None or confidence is None:
        return None
    confidence = max(0.0, min(1.0, round(confidence, 3)))
    warnings: list[AnalysisWarning] = []
    if confidence < 0.45:
        warnings.append(
            AnalysisWarning(
                code="intent_llm_low_confidence",
                message="llm-like response confidence is low; downstream should treat as partial.",
                source_id=source_id,
                metadata={"confidence": confidence},
            )
        )
    if not explanation:
        explanation = "Intent label came from structured llm-like response metadata."
    return label, confidence, explanation, warnings
