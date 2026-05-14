"""Deterministic keyword expansion for dry-run collection planning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


def normalize_keyword(value: str) -> str:
    """Normalize keyword text for deterministic comparison and output."""

    return " ".join(value.strip().lower().split())


@dataclass(frozen=True, slots=True)
class ExpandedKeyword:
    """Expanded keyword candidate with lineage metadata."""

    keyword_id: str
    keyword: str
    source_seed: str
    expansion_method: str


@dataclass(frozen=True, slots=True)
class KeywordExpansionResult:
    """Result object for deterministic keyword expansion stage."""

    expanded_keywords: list[ExpandedKeyword]
    warnings: list[str] = field(default_factory=list)


def _iter_niche_modifiers(niche_metadata: Mapping[str, Any] | None) -> list[str]:
    if not niche_metadata:
        return []

    modifiers: list[str] = []
    raw_modifiers = niche_metadata.get("modifiers", [])
    if isinstance(raw_modifiers, Sequence) and not isinstance(raw_modifiers, (str, bytes)):
        for modifier in raw_modifiers:
            if isinstance(modifier, str):
                normalized = normalize_keyword(modifier)
                if normalized:
                    modifiers.append(normalized)

    niche_name = niche_metadata.get("niche")
    if isinstance(niche_name, str):
        normalized_niche = normalize_keyword(niche_name)
        if normalized_niche:
            modifiers.append(normalized_niche)
    return sorted(set(modifiers))


def expand_keywords(
    seed_keywords: Sequence[str],
    niche_metadata: Mapping[str, Any] | None = None,
    *,
    max_candidates: int = 50,
) -> KeywordExpansionResult:
    """Expand seed keywords without network calls and preserve lineage."""

    if max_candidates <= 0:
        raise ValueError("max_candidates must be greater than zero.")

    normalized_seeds: list[str] = []
    for seed in seed_keywords:
        normalized = normalize_keyword(seed)
        if normalized and normalized not in normalized_seeds:
            normalized_seeds.append(normalized)

    if not normalized_seeds:
        return KeywordExpansionResult(
            expanded_keywords=[],
            warnings=["No seed keywords were provided after normalization."],
        )

    modifiers = _iter_niche_modifiers(niche_metadata)
    seen_keywords: set[str] = set()
    expanded: list[ExpandedKeyword] = []

    for source_seed in normalized_seeds:
        candidates: list[tuple[str, str]] = [(source_seed, "seed_normalized")]
        for modifier in modifiers:
            candidates.append((f"{source_seed} {modifier}", "seed_plus_modifier"))
            candidates.append((f"{modifier} {source_seed}", "modifier_plus_seed"))

        for keyword_text, method in candidates:
            normalized_candidate = normalize_keyword(keyword_text)
            if not normalized_candidate or normalized_candidate in seen_keywords:
                continue
            seen_keywords.add(normalized_candidate)
            expanded.append(
                ExpandedKeyword(
                    keyword_id=f"kw-{len(expanded) + 1:04d}",
                    keyword=normalized_candidate,
                    source_seed=source_seed,
                    expansion_method=method,
                )
            )
            if len(expanded) >= max_candidates:
                return KeywordExpansionResult(
                    expanded_keywords=expanded,
                    warnings=[f"Expansion capped at {max_candidates} candidates."],
                )

    return KeywordExpansionResult(expanded_keywords=expanded)
