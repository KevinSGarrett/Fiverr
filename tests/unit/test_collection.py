"""Unit tests for Epic 02 collection dry-run planning components."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from src.collection.checkpoint import (
    QueueCheckpointError,
    checkpoint_queue_state,
    load_queue_checkpoint,
)
from src.collection.keyword_expansion import expand_keywords
from src.collection.queue import enqueue_search_plan
from src.collection.search_plan import build_search_plan
from src.collection.selectors import (
    REQUIRED_SELECTORS,
    get_selector,
    parse_search_result_cards_from_html,
    validate_selector_registry,
)
from src.collection.session import (
    BrowserSessionConfig,
    ManagedBrowserSession,
    build_browser_launch_options,
    validate_storage_state_path,
)


def test_validate_storage_state_requires_file_for_authenticated_mode(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing-state.json"
    with pytest.raises(FileNotFoundError):
        validate_storage_state_path(missing_path)


def test_build_browser_launch_options_respects_headless_timeout_and_user_agent(tmp_path: Path) -> None:
    storage_state = tmp_path / "state.json"
    storage_state.write_text("{}", encoding="utf-8")
    options = build_browser_launch_options(
        BrowserSessionConfig(
            headless=False,
            storage_state_path=storage_state,
            user_agent="AgentB/1.0",
            timeout_ms=45_000,
            authenticated_mode=True,
        )
    )
    assert options["headless"] is False
    assert options["timeout"] == 45_000
    assert options["user_agent"] == "AgentB/1.0"
    assert options["storage_state"] == str(storage_state.resolve())


def test_managed_session_closes_injected_browser_cleanly() -> None:
    class FakeBrowser:
        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    browser = FakeBrowser()

    async def _run() -> None:
        async with ManagedBrowserSession(BrowserSessionConfig(), browser=browser) as active:
            assert active is browser

    asyncio.run(_run())
    assert browser.closed is True


def test_selector_registry_contains_required_groups_and_selectors() -> None:
    assert validate_selector_registry() == []
    for group, selector_names in REQUIRED_SELECTORS.items():
        for selector_name in selector_names:
            assert get_selector(group, selector_name)


def test_missing_selector_raises_clear_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown selector"):
        get_selector("search_results", "does_not_exist")


def test_fixture_search_page_extracts_two_or_more_result_cards() -> None:
    fixture_path = Path("tests/fixtures/collection/search_results.html")
    cards = parse_search_result_cards_from_html(fixture_path.read_text(encoding="utf-8"))
    assert len(cards) >= 2
    assert all(card.url.startswith("/services/") for card in cards)


def test_duplicate_seeds_collapse_deterministically() -> None:
    result = expand_keywords([" Logo Design ", "logo   design", "LOGO DESIGN"], max_candidates=10)
    assert [item.keyword for item in result.expanded_keywords] == ["logo design"]


def test_keyword_expansion_preserves_lineage() -> None:
    result = expand_keywords(["seo audit"], niche_metadata={"modifiers": ["local"]}, max_candidates=10)
    assert result.expanded_keywords
    assert {item.source_seed for item in result.expanded_keywords} == {"seo audit"}
    assert {item.expansion_method for item in result.expanded_keywords} >= {"seed_normalized"}


def test_keyword_expansion_enforces_candidate_cap() -> None:
    result = expand_keywords(
        ["seo audit", "landing page copy"],
        niche_metadata={"modifiers": ["local", "b2b", "enterprise"]},
        max_candidates=3,
    )
    assert len(result.expanded_keywords) == 3
    assert any("capped" in warning for warning in result.warnings)


def test_keyword_expansion_empty_seeds_returns_warning() -> None:
    result = expand_keywords([], max_candidates=5)
    assert result.expanded_keywords == []
    assert any("No seed keywords" in warning for warning in result.warnings)


def test_search_plan_url_encoding_and_lineage() -> None:
    expanded = expand_keywords(["Logo Design"], max_candidates=5).expanded_keywords
    plan = build_search_plan(expanded, region="United States", language="en", sort="rating", max_pages=2)
    assert plan.items
    first = plan.items[0]
    assert "query=logo+design" in first.url
    assert "location=United+States" in first.url
    assert first.source_seed == "logo design"


def test_search_plan_page_range_respects_max_pages() -> None:
    expanded = expand_keywords(["keyword"], max_candidates=5).expanded_keywords
    plan = build_search_plan(expanded, max_pages=3)
    assert [item.page_number for item in plan.items] == [1, 2, 3]


def test_search_plan_invalid_max_pages_fails() -> None:
    expanded = expand_keywords(["keyword"], max_candidates=5).expanded_keywords
    with pytest.raises(ValueError, match="max_pages"):
        build_search_plan(expanded, max_pages=0)


def test_enqueue_search_plan_creates_expected_job_count() -> None:
    expanded = expand_keywords(["logo design"], max_candidates=5).expanded_keywords
    plan = build_search_plan(expanded, max_pages=2)
    queue = enqueue_search_plan(plan)
    assert len(queue.jobs) == 2


def test_checkpoint_writes_valid_json_atomically(tmp_path: Path) -> None:
    expanded = expand_keywords(["logo design"], max_candidates=5).expanded_keywords
    plan = build_search_plan(expanded, max_pages=1)
    queue = enqueue_search_plan(plan)
    checkpoint_path = tmp_path / "queue.json"
    saved_path = checkpoint_queue_state(queue, checkpoint_path)
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload["jobs"][0]["status"] == "pending"


def test_corrupted_checkpoint_returns_controlled_error(tmp_path: Path) -> None:
    corrupted_path = tmp_path / "bad.json"
    corrupted_path.write_text("{bad-json", encoding="utf-8")
    with pytest.raises(QueueCheckpointError):
        load_queue_checkpoint(corrupted_path)


def test_job_ordering_is_deterministic() -> None:
    expanded = expand_keywords(["b", "a"], max_candidates=10).expanded_keywords
    plan = build_search_plan(expanded, max_pages=2)
    queue = enqueue_search_plan(plan)
    ordered = [job.job_id for job in queue.jobs]
    assert ordered == sorted(ordered)
