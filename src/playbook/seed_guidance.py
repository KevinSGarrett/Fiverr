"""Seed payload guidance helpers for onboarding and playbook workflows."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REQUIRED_SEED_FIELDS = ["niche_id", "keywords"]
MIN_KEYWORDS = 6
NICHE_ID_PATTERN = re.compile(r"^[a-z0-9_]+$")

SEED_SHAPE_MESSAGE = (
    "Each niche seed payload must include 'niche_id' and at least 6 keywords in 'keywords'."
)


def get_seed_guidance_summary() -> str:
    """Return concise guidance for operator docs and onboarding flows."""
    return (
        "Seed payloads must include niche_id and keywords. "
        "niche_id uses lowercase letters, numbers, and underscores only. "
        "keywords must be non-empty strings with no case-insensitive duplicates. "
        "Seed payloads should align with niche identifiers in config.yaml."
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

    keywords = payload.get("keywords")
    if not isinstance(keywords, list):
        raise ValueError(f"Missing or invalid keywords list. {SEED_SHAPE_MESSAGE}")

    keyword_count = len(keywords)
    if keyword_count < MIN_KEYWORDS:
        raise ValueError(
            f"Keywords must include at least {MIN_KEYWORDS} items. "
            f"Received {keyword_count}. {SEED_SHAPE_MESSAGE}"
        )

    if any(not isinstance(keyword, str) or not keyword.strip() for keyword in keywords):
        raise ValueError(f"Keywords must be non-empty strings. {SEED_SHAPE_MESSAGE}")

    normalized_keywords = [keyword.strip().lower() for keyword in keywords]
    if len(set(normalized_keywords)) != len(normalized_keywords):
        raise ValueError("Duplicate keywords are not allowed (case-insensitive, trimmed comparison).")

    return True

