"""Fixture-backed autocomplete ingestion and dry-run planning."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.collection.keyword_expansion import normalize_keyword


class AutocompleteFixtureError(ValueError):
    """Raised when autocomplete fixture payload is invalid."""


@dataclass(frozen=True, slots=True)
class AutocompleteSuggestion:
    """Single normalized autocomplete suggestion."""

    suggestion: str
    seed_keyword: str
    source: str
    mode: str = "fixture"


@dataclass(frozen=True, slots=True)
class AutocompletePlan:
    """Dry-run autocomplete plan result."""

    seed_keyword: str
    mode: str
    suggestions: list[AutocompleteSuggestion] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _coerce_suggestion_items(payload: object) -> list[str]:
    if isinstance(payload, list):
        items: list[str] = []
        for item in payload:
            if isinstance(item, str):
                items.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                items.append(item["text"])
            else:
                raise AutocompleteFixtureError("Invalid suggestion item in fixture payload.")
        return items
    if isinstance(payload, dict):
        suggestions = payload.get("suggestions", [])
        if isinstance(suggestions, list):
            return _coerce_suggestion_items(suggestions)
    raise AutocompleteFixtureError("Autocomplete fixture must be a list or object with suggestions.")


def load_autocomplete_fixture(
    fixture_path: Path | str,
    *,
    seed_keyword: str,
    source: str = "fixture",
) -> AutocompletePlan:
    """Load local autocomplete fixture and return dry-run plan."""

    path = Path(fixture_path)
    raw = path.read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AutocompleteFixtureError(f"Invalid autocomplete fixture JSON: {exc.msg}") from exc

    warnings: list[str] = []
    normalized_seed = normalize_keyword(seed_keyword)
    if not normalized_seed:
        raise AutocompleteFixtureError("Seed keyword must not be empty after normalization.")

    raw_items = _coerce_suggestion_items(payload)
    seen: set[str] = set()
    suggestions: list[AutocompleteSuggestion] = []
    for item in raw_items:
        normalized = normalize_keyword(item)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        suggestions.append(
            AutocompleteSuggestion(
                suggestion=normalized,
                seed_keyword=normalized_seed,
                source=source,
                mode="fixture",
            )
        )

    if not suggestions:
        warnings.append("Autocomplete fixture yielded no suggestions.")

    return AutocompletePlan(
        seed_keyword=normalized_seed,
        mode="dry_run",
        suggestions=suggestions,
        warnings=warnings,
    )
