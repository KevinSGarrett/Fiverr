"""Fixture-backed external trend signal contracts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path


class SignalSource(StrEnum):
    """Allowed signal source names."""

    GOOGLE_TRENDS = "google_trends"
    EXPLODING_TOPICS = "exploding_topics"
    MARKETPLACE_INDEX = "marketplace_index"


class SignalFreshness(StrEnum):
    """Freshness state for ingested signal records."""

    FRESH = "fresh"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class ExternalSignal:
    """External trend signal record."""

    keyword: str
    source: SignalSource
    score: float
    captured_at: datetime
    source_keyword: str
    freshness: SignalFreshness


class LiveSignalConnectorDisabledError(RuntimeError):
    """Raised when a live connector is requested before implementation."""


def _parse_source(value: str) -> SignalSource:
    try:
        return SignalSource(value)
    except ValueError as exc:
        allowed = ", ".join(source.value for source in SignalSource)
        raise ValueError(f"Unsupported signal source '{value}'. Allowed: {allowed}.") from exc


def load_external_signal_fixture(
    fixture_path: Path | str,
    *,
    stale_after_days: int = 14,
    now: datetime | None = None,
) -> list[ExternalSignal]:
    """Read external trend signals from local fixture JSON only."""

    path = Path(fixture_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("External signal fixture must be a JSON array.")

    now_utc = now or datetime.now(UTC)
    stale_cutoff = now_utc - timedelta(days=stale_after_days)
    records: list[ExternalSignal] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid external signal at index {index}.")
        keyword = item.get("keyword")
        source_keyword = item.get("source_keyword", keyword)
        source = item.get("source")
        captured_at_raw = item.get("captured_at")
        score = item.get("score")
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError(f"Invalid keyword at index {index}.")
        if not isinstance(source_keyword, str) or not source_keyword.strip():
            raise ValueError(f"Invalid source_keyword at index {index}.")
        if not isinstance(source, str):
            raise ValueError(f"Invalid source at index {index}.")
        if not isinstance(captured_at_raw, str):
            raise ValueError(f"Invalid captured_at at index {index}.")
        if not isinstance(score, (int, float)):
            raise ValueError(f"Invalid score at index {index}.")

        captured_at = datetime.fromisoformat(captured_at_raw.replace("Z", "+00:00")).astimezone(UTC)
        freshness = SignalFreshness.STALE if captured_at < stale_cutoff else SignalFreshness.FRESH
        records.append(
            ExternalSignal(
                keyword=keyword.strip(),
                source=_parse_source(source.strip()),
                score=float(score),
                captured_at=captured_at,
                source_keyword=source_keyword.strip(),
                freshness=freshness,
            )
        )
    return records


def fetch_external_signals_live(*_: object, **__: object) -> list[ExternalSignal]:
    """Disallow live connector calls until explicitly implemented."""

    raise LiveSignalConnectorDisabledError(
        "Live external signal connector is disabled by default. Use fixture ingestion instead."
    )
