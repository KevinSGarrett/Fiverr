"""Playwright session configuration helpers for dry-run collection."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BrowserSessionConfig:
    """Configuration used to build safe browser launch options."""

    headless: bool = True
    storage_state_path: Path | None = None
    user_agent: str | None = None
    timeout_ms: int = 30_000
    authenticated_mode: bool = False


def validate_storage_state_path(path: Path | str | None) -> Path:
    """Validate storage state path for authenticated read-only workflows."""

    if path is None:
        raise ValueError("Authenticated mode requires a storage_state_path.")

    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Storage state file not found: {resolved}")
    if not resolved.is_file():
        raise ValueError(f"Storage state path must be a file: {resolved}")
    return resolved


def build_browser_launch_options(config: BrowserSessionConfig) -> dict[str, Any]:
    """Build deterministic launch options without launching a browser."""

    if config.timeout_ms <= 0:
        raise ValueError("timeout_ms must be greater than zero.")

    options: dict[str, Any] = {"headless": config.headless, "timeout": config.timeout_ms}
    if config.user_agent:
        options["user_agent"] = config.user_agent

    if config.authenticated_mode:
        options["storage_state"] = str(validate_storage_state_path(config.storage_state_path))
    return options


async def _maybe_await(value: Any) -> Any:
    """Await value when needed for injected async fakes."""

    if inspect.isawaitable(value):
        return await value
    return value


class ManagedBrowserSession:
    """Async context manager skeleton with dependency injection hooks for tests."""

    def __init__(
        self,
        config: BrowserSessionConfig,
        *,
        playwright_factory: Callable[[], Awaitable[Any] | Any] | None = None,
        browser: Any | None = None,
    ) -> None:
        self._config = config
        self._playwright_factory = playwright_factory
        self._injected_browser = browser
        self._playwright: Any | None = None
        self._browser: Any | None = None

    async def __aenter__(self) -> Any:
        build_browser_launch_options(self._config)

        if self._injected_browser is not None:
            self._browser = self._injected_browser
            return self._browser

        if self._playwright_factory is None:
            raise RuntimeError("ManagedBrowserSession requires injected browser or playwright_factory.")

        self._playwright = await _maybe_await(self._playwright_factory())
        chromium = getattr(self._playwright, "chromium", None)
        if chromium is None:
            raise RuntimeError("Injected playwright object must expose a chromium launcher.")
        self._browser = await _maybe_await(chromium.launch(**build_browser_launch_options(self._config)))
        return self._browser

    async def __aexit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        if self._browser is not None:
            close = getattr(self._browser, "close", None)
            if close is not None:
                await _maybe_await(close())

        if self._playwright is not None:
            stop = getattr(self._playwright, "stop", None)
            if stop is not None:
                await _maybe_await(stop())
