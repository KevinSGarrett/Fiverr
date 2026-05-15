"""Deterministic fixture factories for analysis-stage tests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def _load_fixture(name: str) -> dict[str, Any]:
    fixture_path = Path(__file__).resolve().parent / name
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def make_complete_market_payload() -> dict[str, Any]:
    """Return a full fixture with keywords, gig, competitors, sellers, reviews, and intent."""
    return deepcopy(_load_fixture("complete_payload.json"))


def make_sparse_gig_only_payload() -> dict[str, Any]:
    """Return sparse payload with mostly gig-only data and minimal supporting context."""
    payload = {
        "run_id": "run-factory-sparse-gig-only",
        "source_id": "src-factory-sparse-gig-only",
        "keywords": ["automation"],
        "gig": {"gig_id": "gig-factory-sparse"},
        "intent": {"keyword_text": "automation service"},
    }
    return deepcopy(payload)


def make_missing_seller_payload() -> dict[str, Any]:
    """Return payload with no seller records but other analysis inputs present."""
    payload = make_complete_market_payload()
    payload.pop("seller", None)
    payload.pop("sellers", None)
    return payload


def make_missing_reviews_payload() -> dict[str, Any]:
    """Return payload where reviews are intentionally absent for sparse compatibility checks."""
    payload = make_complete_market_payload()
    payload.pop("reviews", None)
    return payload


def make_empty_upstream_payload() -> dict[str, Any]:
    """Return near-empty payload to validate safe stage degradation paths."""
    payload = {
        "run_id": "run-factory-empty-upstream",
        "source_id": "src-factory-empty-upstream",
    }
    return deepcopy(payload)
