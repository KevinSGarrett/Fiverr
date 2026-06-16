from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from automation.adapters import codex_subscription_adapter as module
from automation.adapters.codex_subscription_adapter import (
    AdapterBlockedError,
    CodexSubscriptionAdapter,
)
from automation.adapters.openai_api_adapter import OpenAIApiAdapter


def _write_state(path: Path, *, billing_mode: str = "chatgpt_subscription_only", api_key_present: bool = False) -> None:
    path.write_text(
        json.dumps({"billing_mode": billing_mode, "api_key_present": api_key_present}, indent=2),
        encoding="utf-8",
    )


@pytest.fixture(autouse=True)
def clear_openai_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def test_importable() -> None:
    assert CodexSubscriptionAdapter is not None
    assert AdapterBlockedError is not None


def test_blocks_api_key_billing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    with pytest.raises(AdapterBlockedError):
        CodexSubscriptionAdapter().preflight(Path("validated/prompt.md"), "082", "B")


def test_blocks_draft_prompt_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    with pytest.raises(AdapterBlockedError):
        CodexSubscriptionAdapter().preflight(Path("prompts/drafts/prompt.md"), "082", "B")


def test_blocks_missing_state_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "missing.json"
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    with pytest.raises(AdapterBlockedError):
        CodexSubscriptionAdapter().preflight(Path("validated/prompt.md"), "082", "B")


def test_blocks_wrong_billing_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path, billing_mode="openai_api")
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    with pytest.raises(AdapterBlockedError):
        CodexSubscriptionAdapter().preflight(Path("validated/prompt.md"), "082", "B")


def test_blocks_api_key_present_in_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path, api_key_present=True)
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    with pytest.raises(AdapterBlockedError):
        CodexSubscriptionAdapter().preflight(Path("validated/prompt.md"), "082", "B")


def test_preflight_passes_when_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=0))
    CodexSubscriptionAdapter().preflight(Path("validated/prompt.md"), "082", "B")


def test_run_agent_mocked_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    responses = [
        SimpleNamespace(returncode=0, stdout="0.1.0", stderr=""),
        SimpleNamespace(returncode=0, stdout="AGENT_COMPLETE", stderr=""),
    ]
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: responses.pop(0))
    result = CodexSubscriptionAdapter().run_agent(prompt, "082", "B")
    assert result.agent_complete is True
    assert result.status == "SUCCESS"


def test_run_agent_mocked_no_complete(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_path = tmp_path / "state.json"
    _write_state(state_path)
    prompt = tmp_path / "prompt.md"
    prompt.write_text("hello", encoding="utf-8")
    monkeypatch.setattr(CodexSubscriptionAdapter, "STATE_PATH", state_path)
    responses = [
        SimpleNamespace(returncode=0, stdout="0.1.0", stderr=""),
        SimpleNamespace(returncode=0, stdout="done", stderr=""),
    ]
    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: responses.pop(0))
    result = CodexSubscriptionAdapter().run_agent(prompt, "082", "B")
    assert result.status == "FAIL"
    assert result.agent_complete is False


def test_distinct_from_openai_api_adapter() -> None:
    assert CodexSubscriptionAdapter is not OpenAIApiAdapter
    assert CodexSubscriptionAdapter.CLI_COMMAND == "codex"
