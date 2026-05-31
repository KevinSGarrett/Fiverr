"""Result-set relevance validation for Stage 3.5 (SRDI Tier-0 R2)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

NICHE_VALIDATION_CONFIG_VERSION = "r2.1"
_NEXT_REVIEW = "2026-07-01"
NICHE_VALIDATION_CONFIG_NEXT_REVIEW = _NEXT_REVIEW

GENERIC_PHRASES = [
    "i will",
    "professional",
    "expert",
    "high quality",
    "fast delivery",
    "best",
    "cheap",
    "any",
]


@dataclass
class GigRelevanceResult:
    gig_url: str
    gig_title: str
    relevance_score: float
    relevance_flag: bool
    relevance_signals: dict[str, Any] = field(default_factory=dict)
    rejection_reason: str | None = None


@dataclass
class ResultSetValidationResult:
    total_analyzed: int
    relevant_count: int
    sponsored_count: int
    result_set_relevance_score: float
    category_contamination_flag: bool
    ghost_market_flag: bool
    confidence_deduction: float
    gig_results: list[GigRelevanceResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())).strip()


def _tokenize(text: str) -> list[str]:
    normalized = _normalize(text)
    return [token for token in normalized.split(" ") if token]


def _deduction_for(score: float) -> float:
    if score >= 0.80:
        return 0.0
    if score >= 0.60:
        return -0.05
    if score >= 0.40:
        return -0.15
    if score >= 0.20:
        return -0.30
    return -0.50


def compute_gig_relevance(
    gig_title: str,
    keyword_text: str,
    niche_id: str | int,
    validation_config: dict[str, Any],
) -> GigRelevanceResult:
    if not gig_title or not gig_title.strip():
        return GigRelevanceResult(
            gig_url="",
            gig_title=gig_title or "",
            relevance_score=0.0,
            relevance_flag=False,
            relevance_signals={},
            rejection_reason="missing_title",
        )

    del niche_id  # scorer is pure and intentionally DB-agnostic
    title_l = _normalize(gig_title)
    title_tokens = set(_tokenize(gig_title))
    keyword_l = _normalize(keyword_text)
    keyword_tokens = [token for token in _tokenize(keyword_text) if len(token) > 3]

    core_terms = [str(value).lower() for value in validation_config.get("core_terms", [])]
    exclusion_terms = [str(value).lower() for value in validation_config.get("exclusion_terms", [])]
    threshold = float(validation_config.get("relevance_flag_threshold", 0.35))

    if keyword_l and keyword_l in title_l:
        signal_phrase = 0.40
    else:
        overlap = len([token for token in keyword_tokens if token in title_tokens]) / max(len(keyword_tokens), 1)
        signal_phrase = overlap * 0.40 * 0.70

    core_present = sum(1 for term in core_terms if term in title_l)
    signal_core = (core_present / max(len(core_terms), 1)) * 0.35

    exclusion_hits = sum(1 for term in exclusion_terms if term in title_l)
    signal_exclusion = -0.25 * exclusion_hits

    generic_hits = sum(1 for phrase in GENERIC_PHRASES if phrase in title_l)
    signal_generic = -0.15 if generic_hits >= 3 and core_present == 0 else 0.0

    score = max(0.0, min(1.0, signal_phrase + signal_core + signal_exclusion + signal_generic))
    flagged = score >= threshold

    reason: str | None = None
    if exclusion_hits > 0 and not flagged:
        reason = "exclusion_term"
    elif core_present == 0 and not flagged:
        reason = "no_niche_terms"
    elif not flagged:
        reason = "low_score"

    signals = {
        "phrase_token": round(signal_phrase, 4),
        "core_term_ratio": round(signal_core, 4),
        "exclusion_penalty": round(signal_exclusion, 4),
        "generic_penalty": round(signal_generic, 4),
        "core_terms_present": core_present,
        "generic_phrases_hit": generic_hits,
        "exclusion_terms_hit": exclusion_hits,
    }
    return GigRelevanceResult(
        gig_url="",
        gig_title=gig_title,
        relevance_score=round(score, 4),
        relevance_flag=flagged,
        relevance_signals=signals,
        rejection_reason=reason,
    )


def validate_result_set(
    gig_cards: list[dict[str, Any]],
    keyword_text: str,
    niche_id: str | int,
    validation_config: dict[str, Any],
) -> ResultSetValidationResult:
    total = len(gig_cards)
    if total == 0:
        return ResultSetValidationResult(
            total_analyzed=0,
            relevant_count=0,
            sponsored_count=0,
            result_set_relevance_score=0.0,
            category_contamination_flag=False,
            ghost_market_flag=True,
            confidence_deduction=-0.50,
            gig_results=[],
            warnings=["no_results_to_validate"],
        )

    results: list[GigRelevanceResult] = []
    sponsored_count = 0
    for card in gig_cards:
        if bool(card.get("sponsored")) or bool(card.get("sponsored_flag")):
            sponsored_count += 1
        result = compute_gig_relevance(
            gig_title=str(card.get("gig_title", "")),
            keyword_text=keyword_text,
            niche_id=niche_id,
            validation_config=validation_config,
        )
        result.gig_url = str(card.get("gig_url", ""))
        results.append(result)

    relevant_count = sum(1 for result in results if result.relevance_flag)
    score = relevant_count / total
    ghost_threshold = float(validation_config.get("ghost_market_threshold", 0.20))
    ghost = score < ghost_threshold and total > 5
    contamination = (0.40 <= score < 0.60) and total >= 5 and not ghost
    deduction = _deduction_for(score)

    if ghost:
        warning = f"ghost_market_{score:.2f}"
    elif score >= 0.80:
        warning = "clean_results_1.00"
    elif score >= 0.60:
        warning = f"mild_contamination_{score:.2f}"
    elif score >= 0.40:
        warning = f"moderate_contamination_{score:.2f}"
    elif score >= 0.20:
        warning = f"heavy_contamination_{score:.2f}"
    else:
        warning = f"severe_contamination_{score:.2f}"

    return ResultSetValidationResult(
        total_analyzed=total,
        relevant_count=relevant_count,
        sponsored_count=sponsored_count,
        result_set_relevance_score=round(score, 4),
        category_contamination_flag=contamination,
        ghost_market_flag=ghost,
        confidence_deduction=deduction,
        gig_results=results,
        warnings=[warning],
    )


NICHE_VALIDATION_CONFIG: dict[str, dict[str, Any]] = {
    "mcp_servers": {
        "core_terms": [
            "mcp",
            "model context protocol",
            "claude",
            "server",
            "integration",
            "tool",
        ],
        "exclusion_terms": ["logo", "video", "resume", "wordpress theme"],
        "ghost_market_threshold": 0.10,
    },
    "gumloop_workflows": {
        "core_terms": [
            "gumloop",
            "workflow",
            "automation",
            "no-code",
            "pipeline",
            "integration",
        ],
        "exclusion_terms": ["logo", "essay", "resume", "voiceover"],
        "ghost_market_threshold": 0.10,
    },
    "devvit_apps": {
        "core_terms": [
            "devvit",
            "reddit app",
            "reddit",
            "developer platform",
            "subreddit",
            "bot",
        ],
        "exclusion_terms": ["logo", "nft", "resume", "squarespace"],
        "ghost_market_threshold": 0.10,
    },
    "support_kb_readiness": {
        "core_terms": [
            "knowledge base",
            "help center",
            "support docs",
            "faq",
            "documentation",
            "help desk",
            "chatbot handoff",
            "support agent",
        ],
        "exclusion_terms": ["logo", "video", "wedding invitation", "gaming montage"],
        "ghost_market_threshold": 0.20,
    },
    "chatbot_build": {
        "core_terms": [
            "chatbot",
            "conversational",
            "dialogflow",
            "bot",
            "assistant",
            "nlp",
        ],
        "exclusion_terms": ["logo", "resume", "medical tutoring", "essay"],
        "ghost_market_threshold": 0.20,
    },
    "data_pipeline": {
        "core_terms": [
            "data pipeline",
            "etl",
            "ingestion",
            "airflow",
            "warehouse",
            "transform",
        ],
        "exclusion_terms": ["logo", "tutoring", "resume", "social media post"],
        "ghost_market_threshold": 0.20,
    },
    "prompt_engineering": {
        "core_terms": [
            "prompt",
            "prompt engineering",
            "llm",
            "gpt",
            "fine-tune",
            "system prompt",
        ],
        "exclusion_terms": ["logo", "essay", "translation", "resume"],
        "ghost_market_threshold": 0.20,
    },
    "api_integration": {
        "core_terms": [
            "api",
            "integration",
            "rest",
            "webhook",
            "endpoint",
            "oauth",
        ],
        "exclusion_terms": ["logo", "writing", "resume", "essay"],
        "ghost_market_threshold": 0.20,
    },
    "browser_automation": {
        "core_terms": [
            "browser automation",
            "playwright",
            "selenium",
            "puppeteer",
            "scraping",
            "automation",
        ],
        "exclusion_terms": ["logo", "resume", "wedding invitation", "voiceover"],
        "ghost_market_threshold": 0.20,
    },
}

DEFAULT_VALIDATION_CONFIG = {
    "core_terms": [],
    "exclusion_terms": [],
    "ghost_market_threshold": 0.20,
}

_LEGACY_NICHE_ALIASES = {
    "prd_ai_saas": "support_kb_readiness",
    "gumloop_lindy_workflow": "gumloop_workflows",
    "mcp_ai_agent": "mcp_servers",
    "python_automation": "api_integration",
    "ai_tool_llm_integration": "prompt_engineering",
    "ai_agent_development": "chatbot_build",
    "workflow_automation": "data_pipeline",
    "python_web_scraping": "browser_automation",
}

_NUMERIC_NICHE_ALIASES = {
    1: "support_kb_readiness",
}


def _niche_slug_for_id(niche_id: int) -> str | None:
    if niche_id in _NUMERIC_NICHE_ALIASES:
        return _NUMERIC_NICHE_ALIASES[niche_id]
    niche_text = str(niche_id)
    if niche_text in NICHE_VALIDATION_CONFIG:
        return niche_text
    return None


def get_validation_config(niche_id: str | int) -> dict[str, Any]:
    if isinstance(niche_id, str):
        lookup_key = _LEGACY_NICHE_ALIASES.get(niche_id, niche_id)
        if lookup_key in NICHE_VALIDATION_CONFIG:
            return dict(NICHE_VALIDATION_CONFIG[lookup_key])
    if isinstance(niche_id, int):
        slug = _niche_slug_for_id(niche_id)
        if slug is not None:
            return dict(NICHE_VALIDATION_CONFIG[slug])
    return dict(DEFAULT_VALIDATION_CONFIG)
