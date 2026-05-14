"""Unit tests for proxy configuration helpers."""

from __future__ import annotations

import pytest
from src.collection.proxy import ProxyConfig, ProxyConfigurationError, ProxyProvider


def test_proxy_provider_returns_none_when_disabled() -> None:
    provider = ProxyProvider()
    assert provider.build_proxy_settings(ProxyConfig(enabled=False)) is None


def test_proxy_provider_requires_server_and_env_var_names() -> None:
    provider = ProxyProvider()
    with pytest.raises(ProxyConfigurationError, match="Proxy server missing"):
        provider.build_proxy_settings(ProxyConfig(enabled=True))

    with pytest.raises(ProxyConfigurationError, match="username_env_var"):
        provider.build_proxy_settings(ProxyConfig(enabled=True, server="http://proxy.local"))


def test_proxy_provider_requires_env_values_without_leaking_secrets() -> None:
    provider = ProxyProvider(env_provider=lambda _name: None)
    config = ProxyConfig(
        enabled=True,
        server="http://proxy.local",
        username_env_var="PROXY_USER",
        password_env_var="PROXY_PASS",
    )
    with pytest.raises(ProxyConfigurationError, match="missing in environment"):
        provider.build_proxy_settings(config)

    assert "***" in repr(config)


def test_proxy_provider_builds_playwright_settings() -> None:
    env = {"PROXY_USER": "user", "PROXY_PASS": "pass"}
    provider = ProxyProvider(env_provider=env.get)
    config = ProxyConfig(
        enabled=True,
        server="http://proxy.local:8080",
        username_env_var="PROXY_USER",
        password_env_var="PROXY_PASS",
    )
    settings = provider.build_proxy_settings(config)
    assert settings == {
        "server": "http://proxy.local:8080",
        "username": "user",
        "password": "pass",
    }
