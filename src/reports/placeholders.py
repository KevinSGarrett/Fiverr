"""Placeholder reporting models for foundation scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True, frozen=True)
class ReportPlaceholder:
    """Minimal placeholder for report generation state."""

    report_type: str
    status: str
    message: str


GOVERNANCE_REPORT_ORDER = (
    "local_parity",
    "github_actions",
    "codecov_project",
    "codecov_patch",
    "codex_disposition",
)

JIRA_MAPPING_TYPES = frozenset({"governance", "product"})
JIRA_UPDATED_BY_VALUES = frozenset({"pm", "cursor_agent", "pm_and_cursor_agent", "unknown"})
ACTIVE_STORY_STATUSES = frozenset({"in_progress", "in_review", "blocked"})
DEFAULT_VALIDATION_COMMANDS = (
    "python -m ruff check .",
    "python -m mypy src",
    "python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90",
    "python run.py config-check",
    "python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle014.db",
    "python run.py phase2-smoke",
)


def build_governance_report_placeholders(
    *,
    local_parity: str = "pending",
    github_actions: str = "pending",
    codecov_project: str = "pending",
    codecov_patch: str = "pending",
    codex_disposition: str = "pending",
) -> tuple[ReportPlaceholder, ...]:
    """Return user-facing governance checks with deterministic ordering."""
    statuses = {
        "local_parity": local_parity,
        "github_actions": github_actions,
        "codecov_project": codecov_project,
        "codecov_patch": codecov_patch,
        "codex_disposition": codex_disposition,
    }
    messages = {
        "local_parity": "Local parity checks (ruff, mypy, pytest coverage gate, config-check, foundation-gate, phase2-smoke).",
        "github_actions": "GitHub Actions workflow checks for the PR head commit.",
        "codecov_project": "Codecov project status check for repository-wide coverage.",
        "codecov_patch": "Codecov patch status check for diff coverage.",
        "codex_disposition": "Codex review-thread disposition and resolution state.",
    }
    return tuple(
        ReportPlaceholder(report_type=report_type, status=statuses[report_type], message=messages[report_type])
        for report_type in GOVERNANCE_REPORT_ORDER
    )


def build_jira_mapping_table(
    rows: list[dict[str, Any]],
    *,
    output_format: str = "dict",
) -> list[dict[str, Any]] | str:
    """Build deterministic Jira mapping rows for governance and product stories."""
    normalized_rows: list[dict[str, Any]] = []
    seen_jira_keys: set[str] = set()
    for raw_row in rows:
        changed_file_group = str(raw_row.get("changed_file_group", "")).strip()
        jira_keys = raw_row.get("jira_keys")
        mapping_type = str(raw_row.get("mapping_type", "governance")).strip().lower() or "governance"
        status = str(raw_row.get("status", "pending")).strip() or "pending"
        dod_status = str(raw_row.get("dod_status", "pending")).strip() or "pending"
        agent = str(raw_row.get("agent", "unknown")).strip() or "unknown"
        cycle = str(raw_row.get("cycle", "unknown")).strip() or "unknown"
        branch = str(raw_row.get("branch", "unknown")).strip() or "unknown"
        pull_request = str(raw_row.get("pull_request", "pending")).strip() or "pending"
        jira_updated_by = str(raw_row.get("jira_updated_by", "unknown")).strip().lower() or "unknown"
        not_applicable_reason = str(raw_row.get("not_applicable_reason", "")).strip()

        if not changed_file_group:
            raise ValueError("changed_file_group is required for Jira mapping rows.")
        if mapping_type not in JIRA_MAPPING_TYPES:
            raise ValueError("mapping_type must be 'governance' or 'product'.")
        if jira_updated_by not in JIRA_UPDATED_BY_VALUES:
            raise ValueError("jira_updated_by must be pm, cursor_agent, pm_and_cursor_agent, or unknown.")

        normalized_keys: list[str] = []
        if jira_keys is None:
            normalized_keys = []
        elif isinstance(jira_keys, str):
            normalized_keys = [jira_keys.strip()] if jira_keys.strip() else []
        else:
            normalized_keys = [str(key).strip() for key in jira_keys if str(key).strip()]
        if len(set(normalized_keys)) != len(normalized_keys):
            raise ValueError("jira_keys contains duplicates inside a mapping row.")

        if not normalized_keys and not not_applicable_reason:
            raise ValueError("jira_keys are required unless not_applicable_reason is provided.")
        for key in normalized_keys:
            if key in seen_jira_keys:
                raise ValueError(f"jira_keys contains duplicate key across rows: {key}")
            seen_jira_keys.add(key)

        normalized_rows.append(
            {
                "changed_file_group": changed_file_group,
                "mapping_type": mapping_type,
                "jira_keys": normalized_keys,
                "status": status,
                "dod_status": dod_status,
                "agent": agent,
                "cycle": cycle,
                "branch": branch,
                "pull_request": pull_request,
                "jira_updated_by": jira_updated_by,
                "not_applicable_reason": not_applicable_reason,
            }
        )
    normalized_rows.sort(key=lambda row: (row["mapping_type"], row["changed_file_group"], row["agent"]))

    if output_format == "dict":
        return normalized_rows
    if output_format != "markdown":
        raise ValueError("output_format must be 'dict' or 'markdown'.")

    header = (
        "| Mapping Type | Changed File Group | Jira Keys | Status | DOD Status | Agent | Cycle | Branch | PR | Jira Updated By | Not Applicable Reason |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    body_lines = []
    for row in normalized_rows:
        jira_keys = ", ".join(row["jira_keys"]) if row["jira_keys"] else "-"
        not_applicable_reason = row["not_applicable_reason"] or "-"
        body_lines.append(
            f"| {row['mapping_type']} | {row['changed_file_group']} | {jira_keys} | {row['status']} | {row['dod_status']} | {row['agent']} | {row['cycle']} | {row['branch']} | {row['pull_request']} | {row['jira_updated_by']} | {not_applicable_reason} |"
        )
    return "\n".join([header, *body_lines])


def build_active_story_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group active Jira-mapped stories from report/manifest evidence."""
    grouped: dict[str, dict[str, Any]] = {}
    for raw_row in rows:
        status = str(raw_row.get("status", "")).strip().lower()
        if status not in ACTIVE_STORY_STATUSES:
            continue
        story_group = str(raw_row.get("story_group") or raw_row.get("changed_file_group", "")).strip()
        if not story_group:
            continue
        jira_keys_value = raw_row.get("jira_keys")
        if isinstance(jira_keys_value, str):
            jira_keys = [jira_keys_value.strip()] if jira_keys_value.strip() else []
        else:
            jira_keys = [str(key).strip() for key in jira_keys_value or [] if str(key).strip()]
        source = str(raw_row.get("source", "report")).strip() or "report"
        cycle = str(raw_row.get("cycle", "unknown")).strip() or "unknown"
        branch = str(raw_row.get("branch", "unknown")).strip() or "unknown"

        group = grouped.setdefault(
            story_group,
            {
                "story_group": story_group,
                "jira_keys": set(),
                "statuses": set(),
                "sources": set(),
                "cycles": set(),
                "branches": set(),
            },
        )
        group["jira_keys"].update(jira_keys)
        group["statuses"].add(status)
        group["sources"].add(source)
        group["cycles"].add(cycle)
        group["branches"].add(branch)

    normalized_groups: list[dict[str, Any]] = []
    for story_group in sorted(grouped):
        group = grouped[story_group]
        normalized_groups.append(
            {
                "story_group": story_group,
                "jira_keys": sorted(group["jira_keys"]),
                "statuses": sorted(group["statuses"]),
                "sources": sorted(group["sources"]),
                "cycles": sorted(group["cycles"]),
                "branches": sorted(group["branches"]),
            }
        )
    return normalized_groups


def build_integration_evidence_summary(
    *,
    validation_commands: tuple[str, ...] = DEFAULT_VALIDATION_COMMANDS,
    stage_status: dict[str, str] | None = None,
    codex_status: str = "pending",
    codecov_project_status: str = "pending",
    codecov_patch_status: str = "pending",
    jira_progress: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one deterministic summary covering validation, checks, and Jira progress."""
    normalized_stages = dict(stage_status or {})
    normalized_jira_rows = []
    for row in jira_progress or []:
        normalized_jira_rows.append(
            {
                "jira_key": str(row.get("jira_key", "")).strip(),
                "ac_advanced": str(row.get("ac_advanced", "")).strip(),
                "dod_remaining": str(row.get("dod_remaining", "")).strip(),
                "status_recommendation": str(row.get("status_recommendation", "in_progress")).strip(),
            }
        )
    return {
        "validation_commands": list(validation_commands),
        "stage_status": normalized_stages,
        "codex_status": codex_status.strip().lower() or "pending",
        "codecov": {
            "project": codecov_project_status.strip().lower() or "pending",
            "patch": codecov_patch_status.strip().lower() or "pending",
        },
        "jira_progress": normalized_jira_rows,
        "summary": {
            "validation_count": len(validation_commands),
            "stages_reported": len(normalized_stages),
            "jira_rows": len(normalized_jira_rows),
        },
    }


def build_runtime_diagnostics_markdown_table(
    *,
    diagnostics: dict[str, Any],
    include_header: bool = True,
) -> str:
    """Render deterministic markdown table for app/query diagnostics handoff."""
    categories = diagnostics.get("categories", {})
    warning_categories = set(diagnostics.get("warning_categories", []))
    blocking_categories = set(diagnostics.get("blocking_categories", []))
    rows: list[str] = []
    if include_header:
        rows.extend(
            [
                "| Diagnostic | Status | Severity | Notes |",
                "| --- | --- | --- | --- |",
            ]
        )
    for category in sorted(categories):
        status = str(categories.get(category, "unknown")).strip() or "unknown"
        severity = "error" if category in blocking_categories else ("warning" if category in warning_categories else "ok")
        notes = "blocking" if severity == "error" else ("review recommended" if severity == "warning" else "ready")
        rows.append(f"| {category} | {status} | {severity} | {notes} |")
    if len(rows) <= (2 if include_header else 0):
        rows.append("| diagnostics | unknown | warning | no categories were provided |")
    return "\n".join(rows)


def _to_float_or_none(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    return None


def _sanitize_confidence(value: Any) -> float:
    parsed = _to_float_or_none(value)
    if parsed is None:
        return 0.0
    return max(0.0, min(1.0, round(parsed, 3)))


def _sanitize_score(value: Any) -> float:
    parsed = _to_float_or_none(value)
    if parsed is None:
        return 0.0
    return max(0.0, min(100.0, round(parsed, 2)))


def build_analysis_summary_rows(
    stage_outputs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Build compact, safe analysis summary rows for reports/exports."""
    rows: list[dict[str, Any]] = []
    warnings: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for index, output in enumerate(stage_outputs, start=1):
        stage = str(output.get("stage", "unknown")).strip() or "unknown"
        row_id = str(output.get("id", f"{stage}:{index}")).strip() or f"{stage}:{index}"
        if row_id in seen_ids:
            warnings.append(
                {
                    "code": "duplicate_identifier",
                    "message": f"Duplicate analysis summary row id '{row_id}' was skipped.",
                }
            )
            continue
        seen_ids.add(row_id)

        confidence_raw = output.get("confidence")
        confidence = _sanitize_confidence(confidence_raw)
        if confidence_raw is not None and confidence != confidence_raw:
            warnings.append(
                {
                    "code": "confidence_clamped",
                    "message": f"Confidence out of range for '{row_id}' was clamped.",
                }
            )

        score_raw = output.get("score")
        score = _sanitize_score(score_raw)
        if score_raw is not None and score != score_raw:
            warnings.append(
                {
                    "code": "score_clamped",
                    "message": f"Score out of range for '{row_id}' was clamped.",
                }
            )

        rows.append(
            {
                "id": row_id,
                "stage": stage,
                "status": str(output.get("status", "unknown")).strip() or "unknown",
                "score": score,
                "confidence": confidence,
                "warning_count": int(output.get("warning_count", 0))
                if isinstance(output.get("warning_count"), int)
                else 0,
                "source_id": str(output.get("source_id", "analysis-dry-run")).strip() or "analysis-dry-run",
            }
        )

    return rows, warnings

