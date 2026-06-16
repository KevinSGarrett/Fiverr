from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from automation.adapters import openai_api_adapter as oaa
from automation.adapters.openai_api_adapter import AdapterBlockedError, OpenAIApiAdapter


class _FakeResponses:
    def create(self, **kwargs):
        _ = kwargs
        return SimpleNamespace(output_text="ok")


class _FakeOpenAI:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.responses = _FakeResponses()


@pytest.fixture
def fake_openai_module(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = ModuleType("openai")
    fake_module.OpenAI = _FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_module)


def test_preflight_blocks_daily_hard_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oaa, "load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(status="HARDBLOCK")
    )
    with pytest.raises(AdapterBlockedError):
        adapter.preflight(task_type="prompt_lint", estimated_cost=0.1)


def test_preflight_blocks_monthly_hard_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oaa, "load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(status="HARDBLOCK")
    )
    with pytest.raises(AdapterBlockedError):
        adapter.preflight(task_type="json_classification", estimated_cost=1.0)


def test_preflight_passes_under_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oaa, "load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(status="PASS")
    )
    adapter.preflight(task_type="prompt_lint", estimated_cost=0.1)


def test_preflight_blocks_when_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oaa, "load_secrets", lambda: {})
    adapter = OpenAIApiAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.preflight(task_type="prompt_lint", estimated_cost=0.1)


def test_runner_env_only_key_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAIAPIKEY", "from_env")
    monkeypatch.setattr(oaa, "load_secrets", lambda: {})
    adapter = OpenAIApiAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.preflight(task_type="prompt_lint", estimated_cost=0.1)


def test_send_prompt_writes_usage_ledger(monkeypatch: pytest.MonkeyPatch, fake_openai_module) -> None:
    _ = fake_openai_module
    monkeypatch.setattr(oaa, "load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    monkeypatch.setattr(oaa, "update_spend", lambda provider, actual_cost: None)
    ledger_entries: list[object] = []
    monkeypatch.setattr(oaa, "record_call", lambda entry: ledger_entries.append(entry))
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(status="PASS")
    )
    result = adapter.send_prompt("hello world", task_type="prompt_lint", cycle="079")
    assert result.status == "SUCCESS"
    assert len(ledger_entries) == 1
    assert ledger_entries[0].provider == "openaiapi"


def test_send_prompt_hardblock_returns_blocked_without_ledger(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(oaa, "load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    monkeypatch.setattr(oaa, "update_spend", lambda provider, actual_cost: None)
    ledger_entries: list[object] = []
    monkeypatch.setattr(oaa, "record_call", lambda entry: ledger_entries.append(entry))
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(status="HARDBLOCK")
    )
    result = adapter.send_prompt("hello", task_type="prompt_lint", cycle="079")
    assert result.status == "BLOCKED"
    assert ledger_entries == []


def test_send_prompt_writes_advisory_file(monkeypatch: pytest.MonkeyPatch, fake_openai_module) -> None:
    _ = fake_openai_module
    monkeypatch.setattr(oaa, "load_secrets", lambda: {"OPENAIAPIKEY": "k"})
    monkeypatch.setattr(oaa, "update_spend", lambda provider, actual_cost: None)
    adapter = OpenAIApiAdapter()
    adapter.cost_guard = SimpleNamespace(
        check_budget=lambda provider, estimated_cost: SimpleNamespace(status="PASS")
    )
    result = adapter.send_prompt("hello", task_type="prompt_lint", cycle="079")
    assert result.status in {"SUCCESS", "ERROR"}
    advisory_root = Path("C:/AI_Runner/runs/CYCLE_079/openai_advisory")
    assert advisory_root.exists()
    advisory_files = sorted(advisory_root.glob("openai_advisory_*.json"))
    assert advisory_files
    payload = json.loads(advisory_files[-1].read_text(encoding="utf-8"))
    assert payload["task_type"] == "prompt_lint"
