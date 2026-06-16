from __future__ import annotations

import json
from pathlib import Path

import pytest
from automation.provider_health import (
    ProviderHealth,
    refresh_after_dispatch,
    update_provider_status,
)


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


def test_degraded_editing_provider_with_smoke_pass_returns_degraded(tmp_path: Path) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "DEGRADED", "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    health = ProviderHealth(health_path=health_path)
    assert health.get_status("cursorcli") == "DEGRADED"


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


def test_update_provider_status_changes_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    update_provider_status("cursorcli", "DEGRADED")
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    assert payload["cursorcli"]["status"] == "DEGRADED"


def test_update_provider_status_invalid_status_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(health_path, {"cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"}})
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    with pytest.raises(ValueError):
        update_provider_status("cursorcli", "UNKNOWN")


def test_refresh_after_dispatch_success_stays_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "error_count": 1, "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    refresh_after_dispatch("cursorcli", "SUCCESS", run_dir=tmp_path / "run_a")
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    assert payload["cursorcli"]["status"] == "READY"
    assert payload["cursorcli"]["error_count"] == 0
    assert payload["cursorcli"]["last_run_dir"] == str(tmp_path / "run_a")


def test_refresh_after_dispatch_error_degrades(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "error_count": 0, "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    refresh_after_dispatch("cursorcli", "ERROR", run_dir=tmp_path / "run_b")
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    assert payload["cursorcli"]["status"] == "DEGRADED"
    assert payload["cursorcli"]["error_count"] == 1


def test_refresh_after_dispatch_repeated_error_blocks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(
        health_path,
        {
            "cursorcli": {"status": "READY", "error_count": 0, "full_size_prompt_smoke": "PASS"},
            "claudesubscription": {"status": "READY"},
            "openaiapi": {"status": "READY"},
            "codexsubscription": {"status": "READY", "full_size_prompt_smoke": "PASS"},
        },
    )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    refresh_after_dispatch("cursorcli", "ERROR", run_dir=tmp_path / "run_1")
    refresh_after_dispatch("cursorcli", "ERROR", run_dir=tmp_path / "run_2")
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    assert payload["cursorcli"]["status"] == "BLOCKED"
    assert payload["cursorcli"]["error_count"] == 2


def test_get_status_unknown_provider_is_blocked(tmp_path: Path) -> None:
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
    assert health.get_status("unknown-provider") == "BLOCKED"


def test_update_provider_status_accepts_not_verified_alias(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    health_path = tmp_path / "provider_health.json"
    _write_health(health_path, {"cursorcli": {"status": "READY", "full_size_prompt_smoke": "PASS"}})
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(health_path))
    update_provider_status("cursor_cli", "NOT_VERIFIED")
    payload = json.loads(health_path.read_text(encoding="utf-8"))
    assert payload["cursorcli"]["status"] == "NOT_VERIFIED"
