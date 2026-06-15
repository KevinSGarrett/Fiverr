from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from automation.adapters import cursor_worker_adapter as cwa
from automation.adapters.cursor_worker_adapter import AdapterBlockedError, CursorWorkerAdapter


def test_draft_prompt_path_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cwa.model_gate, "check", lambda: SimpleNamespace(passed=True))
    adapter = CursorWorkerAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.run_agent(Path("PM_Pack/automation/prompts/drafts/test.md"), cycle="079", agent="A")


def test_validated_prompt_path_check_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cwa.model_gate, "check", lambda: SimpleNamespace(passed=True))
    adapter = CursorWorkerAdapter()
    assert (
        adapter._validate_prompt_path(Path("PM_Pack/automation/prompts/validated/CYCLE_079_AGENT_A_PROMPT.md"))
        is True
    )


def test_preflight_blocks_when_model_unverified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cwa.model_gate, "check", lambda: SimpleNamespace(passed=False))
    adapter = CursorWorkerAdapter()
    with pytest.raises(AdapterBlockedError):
        adapter.preflight()


def test_preflight_passes_when_model_verified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cwa.model_gate, "check", lambda: SimpleNamespace(passed=True))
    adapter = CursorWorkerAdapter()
    adapter.preflight()


def test_desktop_binary_path_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cwa.model_gate, "check", lambda: SimpleNamespace(passed=True))
    adapter = CursorWorkerAdapter()
    adapter.binary = r"C:\Users\Windows 11\AppData\Local\Programs\Cursor\resources\app\bin\cursor.cmd"
    with pytest.raises(AdapterBlockedError):
        adapter.preflight()


def test_run_agent_success_when_report_complete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cwa.model_gate, "check", lambda: SimpleNamespace(passed=True))
    monkeypatch.setattr(
        cwa,
        "cursor_run_agent",
        lambda **kwargs: SimpleNamespace(status="complete", error_message="", **kwargs),
    )
    report_dir = Path("docs/cycle_reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report = report_dir / "CYCLE_079_AGENT_A.md"
    report.write_text("AGENT_COMPLETE\n", encoding="utf-8")
    prompt = tmp_path / "PM_Pack/automation/prompts/validated/CYCLE_079_AGENT_A_PROMPT.md"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("prompt", encoding="utf-8")
    adapter = CursorWorkerAdapter()
    result = adapter.run_agent(prompt_path=prompt, cycle="079", agent="A")
    assert result.status == "SUCCESS"
