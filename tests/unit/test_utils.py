"""Unit tests for shared utility modules."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
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
