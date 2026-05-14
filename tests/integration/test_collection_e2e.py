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
    )

    assert result.status == CollectionStageStatus.SUCCESS
    assert result.metadata["expanded_keywords_count"] > 0
    assert result.metadata["search_plan_items_count"] > 0
    assert result.metadata["queue_jobs_count"] > 0
    assert checkpoint_path.exists()


def test_collection_dry_run_invalid_input_returns_failed_result(tmp_path) -> None:
    result = run_collection_dry_run(
        ["seed"],
        max_pages=0,
        checkpoint_path=tmp_path / "invalid.json",
    )
    assert result.status == CollectionStageStatus.FAILED
    assert result.errors
