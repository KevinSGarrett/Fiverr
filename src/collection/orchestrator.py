"""Dry-run collection orchestration with no browser or network usage."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.collection.autocomplete import AutocompleteFixtureError, load_autocomplete_fixture
from src.collection.checkpoint import (
    checkpoint_queue_state,
    load_checkpoint_stage_summary_or_fallback,
)
from src.collection.community_signals import load_community_signal_fixture
from src.collection.contracts import (
    RECORDS_SEEN_STAGE_NAMES,
    RECORDS_WRITTEN_STAGE_NAMES,
    STABLE_COLLECTION_STAGE_NAMES,
    CollectionCheckpointEvidence,
    CollectionError,
    CollectionStageResult,
    CollectionStageStatus,
    validate_collection_stage_summary,
)
from src.collection.external_signals import load_external_signal_fixture
from src.collection.gig_detail import parse_gig_detail_from_html
from src.collection.keyword_expansion import expand_keywords
from src.collection.queue import enqueue_search_plan
from src.collection.search_plan import build_search_plan
from src.collection.seller_profile import parse_seller_profile_from_html


@dataclass(slots=True)
class _DryRunJob:
    id: int
    run_id: str
    job_type: str
    stage: int
    payload: dict[str, Any] = field(default_factory=dict)
    priority: str = "STANDARD"
    status: str = "QUEUED"
    retry_count: int = 0
    max_retries: int = 1
    error_log: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None

    def mark_running(self) -> None:
        self.status = "RUNNING"
        self.started_at = datetime.now(UTC)

    def mark_complete(self) -> None:
        self.status = "COMPLETE"
        self.completed_at = datetime.now(UTC)
        if self.started_at is not None:
            self.duration_seconds = max(0.0, (self.completed_at - self.started_at).total_seconds())

    def mark_failed(self, message: str) -> None:
        self.retry_count += 1
        self.error_log.append(message)
        if self.retry_count >= self.max_retries:
            self.status = "DEAD_LETTER"
        else:
            self.status = "FAILED"

    def should_dead_letter(self) -> bool:
        return self.retry_count >= self.max_retries


class _InMemoryQueryResult:
    def __init__(self, payload: dict[str, Any] | None) -> None:
        self._payload = payload

    def mappings(self) -> _InMemoryQueryResult:
        return self

    def first(self) -> dict[str, Any] | None:
        return self._payload


class _InMemoryORMQuery:
    def __init__(self, db: _InMemoryQueueDb) -> None:
        self._db = db

    def filter(self, *_args: Any, **_kwargs: Any) -> _InMemoryORMQuery:
        return self

    def first(self) -> _DryRunJob | None:
        return self._db.selected_job


class _InMemoryQueueDb:
    def __init__(self, jobs: list[_DryRunJob]) -> None:
        self.jobs = jobs
        self.selected_job: _DryRunJob | None = None

    def execute(self, _query: Any, params: dict[str, Any]) -> _InMemoryQueryResult:
        run_id = str(params.get("run_id", ""))
        candidates = [
            job
            for job in self.jobs
            if job.run_id == run_id and job.status == "QUEUED"
        ]
        candidates.sort(key=lambda item: (item.stage, item.id))
        self.selected_job = candidates[0] if candidates else None
        payload = {"id": self.selected_job.id} if self.selected_job else None
        return _InMemoryQueryResult(payload)

    def query(self, _model: Any) -> _InMemoryORMQuery:
        return _InMemoryORMQuery(self)

    def commit(self) -> None:
        return None


async def run_collection_pipeline(
    run_id: str,
    db: Any,
    config: dict[str, Any],
    session_manager: Any,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Run the Stage 1-12 dry-run orchestration contract.

    Real collection (dry_run=False) remains intentionally blocked until browser wiring lands.
    """
    from src.analysis.competitor_profiler import run_competitor_profiling_for_niche
    from src.analysis.gig_quality_rubric import run_gig_quality_analysis_for_niche
    from src.analysis.keyword_clusterer import run_clustering_for_niche
    from src.analysis.review_analyzer import run_review_analysis_for_niche
    from src.collection.checkpoint import CheckpointManager
    from src.collection.pacing import PacingManager
    from src.collection.workflows.autocomplete import run_autocomplete_collection
    from src.collection.workflows.fiverr_search import run_fiverr_search_collection
    from src.collection.workflows.gig_detail import run_gig_detail_collection
    from src.collection.workflows.google_trends import run_google_trends_collection
    from src.collection.workflows.keyword_expansion import run_keyword_expansion
    from src.collection.workflows.niche_init import run_niche_initialization
    from src.collection.workflows.reddit_signals import run_reddit_signals_collection
    from src.collection.workflows.seller_profile import run_seller_profile_collection
    from src.collection.workflows.youtube_count import run_youtube_count_collection
    from src.scheduler.queue_processor import QueueProcessor

    if not dry_run:
        raise NotImplementedError(
            "Real collection (dry_run=False) not yet implemented. "
            "Set dry_run=True or await browser wiring in Cycle 026."
        )

    pacing = PacingManager(config if isinstance(config, dict) else {})
    checkpoint_mgr = CheckpointManager(run_id, data_dir="data")
    summary: dict[str, Any] = {
        "run_id": run_id,
        "dry_run": dry_run,
        "stages_run": [],
        "niches_initialized": 0,
        "keywords_queued": 0,
        "search_jobs_run": 0,
        "gig_detail_jobs_run": 0,
        "seller_profile_jobs_run": 0,
        "autocomplete_jobs_run": 0,
        "google_trends_niches_run": 0,
        "reddit_signals_niches_run": 0,
        "youtube_count_niches_run": 0,
        "clustering_niches_run": 0,
        "competitor_profiling_niches_run": 0,
        "gig_quality_analysis_niches_run": 0,
        "review_analysis_niches_run": 0,
        "google_trends_results": [],
        "reddit_signals_results": [],
        "youtube_count_results": [],
        "clustering_results": [],
        "competitor_profiling_results": [],
        "gig_quality_analysis_results": [],
        "review_analysis_results": [],
        "errors": [],
    }

    stage1_result: dict[str, Any] = {"niche_specs": []}
    try:
        stage1_result = await run_niche_initialization(config, db, run_id, dry_run=dry_run)
        summary["niches_initialized"] = int(stage1_result.get("niches_processed", 0))
        checkpoint_mgr.write(
            "stage01",
            "all_niches",
            {"niches_processed": summary["niches_initialized"]},
        )
    except Exception as exc:  # noqa: BLE001
        summary["errors"].append(f"Stage 1 error: {exc}")
    finally:
        summary["stages_run"].append("stage01_niche_init")

    for niche_spec in stage1_result.get("niche_specs", []):
        try:
            stage2_result = await run_keyword_expansion(
                niche_id=str(niche_spec.get("niche_id", "")),
                seeds=list(niche_spec.get("seeds", [])),
                depth=str(niche_spec.get("depth", "standard")),
                run_id=run_id,
                db=db,
                session_manager=session_manager,
                pacing_manager=pacing,
                dry_run=dry_run,
            )
            summary["keywords_queued"] += int(stage2_result.get("keywords_queued", 0))
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"Stage 2 error ({niche_spec.get('niche_id')}): {exc}")
    summary["stages_run"].append("stage02_keyword_expansion")

    config_payload = config if isinstance(config, dict) else {}
    niche_config_map: dict[str, dict[str, Any]] = {}
    raw_niches = config_payload.get("niches", [])
    if isinstance(raw_niches, list):
        for item in raw_niches:
            if not isinstance(item, dict):
                continue
            niche_id = str(item.get("niche_id", "")).strip()
            if niche_id:
                niche_config_map[niche_id] = item
    elif isinstance(raw_niches, dict):
        for value in raw_niches.values():
            if not isinstance(value, dict):
                continue
            niche_id = str(value.get("niche_id", "")).strip()
            if niche_id:
                niche_config_map[niche_id] = value

    queue_db = _InMemoryQueueDb(
        [
            _DryRunJob(
                id=1,
                run_id=run_id,
                job_type="FIVERR_SEARCH",
                stage=3,
                payload={
                    "keyword_id": 0,
                    "keyword_text": "_dry_run_test_",
                    "niche_id": "dry_run",
                    "depth": "standard",
                },
            ),
            _DryRunJob(
                id=2,
                run_id=run_id,
                job_type="GIG_DETAIL",
                stage=4,
                payload={
                    "gig_url": "https://dry-run-test.invalid/",
                    "keyword_id": 0,
                    "niche_id": "dry_run",
                    "depth": "standard",
                },
            ),
            _DryRunJob(
                id=3,
                run_id=run_id,
                job_type="SELLER_PROFILE",
                stage=5,
                payload={
                    "seller_username": "_dry_run_test_",
                    "niche_id": "dry_run",
                },
            ),
        ]
    )
    queue_processor = QueueProcessor(
        db=queue_db,  # type: ignore[arg-type]
        config=config,
        session_manager=session_manager,
        pacing_manager=pacing,
    )

    async def _handle_stage3(job: _DryRunJob, **_kwargs: Any) -> None:
        await run_fiverr_search_collection(
            keyword_id=int(job.payload["keyword_id"]),
            keyword_text=str(job.payload["keyword_text"]),
            niche_id=str(job.payload["niche_id"]),
            depth=str(job.payload["depth"]),
            run_id=run_id,
            db=db,
            session_manager=session_manager,
            pacing_manager=pacing,
            dry_run=True,
        )
        summary["search_jobs_run"] += 1

    async def _handle_stage4(job: _DryRunJob, **_kwargs: Any) -> None:
        await run_gig_detail_collection(
            gig_url=str(job.payload["gig_url"]),
            keyword_id=int(job.payload["keyword_id"]),
            niche_id=str(job.payload["niche_id"]),
            depth=str(job.payload["depth"]),
            run_id=run_id,
            db=db,
            session_manager=session_manager,
            pacing_manager=pacing,
            checkpoint_manager=checkpoint_mgr,
            dry_run=True,
        )
        summary["gig_detail_jobs_run"] += 1

    async def _handle_stage5(job: _DryRunJob, **_kwargs: Any) -> None:
        await run_seller_profile_collection(
            seller_username=str(job.payload["seller_username"]),
            niche_id=str(job.payload["niche_id"]),
            run_id=run_id,
            db=db,
            session_manager=session_manager,
            pacing_manager=pacing,
            checkpoint_manager=checkpoint_mgr,
            dry_run=True,
        )
        summary["seller_profile_jobs_run"] += 1

    queue_processor.register_handler("FIVERR_SEARCH", _handle_stage3)
    queue_processor.register_handler("GIG_DETAIL", _handle_stage4)
    queue_processor.register_handler("SELLER_PROFILE", _handle_stage5)

    try:
        _processed, _failed = await queue_processor.run_until_empty(run_id)
    except Exception as exc:  # noqa: BLE001
        summary["errors"].append(f"Queue processing error: {exc}")

    summary["stages_run"].extend(
        [
            "stage03_fiverr_search",
            "stage04_gig_detail",
            "stage05_seller_profile",
        ]
    )

    for niche_spec in stage1_result.get("niche_specs", []):
        niche_id = str(niche_spec.get("niche_id", ""))
        seeds = [seed for seed in niche_spec.get("seeds", []) if isinstance(seed, str)]
        niche_cfg = niche_config_map.get(niche_id, {})

        external_sources = niche_cfg.get("external_sources", {})
        if not isinstance(external_sources, dict):
            external_sources = {}
        google_enabled = bool(external_sources.get("google_trends", True))
        reddit_enabled = bool(external_sources.get("reddit", True))
        youtube_enabled = bool(external_sources.get("youtube", True))

        raw_subreddits = niche_cfg.get("reddit_subreddits", niche_cfg.get("subreddits", []))
        if not isinstance(raw_subreddits, list):
            raw_subreddits = []
        subreddits = [value.strip() for value in raw_subreddits if isinstance(value, str) and value.strip()]
        if not subreddits:
            metadata = niche_cfg.get("metadata", {})
            if isinstance(metadata, dict):
                metadata_subreddits = metadata.get("subreddits", [])
                if isinstance(metadata_subreddits, list):
                    subreddits = [
                        value.strip() for value in metadata_subreddits if isinstance(value, str) and value.strip()
                    ]

        if google_enabled:
            try:
                trends_result = await run_google_trends_collection(
                    niche_id=niche_id,
                    keywords=seeds,
                    run_id=run_id,
                    db=db,
                    pacing_manager=pacing,
                    dry_run=dry_run,
                )
                summary["google_trends_results"].append(trends_result)
                summary["google_trends_niches_run"] += 1
            except Exception as exc:  # noqa: BLE001
                summary["errors"].append(f"Stage 6a error ({niche_id}): {exc}")

        if reddit_enabled:
            try:
                reddit_result = await run_reddit_signals_collection(
                    niche_id=niche_id,
                    seed_keywords=seeds,
                    subreddits=subreddits,
                    run_id=run_id,
                    db=db,
                    pacing_manager=pacing,
                    llm_client=None,
                    cache=None,
                    checkpoint_manager=checkpoint_mgr,
                    dry_run=dry_run,
                )
                summary["reddit_signals_results"].append(reddit_result)
                summary["reddit_signals_niches_run"] += 1
            except Exception as exc:  # noqa: BLE001
                summary["errors"].append(f"Stage 6b error ({niche_id}): {exc}")

        if youtube_enabled:
            try:
                youtube_result = await run_youtube_count_collection(
                    niche_id=niche_id,
                    seed_keywords=seeds,
                    run_id=run_id,
                    db=db,
                    pacing_manager=pacing,
                    checkpoint_manager=checkpoint_mgr,
                    dry_run=dry_run,
                )
                summary["youtube_count_results"].append(youtube_result)
                summary["youtube_count_niches_run"] += 1
            except Exception as exc:  # noqa: BLE001
                summary["errors"].append(f"Stage 6c error ({niche_id}): {exc}")

    summary["stages_run"].extend(
        [
            "stage06a_google_trends",
            "stage06b_reddit_signals",
            "stage06c_youtube_count",
        ]
    )

    stage8_niche_id = "dry_run"
    stage8_keyword_text = "_dry_run_test_"
    first_niche = stage1_result.get("niche_specs", [])
    if first_niche and isinstance(first_niche[0], dict):
        stage8_niche_id = str(first_niche[0].get("niche_id", "dry_run"))
        seeds = first_niche[0].get("seeds", [])
        if isinstance(seeds, list) and seeds and isinstance(seeds[0], str):
            stage8_keyword_text = seeds[0]
    try:
        await run_autocomplete_collection(
            keyword_id=0,
            keyword_text=stage8_keyword_text,
            niche_id=stage8_niche_id,
            run_id=run_id,
            db=db,
            session_manager=session_manager,
            pacing_manager=pacing,
            checkpoint_manager=checkpoint_mgr,
            dry_run=True,
        )
        summary["autocomplete_jobs_run"] += 1
    except Exception as exc:  # noqa: BLE001
        summary["errors"].append(f"Stage 8 error ({stage8_niche_id}): {exc}")
    summary["stages_run"].append("stage08_autocomplete")

    for niche_spec in stage1_result.get("niche_specs", []):
        niche_id = str(niche_spec.get("niche_id", ""))
        depth = str(niche_spec.get("depth", "standard")).strip().lower()
        if depth == "feasibility":
            summary["clustering_results"].append(
                {
                    "niche_id": niche_id,
                    "clustered": False,
                    "reason": "feasibility_depth_skip",
                }
            )
            continue
        try:
            clustering_result = await run_clustering_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config_payload,
                llm_client=None,
                cache=None,
            )
            summary["clustering_results"].append(clustering_result)
            if clustering_result.get("clustered") is True:
                summary["clustering_niches_run"] += 1
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"Stage 9 error ({niche_id}): {exc}")
    summary["stages_run"].append("stage09_keyword_clustering")

    for niche_spec in stage1_result.get("niche_specs", []):
        niche_id = str(niche_spec.get("niche_id", ""))
        try:
            profiling_result = await run_competitor_profiling_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config if isinstance(config, dict) else {},
                llm_client=None,
            )
            summary["competitor_profiling_results"].append(profiling_result)
            if profiling_result.get("profiled") is True:
                summary["competitor_profiling_niches_run"] += 1
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"Stage 10 error ({niche_id}): {exc}")

    for niche_spec in stage1_result.get("niche_specs", []):
        niche_id = str(niche_spec.get("niche_id", ""))
        try:
            gig_quality_result = await run_gig_quality_analysis_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config if isinstance(config, dict) else {},
                llm_client=None,
            )
            summary["gig_quality_analysis_results"].append(gig_quality_result)
            if gig_quality_result.get("analyzed") is True:
                summary["gig_quality_analysis_niches_run"] += 1
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"Stage 11 error ({niche_id}): {exc}")

    for niche_spec in stage1_result.get("niche_specs", []):
        niche_id = str(niche_spec.get("niche_id", ""))
        try:
            review_result = await run_review_analysis_for_niche(
                niche_id=niche_id,
                run_id=run_id,
                db=db,
                config=config if isinstance(config, dict) else {},
                llm_client=None,
            )
            summary["review_analysis_results"].append(review_result)
            if review_result.get("analyzed") is True:
                summary["review_analysis_niches_run"] += 1
        except Exception as exc:  # noqa: BLE001
            summary["errors"].append(f"Stage 12 error ({niche_id}): {exc}")

    summary["stages_run"].extend(
        [
            "stage10_competitor_profiling",
            "stage11_gig_quality_analysis",
            "stage12_review_analysis",
        ]
    )
    return summary


def _resolve_max_candidates(
    seed_keywords: Sequence[str],
    niche_metadata: Mapping[str, Any] | None,
    requested_max_candidates: int,
) -> tuple[int, str | None]:
    if requested_max_candidates > 0:
        return requested_max_candidates, None

    normalized_seeds = {" ".join(seed.strip().lower().split()) for seed in seed_keywords if seed.strip()}
    raw_modifiers = niche_metadata.get("modifiers", []) if niche_metadata else []
    modifier_count = 0
    if isinstance(raw_modifiers, Sequence) and not isinstance(raw_modifiers, (str | bytes)):
        modifier_count = len({modifier.strip().lower() for modifier in raw_modifiers if isinstance(modifier, str)})
    if niche_metadata and isinstance(niche_metadata.get("niche"), str) and niche_metadata.get("niche", "").strip():
        modifier_count += 1

    safe_cap = max(1, len(normalized_seeds) * (1 + (2 * modifier_count)))
    warning = (
        "Received non-positive max_candidates; "
        f"using deterministic safe cap of {safe_cap} for dry-run expansion."
    )
    return safe_cap, warning


def _build_resumable_stage_id(run_id: str, stage_name: str, execution_index: int) -> str:
    return f"{run_id}:{execution_index:02d}:{stage_name}"


def _load_raw_autocomplete_count(fixture_path: Path | str) -> int | None:
    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict) and isinstance(payload.get("suggestions"), list):
        return len(payload["suggestions"])
    return None


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
    resume_checkpoint_path: Path | str | None = None,
) -> CollectionStageResult:
    """Run collection planning stages without external side effects."""

    started_at = datetime.now(UTC)
    run_id = f"dryrun-{uuid4().hex[:12]}"
    current_stage_name = "stage_1_keyword_expansion"
    try:
        if not isinstance(seed_keywords, Sequence) or isinstance(seed_keywords, (str | bytes)):
            raise ValueError("seed_keywords must be a sequence of strings.")

        resume_summary = (
            load_checkpoint_stage_summary_or_fallback(resume_checkpoint_path) if resume_checkpoint_path else None
        )

        resolved_max_candidates, cap_warning = _resolve_max_candidates(
            seed_keywords,
            niche_metadata,
            max_candidates,
        )
        expanded = expand_keywords(
            seed_keywords,
            niche_metadata=niche_metadata,
            max_candidates=resolved_max_candidates,
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
        if cap_warning:
            warnings.append(cap_warning)
        stage_counts: dict[str, int] = {stage_name: 0 for stage_name in STABLE_COLLECTION_STAGE_NAMES}
        stage_counts["stage_1_keyword_expansion"] = len(expanded.expanded_keywords)
        stage_counts["stage_2_search_plan"] = len(plan.items)
        stage_counts["stage_3_queue"] = len(queue.jobs)
        stage_warnings: dict[str, list[str]] = {}
        stage_statuses: dict[str, str] = {
            "stage_1_keyword_expansion": CollectionStageStatus.SUCCESS.value,
            "stage_2b_autocomplete": CollectionStageStatus.SKIPPED.value,
            "stage_2_search_plan": CollectionStageStatus.SUCCESS.value,
            "stage_3_queue": CollectionStageStatus.SUCCESS.value,
            "stage_4_gig_detail": CollectionStageStatus.SKIPPED.value,
            "stage_5_seller_profile": CollectionStageStatus.SKIPPED.value,
            "stage_6a_external_signals": CollectionStageStatus.SKIPPED.value,
            "stage_6b_community_signals": CollectionStageStatus.SKIPPED.value,
            "stage_7_checkpoint_metadata": CollectionStageStatus.SUCCESS.value,
            "stage_8_pacing_decisions": CollectionStageStatus.SUCCESS.value,
            "stage_9_auto_promotion_decision": CollectionStageStatus.SKIPPED.value,
        }
        stage_skip_reasons: dict[str, str] = {}
        stage_metrics: dict[str, dict[str, Any]] = {}
        fixture_sources: dict[str, str] = {
            "stage_1_keyword_expansion": "derived_seed_keywords",
            "stage_2_search_plan": "derived_search_plan",
            "stage_3_queue": "derived_queue_plan",
            "stage_2b_autocomplete": str(autocomplete_fixture_path) if autocomplete_fixture_path else "placeholder",
            "stage_4_gig_detail": str(gig_detail_fixture_path) if gig_detail_fixture_path else "placeholder",
            "stage_5_seller_profile": str(seller_profile_fixture_path) if seller_profile_fixture_path else "placeholder",
            "stage_6a_external_signals": (
                str(external_signal_fixture_path) if external_signal_fixture_path else "placeholder"
            ),
            "stage_6b_community_signals": (
                str(community_signal_fixture_path) if community_signal_fixture_path else "placeholder"
            ),
            "stage_7_checkpoint_metadata": "derived_checkpoint_contract",
            "stage_8_pacing_decisions": "derived_pacing_contract",
            "stage_9_auto_promotion_decision": "derived_readiness_contract",
        }
        pacing_decisions = {
            "queue_mode": "deterministic_fixture",
            "per_page_limit": max_pages,
            "queue_jobs": len(queue.jobs),
            "candidate_cap": resolved_max_candidates,
        }
        stage_metrics["stage_8_pacing_decisions"] = {
            "implemented": True,
            "decision_count": len(pacing_decisions),
        }
        if resume_checkpoint_path and resume_summary is None:
            warning = "Resume checkpoint was unavailable or invalid; dry-run started from stage_1."
            warnings.append(warning)
            stage_warnings.setdefault("stage_7_checkpoint_metadata", []).append(warning)

        if autocomplete_fixture_path:
            current_stage_name = "stage_2b_autocomplete"
            autocomplete_plan = load_autocomplete_fixture(
                autocomplete_fixture_path,
                seed_keyword=expanded.expanded_keywords[0].source_seed if expanded.expanded_keywords else "seed",
            )
            stage_counts["stage_2b_autocomplete"] = len(autocomplete_plan.suggestions)
            stage_statuses["stage_2b_autocomplete"] = CollectionStageStatus.SUCCESS.value
            raw_suggestion_count = _load_raw_autocomplete_count(autocomplete_fixture_path)
            deduplicated_count = len(autocomplete_plan.suggestions)
            stage_metrics["stage_2b_autocomplete"] = {
                "implemented": True,
                "dedupe_metadata": {
                    "raw_suggestion_count": raw_suggestion_count,
                    "deduplicated_suggestion_count": deduplicated_count,
                    "duplicates_removed": (
                        raw_suggestion_count - deduplicated_count
                        if isinstance(raw_suggestion_count, int) and raw_suggestion_count >= deduplicated_count
                        else 0
                    ),
                },
            }
            if autocomplete_plan.warnings:
                stage_warnings["stage_2b_autocomplete"] = list(autocomplete_plan.warnings)
                warnings.extend(autocomplete_plan.warnings)
        else:
            skip_reason = "Autocomplete fixture not provided; stage skipped in fixture-only dry-run."
            stage_skip_reasons["stage_2b_autocomplete"] = skip_reason
            stage_warnings.setdefault("stage_2b_autocomplete", []).append(skip_reason)
            stage_metrics["stage_2b_autocomplete"] = {"implemented": False, "readiness_status": "skipped"}
            warnings.append(skip_reason)

        if gig_detail_fixture_path:
            current_stage_name = "stage_4_gig_detail"
            gig_detail_html = Path(gig_detail_fixture_path).read_text(encoding="utf-8")
            gig_detail = parse_gig_detail_from_html(gig_detail_html)
            stage_counts["stage_4_gig_detail"] = 1 if gig_detail.title else 0
            stage_statuses["stage_4_gig_detail"] = CollectionStageStatus.SUCCESS.value
            stage_metrics["stage_4_gig_detail"] = {
                "implemented": True,
                "title_found": bool(gig_detail.title),
                "package_count": len(gig_detail.packages),
            }
            if gig_detail.warnings:
                stage_warnings["stage_4_gig_detail"] = list(gig_detail.warnings)
                warnings.extend(gig_detail.warnings)
        else:
            skip_reason = "Gig detail fixture not provided; stage skipped in fixture-only dry-run."
            stage_skip_reasons["stage_4_gig_detail"] = skip_reason
            stage_warnings.setdefault("stage_4_gig_detail", []).append(skip_reason)
            stage_metrics["stage_4_gig_detail"] = {"implemented": False, "readiness_status": "skipped"}
            warnings.append(skip_reason)

        if seller_profile_fixture_path:
            current_stage_name = "stage_5_seller_profile"
            seller_profile_html = Path(seller_profile_fixture_path).read_text(encoding="utf-8")
            seller_profile = parse_seller_profile_from_html(seller_profile_html)
            stage_counts["stage_5_seller_profile"] = 1 if seller_profile.display_name or seller_profile.username else 0
            stage_statuses["stage_5_seller_profile"] = CollectionStageStatus.SUCCESS.value
            stage_metrics["stage_5_seller_profile"] = {
                "readiness_status": "implemented",
                "implemented": True,
                "records_seen": 1,
                "records_written": stage_counts["stage_5_seller_profile"],
            }
            if stage_counts["stage_5_seller_profile"] == 0:
                warning = (
                    "Seller profile fixture did not include seller identity detail; "
                    "Stage 5 readiness is blocked until fixture coverage improves."
                )
                stage_metrics["stage_5_seller_profile"]["readiness_status"] = "blocked"
                stage_warnings.setdefault("stage_5_seller_profile", []).append(warning)
                warnings.append(warning)
            if seller_profile.warnings:
                stage_warnings.setdefault("stage_5_seller_profile", []).extend(seller_profile.warnings)
                warnings.extend(seller_profile.warnings)
        else:
            skip_reason = (
                "Seller profile fixture not provided; stage skipped and Stage 5 readiness remains fixture-blocked."
            )
            stage_skip_reasons["stage_5_seller_profile"] = skip_reason
            stage_warnings.setdefault("stage_5_seller_profile", []).append(skip_reason)
            stage_metrics["stage_5_seller_profile"] = {
                "readiness_status": "skipped",
                "implemented": False,
                "records_seen": 0,
                "records_written": 0,
            }
            warnings.append(skip_reason)

        if external_signal_fixture_path:
            current_stage_name = "stage_6a_external_signals"
            external_signals = load_external_signal_fixture(external_signal_fixture_path)
            stage_counts["stage_6a_external_signals"] = len(external_signals)
            stage_statuses["stage_6a_external_signals"] = CollectionStageStatus.SUCCESS.value
            stage_metrics["stage_6a_external_signals"] = {
                "readiness_status": "implemented",
                "implemented": True,
                "signal_sources": sorted({signal.source.value for signal in external_signals}),
            }
            if not external_signals:
                warning = "External signal fixture returned zero records."
                stage_warnings["stage_6a_external_signals"] = [warning]
                warnings.append(warning)
                stage_metrics["stage_6a_external_signals"]["readiness_status"] = "blocked"
        else:
            skip_reason = "External signal fixture not provided; stage skipped with zero counts."
            stage_skip_reasons["stage_6a_external_signals"] = skip_reason
            stage_warnings.setdefault("stage_6a_external_signals", []).append(skip_reason)
            stage_metrics["stage_6a_external_signals"] = {
                "readiness_status": "skipped",
                "implemented": False,
                "signal_sources": [],
            }
            warnings.append(skip_reason)

        if community_signal_fixture_path:
            current_stage_name = "stage_6b_community_signals"
            community_signals, community_warnings = load_community_signal_fixture(community_signal_fixture_path)
            stage_counts["stage_6b_community_signals"] = len(community_signals)
            stage_statuses["stage_6b_community_signals"] = CollectionStageStatus.SUCCESS.value
            stage_metrics["stage_6b_community_signals"] = {
                "readiness_status": "implemented",
                "implemented": True,
                "record_count": len(community_signals),
            }
            if not community_signals:
                warning = "Community signal fixture returned zero records."
                stage_warnings.setdefault("stage_6b_community_signals", []).append(warning)
                warnings.append(warning)
                stage_metrics["stage_6b_community_signals"]["readiness_status"] = "blocked"
            if community_warnings:
                stage_warnings.setdefault("stage_6b_community_signals", []).extend(community_warnings)
                warnings.extend(community_warnings)
        else:
            skip_reason = "Community signal fixture not provided; stage skipped with zero counts."
            stage_skip_reasons["stage_6b_community_signals"] = skip_reason
            stage_warnings.setdefault("stage_6b_community_signals", []).append(skip_reason)
            stage_metrics["stage_6b_community_signals"] = {
                "readiness_status": "skipped",
                "implemented": False,
                "record_count": 0,
            }
            warnings.append(skip_reason)

        auto_promotion_lineage: dict[str, Any] = {
            "seed_keywords": sorted({item.source_seed for item in expanded.expanded_keywords}),
            "queue_job_ids": [job.job_id for job in queue.jobs[:5]],
        }
        criteria_evaluated = [
            "gig_detail_fixture_available",
            "seller_profile_fixture_available",
            "external_or_community_signal_available",
            "queue_has_candidates",
        ]
        has_required_lineage = (
            stage_counts["stage_4_gig_detail"] > 0
            and stage_counts["stage_3_queue"] > 0
            and (stage_counts["stage_6a_external_signals"] > 0 or stage_counts["stage_6b_community_signals"] > 0)
        )
        if has_required_lineage:
            current_stage_name = "stage_9_auto_promotion_decision"
            stage_counts["stage_9_auto_promotion_decision"] = 1
            stage_statuses["stage_9_auto_promotion_decision"] = CollectionStageStatus.SUCCESS.value
            stage_metrics["stage_9_auto_promotion_decision"] = {
                "readiness_status": "implemented",
                "decision_status": "not_promoted",
                "criteria_evaluated": criteria_evaluated,
                "lineage": auto_promotion_lineage,
            }
        else:
            skip_reason = "Auto-promotion placeholder skipped; insufficient fixture lineage for deterministic decision."
            stage_skip_reasons["stage_9_auto_promotion_decision"] = skip_reason
            stage_warnings.setdefault("stage_9_auto_promotion_decision", []).append(skip_reason)
            stage_metrics["stage_9_auto_promotion_decision"] = {
                "readiness_status": "skipped",
                "decision_status": "blocked",
                "criteria_evaluated": criteria_evaluated,
                "lineage": auto_promotion_lineage,
            }
            warnings.append(skip_reason)

        stage_summary: dict[str, object] = {
            "stage_counts": stage_counts,
            "stage_names": list(STABLE_COLLECTION_STAGE_NAMES),
            "stage_warnings": stage_warnings,
            "stage_metrics": stage_metrics,
            "fixture_sources": fixture_sources,
            "checkpoint_metadata": {
                "schema_version": "1.0",
                "job_count": len(queue.jobs),
                "checkpoint_requested": str(checkpoint_path),
            },
            "pacing_decisions": pacing_decisions,
            "stage_order_contract": "stage_names_execution_order__stage_counts_unordered",
            "mode": "dry_run_fixture_optional",
        }
        stage_counts["stage_7_checkpoint_metadata"] = 1
        stage_counts["stage_8_pacing_decisions"] = 1
        records_seen = sum(stage_counts.get(stage_name, 0) for stage_name in RECORDS_SEEN_STAGE_NAMES)
        records_written = sum(stage_counts.get(stage_name, 0) for stage_name in RECORDS_WRITTEN_STAGE_NAMES)
        stage_execution: list[dict[str, object]] = []
        resume_stage_id_by_name: dict[str, str] = {}
        if isinstance(resume_summary, dict):
            previous_stage_execution = resume_summary.get("stage_execution")
            if isinstance(previous_stage_execution, list):
                for entry in previous_stage_execution:
                    if isinstance(entry, dict):
                        previous_stage_name = entry.get("stage_name")
                        previous_stage_id = entry.get("resumable_stage_id")
                        if isinstance(previous_stage_name, str) and isinstance(previous_stage_id, str):
                            resume_stage_id_by_name[previous_stage_name] = previous_stage_id
        for index, stage_name in enumerate(STABLE_COLLECTION_STAGE_NAMES, start=1):
            stage_started_at = (started_at + timedelta(milliseconds=(index * 2) - 1)).isoformat()
            stage_finished_at = (started_at + timedelta(milliseconds=index * 2)).isoformat()
            stage_entry: dict[str, object] = {
                "stage_name": stage_name,
                "execution_index": index,
                "status": stage_statuses[stage_name],
                "started_at": stage_started_at,
                "finished_at": stage_finished_at,
                "resumable_stage_id": _build_resumable_stage_id(run_id, stage_name, index),
            }
            if stage_name in stage_skip_reasons:
                stage_entry["skip_reason"] = stage_skip_reasons[stage_name]
            previous_stage_id = resume_stage_id_by_name.get(stage_name)
            if previous_stage_id:
                stage_entry["resumed_from_stage_id"] = previous_stage_id
            stage_execution.append(stage_entry)
        skipped_stage_names = [
            stage_name
            for stage_name in STABLE_COLLECTION_STAGE_NAMES
            if stage_statuses[stage_name] == CollectionStageStatus.SKIPPED.value
        ]
        failed_stage_names = [
            stage_name
            for stage_name in STABLE_COLLECTION_STAGE_NAMES
            if stage_statuses[stage_name] == CollectionStageStatus.FAILED.value
        ]
        stage_summary["stage_execution"] = stage_execution
        stage_summary["skipped_stage_names"] = skipped_stage_names
        stage_summary["failed_stage_names"] = failed_stage_names
        stage_summary["resumable_stage_identity"] = {
            "run_id": run_id,
            "last_completed_stage_id": stage_execution[-1]["resumable_stage_id"],
            "resume_checkpoint_path": str(resume_checkpoint_path) if resume_checkpoint_path else None,
        }
        checkpoint_evidence = CollectionCheckpointEvidence(
            checkpoint_path=str(checkpoint_path),
            pacing_decisions=pacing_decisions,
            cooldown_applied=False,
            retry_count=0,
            fixture_mode=True,
        )
        stage_summary["records_seen"] = records_seen
        stage_summary["records_written"] = records_written
        stage_summary["warnings"] = list(warnings)
        stage_summary["warning_count"] = len(warnings)
        stage_summary["failed"] = False
        stage_summary["checkpoint_evidence"] = checkpoint_evidence.model_dump()
        validate_collection_stage_summary(stage_summary)
        saved_checkpoint = checkpoint_queue_state(queue, checkpoint_path, stage_summary=stage_summary)
        persisted_checkpoint_evidence = checkpoint_evidence.model_copy(
            update={"checkpoint_path": str(saved_checkpoint)}
        )

        return CollectionStageResult(
            stage_name="collection_dry_run",
            status=CollectionStageStatus.SUCCESS,
            records_seen=records_seen,
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
                "stage_execution": stage_execution,
                "skipped_stage_names": skipped_stage_names,
                "fixture_sources": fixture_sources,
                "max_pages": max_pages,
                "checkpoint_evidence": persisted_checkpoint_evidence.model_dump(),
                "resumable_stage_identity": stage_summary["resumable_stage_identity"],
                "stage_metrics": stage_metrics,
            },
        )
    except (FileNotFoundError, AutocompleteFixtureError) as exc:
        failed_stage_id = _build_resumable_stage_id(run_id, current_stage_name, 0)
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
            metadata={
                "stage_summary": {
                    "failed": True,
                    "error_code": "fixture_unavailable",
                    "failed_stage_names": [current_stage_name],
                    "stage_execution": [
                        {
                            "stage_name": current_stage_name,
                            "execution_index": 1,
                            "status": CollectionStageStatus.FAILED.value,
                            "failure_code": "fixture_unavailable",
                            "started_at": started_at.isoformat(),
                            "finished_at": datetime.now(UTC).isoformat(),
                            "resumable_stage_id": failed_stage_id,
                        }
                    ],
                }
            },
        )
    except Exception as exc:
        failed_stage_id = _build_resumable_stage_id(run_id, current_stage_name, 0)
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
            metadata={
                "stage_summary": {
                    "failed": True,
                    "error_code": "dry_run_failed",
                    "failed_stage_names": [current_stage_name],
                    "stage_execution": [
                        {
                            "stage_name": current_stage_name,
                            "execution_index": 1,
                            "status": CollectionStageStatus.FAILED.value,
                            "failure_code": "dry_run_failed",
                            "started_at": started_at.isoformat(),
                            "finished_at": datetime.now(UTC).isoformat(),
                            "resumable_stage_id": failed_stage_id,
                        }
                    ],
                }
            },
        )
