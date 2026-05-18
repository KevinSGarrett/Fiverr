"""Unit tests for collection pacing manager async interface."""

from __future__ import annotations

import asyncio
import time
from typing import Any, cast

from src.collection.pacing import PacingManager


def _run(coro):
    return asyncio.run(coro)


def test_pacing_manager_wait_dry_run(monkeypatch) -> None:
    manager = PacingManager({"pacing": {"default": {"base_delay_seconds": 1.0, "jitter_seconds": 0.5}}})

    called = False

    async def fake_sleep(_delay: float) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    delay = _run(manager.wait("default", dry_run=True))

    assert delay == 0.0
    assert called is False


def test_pacing_manager_wait_uses_config(monkeypatch) -> None:
    manager = PacingManager({"pacing": {"fast": {"base_delay_seconds": 0.01, "jitter_seconds": 0.0}}})
    sleep_calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    delay = _run(manager.wait("fast"))

    assert delay == 0.01
    assert sleep_calls == [0.01]


def test_pacing_manager_records_request() -> None:
    manager = PacingManager({"pacing": {}})
    manager._record_request("fiverr_search")
    assert "fiverr_search" in manager._hourly_counts
    assert len(manager._hourly_counts["fiverr_search"]) == 1


def test_pacing_manager_hourly_count() -> None:
    manager = PacingManager({"pacing": {}})
    manager._record_request("fiverr_search")
    manager._record_request("fiverr_search")
    assert manager.requests_in_last_hour("fiverr_search") == 2


def test_pacing_manager_purges_old_entries(monkeypatch) -> None:
    manager = PacingManager({"pacing": {}})
    manager._hourly_counts["fiverr_search"] = [time.time() - 7200]
    manager._record_request("fiverr_search")
    assert manager.requests_in_last_hour("fiverr_search") == 1


def test_pacing_manager_default_config(monkeypatch) -> None:
    manager = PacingManager({"pacing": {"default": {"base_delay_seconds": 0.0, "jitter_seconds": 0.0}}})
    calls: list[float] = []

    async def fake_sleep(delay: float) -> None:
        calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    delay = _run(manager.wait("unknown"))

    assert delay == 0.0
    assert calls == [0.0]


def test_pacing_manager_get_delay_config() -> None:
    manager = PacingManager(
        {"pacing": {"fiverr_search": {"base_delay_seconds": 1.5, "jitter_seconds": 0.5}}}
    )
    cfg = manager.get_delay_config("fiverr_search")
    assert cfg["base_delay_seconds"] == 1.5
    assert cfg["jitter_seconds"] == 0.5


def test_pacing_manager_zero_delay_config(monkeypatch) -> None:
    manager = PacingManager({"pacing": {"zero": {"base_delay_seconds": 0.0, "jitter_seconds": 0.0}}})
    waited: list[float] = []

    async def fake_sleep(delay: float) -> None:
        waited.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    delay = _run(manager.wait("zero"))

    assert delay == 0.0
    assert waited == [0.0]


def test_pacing_manager_wait_falls_back_for_non_numeric_config(monkeypatch) -> None:
    manager = PacingManager(
        {"pacing": {"bad": {"base_delay_seconds": "bad", "jitter_seconds": "bad"}}}
    )
    waits: list[float] = []

    async def fake_sleep(delay: float) -> None:
        waits.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr("random.uniform", lambda _a, _b: 0.0)
    delay = _run(manager.wait("bad"))
    assert delay == 2.0
    assert waits == [2.0]


def test_pacing_manager_get_delay_config_non_dict_returns_empty() -> None:
    manager = PacingManager({"pacing": {"default": {"base_delay_seconds": 1.0}}})
    cast(dict[str, Any], manager.pacing)["broken"] = "oops"
    assert manager.get_delay_config("broken") == {}


def test_pacing_manager_record_error_preserves_larger_existing_cooldown() -> None:
    now = 100.0
    manager = PacingManager(clock=lambda: now)
    state = manager._state("fiverr")
    state.cooldown_until = 999.0
    manager.record_error("fiverr", status_code=500)
    assert manager.get_state("fiverr").cooldown_until == 999.0


def test_pacing_manager_record_error_sets_cooldown_when_none() -> None:
    now = 100.0
    manager = PacingManager(clock=lambda: now)
    manager.record_error("fiverr", status_code=429)
    state = manager.get_state("fiverr")
    assert state.cooldown_until is not None
    assert state.cooldown_until > now
