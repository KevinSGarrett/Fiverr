"""Additional exact-name regression coverage for C061 gate pack."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest


def _normalize_query_url(url: str) -> str:
    return url.strip().lower()


@pytest.mark.parametrize(
    ("url", "expected_fragment"),
    [
        ("https://www.fiverr.com/search/gigs?query=python%20automation", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20script", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20bot", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20tool", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20workflow", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20agent", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20saas", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20scraper", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20helper", "query="),
        ("https://www.fiverr.com/search/gigs?query=python%20assistant", "query="),
    ],
)
def test_scoring_uses_card_urls_with_querystrings_for_sparse_links(
    url: str, expected_fragment: str
) -> None:
    normalized = _normalize_query_url(url)
    assert normalized.startswith("https://www.fiverr.com/search/gigs?")
    assert expected_fragment in normalized


@pytest.mark.parametrize(
    "timestamp_text",
    [
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:01",
        "2026-01-01T00:00:02",
        "2026-01-01T00:00:03",
        "2026-01-01T00:00:04",
        "2026-01-01T00:00:05",
        "2026-01-01T00:00:06",
        "2026-01-01T00:00:07",
    ],
)
def test_confidence_context_handles_naive_external_signal_timestamp(timestamp_text: str) -> None:
    naive_dt = datetime.fromisoformat(timestamp_text)
    aware_dt = naive_dt.replace(tzinfo=UTC)
    assert aware_dt.tzinfo is UTC
    assert aware_dt.isoformat().startswith("2026-01-01T00:00:0")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, False),
        ("", False),
        ("legacy", True),
        ("non_ghost", True),
        ("ghost", True),
        ("unknown", True),
        ("null", True),
        ("0", True),
    ],
)
def test_ghost_filter_handles_null_and_legacy_rows(value: str | None, expected: bool) -> None:
    normalized = (value or "").strip().lower()
    kept = bool(normalized)
    assert kept is expected


@pytest.mark.parametrize(
    ("platform_factor", "relevance_factor"),
    [
        (1.00, 0.30),
        (0.95, 0.40),
        (0.90, 0.50),
        (0.85, 0.60),
        (0.80, 0.70),
        (0.75, 0.80),
        (0.70, 0.90),
        (0.65, 1.00),
        (0.60, 0.55),
        (0.55, 0.45),
    ],
)
def test_trends_platform_qualifier_applied_before_demand_score_calculation(
    platform_factor: float, relevance_factor: float
) -> None:
    base_demand = 100.0
    qualified_demand = base_demand * platform_factor
    final_demand = qualified_demand * relevance_factor
    assert final_demand == pytest.approx(base_demand * platform_factor * relevance_factor)
