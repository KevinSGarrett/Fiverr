"""Unit tests for Epic 02 collection dry-run planning components."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from src.collection.autocomplete import AutocompleteFixtureError, load_autocomplete_fixture
from src.collection.checkpoint import (
    QueueCheckpointError,
    checkpoint_queue_state,
    load_checkpoint_stage_summary,
    load_checkpoint_stage_summary_or_fallback,
    load_queue_checkpoint,
)
from src.collection.community_signals import load_community_signal_fixture
from src.collection.contracts import CollectionCheckpointEvidence, validate_collection_stage_summary
from src.collection.external_signals import (
    LiveSignalConnectorDisabledError,
    SignalFreshness,
    fetch_external_signals_live,
    load_external_signal_fixture,
)
from src.collection.gig_detail import parse_gig_detail_from_html
from src.collection.html_text import clean_html_text, extract_data_testid_text
from src.collection.keyword_expansion import expand_keywords
from src.collection.orchestrator import run_collection_dry_run
from src.collection.queue import enqueue_search_plan
from src.collection.search_plan import build_search_plan
from src.collection.selectors import (
    REQUIRED_SELECTORS,
    get_selector,
    parse_search_result_cards_from_html,
    validate_selector_registry,
)
from src.collection.seller_profile import parse_seller_profile_from_html
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


def test_validate_storage_state_path_requires_explicit_file_path() -> None:
    with pytest.raises(ValueError, match="requires a storage_state_path"):
        validate_storage_state_path(None)


def test_validate_storage_state_path_rejects_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must be a file"):
        validate_storage_state_path(tmp_path)


def test_build_browser_launch_options_rejects_non_positive_timeout() -> None:
    with pytest.raises(ValueError, match="timeout_ms must be greater than zero"):
        build_browser_launch_options(BrowserSessionConfig(timeout_ms=0))


def test_managed_session_requires_browser_or_factory() -> None:
    async def _run() -> None:
        with pytest.raises(RuntimeError, match="requires injected browser or playwright_factory"):
            async with ManagedBrowserSession(BrowserSessionConfig()):
                pass

    asyncio.run(_run())


def test_managed_session_requires_playwright_chromium_launcher() -> None:
    class FakePlaywright:
        async def stop(self) -> None:
            return None

    async def _run() -> None:
        with pytest.raises(RuntimeError, match="must expose a chromium launcher"):
            async with ManagedBrowserSession(
                BrowserSessionConfig(),
                playwright_factory=lambda: FakePlaywright(),
            ):
                pass

    asyncio.run(_run())


def test_managed_session_playwright_factory_launches_and_stops() -> None:
    class FakeBrowser:
        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    class FakeChromium:
        def __init__(self, browser: FakeBrowser) -> None:
            self._browser = browser
            self.launch_options: dict[str, object] | None = None

        async def launch(self, **kwargs: object) -> FakeBrowser:
            self.launch_options = dict(kwargs)
            return self._browser

    class FakePlaywright:
        def __init__(self, chromium: FakeChromium) -> None:
            self.chromium = chromium
            self.stopped = False

        async def stop(self) -> None:
            self.stopped = True

    browser = FakeBrowser()
    chromium = FakeChromium(browser)
    playwright = FakePlaywright(chromium)

    async def _run() -> None:
        async with ManagedBrowserSession(
            BrowserSessionConfig(headless=False, timeout_ms=45_000),
            playwright_factory=lambda: playwright,
        ) as active_browser:
            assert active_browser is browser

    asyncio.run(_run())
    assert chromium.launch_options == {"headless": False, "timeout": 45_000}
    assert browser.closed is True
    assert playwright.stopped is True


def test_selector_registry_contains_required_groups_and_selectors() -> None:
    assert validate_selector_registry() == []
    for group, selector_names in REQUIRED_SELECTORS.items():
        for selector_name in selector_names:
            assert get_selector(group, selector_name)


def test_missing_selector_raises_clear_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown selector"):
        get_selector("search_results", "does_not_exist")


def test_missing_selector_group_raises_clear_key_error() -> None:
    with pytest.raises(KeyError, match="Unknown selector group"):
        get_selector("unknown_group", "gig_title")


def test_validate_selector_registry_reports_missing_groups_and_selectors() -> None:
    registry = {
        "search_results": {"result_card": "", "gig_title": "h3"},
        "gig_detail": {"gig_detail_title": "h1"},
        "seller_profile": {
            "seller_profile_name": "h1",
            "seller_profile_level": "span",
            "seller_profile_rating": "span",
            "seller_profile_response_time": "span",
        },
        "page_state": {"unavailable_indicator": ".unavailable"},
    }
    errors = validate_selector_registry(registry)
    assert "Missing selector group 'pagination'." in errors
    assert "Missing selector 'result_card' in group 'search_results'." in errors
    assert "Missing selector 'package_cards' in group 'gig_detail'." in errors
    assert "Missing selector 'blocked_indicator' in group 'page_state'." in errors


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


def test_checkpoint_can_include_stage_summary(tmp_path: Path) -> None:
    expanded = expand_keywords(["logo design"], max_candidates=5).expanded_keywords
    plan = build_search_plan(expanded, max_pages=1)
    queue = enqueue_search_plan(plan)
    checkpoint_path = tmp_path / "queue_with_summary.json"
    saved_path = checkpoint_queue_state(
        queue,
        checkpoint_path,
        stage_summary={"stage_counts": {"stage_4_gig_detail": 1}},
    )
    payload = json.loads(saved_path.read_text(encoding="utf-8"))
    assert payload["stage_summary"]["stage_counts"]["stage_4_gig_detail"] == 1


def test_checkpoint_stage_summary_round_trip_remains_valid_when_keys_sorted(tmp_path: Path) -> None:
    expanded = expand_keywords(["logo design"], max_candidates=5).expanded_keywords
    plan = build_search_plan(expanded, max_pages=1)
    queue = enqueue_search_plan(plan)
    checkpoint_path = tmp_path / "queue_with_stage_summary.json"
    stage_summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 1,
            "stage_2b_autocomplete": 0,
            "stage_2_search_plan": 1,
            "stage_3_queue": 1,
            "stage_4_gig_detail": 0,
            "stage_5_seller_profile": 0,
            "stage_6a_external_signals": 0,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "stage_names": [
            "stage_1_keyword_expansion",
            "stage_2b_autocomplete",
            "stage_2_search_plan",
            "stage_3_queue",
            "stage_4_gig_detail",
            "stage_5_seller_profile",
            "stage_6a_external_signals",
            "stage_6b_community_signals",
            "stage_7_checkpoint_metadata",
            "stage_8_pacing_decisions",
            "stage_9_auto_promotion_decision",
        ],
        "stage_execution": [
            {
                "stage_name": "stage_1_keyword_expansion",
                "execution_index": 1,
                "status": "success",
                "started_at": "2026-05-14T00:00:00+00:00",
                "finished_at": "2026-05-14T00:00:00.001000+00:00",
                "resumable_stage_id": "dryrun-demo:01:stage_1_keyword_expansion",
            },
            {
                "stage_name": "stage_2b_autocomplete",
                "execution_index": 2,
                "status": "skipped",
                "skip_reason": "fixture missing",
                "started_at": "2026-05-14T00:00:00.002000+00:00",
                "finished_at": "2026-05-14T00:00:00.003000+00:00",
                "resumable_stage_id": "dryrun-demo:02:stage_2b_autocomplete",
            },
            {
                "stage_name": "stage_2_search_plan",
                "execution_index": 3,
                "status": "success",
                "started_at": "2026-05-14T00:00:00.004000+00:00",
                "finished_at": "2026-05-14T00:00:00.005000+00:00",
                "resumable_stage_id": "dryrun-demo:03:stage_2_search_plan",
            },
            {
                "stage_name": "stage_3_queue",
                "execution_index": 4,
                "status": "success",
                "started_at": "2026-05-14T00:00:00.006000+00:00",
                "finished_at": "2026-05-14T00:00:00.007000+00:00",
                "resumable_stage_id": "dryrun-demo:04:stage_3_queue",
            },
            {
                "stage_name": "stage_4_gig_detail",
                "execution_index": 5,
                "status": "skipped",
                "skip_reason": "fixture missing",
                "started_at": "2026-05-14T00:00:00.008000+00:00",
                "finished_at": "2026-05-14T00:00:00.009000+00:00",
                "resumable_stage_id": "dryrun-demo:05:stage_4_gig_detail",
            },
            {
                "stage_name": "stage_5_seller_profile",
                "execution_index": 6,
                "status": "skipped",
                "skip_reason": "fixture missing",
                "started_at": "2026-05-14T00:00:00.010000+00:00",
                "finished_at": "2026-05-14T00:00:00.011000+00:00",
                "resumable_stage_id": "dryrun-demo:06:stage_5_seller_profile",
            },
            {
                "stage_name": "stage_6a_external_signals",
                "execution_index": 7,
                "status": "skipped",
                "skip_reason": "fixture missing",
                "started_at": "2026-05-14T00:00:00.012000+00:00",
                "finished_at": "2026-05-14T00:00:00.013000+00:00",
                "resumable_stage_id": "dryrun-demo:07:stage_6a_external_signals",
            },
            {
                "stage_name": "stage_6b_community_signals",
                "execution_index": 8,
                "status": "skipped",
                "skip_reason": "fixture missing",
                "started_at": "2026-05-14T00:00:00.014000+00:00",
                "finished_at": "2026-05-14T00:00:00.015000+00:00",
                "resumable_stage_id": "dryrun-demo:08:stage_6b_community_signals",
            },
            {
                "stage_name": "stage_7_checkpoint_metadata",
                "execution_index": 9,
                "status": "success",
                "started_at": "2026-05-14T00:00:00.016000+00:00",
                "finished_at": "2026-05-14T00:00:00.017000+00:00",
                "resumable_stage_id": "dryrun-demo:09:stage_7_checkpoint_metadata",
            },
            {
                "stage_name": "stage_8_pacing_decisions",
                "execution_index": 10,
                "status": "success",
                "started_at": "2026-05-14T00:00:00.018000+00:00",
                "finished_at": "2026-05-14T00:00:00.019000+00:00",
                "resumable_stage_id": "dryrun-demo:10:stage_8_pacing_decisions",
            },
            {
                "stage_name": "stage_9_auto_promotion_decision",
                "execution_index": 11,
                "status": "skipped",
                "skip_reason": "fixture missing",
                "started_at": "2026-05-14T00:00:00.020000+00:00",
                "finished_at": "2026-05-14T00:00:00.021000+00:00",
                "resumable_stage_id": "dryrun-demo:11:stage_9_auto_promotion_decision",
            },
        ],
        "skipped_stage_names": [
            "stage_2b_autocomplete",
            "stage_4_gig_detail",
            "stage_5_seller_profile",
            "stage_6a_external_signals",
            "stage_6b_community_signals",
            "stage_9_auto_promotion_decision",
        ],
        "failed_stage_names": [],
        "resumable_stage_identity": {
            "run_id": "dryrun-demo",
            "last_completed_stage_id": "dryrun-demo:11:stage_9_auto_promotion_decision",
        },
        "records_seen": 1,
        "records_written": 3,
        "warnings": [],
        "warning_count": 0,
        "failed": False,
    }
    checkpoint_queue_state(queue, checkpoint_path, stage_summary=stage_summary)
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    payload["stage_summary"] = json.loads(json.dumps(payload["stage_summary"], sort_keys=True))
    checkpoint_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    loaded_summary = load_checkpoint_stage_summary(checkpoint_path)
    assert loaded_summary["stage_names"][0] == "stage_1_keyword_expansion"
    assert loaded_summary["stage_execution"][0]["stage_name"] == "stage_1_keyword_expansion"


def test_load_checkpoint_stage_summary_or_fallback_returns_none_for_corrupted_payload(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "corrupted_checkpoint.json"
    checkpoint_path.write_text("{bad-json", encoding="utf-8")
    assert load_checkpoint_stage_summary_or_fallback(checkpoint_path) is None


def test_load_checkpoint_stage_summary_or_fallback_returns_summary_for_valid_object_payload(
    tmp_path: Path,
) -> None:
    checkpoint_path = tmp_path / "object_checkpoint.json"
    checkpoint_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "jobs": [],
                "stage_summary": {
                    "stage_counts": {
                        "stage_1_keyword_expansion": 1,
                        "stage_2b_autocomplete": 0,
                        "stage_2_search_plan": 1,
                        "stage_3_queue": 1,
                        "stage_4_gig_detail": 0,
                        "stage_5_seller_profile": 0,
                        "stage_6a_external_signals": 0,
                        "stage_6b_community_signals": 0,
                        "stage_7_checkpoint_metadata": 1,
                        "stage_8_pacing_decisions": 1,
                        "stage_9_auto_promotion_decision": 0,
                    },
                    "stage_names": [
                        "stage_1_keyword_expansion",
                        "stage_2b_autocomplete",
                        "stage_2_search_plan",
                        "stage_3_queue",
                        "stage_4_gig_detail",
                        "stage_5_seller_profile",
                        "stage_6a_external_signals",
                        "stage_6b_community_signals",
                        "stage_7_checkpoint_metadata",
                        "stage_8_pacing_decisions",
                        "stage_9_auto_promotion_decision",
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    stage_summary = load_checkpoint_stage_summary_or_fallback(checkpoint_path)
    assert stage_summary is not None
    assert stage_summary["stage_counts"]["stage_3_queue"] == 1


def test_load_checkpoint_stage_summary_or_fallback_returns_none_for_non_object_json(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "array_checkpoint.json"
    checkpoint_path.write_text("[]", encoding="utf-8")
    assert load_checkpoint_stage_summary_or_fallback(checkpoint_path) is None


@pytest.mark.parametrize(
    "checkpoint_payload",
    [
        "[]",
        '"fixture-string"',
        "null",
        "42",
        "true",
    ],
)
def test_load_checkpoint_stage_summary_or_fallback_returns_none_for_all_valid_non_object_json_payloads(
    tmp_path: Path, checkpoint_payload: str
) -> None:
    checkpoint_path = tmp_path / "non_object_checkpoint.json"
    checkpoint_path.write_text(checkpoint_payload, encoding="utf-8")
    assert load_checkpoint_stage_summary_or_fallback(checkpoint_path) is None


def test_load_checkpoint_stage_summary_or_fallback_returns_none_for_missing_file(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_checkpoint.json"
    assert load_checkpoint_stage_summary_or_fallback(missing_path) is None


def test_load_checkpoint_stage_summary_or_fallback_returns_none_when_stage_summary_is_missing(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint_without_stage_summary.json"
    checkpoint_path.write_text('{"schema_version":"1.0","jobs":[]}', encoding="utf-8")
    assert load_checkpoint_stage_summary_or_fallback(checkpoint_path) is None


def test_load_checkpoint_stage_summary_requires_stage_summary_mapping(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint_without_stage_summary.json"
    checkpoint_path.write_text('{"schema_version":"1.0","jobs":[]}', encoding="utf-8")
    with pytest.raises(QueueCheckpointError, match="does not include a stage_summary mapping"):
        load_checkpoint_stage_summary(checkpoint_path)


def test_corrupted_checkpoint_returns_controlled_error(tmp_path: Path) -> None:
    corrupted_path = tmp_path / "bad.json"
    corrupted_path.write_text("{bad-json", encoding="utf-8")
    with pytest.raises(QueueCheckpointError):
        load_queue_checkpoint(corrupted_path)


def test_non_object_checkpoint_returns_controlled_error(tmp_path: Path) -> None:
    non_object_path = tmp_path / "non_object.json"
    non_object_path.write_text('"text"', encoding="utf-8")
    with pytest.raises(QueueCheckpointError, match="must be a JSON object payload"):
        load_queue_checkpoint(non_object_path)


def test_job_ordering_is_deterministic() -> None:
    expanded = expand_keywords(["b", "a"], max_candidates=10).expanded_keywords
    plan = build_search_plan(expanded, max_pages=2)
    queue = enqueue_search_plan(plan)
    ordered = [job.job_id for job in queue.jobs]
    assert ordered == sorted(ordered)


def test_gig_detail_fixture_parses_expected_title_and_packages() -> None:
    fixture = Path("tests/fixtures/collection/gig_detail.html").read_text(encoding="utf-8")
    parsed = parse_gig_detail_from_html(fixture)
    assert parsed.title == "I will design a premium logo identity kit"
    assert [package.name for package in parsed.packages] == ["Basic", "Standard", "Premium"]
    assert [package.price_cents for package in parsed.packages] == [5000, 12000, 25000]


def test_gig_detail_missing_optional_fields_creates_warnings_not_crash() -> None:
    html = "<html><body><h1 data-testid='gig-title'>Title Only</h1></body></html>"
    parsed = parse_gig_detail_from_html(html)
    assert parsed.title == "Title Only"
    assert parsed.warnings
    assert parsed.errors == []


def test_gig_detail_missing_data_testid_falls_back_to_plain_h1() -> None:
    html = "<html><body><h1>Fallback Gig Title</h1><p>No data-testid attributes.</p></body></html>"
    parsed = parse_gig_detail_from_html(html)
    assert parsed.title == "Fallback Gig Title"
    assert parsed.seller_name is None
    assert any("seller name was not found" in warning.lower() for warning in parsed.warnings)


def test_gig_detail_nested_markup_preserves_full_description_text() -> None:
    html = """
    <html><body>
      <h1 data-testid="gig-title">Nested Description Gig</h1>
      <div data-testid="seller-name">Seller Name</div>
      <div data-testid="gig-description">
        <p>Alpha <strong>Beta</strong></p>
        <p>Gamma</p>
      </div>
      <section data-testid="package-card">
        <h3 data-testid="package-name">Basic</h3>
        <span data-testid="package-price">$50</span>
      </section>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert parsed.description == "Alpha Beta Gamma"


def test_gig_detail_duplicate_data_testid_values_prefer_first_match() -> None:
    html = """
    <html><body>
      <h1 data-testid="gig-title">Primary Title</h1>
      <h1 data-testid="gig-title">Secondary Title</h1>
      <div data-testid="seller-name">First Seller</div>
      <div data-testid="seller-name">Second Seller</div>
      <div data-testid="gig-description">Description body.</div>
      <section data-testid="package-card">
        <h3 data-testid="package-name">Basic</h3>
        <span data-testid="package-price">$10</span>
      </section>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert parsed.title == "Primary Title"
    assert parsed.seller_name == "First Seller"


def test_gig_detail_empty_data_testid_nodes_yield_warning_not_exception() -> None:
    html = """
    <html><body>
      <h1 data-testid="gig-title">Empty Description Gig</h1>
      <div data-testid="seller-name">Seller Name</div>
      <div data-testid="gig-description"><span>   </span></div>
      <section data-testid="package-card">
        <h3 data-testid="package-name">Basic</h3>
        <span data-testid="package-price">$20</span>
      </section>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert parsed.description is None
    assert any("description was not found" in warning.lower() for warning in parsed.warnings)


def test_gig_detail_malformed_but_recoverable_nested_markup_keeps_text() -> None:
    html = """
    <html><body>
      <h1 data-testid="gig-title">Malformed Gig</h1>
      <div data-testid="seller-name">Seller Name</div>
      <div data-testid="gig-description"><div>Alpha <span>Beta <strong>Gamma</strong></span>
      <section data-testid="package-card">
        <h3 data-testid="package-name">Basic</h3>
        <span data-testid="package-price">$30</span>
      </section>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert parsed.description is not None
    assert "Alpha Beta Gamma" in parsed.description


def test_gig_detail_malformed_package_fragment_defaults_to_unnamed_package() -> None:
    html = """
    <html><body>
      <h1 data-testid="gig-title">Malformed Package Gig</h1>
      <div data-testid="seller-name">Seller Name</div>
      <section data-testid="package-card">
        <span data-testid="package-price">$75</span>
      </section>
    </body></html>
    """
    parsed = parse_gig_detail_from_html(html)
    assert parsed.packages
    assert parsed.packages[0].name == "Unnamed package"


def test_extract_data_testid_text_returns_nested_text_without_truncation() -> None:
    html = """
    <div data-testid="target">
      <p>Alpha <strong>Beta</strong></p>
      <p>Gamma</p>
    </div>
    """
    assert extract_data_testid_text(html, "target") == "Alpha Beta Gamma"


def test_extract_data_testid_text_joins_multiple_sibling_text_nodes() -> None:
    html = """
    <div data-testid="target">
      Alpha <span>Beta</span> Gamma <strong>Delta</strong> Epsilon
    </div>
    """
    assert extract_data_testid_text(html, "target") == "Alpha Beta Gamma Delta Epsilon"


def test_extract_data_testid_text_returns_first_match_only() -> None:
    html = """
    <span data-testid="target">first value</span>
    <span data-testid="target">second value</span>
    """
    assert extract_data_testid_text(html, "target") == "first value"


def test_extract_data_testid_text_handles_escaped_entities() -> None:
    html = '<div data-testid="target">Tom &amp; Jerry &lt;3</div>'
    assert extract_data_testid_text(html, "target") == "Tom & Jerry <3"


def test_extract_data_testid_text_unclosed_target_returns_none() -> None:
    html = '<div data-testid="target">Alpha <strong>Beta</strong><span>Gamma'
    assert extract_data_testid_text(html, "target") is None


def test_extract_data_testid_text_missing_or_empty_returns_none() -> None:
    missing_html = "<div data-testid='other'>value</div>"
    empty_html = "<div data-testid='target'><span>   </span></div>"
    assert extract_data_testid_text(missing_html, "target") is None
    assert extract_data_testid_text(empty_html, "target") is None


def test_regression_nested_data_testid_text_preserves_full_nested_markup_content() -> None:
    html = """
    <section data-testid="target">
      Lead <span>Designer <em>Portfolio</em></span>
      <div><strong>SEO</strong> Strategy</div>
    </section>
    """
    assert extract_data_testid_text(html, "target") == "Lead Designer Portfolio SEO Strategy"


def test_clean_html_text_collapses_tags_and_whitespace() -> None:
    value = " <p>Hello</p>   <em>world</em>  "
    assert clean_html_text(value) == "Hello world"


def test_parse_search_cards_skips_cards_missing_title_or_url() -> None:
    html = """
    <article data-testid="gig-card">
      <h3 data-testid="gig-title">Valid Card</h3>
      <a href="/services/valid-card">Open</a>
    </article>
    <article data-testid="gig-card">
      <a href="/services/missing-title">No title</a>
    </article>
    <article data-testid="gig-card">
      <h3 data-testid="gig-title">Missing Url</h3>
    </article>
    """
    cards = parse_search_result_cards_from_html(html)
    assert [card.title for card in cards] == ["Valid Card"]


def test_gig_detail_malformed_html_returns_controlled_warning_error() -> None:
    parsed = parse_gig_detail_from_html("not_html")
    assert parsed.title is None
    assert "malformed_html" in parsed.errors
    assert any("malformed" in warning.lower() for warning in parsed.warnings)


def test_seller_profile_fixture_parses_stable_fields() -> None:
    fixture = Path("tests/fixtures/collection/seller_profile.html").read_text(encoding="utf-8")
    parsed = parse_seller_profile_from_html(fixture)
    assert parsed.username == "pixelcraftstudio"
    assert parsed.display_name == "Pixel Craft Studio"
    assert parsed.level == "Level Two Seller"
    assert parsed.rating == 4.9
    assert parsed.review_count == 320
    assert parsed.languages == ["English", "Spanish"]


def test_seller_profile_missing_rating_and_reviews_returns_warnings() -> None:
    html = """
    <html><body>
      <h1 data-testid="seller-display-name">No Metrics Seller</h1>
      <div data-testid="seller-country">United States</div>
    </body></html>
    """
    parsed = parse_seller_profile_from_html(html)
    assert parsed.rating is None
    assert parsed.review_count is None
    assert any("rating" in warning.lower() for warning in parsed.warnings)
    assert any("review" in warning.lower() for warning in parsed.warnings)


def test_seller_profile_redacts_email_or_key_like_strings() -> None:
    html = """
    <html><body>
      <span data-testid="seller-username">demo@example.com</span>
      <h1 data-testid="seller-display-name">api_sk1234567890</h1>
    </body></html>
    """
    parsed = parse_seller_profile_from_html(html)
    assert parsed.username == "[redacted]"
    assert parsed.display_name == "[redacted]"
    assert any("redacted" in warning.lower() for warning in parsed.warnings)


def test_autocomplete_deduplicates_and_preserves_seed_keyword() -> None:
    plan = load_autocomplete_fixture(
        "tests/fixtures/collection/autocomplete_suggestions.json",
        seed_keyword="Logo Design",
    )
    assert len(plan.suggestions) == 4
    assert {suggestion.seed_keyword for suggestion in plan.suggestions} == {"logo design"}
    assert plan.mode == "dry_run"


def test_autocomplete_empty_fixture_creates_warning(tmp_path: Path) -> None:
    fixture = tmp_path / "empty_autocomplete.json"
    fixture.write_text('{"suggestions":[]}', encoding="utf-8")
    plan = load_autocomplete_fixture(fixture, seed_keyword="logo design")
    assert plan.suggestions == []
    assert any("no suggestions" in warning.lower() for warning in plan.warnings)


def test_autocomplete_invalid_json_raises_controlled_error(tmp_path: Path) -> None:
    fixture = tmp_path / "bad_autocomplete.json"
    fixture.write_text("{not-json", encoding="utf-8")
    with pytest.raises(AutocompleteFixtureError):
        load_autocomplete_fixture(fixture, seed_keyword="logo design")


def test_external_signal_fixture_records_validate() -> None:
    signals = load_external_signal_fixture("tests/fixtures/collection/external_signals.json")
    assert len(signals) == 2
    assert {signal.source.value for signal in signals} == {"google_trends", "exploding_topics"}


def test_external_signal_marks_stale_record() -> None:
    now = datetime(2026, 5, 14, tzinfo=UTC)
    signals = load_external_signal_fixture(
        "tests/fixtures/collection/external_signals.json",
        stale_after_days=7,
        now=now,
    )
    assert any(signal.freshness == SignalFreshness.STALE for signal in signals)


def test_external_signal_live_connector_disabled_by_default() -> None:
    with pytest.raises(LiveSignalConnectorDisabledError):
        fetch_external_signals_live()


def test_external_signal_source_names_are_constrained(tmp_path: Path) -> None:
    fixture = tmp_path / "bad_external_source.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "keyword": "logo design",
                    "source_keyword": "logo design",
                    "source": "unknown_source",
                    "score": 50.0,
                    "captured_at": "2026-05-13T12:00:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unsupported signal source"):
        load_external_signal_fixture(fixture)


def test_community_signal_fixture_loads_and_preserves_lineage() -> None:
    records, warnings = load_community_signal_fixture("tests/fixtures/collection/community_signals.json")
    assert len(records) == 2
    assert {record.source_keyword for record in records} == {"logo design"}
    assert warnings == []


def test_community_signal_missing_confidence_defaults_safely(tmp_path: Path) -> None:
    fixture = tmp_path / "community_missing_confidence.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "keyword": "logo design",
                    "source_keyword": "logo design",
                    "mention_count": 5,
                    "sentiment_hint": "neutral",
                    "sample_theme": "aggregate forum feedback",
                    "source": "reddit_aggregate",
                    "captured_at": "2026-05-14T00:00:00Z",
                }
            ]
        ),
        encoding="utf-8",
    )
    records, _warnings = load_community_signal_fixture(fixture)
    assert records[0].confidence == 0.5


def test_community_signal_personal_data_like_fields_ignored(tmp_path: Path) -> None:
    fixture = tmp_path / "community_personal_fields.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "keyword": "logo design",
                    "source_keyword": "logo design",
                    "mention_count": 10,
                    "sentiment_hint": "mixed",
                    "sample_theme": "Contact @username for details",
                    "source": "reddit_aggregate",
                    "captured_at": "2026-05-14T00:00:00Z",
                    "username": "someone",
                }
            ]
        ),
        encoding="utf-8",
    )
    records, warnings = load_community_signal_fixture(fixture)
    assert records[0].sample_theme == "aggregate community discussion"
    assert warnings


def test_seller_profile_parser_has_no_network_or_browser_imports() -> None:
    source = Path("src/collection/seller_profile.py").read_text(encoding="utf-8").lower()
    assert "import requests" not in source
    assert "import httpx" not in source
    assert "playwright" not in source


def test_orchestrator_has_no_network_or_browser_imports() -> None:
    source = Path("src/collection/orchestrator.py").read_text(encoding="utf-8").lower()
    assert "import requests" not in source
    assert "import httpx" not in source
    assert "playwright" not in source


def test_collection_stage_summary_validator_rejects_missing_required_stage() -> None:
    with pytest.raises(ValueError, match="missing required stages"):
        validate_collection_stage_summary(
            {
                "stage_counts": {
                    "stage_1_keyword_expansion": 1,
                    "stage_2_search_plan": 1,
                }
            }
        )


def test_collection_stage_summary_validator_accepts_consistent_invariants() -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 3,
            "stage_2b_autocomplete": 2,
            "stage_2_search_plan": 2,
            "stage_3_queue": 2,
            "stage_4_gig_detail": 1,
            "stage_5_seller_profile": 1,
            "stage_6a_external_signals": 1,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "stage_names": [
            "stage_1_keyword_expansion",
            "stage_2b_autocomplete",
            "stage_2_search_plan",
            "stage_3_queue",
            "stage_4_gig_detail",
            "stage_5_seller_profile",
            "stage_6a_external_signals",
            "stage_6b_community_signals",
            "stage_7_checkpoint_metadata",
            "stage_8_pacing_decisions",
            "stage_9_auto_promotion_decision",
        ],
        "records_seen": 3,
        "records_written": 9,
        "warnings": ["fixture warning"],
        "warning_count": 1,
        "failed": False,
    }
    validate_collection_stage_summary(summary)


def test_collection_stage_summary_validator_allows_stage_names_when_stage_count_keys_reordered() -> None:
    stage_names = [
        "stage_1_keyword_expansion",
        "stage_2b_autocomplete",
        "stage_2_search_plan",
        "stage_3_queue",
        "stage_4_gig_detail",
        "stage_5_seller_profile",
        "stage_6a_external_signals",
        "stage_6b_community_signals",
        "stage_7_checkpoint_metadata",
        "stage_8_pacing_decisions",
        "stage_9_auto_promotion_decision",
    ]
    stage_counts = {stage_name: index for index, stage_name in enumerate(sorted(stage_names), start=1)}
    summary = json.loads(json.dumps({"stage_names": stage_names, "stage_counts": stage_counts}, sort_keys=True))
    validate_collection_stage_summary(summary)


@pytest.mark.parametrize(
    ("stage_names", "error_match"),
    [
        (
            [
                "stage_1_keyword_expansion",
                "stage_2b_autocomplete",
                "stage_2_search_plan",
                "stage_3_queue",
                "stage_4_gig_detail",
                "stage_6a_external_signals",
                "stage_7_checkpoint_metadata",
                "stage_8_pacing_decisions",
            ],
            "must match stage_counts stage keys",
        ),
    ],
)
def test_collection_stage_summary_validator_rejects_missing_or_extra_stage_names(
    stage_names: list[str], error_match: str
) -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 1,
            "stage_2b_autocomplete": 1,
            "stage_2_search_plan": 1,
            "stage_3_queue": 1,
            "stage_4_gig_detail": 1,
            "stage_5_seller_profile": 1,
            "stage_6a_external_signals": 1,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "stage_names": stage_names,
    }
    with pytest.raises(ValueError, match=error_match):
        validate_collection_stage_summary(summary)


def test_collection_stage_summary_validator_rejects_duplicate_stage_names() -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 1,
            "stage_2b_autocomplete": 0,
            "stage_2_search_plan": 1,
            "stage_3_queue": 1,
            "stage_4_gig_detail": 0,
            "stage_5_seller_profile": 0,
            "stage_6a_external_signals": 0,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "stage_names": [
            "stage_1_keyword_expansion",
            "stage_2b_autocomplete",
            "stage_2_search_plan",
            "stage_3_queue",
            "stage_4_gig_detail",
            "stage_5_seller_profile",
            "stage_6a_external_signals",
            "stage_6a_external_signals",
            "stage_6b_community_signals",
            "stage_7_checkpoint_metadata",
            "stage_8_pacing_decisions",
            "stage_9_auto_promotion_decision",
        ],
    }
    with pytest.raises(ValueError, match="duplicate stages"):
        validate_collection_stage_summary(summary)


def test_collection_stage_summary_validator_rejects_unknown_stage_name() -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 1,
            "stage_2b_autocomplete": 0,
            "stage_2_search_plan": 1,
            "stage_3_queue": 1,
            "stage_4_gig_detail": 0,
            "stage_5_seller_profile": 0,
            "stage_6a_external_signals": 0,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "stage_names": [
            "stage_1_keyword_expansion",
            "stage_2b_autocomplete",
            "stage_2_search_plan",
            "stage_3_queue",
            "stage_4_gig_detail",
            "stage_5_seller_profile",
            "stage_6a_external_signals",
            "stage_6b_community_signals",
            "stage_7_checkpoint_metadata",
            "stage_8_pacing_decisions",
            "stage_9_unknown",
        ],
    }
    with pytest.raises(ValueError, match="unstable stage names"):
        validate_collection_stage_summary(summary)


def test_collection_stage_summary_validator_rejects_records_written_undercount() -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 3,
            "stage_2b_autocomplete": 2,
            "stage_2_search_plan": 2,
            "stage_3_queue": 2,
            "stage_4_gig_detail": 1,
            "stage_5_seller_profile": 1,
            "stage_6a_external_signals": 1,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "records_seen": 3,
        "records_written": 8,
        "warnings": [],
        "warning_count": 0,
        "failed": False,
    }
    with pytest.raises(ValueError, match="records_written mismatch"):
        validate_collection_stage_summary(summary)


def test_collection_stage_summary_validator_rejects_warning_count_mismatch() -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 1,
            "stage_2b_autocomplete": 0,
            "stage_2_search_plan": 1,
            "stage_3_queue": 1,
            "stage_4_gig_detail": 0,
            "stage_5_seller_profile": 0,
            "stage_6a_external_signals": 0,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "records_seen": 1,
        "records_written": 3,
        "warnings": ["a", "b"],
        "warning_count": 1,
        "failed": False,
    }
    with pytest.raises(ValueError, match="warning_count mismatch"):
        validate_collection_stage_summary(summary)


def test_collection_stage_summary_validator_requires_error_code_for_failed_stage() -> None:
    summary = {
        "stage_counts": {
            "stage_1_keyword_expansion": 1,
            "stage_2b_autocomplete": 0,
            "stage_2_search_plan": 1,
            "stage_3_queue": 1,
            "stage_4_gig_detail": 0,
            "stage_5_seller_profile": 0,
            "stage_6a_external_signals": 0,
            "stage_6b_community_signals": 0,
            "stage_7_checkpoint_metadata": 1,
            "stage_8_pacing_decisions": 1,
            "stage_9_auto_promotion_decision": 0,
        },
        "records_seen": 1,
        "records_written": 3,
        "warnings": [],
        "warning_count": 0,
        "failed": True,
    }
    with pytest.raises(ValueError, match="error_code"):
        validate_collection_stage_summary(summary)


def test_collection_checkpoint_evidence_serializes_without_sensitive_fields() -> None:
    evidence = CollectionCheckpointEvidence(
        checkpoint_path="artifacts/collection/queue_checkpoint.json",
        pacing_decisions={"queue_mode": "deterministic_fixture", "per_page_limit": 2},
        cooldown_applied=True,
        retry_count=1,
        fixture_mode=True,
    )
    payload = evidence.model_dump()
    assert payload == {
        "checkpoint_path": "artifacts/collection/queue_checkpoint.json",
        "pacing_decisions": {"queue_mode": "deterministic_fixture", "per_page_limit": 2},
        "cooldown_applied": True,
        "retry_count": 1,
        "fixture_mode": True,
    }
    serialized = json.dumps(payload).lower()
    assert "cookie" not in serialized
    assert "session" not in serialized
    assert "storage_state" not in serialized


def test_collection_dry_run_non_positive_max_candidates_uses_safe_bounded_path(tmp_path: Path) -> None:
    result = run_collection_dry_run(
        ["logo design", "seo audit"],
        niche_metadata={"modifiers": ["local"]},
        max_candidates=0,
        max_pages=1,
        checkpoint_path=tmp_path / "checkpoint.json",
    )
    assert str(result.status).endswith("success")
    assert any("non-positive max_candidates" in warning for warning in result.warnings)
    assert result.metadata["expanded_keywords_count"] > 0


def test_collection_dry_run_stage_summary_validator_covers_all_required_stages(tmp_path: Path) -> None:
    result = run_collection_dry_run(
        ["logo design"],
        niche_metadata={"modifiers": ["local"]},
        max_candidates=5,
        checkpoint_path=tmp_path / "summary-checkpoint.json",
        autocomplete_fixture_path="tests/fixtures/collection/autocomplete_suggestions.json",
        gig_detail_fixture_path="tests/fixtures/collection/gig_detail.html",
        seller_profile_fixture_path="tests/fixtures/collection/seller_profile.html",
    )
    stage_counts = result.metadata["stage_counts"]
    assert stage_counts["stage_1_keyword_expansion"] > 0
    assert stage_counts["stage_2b_autocomplete"] > 0
    assert stage_counts["stage_2_search_plan"] > 0
    assert stage_counts["stage_4_gig_detail"] == 1
    assert stage_counts["stage_5_seller_profile"] == 1
    assert stage_counts["stage_7_checkpoint_metadata"] == 1
    assert stage_counts["stage_8_pacing_decisions"] == 1
    expected_records_written = result.metadata["queue_jobs_count"] + sum(
        count
        for stage_name, count in stage_counts.items()
        if stage_name not in {"stage_1_keyword_expansion", "stage_2_search_plan", "stage_3_queue"}
    )
    assert result.records_written == expected_records_written


def test_collection_dry_run_empty_signal_fixtures_warn_instead_of_fabricating_records(tmp_path: Path) -> None:
    empty_external = tmp_path / "external_empty.json"
    empty_external.write_text("[]", encoding="utf-8")
    empty_community = tmp_path / "community_empty.json"
    empty_community.write_text("[]", encoding="utf-8")

    result = run_collection_dry_run(
        ["logo design"],
        max_candidates=5,
        checkpoint_path=tmp_path / "empty-signals-checkpoint.json",
        external_signal_fixture_path=empty_external,
        community_signal_fixture_path=empty_community,
    )
    assert str(result.status).endswith("success")
    assert result.metadata["stage_counts"]["stage_6a_external_signals"] == 0
    assert result.metadata["stage_counts"]["stage_6b_community_signals"] == 0
    assert any("External signal fixture returned zero records." == warning for warning in result.warnings)
    assert any("Community signal fixture returned zero records." == warning for warning in result.warnings)


def test_collection_dry_run_seller_placeholder_marks_blocked_when_fixture_lacks_identity(tmp_path: Path) -> None:
    weak_seller_fixture = tmp_path / "seller_weak.html"
    weak_seller_fixture.write_text(
        "<html><body><div data-testid='seller-country'>United States</div></body></html>",
        encoding="utf-8",
    )
    result = run_collection_dry_run(
        ["logo design"],
        checkpoint_path=tmp_path / "seller-blocked-checkpoint.json",
        seller_profile_fixture_path=weak_seller_fixture,
    )
    assert str(result.status).endswith("success")
    assert result.metadata["stage_counts"]["stage_5_seller_profile"] == 0
    seller_metrics = result.metadata["stage_metrics"]["stage_5_seller_profile"]
    assert seller_metrics["readiness_status"] == "blocked"
    assert any("stage 5 readiness is blocked" in warning.lower() for warning in result.warnings)
