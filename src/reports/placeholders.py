"""Placeholder reporting models for foundation scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.analysis.contracts import validate_analysis_integrity_records


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
NONCANONICAL_STARTER_KEY_RANGE = range(1, 5)
NONCANONICAL_DUPLICATE_EPIC_RANGE = range(27, 43)
DUPLICATE_DONE_RISK_KEYS = frozenset({"SCRUM-217", "SCRUM-221", "SCRUM-222"})
DEFAULT_VALIDATION_COMMANDS = (
    "python -m ruff check .",
    "python -m mypy src",
    "python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90",
    "python run.py config-check",
    "python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle014.db",
    "python run.py phase2-smoke",
)
RUNTIME_READINESS_STATUS_ORDER = {
    "ready": 0,
    "warning": 1,
    "unknown": 2,
    "blocked": 3,
}
_RUNTIME_STATUS_NORMALIZATION = {
    "ok": "ready",
    "pass": "ready",
    "error": "blocked",
    "fail": "blocked",
}


def _parse_scrum_numeric_id(jira_key: str) -> int | None:
    normalized = jira_key.strip().upper()
    if not normalized.startswith("SCRUM-"):
        return None
    suffix = normalized.removeprefix("SCRUM-")
    if not suffix.isdigit():
        return None
    return int(suffix)


def _is_noncanonical_board_key(jira_key: str) -> bool:
    key_number = _parse_scrum_numeric_id(jira_key)
    if key_number is None:
        return False
    return key_number in NONCANONICAL_STARTER_KEY_RANGE or key_number in NONCANONICAL_DUPLICATE_EPIC_RANGE


def build_board_reconciliation_entries(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build deterministic board reconciliation entries for steward evidence."""
    normalized_entries: list[dict[str, Any]] = []
    for raw_row in rows:
        jira_key = str(raw_row.get("jira_key", "")).strip().upper()
        if not jira_key:
            raise ValueError("jira_key is required for reconciliation entries.")
        status = str(raw_row.get("status", "unknown")).strip().lower() or "unknown"
        touched = bool(raw_row.get("touched", False))
        canonical_scope = str(raw_row.get("canonical_scope", "product")).strip().lower() or "product"
        if canonical_scope not in {"product", "governance", "future_scope", "noncanonical"}:
            raise ValueError("canonical_scope must be product, governance, future_scope, or noncanonical.")
        board_source = str(raw_row.get("board_source", "jira")).strip() or "jira"

        is_duplicate_done_risk = jira_key in DUPLICATE_DONE_RISK_KEYS
        is_noncanonical = canonical_scope == "noncanonical" or _is_noncanonical_board_key(jira_key)
        done_requested = status == "done"

        recommended_status = status
        exclusion_reason = ""
        if is_noncanonical:
            recommended_status = "excluded_noncanonical"
            exclusion_reason = "starter_or_duplicate_epic"
        elif canonical_scope == "future_scope" and touched:
            recommended_status = "blocked_future_scope"
            exclusion_reason = "future_scope_touched"
        elif done_requested and (is_duplicate_done_risk or touched):
            recommended_status = "hold_non_done"
            exclusion_reason = "done_requires_full_source_dod"
        elif done_requested and canonical_scope == "product":
            recommended_status = "verify_done_evidence"
            exclusion_reason = "needs_full_ac_dod_proof"

        normalized_entries.append(
            {
                "jira_key": jira_key,
                "status": status,
                "touched": touched,
                "canonical_scope": canonical_scope,
                "board_source": board_source,
                "is_noncanonical": is_noncanonical,
                "is_duplicate_done_risk": is_duplicate_done_risk,
                "recommended_status": recommended_status,
                "exclusion_reason": exclusion_reason,
            }
        )
    normalized_entries.sort(key=lambda row: row["jira_key"])
    return normalized_entries


def build_ac_dod_progress_markdown_table(rows: list[dict[str, Any]]) -> str:
    """Render stable AC/DoD progress table rows for PR/report bodies."""
    if not rows:
        return (
            "| Jira Key | AC/DoD Progress | Remaining Gap | Status Recommendation |\n"
            "| --- | --- | --- | --- |\n"
            "| - | No AC/DoD updates recorded. | Steward follow-up required. | In Progress |"
        )

    normalized_rows: list[dict[str, str]] = []
    for raw_row in rows:
        jira_key = str(raw_row.get("jira_key", "")).strip().upper()
        progress = str(raw_row.get("ac_dod_progress", "")).strip()
        remaining_gap = str(raw_row.get("remaining_gap", "")).strip()
        recommendation = str(raw_row.get("status_recommendation", "in_progress")).strip() or "in_progress"
        if not jira_key:
            raise ValueError("jira_key is required for AC/DoD progress rows.")
        if not progress:
            raise ValueError(f"ac_dod_progress is required for {jira_key}.")
        if not remaining_gap:
            raise ValueError(f"remaining_gap is required for {jira_key}.")
        normalized_rows.append(
            {
                "jira_key": jira_key,
                "ac_dod_progress": progress,
                "remaining_gap": remaining_gap,
                "status_recommendation": recommendation,
            }
        )
    normalized_rows.sort(key=lambda row: row["jira_key"])

    lines = [
        "| Jira Key | AC/DoD Progress | Remaining Gap | Status Recommendation |",
        "| --- | --- | --- | --- |",
    ]
    for row in normalized_rows:
        lines.append(
            f"| {row['jira_key']} | {row['ac_dod_progress']} | {row['remaining_gap']} | {row['status_recommendation']} |"
        )
    return "\n".join(lines)


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


def build_runtime_diagnostics_section(
    *,
    diagnostics: dict[str, Any],
    stage: str = "app_entry",
    run_id: str | None = None,
    completion_state: str = "in_progress",
) -> dict[str, Any]:
    """Build a concise operator-facing diagnostics section for reports and Jira evidence."""
    categories = diagnostics.get("categories", {})
    warning_categories = diagnostics.get("warning_categories", [])
    blocking_categories = diagnostics.get("blocking_categories", [])
    payload_availability = diagnostics.get("payload_availability", {})
    warning_codes = diagnostics.get("warning_codes", {})
    status = str(diagnostics.get("status", "warning")).strip().lower() or "warning"
    return {
        "stage": stage,
        "run_id": run_id or "unknown",
        "status": status,
        "completion_state": completion_state,
        "category_count": len(categories),
        "warning_count": len(warning_categories),
        "error_count": len(blocking_categories),
        "categories": categories,
        "warning_categories": sorted(str(item) for item in warning_categories),
        "blocking_categories": sorted(str(item) for item in blocking_categories),
        "payload_availability": payload_availability,
        "warning_codes": warning_codes,
        "markdown_table": build_runtime_diagnostics_markdown_table(diagnostics=diagnostics),
    }


def build_integration_run_context_model(
    *,
    expected_root: str,
    git_root: str,
    branch: str,
    worktrees: list[str] | None = None,
    dirty_entries: list[str] | None = None,
    preflight_status: str = "ready",
) -> dict[str, Any]:
    """Build a deterministic root/worktree/run-context model for integration validation."""
    normalized_expected_root = expected_root.strip().replace("/", "\\")
    normalized_git_root = git_root.strip().replace("/", "\\")
    normalized_branch = branch.strip() or "unknown"
    normalized_worktrees = [item.strip().replace("/", "\\") for item in (worktrees or []) if item.strip()]
    normalized_dirty_entries = [item.strip() for item in (dirty_entries or []) if item.strip()]
    unauthorized_worktrees = [
        path for path in normalized_worktrees if path and path != normalized_expected_root
    ]
    root_locked = normalized_git_root == normalized_expected_root
    normalized_preflight = preflight_status.strip().lower() or "unknown"

    runtime_status = "ready"
    if not root_locked or unauthorized_worktrees:
        runtime_status = "blocked"
    elif normalized_preflight in {"unknown", "pending"}:
        runtime_status = "unknown"
    elif normalized_dirty_entries or normalized_preflight in {"warning"}:
        runtime_status = "warning"

    return {
        "status": runtime_status,
        "expected_root": normalized_expected_root,
        "git_root": normalized_git_root,
        "branch": normalized_branch,
        "root_lock": "ready" if root_locked else "blocked",
        "worktree_control": "blocked" if unauthorized_worktrees else "ready",
        "dirty_tree": "warning" if normalized_dirty_entries else "ready",
        "preflight_status": normalized_preflight,
        "worktree_count": len(normalized_worktrees),
        "unauthorized_worktrees": unauthorized_worktrees,
        "dirty_entries": normalized_dirty_entries,
    }


def build_first_run_readiness_baseline_payload(
    *,
    run_context: dict[str, Any],
    diagnostics_status: str,
    niche_validation_status: str,
    data_integrity_signal: dict[str, Any],
) -> dict[str, Any]:
    """Build first-run baseline payload consumed by dashboard/report evidence."""
    def _normalize_status(value: str) -> str:
        normalized = value.strip().lower() or "unknown"
        return _RUNTIME_STATUS_NORMALIZATION.get(normalized, normalized)

    categories = {
        "run_context": _normalize_status(str(run_context.get("status", "unknown"))),
        "diagnostics": _normalize_status(diagnostics_status),
        "niche_validation": _normalize_status(niche_validation_status),
        "data_integrity": _normalize_status(str(data_integrity_signal.get("status", "unknown"))),
    }
    overall = max(categories.values(), key=lambda status: RUNTIME_READINESS_STATUS_ORDER.get(status, 2))
    return {
        "status": overall,
        "categories": categories,
        "warning_codes": list(data_integrity_signal.get("warning_codes", [])),
        "blocking_reasons": list(run_context.get("unauthorized_worktrees", [])),
        "record_count": int(data_integrity_signal.get("record_count", 0)),
    }


def build_data_integrity_summary(
    *,
    records: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Return warning-first integrity summary for dashboard-facing records."""
    normalized_records = [row for row in (records or []) if isinstance(row, dict)]
    warnings: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_sources: set[str] = set()
    for index, row in enumerate(normalized_records, start=1):
        row_id = str(row.get("id", row.get("run_id", ""))).strip()
        if not row_id:
            warnings.append({"code": "missing_id", "message": f"Row {index} is missing id/run_id."})
        elif row_id in seen_ids:
            warnings.append({"code": "duplicate_id", "message": f"Duplicate id '{row_id}' detected."})
        seen_ids.add(row_id)
        rank = row.get("rank")
        if rank is not None and not isinstance(rank, int):
            warnings.append({"code": "invalid_rank", "message": f"Row {index} rank is not an integer."})
        score = row.get("score")
        if score is not None and not isinstance(score, int | float):
            warnings.append({"code": "invalid_score", "message": f"Row {index} score is not numeric."})
        source_name = str(row.get("source_name", "")).strip()
        source_key = str(row.get("source_key", "")).strip()
        if source_name and source_key and source_name != source_key:
            warnings.append(
                {
                    "code": "mismatched_source_key",
                    "message": f"Row {index} has mismatched source_name/source_key values.",
                }
            )
        if source_name:
            seen_sources.add(source_name)
        evidence = row.get("evidence")
        if evidence is not None and not isinstance(evidence, list | dict):
            warnings.append({"code": "malformed_evidence", "message": f"Row {index} evidence is malformed."})
    deduped_warnings = list({(item["code"], item["message"]): item for item in warnings}.values())
    return {
        "status": "warning" if deduped_warnings else "ready",
        "record_count": len(normalized_records),
        "source_count": len(seen_sources),
        "warnings": deduped_warnings,
    }


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

    integrity_warnings = validate_analysis_integrity_records(
        [row for row in stage_outputs if isinstance(row, dict)],
        source_id="analysis_summary_rows",
    )
    warnings.extend(
        {"code": warning.code, "message": warning.message}
        for warning in integrity_warnings
    )

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

