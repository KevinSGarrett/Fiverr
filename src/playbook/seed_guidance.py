"""Seed payload guidance helpers for onboarding and playbook workflows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_SEED_FIELDS = ["niche_id", "keywords"]
MIN_KEYWORDS = 6
MAX_KEYWORDS = 8

SEED_SHAPE_MESSAGE = (
    "Each niche seed payload should contain 'niche_id' and 6-8 keywords in 'keywords'."
)


def validate_seed_payload_shape(payload: Mapping[str, Any]) -> bool:
    """Validate required seed shape without touching config or database layers."""
    niche_id = payload.get("niche_id")
    if not isinstance(niche_id, str) or not niche_id.strip():
        raise ValueError(f"Missing or invalid niche_id. {SEED_SHAPE_MESSAGE}")

    keywords = payload.get("keywords")
    if not isinstance(keywords, list):
        raise ValueError(f"Missing or invalid keywords list. {SEED_SHAPE_MESSAGE}")

    keyword_count = len(keywords)
    if keyword_count < MIN_KEYWORDS or keyword_count > MAX_KEYWORDS:
        raise ValueError(
            f"Keywords must include {MIN_KEYWORDS}-{MAX_KEYWORDS} items. "
            f"Received {keyword_count}. {SEED_SHAPE_MESSAGE}"
        )

    if any(not isinstance(keyword, str) or not keyword.strip() for keyword in keywords):
        raise ValueError(f"Keywords must be non-empty strings. {SEED_SHAPE_MESSAGE}")

    return True

