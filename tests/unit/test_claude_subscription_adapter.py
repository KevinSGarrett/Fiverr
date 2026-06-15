from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from automation.adapters import claude_subscription_adapter as csa
from automation.adapters.claude_subscription_adapter import (
    AdapterBlockedError,
    ClaudeSubscriptionAdapter,
)


@pytest.fixture
def claude_state_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
    cfg = tmp_path / "claude_adapter.yaml"
    state = tmp_path / "claude_model_state.json"
    sub_state = tmp_path / "claude_subscription_state.json"
    incidents = tmp_path / "incidents"
    cfg.write_text("timeout_seconds: 5\n", encoding="utf-8")
    state.write_text(
        json.dumps({"billing_mode": "claude_subscription_only"}, indent=2), encoding="utf-8"
    )
    monkeypatch.setattr(csa, "CLAUDE_ADAPTER_CONFIG", cfg)
    monkeypatch.setattr(csa, "CLAUDE_MODEL_STATE_PATH", state)
    monkeypatch.setattr(csa, "CLAUDE_SUB_STATE_PATH", sub_state)
    monkeypatch.setattr(csa, "INCIDENTS_DIR", incidents)
    return cfg, state, sub_state


def test_preflight_blocks_when_api_key_present(
    claude_state_env: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    monkeypatch.setenv("ANTHROPICAPIKEY", "secret")
    adapter = ClaudeSubscriptionAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.preflight()


def test_preflight_blocks_when_billing_mode_invalid(
    claude_state_env: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _, state, _ = claude_state_env
    state.write_text(json.dumps({"billing_mode": "payg"}), encoding="utf-8")
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    adapter = ClaudeSubscriptionAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.preflight()


def test_preflight_blocks_when_binary_missing(
    claude_state_env: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: None)
    adapter = ClaudeSubscriptionAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.preflight()


def test_preflight_passes_when_subscription_ready(
    claude_state_env: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    monkeypatch.setattr(
        csa.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="ok", stderr=""),
    )
    adapter = ClaudeSubscriptionAdapter()
    adapter.preflight()


def test_run_review_handles_subscription_limit(
    claude_state_env: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, _, sub_state = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    responses = [
        SimpleNamespace(returncode=0, stdout="ok", stderr=""),
        SimpleNamespace(returncode=1, stdout="", stderr="subscription limit reached"),
    ]
    monkeypatch.setattr(csa.subprocess, "run", lambda *args, **kwargs: responses.pop(0))
    adapter = ClaudeSubscriptionAdapter()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("review prompt", encoding="utf-8")
    result = adapter.run_review(prompt, cycle="079", run_dir=tmp_path / "run")
    assert result.status == "BLOCKED"
    assert result.error_message == "SUBSCRIPTIONLIMITREACHED"
    state_payload = json.loads(sub_state.read_text(encoding="utf-8"))
    assert state_payload["limiteventstoday"] == 1


def test_run_review_writes_request_and_response_files(
    claude_state_env: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    responses = [
        SimpleNamespace(returncode=0, stdout="ok", stderr=""),
        SimpleNamespace(returncode=0, stdout="PASS", stderr=""),
    ]
    monkeypatch.setattr(csa.subprocess, "run", lambda *args, **kwargs: responses.pop(0))
    adapter = ClaudeSubscriptionAdapter()
    run_dir = tmp_path / "run"
    prompt = tmp_path / "prompt.md"
    prompt.write_text("request", encoding="utf-8")
    result = adapter.run_review(prompt, cycle="079", run_dir=run_dir)
    assert result.status == "SUCCESS"
    assert (run_dir / "claude_request.md").exists()
    assert (run_dir / "claude_response.md").exists()


def test_run_review_marks_advisory_when_marker_present(
    claude_state_env: tuple[Path, Path, Path], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    responses = [
        SimpleNamespace(returncode=0, stdout="ok", stderr=""),
        SimpleNamespace(returncode=0, stdout="ADVISORY_ONLY", stderr=""),
    ]
    monkeypatch.setattr(csa.subprocess, "run", lambda *args, **kwargs: responses.pop(0))
    adapter = ClaudeSubscriptionAdapter()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("request", encoding="utf-8")
    result = adapter.run_review(prompt, cycle="079", run_dir=tmp_path / "run")
    assert result.status == "ADVISORYONLYBLOCKED"


def test_api_billing_fallback_blocked_by_env_key(
    claude_state_env: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = claude_state_env
    monkeypatch.setattr(csa.shutil, "which", lambda _: "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "api-billing-key")
    adapter = ClaudeSubscriptionAdapter()
    with pytest.raises(AdapterBlockedError, match="SUBSCRIPTION_ONLY_REQUIRED"):
        adapter.preflight()
