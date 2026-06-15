from __future__ import annotations

import json
from pathlib import Path

import pytest
from automation.provider_health import ProviderHealth


def _write_health(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_ready_provider_returns_ready(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    health = ProviderHealth(health_path=health_path)
    assert health.get_status("cursorcli") == "READY"


def test_not_verified_provider_is_blocked(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "NOTVERIFIED"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    health = ProviderHealth(health_path=health_path)
    assert health.get_status("claudesubscription") == "BLOCKED"


def test_editing_provider_without_smoke_is_blocked(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    health = ProviderHealth(health_path=health_path)
    assert health.get_status("cursorcli") == "BLOCKED"


def test_editing_provider_with_smoke_pass_is_ready(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    health = ProviderHealth(health_path=health_path)
    ok, detail = health.is_editing_provider_ready("cursorcli")
    assert ok is True
    assert detail == "READY"


def test_missing_health_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        ProviderHealth(health_path="C:/does/not/exist/provider_health.json")


def test_non_editing_provider_ready_regardless_of_smoke_status(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY", "fullsizepromptsmoke": "FAIL"},
            "openaiapi": {"status": "READY", "full_size_prompt_smoke": "FAIL"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    health = ProviderHealth(health_path=health_path)
    assert health.get_status("claudesubscription") == "READY"
    assert health.get_status("openaiapi") == "READY"


def test_get_all_statuses_returns_all_known_provider_keys(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    statuses = ProviderHealth(health_path=health_path).get_all_statuses()
    assert set(statuses) == {"cursorcli", "claudesubscription", "openaiapi", "codexsubscription"}


def test_is_any_blocked_true_when_any_provider_blocked(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    assert ProviderHealth(health_path=health_path).is_any_blocked() is True
