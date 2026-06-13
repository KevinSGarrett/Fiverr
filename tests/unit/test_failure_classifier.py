from __future__ import annotations

import pytest
from automation.failure_classifier import FailureType, classify, classify_post_cycle_failure


def test_missing_source_prompt_has_steps() -> None:
    result = classify_post_cycle_failure("MISSING_SOURCE_PROMPT")
    assert result.remediation_steps is not None and len(result.remediation_steps) >= 3


def test_model_unverified_has_steps() -> None:
    result = classify_post_cycle_failure("MODEL_UNVERIFIED")
    assert result.remediation_steps is not None and len(result.remediation_steps) >= 3


def test_missing_agent_report_has_steps() -> None:
    result = classify_post_cycle_failure("MISSING_AGENT_REPORT")
    assert result.remediation_steps is not None and len(result.remediation_steps) >= 3


def test_score_cap_violation_has_steps() -> None:
    result = classify_post_cycle_failure("SCORE_CAP_VIOLATION")
    assert result.remediation_steps is not None and len(result.remediation_steps) >= 3


def test_prompt_quality_fail_has_steps() -> None:
    result = classify_post_cycle_failure("PROMPT_QUALITY_FAIL")
    assert result.remediation_steps is not None and len(result.remediation_steps) >= 3


def test_pm_pack_contradiction_has_steps() -> None:
    result = classify_post_cycle_failure("PM_PACK_CONTRADICTION")
    assert result.remediation_steps is not None and len(result.remediation_steps) >= 3


def test_classify_ruff_error_returns_ruff_failure_type() -> None:
    result = classify(
        agent="B",
        cycle=75,
        exit_code=0,
        timed_out=False,
        no_output=False,
        stdout="",
        stderr="",
        changed_files=["automation/x.py"],
        validation_results={"ruff": False},
    )
    assert result.failure_type == FailureType.RUFF_FAILURE


def test_classify_mypy_error_returns_mypy_failure_type() -> None:
    result = classify(
        agent="B",
        cycle=75,
        exit_code=0,
        timed_out=False,
        no_output=False,
        stdout="",
        stderr="",
        changed_files=["automation/x.py"],
        validation_results={"ruff": True, "mypy": False},
    )
    assert result.failure_type == FailureType.MYPY_FAILURE


def test_classify_missing_report_returns_missing_report_type() -> None:
    result = classify(
        agent="D",
        cycle=75,
        exit_code=0,
        timed_out=False,
        no_output=False,
        stdout="",
        stderr="",
        changed_files=["docs/x.md"],
        report_path="C:/path/does/not/exist/report.md",
    )
    assert result.failure_type == FailureType.MISSING_FINAL_REPORT


def test_classify_cursor_timeout_returns_timeout_type() -> None:
    result = classify(
        agent="A",
        cycle=75,
        exit_code=None,
        timed_out=True,
        no_output=False,
        stdout="",
        stderr="",
        changed_files=[],
    )
    assert result.failure_type == FailureType.CURSOR_TIMEOUT


@pytest.mark.parametrize(
    "error_type",
    [
        "MISSING_SOURCE_PROMPT",
        "MODEL_UNVERIFIED",
        "MISSING_AGENT_REPORT",
        "SCORE_CAP_VIOLATION",
        "PROMPT_QUALITY_FAIL",
        "PM_PACK_CONTRADICTION",
        "UNKNOWN_CASE",
    ],
)
def test_remediation_steps_are_at_least_3_per_type(error_type: str) -> None:
    result = classify_post_cycle_failure(error_type)
    assert result.remediation_steps is not None
    assert len(result.remediation_steps) >= 3


def test_classify_unknown_error_returns_unknown_not_raises() -> None:
    result = classify(
        agent="A",
        cycle=75,
        exit_code=0,
        timed_out=False,
        no_output=False,
        stdout="something odd happened",
        stderr="",
        changed_files=["automation/x.py"],
    )
    assert result.failure_type == FailureType.UNKNOWN


def test_classified_failure_has_failure_type_and_remediation() -> None:
    result = classify_post_cycle_failure("MISSING_SOURCE_PROMPT")
    assert isinstance(result.failure_type, FailureType)
    assert result.remediation_steps is not None


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"timed_out": True, "no_output": False, "exit_code": None, "stdout": "", "stderr": "", "changed_files": []}, FailureType.CURSOR_TIMEOUT),
        ({"timed_out": False, "no_output": True, "exit_code": None, "stdout": "", "stderr": "", "changed_files": []}, FailureType.CURSOR_NO_OUTPUT),
        ({"timed_out": False, "no_output": False, "exit_code": 2, "stdout": "", "stderr": "", "changed_files": ["a.py"]}, FailureType.CURSOR_EXIT_NONZERO),
        ({"timed_out": False, "no_output": False, "exit_code": 0, "stdout": "", "stderr": "rate limit", "changed_files": ["a.py"]}, FailureType.RATE_LIMIT),
        ({"timed_out": False, "no_output": False, "exit_code": 0, "stdout": "", "stderr": "merge conflict", "changed_files": ["a.py"]}, FailureType.MERGE_CONFLICT),
        ({"timed_out": False, "no_output": False, "exit_code": 0, "stdout": "", "stderr": "", "changed_files": ["a.py"]}, FailureType.UNKNOWN),
    ],
)
def test_classify_failure_modes_parametrized(kwargs, expected: FailureType) -> None:
    result = classify(agent="A", cycle=75, validation_results=None, report_path=None, **kwargs)
    assert result.failure_type == expected


def test_all_post_cycle_failure_types_have_remediation_steps() -> None:
    for error_type in (
        "MISSING_SOURCE_PROMPT",
        "MODEL_UNVERIFIED",
        "MISSING_AGENT_REPORT",
        "SCORE_CAP_VIOLATION",
        "PROMPT_QUALITY_FAIL",
        "PM_PACK_CONTRADICTION",
    ):
        result = classify_post_cycle_failure(error_type)
        assert result.remediation_steps is not None
        assert len(result.remediation_steps) >= 3


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": None,
                "timed_out": True,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": [],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.CURSOR_TIMEOUT,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": None,
                "timed_out": False,
                "no_output": True,
                "stdout": "",
                "stderr": "",
                "changed_files": [],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.CURSOR_NO_OUTPUT,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 1,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": [],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.CHANGED_FILES_EMPTY,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 1,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.CURSOR_EXIT_NONZERO,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": False},
                "report_path": None,
            },
            FailureType.RUFF_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": True, "mypy": False},
                "report_path": None,
            },
            FailureType.MYPY_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": True, "mypy": True, "pytest": False},
                "report_path": None,
            },
            FailureType.PYTEST_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": True, "mypy": True, "pytest": True, "coverage": False},
                "report_path": None,
            },
            FailureType.COVERAGE_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": True, "mypy": True, "pytest": True, "coverage": True, "config-check": False},
                "report_path": None,
            },
            FailureType.CONFIG_CHECK_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": True, "mypy": True, "pytest": True, "coverage": True, "config-check": True, "foundation-gate": False},
                "report_path": None,
            },
            FailureType.FOUNDATION_GATE_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "",
                "changed_files": ["a.py"],
                "validation_results": {"ruff": True, "mypy": True, "pytest": True, "coverage": True, "config-check": True, "foundation-gate": True, "phase2-smoke": False},
                "report_path": None,
            },
            FailureType.PHASE2_SMOKE_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "merge conflict",
                "changed_files": ["a.py"],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.MERGE_CONFLICT,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "push rejected",
                "changed_files": ["a.py"],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.GITHUB_PUSH_FAILURE,
        ),
        (
            {
                "agent": "A",
                "cycle": 75,
                "exit_code": 0,
                "timed_out": False,
                "no_output": False,
                "stdout": "",
                "stderr": "429 rate limit",
                "changed_files": ["a.py"],
                "validation_results": None,
                "report_path": None,
            },
            FailureType.RATE_LIMIT,
        ),
    ],
)
def test_classify_covers_14_failure_types(kwargs, expected: FailureType) -> None:
    result = classify(**kwargs)
    assert result.failure_type == expected
