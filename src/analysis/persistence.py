"""Persistence helpers for analysis run summaries."""

from __future__ import annotations

from typing import Any

from src.analysis.contracts import AnalysisRunSummary, AnalysisStageSummary
from src.models.analysis import AnalysisResult, AnalysisRun
from src.models.database import create_session_factory, initialize_database
from src.models.runtime import RunLog


def _extract_stage_confidence(stage: AnalysisStageSummary) -> float | None:
    readiness_contract = stage.metadata.get("readiness_contract")
    if isinstance(readiness_contract, dict):
        for key in ("confidence_estimate", "selection_confidence", "coverage_ratio", "completeness_ratio"):
            value = readiness_contract.get(key)
            if isinstance(value, int | float):
                return float(value)
    value = stage.metadata.get("intent_keyword_selection_confidence")
    if isinstance(value, int | float):
        return float(value)
    return None


def _stage_message(stage: AnalysisStageSummary) -> str:
    if stage.status.value == "failed":
        return f"{stage.stage.value} failed"
    if stage.readiness_reasons:
        return f"{stage.stage.value} completed with readiness caveats"
    return f"{stage.stage.value} completed"


def persist_analysis_run_summary(
    summary: AnalysisRunSummary,
    *,
    database_url: str,
    mode: str = "analysis-dry-run",
) -> dict[str, Any]:
    """Persist analysis run and stage summaries into local database tables."""
    engine = initialize_database(database_url=database_url)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        run = AnalysisRun(
            run_label=summary.run_id,
            mode=mode,
            started_by="cli",
            completed_at=summary.finished_at.isoformat(),
            status=summary.status.value,
            run_context_json={
                "source_id": summary.source_id,
                "started_at": summary.started_at.isoformat(),
                "finished_at": summary.finished_at.isoformat(),
                "metadata": summary.metadata,
            },
        )
        session.add(run)
        session.flush()

        persisted_stage_count = 0
        persisted_log_count = 0
        for stage in summary.stages:
            stage_result = AnalysisResult(
                run_id=run.id,
                analysis_type=stage.stage.value,
                explanation=stage.metadata.get("explanation"),
                confidence=_extract_stage_confidence(stage),
                status=stage.status.value,
                raw_json=stage.to_persistence_dict(),
            )
            session.add(stage_result)
            persisted_stage_count += 1

            stage_log = RunLog(
                run_id=run.id,
                mode=mode,
                stage=stage.stage.value,
                status=stage.status.value,
                message=_stage_message(stage),
                details_json={
                    "result_type": stage.result_type,
                    "warning_count": len(stage.warnings),
                    "readiness_status": stage.readiness_status.value,
                    "readiness_reasons": stage.readiness_reasons,
                    "metadata": stage.metadata,
                },
            )
            session.add(stage_log)
            persisted_log_count += 1

        run_log = RunLog(
            run_id=run.id,
            mode=mode,
            stage="analysis_run",
            status=summary.status.value,
            message="analysis run summary persisted",
            details_json={
                "run_id": summary.run_id,
                "source_id": summary.source_id,
                "stage_count": len(summary.stages),
                "warning_count": len(summary.warnings),
            },
        )
        session.add(run_log)
        persisted_log_count += 1

        session.commit()
        return {
            "run_table_id": run.id,
            "persisted_stage_count": persisted_stage_count,
            "persisted_log_count": persisted_log_count,
        }
