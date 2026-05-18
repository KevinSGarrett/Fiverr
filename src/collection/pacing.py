"""Pacing utilities for collection workloads."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PacingConfig:
    """Pacing settings for each source."""

    base_delay_seconds: float = 1.0
    jitter_min_seconds: float = 0.0
    jitter_max_seconds: float = 0.25
    max_requests_per_minute: int = 30
    cooldown_after_error_seconds: float = 10.0
    cooldown_after_429_seconds: float = 30.0
    adaptive_backoff_multiplier: float = 2.0
    max_backoff_seconds: float = 300.0


@dataclass(slots=True)
class SourcePacingState:
    """Mutable pacing state for a source."""

    consecutive_errors: int = 0
    backoff_seconds: float = 0.0
    cooldown_until: float | None = None
    last_status_code: int | None = None
    recent_request_timestamps: list[float] = field(default_factory=list)


class PacingManager:
    """Manages request pacing and legacy cooldown calculations."""

    def __init__(
        self,
        config: PacingConfig | dict[str, object] | None = None,
        source_configs: dict[str, PacingConfig] | None = None,
        random_provider: Callable[[float, float], float] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.config = config if config is not None else {}
        self.pacing: dict[str, dict[str, object]] = {}

        if isinstance(config, dict):
            raw_pacing = config.get("pacing", {})
            if isinstance(raw_pacing, dict):
                self.pacing = {
                    str(key): value
                    for key, value in raw_pacing.items()
                    if isinstance(value, dict)
                }
            self._legacy_config = PacingConfig()
        else:
            self._legacy_config = config or PacingConfig()

        # Tracks request timestamps for the newer hourly count API.
        self._hourly_counts: dict[str, list[float]] = {}
        self._source_configs = source_configs or {}
        self._random = random_provider or random.uniform
        self._clock = clock or time.time
        self._state_by_source: dict[str, SourcePacingState] = {}

    def _state(self, source: str) -> SourcePacingState:
        return self._state_by_source.setdefault(source, SourcePacingState())

    def _config_for_source(self, source: str) -> PacingConfig:
        return self._source_configs.get(source, self._legacy_config)

    @staticmethod
    def _float_value(value: Any, fallback: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    async def wait(self, pacing_key: str, dry_run: bool = False) -> float:
        """
        Wait for configured delay (base + jitter), then record request.

        When `dry_run=True`, skip sleeping and return 0.0.
        """
        if dry_run:
            return 0.0

        import asyncio

        cfg = self.pacing.get(pacing_key, self.pacing.get("default", {}))
        base = self._float_value(cfg.get("base_delay_seconds", 2.0), 2.0)
        jitter_max = self._float_value(cfg.get("jitter_seconds", 1.0), 1.0)
        delay = base + random.uniform(0.0, jitter_max)
        await asyncio.sleep(delay)
        self._record_request(pacing_key)
        return delay

    def _record_request(self, pacing_key: str) -> None:
        """Record timestamp and purge entries older than 1 hour."""
        now = time.time()
        if pacing_key not in self._hourly_counts:
            self._hourly_counts[pacing_key] = []
        self._hourly_counts[pacing_key].append(now)
        cutoff = now - 3600.0
        self._hourly_counts[pacing_key] = [t for t in self._hourly_counts[pacing_key] if t > cutoff]

    def requests_in_last_hour(self, pacing_key: str) -> int:
        """Return number of requests in the last hour for the key."""
        now = time.time()
        cutoff = now - 3600.0
        return sum(1 for t in self._hourly_counts.get(pacing_key, []) if t > cutoff)

    def get_delay_config(self, pacing_key: str) -> dict[str, object]:
        """Return effective config for a pacing key."""
        cfg = self.pacing.get(pacing_key, self.pacing.get("default", {}))
        if isinstance(cfg, dict):
            return dict(cfg)
        return {}

    @staticmethod
    def _prune_request_window(state: SourcePacingState, now: float) -> None:
        state.recent_request_timestamps = [
            timestamp for timestamp in state.recent_request_timestamps if timestamp > (now - 60.0)
        ]

    def next_delay(self, source: str = "fiverr") -> float:
        """Return the next delay callers should apply."""

        config = self._config_for_source(source)
        state = self._state(source)
        now = self._clock()
        self._prune_request_window(state, now)

        request_window_delay = 0.0
        if (
            config.max_requests_per_minute > 0
            and len(state.recent_request_timestamps) >= config.max_requests_per_minute
        ):
            oldest = min(state.recent_request_timestamps)
            request_window_delay = max(0.0, (oldest + 60.0) - now)

        cooldown_remaining = 0.0
        if state.cooldown_until is not None:
            cooldown_remaining = max(0.0, state.cooldown_until - now)
        jitter = self._random(config.jitter_min_seconds, config.jitter_max_seconds)
        base_delay = max(0.0, config.base_delay_seconds + jitter)
        return max(
            0.0,
            cooldown_remaining,
            request_window_delay,
            base_delay + max(0.0, state.backoff_seconds),
        )

    def record_success(self, source: str) -> None:
        """Reduce backoff after successful work without abrupt drops."""

        config = self._config_for_source(source)
        state = self._state(source)
        now = self._clock()
        state.recent_request_timestamps.append(now)
        self._prune_request_window(state, now)
        state.consecutive_errors = max(0, state.consecutive_errors - 1)
        if state.backoff_seconds > 0:
            state.backoff_seconds = max(
                0.0,
                state.backoff_seconds / config.adaptive_backoff_multiplier,
            )
        if state.consecutive_errors == 0 and not self.should_cooldown(source):
            state.cooldown_until = None
            state.last_status_code = None

    def record_error(self, source: str, status_code: int | None = None) -> None:
        """Increase cooldown and backoff after errors."""

        config = self._config_for_source(source)
        state = self._state(source)
        now = self._clock()
        state.recent_request_timestamps.append(now)
        self._prune_request_window(state, now)
        state.consecutive_errors += 1
        state.last_status_code = status_code

        cooldown_floor = (
            config.cooldown_after_429_seconds
            if status_code == 429
            else config.cooldown_after_error_seconds
        )
        multiplier = config.adaptive_backoff_multiplier ** max(0, state.consecutive_errors - 1)
        if status_code == 429:
            multiplier *= config.adaptive_backoff_multiplier

        proposed_backoff = min(
            config.max_backoff_seconds,
            cooldown_floor * multiplier,
        )
        state.backoff_seconds = max(state.backoff_seconds, proposed_backoff)

        proposed_cooldown_until = now + state.backoff_seconds
        if state.cooldown_until is None:
            state.cooldown_until = proposed_cooldown_until
        else:
            state.cooldown_until = max(state.cooldown_until, proposed_cooldown_until)

    def should_cooldown(self, source: str) -> bool:
        """Return whether the source is still in cooldown."""

        state = self._state(source)
        if state.cooldown_until is None:
            return False
        return state.cooldown_until > self._clock()

    def get_state(self, source: str) -> SourcePacingState:
        """Return a copy of pacing state for inspection."""

        state = self._state(source)
        return SourcePacingState(
            consecutive_errors=state.consecutive_errors,
            backoff_seconds=state.backoff_seconds,
            cooldown_until=state.cooldown_until,
            last_status_code=state.last_status_code,
            recent_request_timestamps=list(state.recent_request_timestamps),
        )
