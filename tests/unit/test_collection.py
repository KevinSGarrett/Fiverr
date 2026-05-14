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
    load_queue_checkpoint,
)
from src.collection.community_signals import load_community_signal_fixture
from src.collection.external_signals import (
    LiveSignalConnectorDisabledError,
    SignalFreshness,
    fetch_external_signals_live,
    load_external_signal_fixture,
)
from src.collection.gig_detail import parse_gig_detail_from_html
from src.collection.keyword_expansion import expand_keywords
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
