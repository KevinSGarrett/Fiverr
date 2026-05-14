"""Fixture-backed ingestion for aggregate community signals."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

_SENTIMENT_ALLOWED = {"positive", "neutral", "negative", "mixed"}
_DISALLOWED_KEYS = {"username", "user", "profile_url", "private_email", "account_id"}
_PII_TEXT_RE = re.compile(r"@|https?://|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", flags=re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class CommunitySignal:
    """Aggregate community signal record without personal data."""

    keyword: str
    mention_count: int
    sentiment_hint: str
    sample_theme: str
    source: str
    captured_at: datetime
    confidence: float
    source_keyword: str


def load_community_signal_fixture(fixture_path: Path | str) -> tuple[list[CommunitySignal], list[str]]:
    """Load aggregate-only community signal records from local fixture."""

    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Community signal fixture must be a JSON array.")

    warnings: list[str] = []
    records: list[CommunitySignal] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid community signal record at index {index}.")

        disallowed_found = sorted(key for key in item.keys() if key in _DISALLOWED_KEYS)
        if disallowed_found:
            warnings.append(
                f"Ignored disallowed personal-data-like fields at index {index}: {', '.join(disallowed_found)}."
            )

        keyword = item.get("keyword")
        source_keyword = item.get("source_keyword", keyword)
        mention_count = item.get("mention_count", 0)
        sentiment_hint = item.get("sentiment_hint", "neutral")
        sample_theme = item.get("sample_theme", "")
        source = item.get("source", "community_fixture")
        captured_at = item.get("captured_at")
        confidence = item.get("confidence", 0.5)

        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError(f"Invalid keyword at index {index}.")
        if not isinstance(source_keyword, str) or not source_keyword.strip():
            raise ValueError(f"Invalid source_keyword at index {index}.")
        if not isinstance(mention_count, int) or mention_count < 0:
            raise ValueError(f"Invalid mention_count at index {index}.")
        if not isinstance(sentiment_hint, str) or sentiment_hint not in _SENTIMENT_ALLOWED:
            sentiment_hint = "neutral"
            warnings.append(f"Invalid sentiment_hint at index {index}; defaulted to neutral.")
        if not isinstance(sample_theme, str):
            raise ValueError(f"Invalid sample_theme at index {index}.")
        if not isinstance(source, str) or not source.strip():
            raise ValueError(f"Invalid source at index {index}.")
        if not isinstance(captured_at, str):
            raise ValueError(f"Invalid captured_at at index {index}.")
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
            warnings.append(f"Invalid confidence at index {index}; defaulted to 0.5.")

        # Keep aggregate signal text only; strip direct handles/profile links/emails.
        if _PII_TEXT_RE.search(sample_theme):
            warnings.append(f"Sample theme at index {index} looked personal; replaced with aggregate-safe text.")
            sample_theme = "aggregate community discussion"

        records.append(
            CommunitySignal(
                keyword=keyword.strip(),
                mention_count=mention_count,
                sentiment_hint=sentiment_hint,
                sample_theme=sample_theme.strip(),
                source=source.strip(),
                captured_at=datetime.fromisoformat(captured_at.replace("Z", "+00:00")).astimezone(UTC),
                confidence=float(confidence),
                source_keyword=source_keyword.strip(),
            )
        )

    return records, warnings
