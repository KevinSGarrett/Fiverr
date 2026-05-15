"""Integration checks for collection dry-run orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from src.collection.checkpoint import load_checkpoint_stage_summary_or_fallback
from src.collection.contracts import CollectionStageStatus
from src.collection.orchestrator import run_collection_dry_run
from src.collection.selectors import parse_search_result_cards_from_html


def test_collection_dry_run_pipeline_creates_expected_artifacts(tmp_path) -> None:
    checkpoint_path = tmp_path / "dry-run-checkpoint.json"
    result = run_collection_dry_run(
        ["logo design", "seo audit"],
        niche_metadata={"modifiers": ["local"]},
        max_candidates=12,
        max_pages=2,
        checkpoint_path=checkpoint_path,
        region="US",
        language="en",
        sort="rating",
        autocomplete_fixture_path="tests/fixtures/collection/autocomplete_suggestions.json",
        gig_detail_fixture_path="tests/fixtures/collection/gig_detail.html",
        seller_profile_fixture_path="tests/fixtures/collection/seller_profile.html",
        external_signal_fixture_path="tests/fixtures/collection/external_signals.json",
        community_signal_fixture_path="tests/fixtures/collection/community_signals.json",
    )

    assert result.status == CollectionStageStatus.SUCCESS
    assert result.metadata["expanded_keywords_count"] > 0
    assert result.metadata["search_plan_items_count"] > 0
    assert result.metadata["queue_jobs_count"] > 0
    assert result.metadata["stage_counts"]["stage_2b_autocomplete"] > 0
    assert result.metadata["stage_counts"]["stage_4_gig_detail"] == 1
    assert result.metadata["stage_counts"]["stage_5_seller_profile"] == 1
    assert result.metadata["stage_counts"]["stage_6a_external_signals"] > 0
    assert result.metadata["stage_counts"]["stage_6b_community_signals"] > 0
    assert checkpoint_path.exists()
    checkpoint_payload = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint_payload["stage_summary"]["stage_counts"]["stage_4_gig_detail"] == 1


def test_collection_dry_run_invalid_input_returns_failed_result(tmp_path) -> None:
    result = run_collection_dry_run(
        ["seed"],
        max_pages=0,
        checkpoint_path=tmp_path / "invalid.json",
    )
    assert result.status == CollectionStageStatus.FAILED
    assert result.errors
    stage_summary = result.metadata["stage_summary"]
    assert stage_summary["failed"] is True
    assert stage_summary["failed_stage_names"]
    assert stage_summary["stage_execution"][0]["status"] == CollectionStageStatus.FAILED.value


def test_collection_dry_run_missing_fixture_path_returns_failed_without_traceback(tmp_path) -> None:
    result = run_collection_dry_run(
        ["logo design"],
        checkpoint_path=tmp_path / "checkpoint.json",
        gig_detail_fixture_path=tmp_path / "missing_gig_detail.html",
    )
    assert result.status == CollectionStageStatus.FAILED
    assert result.errors
    assert result.errors[0].code == "fixture_unavailable"
    assert "Traceback" not in result.errors[0].message


def test_collection_fixture_dry_run_smoke_is_deterministic_and_local_only(tmp_path: Path) -> None:
    checkpoint_a = tmp_path / "dry-run-a.json"
    checkpoint_b = tmp_path / "dry-run-b.json"
    kwargs = {
        "niche_metadata": {"modifiers": ["local"]},
        "max_candidates": 6,
        "max_pages": 2,
        "region": "US",
        "language": "en",
        "sort": "rating",
        "autocomplete_fixture_path": "tests/fixtures/collection/autocomplete_suggestions.json",
        "gig_detail_fixture_path": "tests/fixtures/collection/gig_detail.html",
        "seller_profile_fixture_path": "tests/fixtures/collection/seller_profile.html",
        "external_signal_fixture_path": "tests/fixtures/collection/external_signals.json",
        "community_signal_fixture_path": "tests/fixtures/collection/community_signals.json",
    }

    result_a = run_collection_dry_run(["logo design"], checkpoint_path=checkpoint_a, **kwargs)
    result_b = run_collection_dry_run(["logo design"], checkpoint_path=checkpoint_b, **kwargs)

    assert result_a.status == CollectionStageStatus.SUCCESS
    assert result_b.status == CollectionStageStatus.SUCCESS
    assert result_a.warnings == result_b.warnings
    stage_counts = result_a.metadata["stage_counts"]
    required_smoke_stages = {
        "stage_1_keyword_expansion",
        "stage_2_search_plan",
        "stage_3_queue",
        "stage_4_gig_detail",
        "stage_5_seller_profile",
        "stage_6a_external_signals",
    }
    assert required_smoke_stages.issubset(stage_counts)
    assert stage_counts["stage_1_keyword_expansion"] > 0
    assert stage_counts["stage_2_search_plan"] > 0
    assert stage_counts["stage_3_queue"] > 0
    assert stage_counts["stage_4_gig_detail"] == 1
    assert stage_counts["stage_5_seller_profile"] == 1
    assert stage_counts["stage_6a_external_signals"] > 0
    assert stage_counts["stage_6b_community_signals"] > 0
    assert stage_counts["stage_7_checkpoint_metadata"] == 1
    assert stage_counts["stage_8_pacing_decisions"] == 1
    assert stage_counts["stage_9_auto_promotion_decision"] == 1

    fixture_sources = result_a.metadata["fixture_sources"]
    assert fixture_sources["stage_1_keyword_expansion"] == "derived_seed_keywords"
    assert fixture_sources["stage_2_search_plan"] == "derived_search_plan"
    assert fixture_sources["stage_3_queue"] == "derived_queue_plan"
    assert fixture_sources["stage_4_gig_detail"].startswith("tests/fixtures/collection/")
    assert fixture_sources["stage_5_seller_profile"].startswith("tests/fixtures/collection/")
    assert fixture_sources["stage_6a_external_signals"].startswith("tests/fixtures/collection/")
    assert fixture_sources["stage_6b_community_signals"].startswith("tests/fixtures/collection/")

    checkpoint_payload = json.loads(checkpoint_a.read_text(encoding="utf-8"))
    stage_summary = checkpoint_payload["stage_summary"]
    assert stage_summary["stage_counts"]
    assert stage_summary["stage_names"] == [entry["stage_name"] for entry in stage_summary["stage_execution"]]
    assert stage_summary["resumable_stage_identity"]["run_id"].startswith("dryrun-")
    assert stage_summary["failed_stage_names"] == []
    assert stage_summary["checkpoint_metadata"]["schema_version"] == "1.0"
    assert stage_summary["pacing_decisions"]["queue_mode"] == "deterministic_fixture"
    assert stage_summary["fixture_sources"]["stage_4_gig_detail"].startswith("tests/fixtures/collection/")
    assert stage_summary["fixture_sources"]["stage_6a_external_signals"].startswith("tests/fixtures/collection/")

    checkpoint_text = checkpoint_a.read_text(encoding="utf-8").lower()
    assert "playwright" not in checkpoint_text
    assert "storage_state" not in checkpoint_text
    assert "requests" not in checkpoint_text
    assert "httpx" not in checkpoint_text
    assert "session_token" not in checkpoint_text
    leftover_db_files = [path for path in tmp_path.rglob("*") if path.suffix in {".db", ".sqlite", ".sqlite3"}]
    assert leftover_db_files == []
    search_results_html = Path("tests/fixtures/collection/search_results.html").read_text(encoding="utf-8")
    parsed_cards = parse_search_result_cards_from_html(search_results_html)
    assert len(parsed_cards) >= 2
    assert all(card.url.startswith("/services/") for card in parsed_cards)


def test_collection_fixture_dry_run_smoke_distinguishes_safe_skips(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "safe-skip-checkpoint.json"
    result = run_collection_dry_run(
        ["logo design"],
        checkpoint_path=checkpoint_path,
        gig_detail_fixture_path="tests/fixtures/collection/gig_detail.html",
    )
    assert result.status == CollectionStageStatus.SUCCESS
    assert result.metadata["stage_counts"]["stage_4_gig_detail"] == 1
    assert result.metadata["stage_counts"]["stage_5_seller_profile"] == 0
    assert result.metadata["stage_counts"]["stage_6a_external_signals"] == 0
    assert result.metadata["stage_counts"]["stage_6b_community_signals"] == 0
    stage_summary = load_checkpoint_stage_summary_or_fallback(checkpoint_path)
    assert stage_summary is not None
    skipped = set(stage_summary["skipped_stage_names"])
    assert "stage_5_seller_profile" in skipped
    assert "stage_6a_external_signals" in skipped
    assert "stage_6b_community_signals" in skipped
    assert "stage_4_gig_detail" not in skipped


def test_collection_dry_run_resume_identity_uses_previous_checkpoint_stage_ids(tmp_path: Path) -> None:
    paused_checkpoint = tmp_path / "paused.json"
    resumed_checkpoint = tmp_path / "resumed.json"
    paused_result = run_collection_dry_run(
        ["logo design"],
        checkpoint_path=paused_checkpoint,
        autocomplete_fixture_path="tests/fixtures/collection/autocomplete_suggestions.json",
        gig_detail_fixture_path="tests/fixtures/collection/gig_detail.html",
    )
    assert paused_result.status == CollectionStageStatus.SUCCESS

    resumed_result = run_collection_dry_run(
        ["logo design"],
        checkpoint_path=resumed_checkpoint,
        resume_checkpoint_path=paused_checkpoint,
        autocomplete_fixture_path="tests/fixtures/collection/autocomplete_suggestions.json",
        gig_detail_fixture_path="tests/fixtures/collection/gig_detail.html",
        seller_profile_fixture_path="tests/fixtures/collection/seller_profile.html",
        external_signal_fixture_path="tests/fixtures/collection/external_signals.json",
        community_signal_fixture_path="tests/fixtures/collection/community_signals.json",
    )
    assert resumed_result.status == CollectionStageStatus.SUCCESS
    resumed_summary = load_checkpoint_stage_summary_or_fallback(resumed_checkpoint)
    assert resumed_summary is not None
    stage_execution = resumed_summary["stage_execution"]
    assert any("resumed_from_stage_id" in entry for entry in stage_execution)
    assert resumed_summary["resumable_stage_identity"]["resume_checkpoint_path"] == str(paused_checkpoint)
    assert resumed_summary["checkpoint_metadata"]["checkpoint_requested"] == str(resumed_checkpoint)
    assert resumed_summary["checkpoint_metadata"]["schema_version"] == "1.0"
    assert resumed_summary["fixture_sources"]["stage_4_gig_detail"].startswith("tests/fixtures/collection/")
    assert resumed_summary["fixture_sources"]["stage_5_seller_profile"].startswith("tests/fixtures/collection/")
    assert resumed_summary["fixture_sources"]["stage_6a_external_signals"].startswith("tests/fixtures/collection/")
    assert resumed_summary["fixture_sources"]["stage_6b_community_signals"].startswith("tests/fixtures/collection/")
