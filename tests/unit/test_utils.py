"""Unit tests for shared utility modules."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import pytest
from src.scripts.repo_hygiene import find_hygiene_issues
from src.utils.json import safe_json_loads
from src.utils.logging import RedactingFilter
from src.utils.paths import ensure_dir
from src.utils.retry import retry


def test_logging_filter_redacts_api_key_patterns() -> None:
    filt = RedactingFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="token sk-abc123def456ghi789 and api_key=secret12345",
        args=(),
        exc_info=None,
    )

    filt.filter(record)
    message = str(record.msg)
    assert "sk-abc123def456ghi789" not in message
    assert "secret12345" not in message
    assert "[REDACTED" in message


def test_ensure_dir_creates_nested_directory(tmp_path: Path) -> None:
    nested = tmp_path / "one" / "two" / "three"
    resolved = ensure_dir(nested)
    assert resolved.exists()
    assert resolved.is_dir()


def test_retry_recovers_after_transient_failures() -> None:
    attempts = {"count": 0}
    sleeps: list[float] = []

    @retry(max_attempts=4, initial_delay=0.01, sleep_func=sleeps.append)
    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary failure")
        return "ok"

    assert flaky() == "ok"
    assert attempts["count"] == 3
    assert sleeps


def test_retry_stops_after_max_attempts() -> None:
    @retry(max_attempts=2, initial_delay=0.01, sleep_func=lambda _delay: None)
    def always_fails() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        always_fails()


def test_safe_json_loads_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="Malformed JSON"):
        safe_json_loads("{bad json")


@dataclass
class _CompletedProcess:
    returncode: int
    stdout: str


def test_repo_hygiene_detects_forbidden_and_runtime_files(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(command: list[str], **_kwargs: object) -> _CompletedProcess:
        if command[1:] == ["ls-files"]:
            return _CompletedProcess(
                returncode=0,
                stdout="src/app.py\n__pycache__/bad.pyc\n.pytest_cache/state\n",
            )
        if command[1:] == ["ls-files", "--others", "--exclude-standard"]:
            return _CompletedProcess(
                returncode=0,
                stdout="data/runtime.db\ndata/nested/run.sqlite3\nplaywright/.auth/state.json\nnotes.txt\n",
            )
        return _CompletedProcess(returncode=1, stdout="")

    monkeypatch.setattr("src.scripts.repo_hygiene.subprocess.run", fake_run)
    issues = find_hygiene_issues(repo_root=tmp_path)

    paths = [issue.path for issue in issues]
    assert "__pycache__/bad.pyc" in paths
    assert ".pytest_cache/state" in paths
    assert "data/runtime.db" in paths
    assert "data/nested/run.sqlite3" in paths
    assert "playwright/.auth/state.json" in paths


def test_gitattributes_contains_line_ending_rules() -> None:
    content = Path(".gitattributes").read_text(encoding="utf-8")
    assert "*.py text eol=lf" in content
    assert "*.md text eol=lf" in content
    assert "*.yaml text eol=lf" in content
    assert "*.yml text eol=lf" in content


def test_repo_hygiene_passes_clean_repository(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(_command: list[str], **_kwargs: object) -> _CompletedProcess:
        return _CompletedProcess(returncode=0, stdout="")

    monkeypatch.setattr("src.scripts.repo_hygiene.subprocess.run", fake_run)
    issues = find_hygiene_issues(repo_root=tmp_path)
    assert issues == []
