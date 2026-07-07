"""Seed payload guidance helpers for onboarding and playbook workflows."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REQUIRED_SEED_FIELDS = ["niche_id", "keywords", "source_lineage"]
MIN_KEYWORDS = 6
NICHE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")

SEED_SHAPE_MESSAGE = (
    "Each niche seed payload must include 'niche_id' and at least 6 keywords in 'keywords'."
)


def get_seed_guidance_summary() -> str:
    """Return concise guidance for operator docs and onboarding flows."""
    return (
        "Seed payloads must include niche_id, keywords, and source_lineage. "
        "niche_id uses lowercase letters, numbers, and underscores only. "
        "keywords must be non-empty strings with no case-insensitive duplicates. "
        "config.yaml stores niche configuration, seed payloads preserve keyword lineage, "
        "and the database stores imported records."
    )


def validate_seed_payload_shape(payload: Mapping[str, Any]) -> bool:
    """Validate required seed shape without touching config or database layers."""
    niche_id = payload.get("niche_id")
    if not isinstance(niche_id, str) or not niche_id.strip():
        raise ValueError(f"Missing or invalid niche_id. {SEED_SHAPE_MESSAGE}")
    if not NICHE_ID_PATTERN.fullmatch(niche_id):
        raise ValueError(
            "niche_id must match ^[a-z0-9_]+$ (lowercase letters, numbers, underscores only)."
        )

    source_lineage = payload.get("source_lineage")
    if not isinstance(source_lineage, Mapping):
        raise ValueError("Missing or invalid source_lineage mapping.")

    source = source_lineage.get("source")
    lineage_method = source_lineage.get("method")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("source_lineage.source is required.")
    if not isinstance(lineage_method, str) or not lineage_method.strip():
        raise ValueError("source_lineage.method is required.")

    keywords = payload.get("keywords")
    if not isinstance(keywords, list):
        raise ValueError(f"Missing or invalid keywords list. {SEED_SHAPE_MESSAGE}")

    keyword_count = len(keywords)
    if keyword_count < MIN_KEYWORDS:
        raise ValueError(
            f"Keywords must include at least {MIN_KEYWORDS} items. "
            f"Received {keyword_count}. {SEED_SHAPE_MESSAGE}"
        )

    # Real data/seeds/*.yaml entries are mappings ({"keyword": ..., "normalized_keyword":
    # ..., "language": ..., "source": ...}); plain strings are also accepted for
    # config-style seed lists. The string-only assumption previously meant this gate
    # could never validate the shipped seed files at all (SCRUM-1115).
    keyword_texts: list[str] = []
    for entry in keywords:
        if isinstance(entry, str):
            keyword_text = entry
        elif isinstance(entry, Mapping):
            raw_text = entry.get("keyword")
            keyword_text = raw_text if isinstance(raw_text, str) else ""
        else:
            keyword_text = ""
        if not keyword_text.strip():
            raise ValueError(
                f"Keywords must be non-empty strings or mappings with a non-empty "
                f"'keyword' key. {SEED_SHAPE_MESSAGE}"
            )
        keyword_texts.append(keyword_text)

    normalized_keywords = [keyword.strip().lower() for keyword in keyword_texts]
    if len(set(normalized_keywords)) != len(normalized_keywords):
        raise ValueError("Duplicate keywords are not allowed (case-insensitive, trimmed comparison).")

    return True

