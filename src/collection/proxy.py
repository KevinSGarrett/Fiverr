"""Proxy configuration abstractions with redacted error handling."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass


class ProxyConfigurationError(RuntimeError):
    """Raised for invalid proxy setup."""


@dataclass(frozen=True, slots=True)
class ProxyConfig:
    enabled: bool = False
    server: str | None = None
    username_env_var: str | None = None
    password_env_var: str | None = None
    country: str | None = None
    provider_name: str | None = None

    def redact(self) -> dict[str, str | bool | None]:
        return {
            "enabled": self.enabled,
            "server": self.server,
            "username_env_var": self.username_env_var,
            "password_env_var": "***" if self.password_env_var else None,
            "country": self.country,
            "provider_name": self.provider_name,
        }

    def __repr__(self) -> str:
        return f"ProxyConfig({self.redact()})"


class ProxyProvider:
    """Builds Playwright-compatible proxy config without leaking secrets."""

    def __init__(self, env_provider: Callable[[str], str | None] | None = None) -> None:
        self._env_provider = env_provider or os.getenv

    def build_proxy_settings(self, config: ProxyConfig) -> dict[str, str] | None:
        if not config.enabled:
            return None
        if not config.server:
            raise ProxyConfigurationError(
                f"Proxy server missing for enabled proxy: {config.redact()}."
            )
        if not (config.username_env_var and config.password_env_var):
            raise ProxyConfigurationError(
                "Enabled proxy requires username_env_var and password_env_var. "
                f"Context={config.redact()}."
            )

        proxy: dict[str, str] = {"server": config.server}
        username = self._env_provider(config.username_env_var)
        password = self._env_provider(config.password_env_var)
        if not username or not password:
            raise ProxyConfigurationError(
                "Proxy credentials are missing in environment. "
                f"Context={config.redact()}."
            )
        proxy["username"] = username
        proxy["password"] = password
        return proxy
