"""Integration checks for collection dry-run orchestration."""

from __future__ import annotations

from src.collection.contracts import CollectionStageStatus
from src.collection.orchestrator import run_collection_dry_run


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


def test_collection_dry_run_invalid_input_returns_failed_result(tmp_path) -> None:
    result = run_collection_dry_run(
        ["seed"],
        max_pages=0,
        checkpoint_path=tmp_path / "invalid.json",
    )
    assert result.status == CollectionStageStatus.FAILED
    assert result.errors


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
