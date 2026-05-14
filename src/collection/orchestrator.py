"""Dry-run collection orchestration with no browser or network usage."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.collection.autocomplete import AutocompleteFixtureError, load_autocomplete_fixture
from src.collection.checkpoint import checkpoint_queue_state
from src.collection.community_signals import load_community_signal_fixture
from src.collection.contracts import CollectionError, CollectionStageResult, CollectionStageStatus
from src.collection.external_signals import load_external_signal_fixture
from src.collection.gig_detail import parse_gig_detail_from_html
from src.collection.keyword_expansion import expand_keywords
from src.collection.queue import enqueue_search_plan
from src.collection.search_plan import build_search_plan
from src.collection.seller_profile import parse_seller_profile_from_html


def run_collection_dry_run(
    seed_keywords: Sequence[str],
    *,
    niche_metadata: Mapping[str, Any] | None = None,
    max_candidates: int = 50,
    max_pages: int = 1,
    checkpoint_path: Path | str = "artifacts/collection/queue_checkpoint.json",
    region: str | None = None,
    language: str | None = None,
    sort: str | None = None,
    autocomplete_fixture_path: Path | str | None = None,
    gig_detail_fixture_path: Path | str | None = None,
    seller_profile_fixture_path: Path | str | None = None,
    external_signal_fixture_path: Path | str | None = None,
    community_signal_fixture_path: Path | str | None = None,
) -> CollectionStageResult:
    """Run collection planning stages without external side effects."""

    started_at = datetime.now(UTC)
    try:
        if not isinstance(seed_keywords, Sequence) or isinstance(seed_keywords, (str, bytes)):
            raise ValueError("seed_keywords must be a sequence of strings.")

        expanded = expand_keywords(
            seed_keywords,
            niche_metadata=niche_metadata,
            max_candidates=max_candidates,
        )
        plan = build_search_plan(
            expanded.expanded_keywords,
            region=region,
            language=language,
            sort=sort,
            max_pages=max_pages,
        )
        queue = enqueue_search_plan(plan)

        warnings = list(expanded.warnings) + list(plan.warnings)
        stage_counts: dict[str, int] = {
            "stage_1_keyword_expansion": len(expanded.expanded_keywords),
            "stage_2_search_plan": len(plan.items),
            "stage_3_queue": len(queue.jobs),
            "stage_2b_autocomplete": 0,
            "stage_4_gig_detail": 0,
            "stage_5_seller_profile": 0,
            "stage_6a_external_signals": 0,
            "stage_6b_community_signals": 0,
        }
        stage_warnings: dict[str, list[str]] = {}

        if autocomplete_fixture_path:
            autocomplete_plan = load_autocomplete_fixture(
                autocomplete_fixture_path,
                seed_keyword=expanded.expanded_keywords[0].source_seed if expanded.expanded_keywords else "seed",
            )
            stage_counts["stage_2b_autocomplete"] = len(autocomplete_plan.suggestions)
            if autocomplete_plan.warnings:
                stage_warnings["stage_2b_autocomplete"] = list(autocomplete_plan.warnings)
                warnings.extend(autocomplete_plan.warnings)

        if gig_detail_fixture_path:
            gig_detail_html = Path(gig_detail_fixture_path).read_text(encoding="utf-8")
            gig_detail = parse_gig_detail_from_html(gig_detail_html)
            stage_counts["stage_4_gig_detail"] = 1 if gig_detail.title else 0
            if gig_detail.warnings:
                stage_warnings["stage_4_gig_detail"] = list(gig_detail.warnings)
                warnings.extend(gig_detail.warnings)

        if seller_profile_fixture_path:
            seller_profile_html = Path(seller_profile_fixture_path).read_text(encoding="utf-8")
            seller_profile = parse_seller_profile_from_html(seller_profile_html)
            stage_counts["stage_5_seller_profile"] = 1 if seller_profile.display_name or seller_profile.username else 0
            if seller_profile.warnings:
                stage_warnings["stage_5_seller_profile"] = list(seller_profile.warnings)
                warnings.extend(seller_profile.warnings)

        if external_signal_fixture_path:
            external_signals = load_external_signal_fixture(external_signal_fixture_path)
            stage_counts["stage_6a_external_signals"] = len(external_signals)

        if community_signal_fixture_path:
            community_signals, community_warnings = load_community_signal_fixture(community_signal_fixture_path)
            stage_counts["stage_6b_community_signals"] = len(community_signals)
            if community_warnings:
                stage_warnings["stage_6b_community_signals"] = list(community_warnings)
                warnings.extend(community_warnings)

        records_written = len(queue.jobs) + sum(
            count
            for stage_name, count in stage_counts.items()
            if stage_name not in {"stage_1_keyword_expansion", "stage_2_search_plan", "stage_3_queue"}
        )
        stage_summary: dict[str, object] = {
            "stage_counts": stage_counts,
            "stage_warnings": stage_warnings,
            "mode": "dry_run_fixture_optional",
        }
        saved_checkpoint = checkpoint_queue_state(queue, checkpoint_path, stage_summary=stage_summary)

        return CollectionStageResult(
            stage_name="collection_dry_run",
            status=CollectionStageStatus.SUCCESS,
            records_seen=len(expanded.expanded_keywords),
            records_written=records_written,
            warnings=warnings,
            checkpoint_path=saved_checkpoint,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            metadata={
                "expanded_keywords_count": len(expanded.expanded_keywords),
                "search_plan_items_count": len(plan.items),
                "queue_jobs_count": len(queue.jobs),
                "stage_counts": stage_counts,
                "stage_warnings": stage_warnings,
                "max_pages": max_pages,
            },
        )
    except (FileNotFoundError, AutocompleteFixtureError) as exc:
        return CollectionStageResult(
            stage_name="collection_dry_run",
            status=CollectionStageStatus.FAILED,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            errors=[
                CollectionError(
                    code="fixture_unavailable",
                    message=str(exc),
                )
            ],
        )
    except Exception as exc:
        return CollectionStageResult(
            stage_name="collection_dry_run",
            status=CollectionStageStatus.FAILED,
            started_at=started_at,
            finished_at=datetime.now(UTC),
            errors=[
                CollectionError(
                    code="dry_run_failed",
                    message=str(exc),
                )
            ],
        )
