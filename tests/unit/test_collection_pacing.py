"""Unit tests for deterministic pacing logic."""

from __future__ import annotations

from src.collection.pacing import PacingConfig, PacingManager


class _Clock:
    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def test_next_delay_uses_base_delay_jitter_and_backoff() -> None:
    clock = _Clock(100.0)
    manager = PacingManager(
        config=PacingConfig(base_delay_seconds=1.0),
        random_provider=lambda _a, _b: 0.25,
        clock=clock,
    )
    manager.record_error("fiverr", status_code=500)
    delay = manager.next_delay("fiverr")
    assert delay >= 10.0


def test_rate_limit_window_adds_delay_when_request_cap_reached() -> None:
    clock = _Clock(120.0)
    config = PacingConfig(
        base_delay_seconds=0.0,
        jitter_min_seconds=0.0,
        jitter_max_seconds=0.0,
        max_requests_per_minute=2,
    )
    manager = PacingManager(config=config, random_provider=lambda _a, _b: 0.0, clock=clock)
    manager.record_success("fiverr")
    clock.now = 121.0
    manager.record_success("fiverr")
    clock.now = 122.0
    # oldest timestamp is 120 => wait until 180 for request window.
    assert manager.next_delay("fiverr") == 58.0


def test_record_error_429_applies_stronger_backoff_and_cooldown() -> None:
    clock = _Clock(5.0)
    manager = PacingManager(clock=clock, random_provider=lambda _a, _b: 0.0)

    manager.record_error("fiverr", status_code=429)
    state = manager.get_state("fiverr")

    assert state.last_status_code == 429
    assert state.backoff_seconds >= 60.0
    assert manager.should_cooldown("fiverr") is True


def test_record_success_reduces_backoff_and_clears_terminal_cooldown() -> None:
    clock = _Clock(10.0)
    manager = PacingManager(clock=clock, random_provider=lambda _a, _b: 0.0)
    manager.record_error("fiverr", status_code=500)

    clock.now = 100.0
    manager.record_success("fiverr")
    state = manager.get_state("fiverr")

    assert state.backoff_seconds <= 5.0
    assert state.consecutive_errors == 0
    assert manager.should_cooldown("fiverr") is False


def test_get_state_returns_copy_not_mutable_reference() -> None:
    clock = _Clock(30.0)
    manager = PacingManager(clock=clock, random_provider=lambda _a, _b: 0.0)
    manager.record_success("fiverr")
    state = manager.get_state("fiverr")
    state.recent_request_timestamps.append(9999.0)

    refreshed = manager.get_state("fiverr")
    assert 9999.0 not in refreshed.recent_request_timestamps
