"""
failure_classifier.py — Classify agent run and validation failures into
typed failure codes that drive the repair loop.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class FailureType(str, Enum):
    CURSOR_TIMEOUT            = "cursor_timeout"
    CURSOR_NO_OUTPUT          = "cursor_no_output"
    CURSOR_EXIT_NONZERO       = "cursor_exit_nonzero"
    MISSING_FINAL_REPORT      = "missing_final_report"
    CHANGED_FILES_EMPTY       = "changed_files_empty"
    UNAUTHORIZED_FILE_CHANGE  = "unauthorized_file_change"
    RUFF_FAILURE              = "ruff_failure"
    MYPY_FAILURE              = "mypy_failure"
    PYTEST_FAILURE            = "pytest_failure"
    COVERAGE_FAILURE          = "coverage_failure"
    CONFIG_CHECK_FAILURE      = "config_check_failure"
    FOUNDATION_GATE_FAILURE   = "foundation_gate_failure"
    PHASE2_SMOKE_FAILURE      = "phase2_smoke_failure"
    MERGE_CONFLICT            = "merge_conflict"
    GITHUB_PUSH_FAILURE       = "github_push_failure"
    PR_CHECK_FAILURE          = "pr_check_failure"
    CODECOV_PROJECT_FAILURE   = "codecov_project_failure"
    CODECOV_PATCH_FAILURE     = "codecov_patch_failure"
    CODEX_THREAD_VALID        = "codex_thread_valid"
    JIRA_UPDATE_FAILURE       = "jira_update_failure"
    RATE_LIMIT                = "rate_limit"
    PROMPT_INVALID            = "prompt_invalid"
    ENVIRONMENT_FAILURE       = "environment_failure"
    MODEL_GATE_FAILURE        = "model_gate_failure"
    SECRET_DETECTED           = "secret_detected"
    UNKNOWN                   = "unknown"


# Which agent handles each failure type in repair
REPAIR_AGENT_MAP: dict[FailureType, str] = {
    FailureType.RUFF_FAILURE:           "B",   # whoever last wrote bad code
    FailureType.MYPY_FAILURE:           "B",
    FailureType.PYTEST_FAILURE:         "F",   # coverage/test agent
    FailureType.COVERAGE_FAILURE:       "F",
    FailureType.CONFIG_CHECK_FAILURE:   "A",   # config owner
    FailureType.MISSING_FINAL_REPORT:   "D",   # steward
    FailureType.UNAUTHORIZED_FILE_CHANGE: "D",
    FailureType.CODEX_THREAD_VALID:     "D",
    FailureType.PR_CHECK_FAILURE:       "D",
    FailureType.CODECOV_PATCH_FAILURE:  "F",
    FailureType.CODECOV_PROJECT_FAILURE: "F",
}

# Failures that are automatically retryable without a repair prompt
AUTO_RETRY_TYPES = {
    FailureType.RATE_LIMIT,
    FailureType.GITHUB_PUSH_FAILURE,
    FailureType.JIRA_UPDATE_FAILURE,
}

# Failures that should block the whole cycle (not just one agent)
CYCLE_BLOCKERS = {
    FailureType.MODEL_GATE_FAILURE,
    FailureType.SECRET_DETECTED,
    FailureType.MERGE_CONFLICT,
    FailureType.ENVIRONMENT_FAILURE,
}


@dataclass
class ClassifiedFailure:
    failure_type: FailureType
    agent: str
    cycle: int
    evidence: str
    repair_agent: str | None = None
    is_cycle_blocker: bool = False
    is_auto_retry: bool = False
    attempt: int = 1


def classify(
    agent: str,
    cycle: int,
    exit_code: int | None,
    timed_out: bool,
    no_output: bool,
    stdout: str,
    stderr: str,
    changed_files: list[str],
    validation_results: dict[str, Any] | None = None,
    report_path: str | None = None,
) -> ClassifiedFailure:
    """Classify a failure from an agent run or post-agent validation."""

    # Model gate failure (special case — must bubble up)
    combined = (stdout + stderr).lower()

    # Timeout variants
    if timed_out:
        ft = FailureType.CURSOR_TIMEOUT
    elif no_output:
        ft = FailureType.CURSOR_NO_OUTPUT
    elif exit_code not in (0, None) and not changed_files:
        ft = FailureType.CHANGED_FILES_EMPTY
    elif exit_code not in (0, None):
        ft = FailureType.CURSOR_EXIT_NONZERO

    # Validation gate failures
    elif validation_results:
        if not validation_results.get("ruff", True):
            ft = FailureType.RUFF_FAILURE
        elif not validation_results.get("mypy", True):
            ft = FailureType.MYPY_FAILURE
        elif not validation_results.get("pytest", True) or not validation_results.get("pytest-coverage", True):
            ft = FailureType.PYTEST_FAILURE
        elif not validation_results.get("coverage", True):
            ft = FailureType.COVERAGE_FAILURE
        elif not validation_results.get("config-check", True):
            ft = FailureType.CONFIG_CHECK_FAILURE
        elif not validation_results.get("foundation-gate", True):
            ft = FailureType.FOUNDATION_GATE_FAILURE
        elif not validation_results.get("phase2-smoke", True):
            ft = FailureType.PHASE2_SMOKE_FAILURE
        else:
            ft = FailureType.UNKNOWN

    # Missing report
    elif report_path and not __import__("pathlib").Path(report_path).exists():
        ft = FailureType.MISSING_FINAL_REPORT

    # Merge conflict
    elif "conflict" in combined or "merge conflict" in combined:
        ft = FailureType.MERGE_CONFLICT

    # Push failure
    elif "push" in combined and ("rejected" in combined or "error" in combined):
        ft = FailureType.GITHUB_PUSH_FAILURE

    # Rate limit
    elif "rate limit" in combined or "429" in combined:
        ft = FailureType.RATE_LIMIT

    else:
        ft = FailureType.UNKNOWN

    evidence_parts = []
    if stdout.strip():
        evidence_parts.append(stdout[-500:])
    if stderr.strip():
        evidence_parts.append(stderr[-500:])

    return ClassifiedFailure(
        failure_type=ft,
        agent=agent,
        cycle=cycle,
        evidence="\n".join(evidence_parts)[-1000:],
        repair_agent=REPAIR_AGENT_MAP.get(ft, agent),
        is_cycle_blocker=ft in CYCLE_BLOCKERS,
        is_auto_retry=ft in AUTO_RETRY_TYPES,
    )
