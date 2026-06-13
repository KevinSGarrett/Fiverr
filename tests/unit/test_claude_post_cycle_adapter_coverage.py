"""Coverage tests for claude_post_cycle_adapter behavior branches."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from automation import claude_post_cycle_adapter as adapter


def test_verify_subscription_preflight_blocks_when_api_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "abc")
    result = adapter.verify_subscription_preflight()
    assert result["passed"] is False
    assert result["reason"] == "BLOCKED_CLAUDE_API_KEY_PRESENT"


def test_parse_outcome_variants() -> None:
    assert adapter._parse_review_outcome("review result: pass") == "PASS"
    assert adapter._parse_review_outcome("post-cycle review: FAIL") == "FAIL"
    assert adapter._parse_review_outcome("dispatch blocked now") == "BLOCKED"
    assert adapter._parse_review_outcome("neutral output") == "ADVISORY_ONLY"


def test_run_post_cycle_review_binary_missing_advisory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(adapter, "verify_subscription_preflight", lambda: {"passed": True})
    monkeypatch.setattr(adapter, "_find_claude_binary", lambda: None)
    result = adapter.run_post_cycle_review(77, tmp_path, "prompt", '{"x":1}')
    assert result.status == "ADVISORY_ONLY"
    assert result.blocks_dispatch is True
    assert Path(result.request_path).exists()


def test_run_post_cycle_review_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(adapter, "verify_subscription_preflight", lambda: {"passed": True})
    monkeypatch.setattr(adapter, "_find_claude_binary", lambda: "claude")

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(adapter.subprocess, "run", raise_timeout)
    result = adapter.run_post_cycle_review(77, tmp_path, "prompt", '{"x":1}')
    assert result.status == "ADVISORY_ONLY"
    assert "timed out" in result.error.lower()


def test_run_post_cycle_review_pass_and_state_update(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_path = tmp_path / "state/claude_model_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(adapter, "CLAUDE_STATE_PATH", state_path)
    monkeypatch.setattr(adapter, "verify_subscription_preflight", lambda: {"passed": True})
    monkeypatch.setattr(adapter, "_find_claude_binary", lambda: "claude")
    monkeypatch.setattr(adapter, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(
        adapter.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="REVIEW RESULT: PASS claude-sonnet", stderr=""
        ),
    )
    result = adapter.run_post_cycle_review(77, tmp_path, "prompt", json.dumps({"ok": True}))
    assert result.status == "PASS"
    assert result.blocks_dispatch is False
    assert Path(result.response_path).exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["observed_model"] == "claude-sonnet-4-6"


def test_preflight_block_report_written(tmp_path: Path) -> None:
    adapter._write_preflight_block_report(
        77,
        tmp_path,
        {
            "reason": "BLOCKED_CLAUDE_API_KEY_PRESENT",
            "findings": ["x"],
            "action": "remove key",
        },
    )
    path = tmp_path / "post_cycle_review/claude/BLOCKED_API_KEY_PRESENT.md"
    assert path.exists()


def test_advisory_report_written(tmp_path: Path) -> None:
    adapter._write_advisory_report(77, tmp_path, "missing binary")
    path = tmp_path / "post_cycle_review/claude/ADVISORY_ONLY.md"
    assert path.exists()


def test_find_claude_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    monkeypatch.setattr(shutil, "which", lambda _: "C:/bin/claude.exe")
    assert adapter._find_claude_binary() == "C:/bin/claude.exe"
