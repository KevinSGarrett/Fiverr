from __future__ import annotations

import importlib
import json
from pathlib import Path

from automation import stage_executor as module
from automation.stage_executor import AgentRunResult, FullCycleResult, StageExecutor, StageResult


class _FakeController:
    def __init__(
        self,
        *,
        stage2_result: AgentRunResult | None = None,
        stage3_result: FullCycleResult | None = None,
    ) -> None:
        self._stage2_result = stage2_result or AgentRunResult(
            cursor_invoked=True,
            agent_complete=True,
            duration_seconds=1,
            files_changed=[],
        )
        self._stage3_result = stage3_result or FullCycleResult(
            all_agents_complete=True,
            agents_complete={"A": True, "B": True, "E": True, "C": True, "F": True, "D": True},
            pr_opened=True,
            pr_number=123,
            pr_status="OPEN",
            ci_status="PASS",
            test_suite_result="PASS",
        )

    def run_agent(self, cycle: int, agent: str, safe_docs_only: bool = False) -> AgentRunResult:
        _ = cycle, agent, safe_docs_only
        return self._stage2_result

    def run_full_cycle(self, auto_merge: bool = False) -> FullCycleResult:
        _ = auto_merge
        return self._stage3_result

    def run_post_cycle_review(self, cycle: int) -> bool:
        _ = cycle
        return True


def _seed_stage_state(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_stage_executor_reads_stage_2_as_current(tmp_path: Path, monkeypatch) -> None:
    stage_state = tmp_path / "stage_state.json"
    _seed_stage_state(stage_state, {"current_stage": 2})
    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    executor = StageExecutor(controller=_FakeController(), config={})
    assert executor.get_current_stage() == 2


def test_stage2_advances_when_cursor_invoked_and_complete(tmp_path: Path, monkeypatch) -> None:
    stage_state = tmp_path / "stage_state.json"
    evidence_dir = tmp_path / "stages"
    _seed_stage_state(stage_state, {"current_stage": 2})
    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    monkeypatch.setattr(module, "STAGE_EVIDENCE_DIR", evidence_dir)
    executor = StageExecutor(
        controller=_FakeController(
            stage2_result=AgentRunResult(
                cursor_invoked=True,
                agent_complete=True,
                duration_seconds=1,
                files_changed=["docs/foo.md"],
            )
        ),
        config={},
    )
    assert executor.advance_if_ready() is True


def test_stage2_does_not_advance_without_cursor_invoked(tmp_path: Path, monkeypatch) -> None:
    stage_state = tmp_path / "stage_state.json"
    evidence_dir = tmp_path / "stages"
    _seed_stage_state(stage_state, {"current_stage": 2})
    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    monkeypatch.setattr(module, "STAGE_EVIDENCE_DIR", evidence_dir)
    executor = StageExecutor(
        controller=_FakeController(
            stage2_result=AgentRunResult(
                cursor_invoked=False,
                agent_complete=False,
                duration_seconds=1,
                files_changed=[],
            )
        ),
        config={},
    )
    assert executor.advance_if_ready() is False


def test_stage3_requires_all_components_complete(tmp_path: Path, monkeypatch) -> None:
    stage_state = tmp_path / "stage_state.json"
    evidence_dir = tmp_path / "stages"
    _seed_stage_state(stage_state, {"current_stage": 3})
    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    monkeypatch.setattr(module, "STAGE_EVIDENCE_DIR", evidence_dir)
    executor = StageExecutor(
        controller=_FakeController(
            stage3_result=FullCycleResult(
                all_agents_complete=False,
                agents_complete={"A": True, "B": False},
                pr_opened=False,
                pr_number=None,
                pr_status="FAILED",
                ci_status="FAIL",
                test_suite_result="FAIL",
            )
        ),
        config={},
    )
    assert executor.advance_if_ready() is False


def test_stage4_requires_repair_succeeded(monkeypatch) -> None:
    executor = StageExecutor(controller=_FakeController(), config={})
    monkeypatch.setattr(
        executor,
        "_execute_stage_4",
        lambda: {
            "stage": 4,
            "status": "FAIL",
            "failure_injected": True,
            "repair_succeeded": False,
            "timestamp": module.iso_now(),
        },
    )
    result = executor.execute_stage(4)
    assert result.status == "FAIL"


def test_stage_advance_updates_stage_state_json(tmp_path: Path, monkeypatch) -> None:
    stage_state = tmp_path / "stage_state.json"
    evidence_dir = tmp_path / "stages"
    _seed_stage_state(
        stage_state,
        {
            "current_stage": 2,
            "stage_2": {"status": "PENDING"},
            "stage_3": {"status": "LOCKED"},
        },
    )
    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    monkeypatch.setattr(module, "STAGE_EVIDENCE_DIR", evidence_dir)
    executor = StageExecutor(controller=_FakeController(), config={})
    assert executor.advance_if_ready() is True
    payload = json.loads(stage_state.read_text(encoding="utf-8"))
    assert payload["current_stage"] == 3
    assert payload["stage_2"]["status"] == "PASS"


def test_locked_stages_cannot_advance(tmp_path: Path, monkeypatch) -> None:
    stage_state = tmp_path / "stage_state.json"
    evidence_dir = tmp_path / "stages"
    _seed_stage_state(
        stage_state,
        {
            "current_stage": 3,
            "stage_3": {"status": "PENDING"},
            "stage_4": {"status": "LOCKED"},
        },
    )
    monkeypatch.setattr(module, "STAGE_STATE_PATH", stage_state)
    monkeypatch.setattr(module, "STAGE_EVIDENCE_DIR", evidence_dir)
    executor = StageExecutor(
        controller=_FakeController(
            stage3_result=FullCycleResult(
                all_agents_complete=False,
                agents_complete={"A": True, "B": False},
                pr_opened=False,
                pr_number=None,
                pr_status="FAILED",
                ci_status="FAIL",
                test_suite_result="FAIL",
            )
        ),
        config={},
    )
    assert executor.advance_if_ready() is False
    payload = json.loads(stage_state.read_text(encoding="utf-8"))
    assert payload["current_stage"] == 3
    assert payload["stage_4"]["status"] == "LOCKED"


def test_stage_executor_writes_evidence_file(tmp_path: Path, monkeypatch) -> None:
    evidence_dir = tmp_path / "stages"
    monkeypatch.setattr(module, "STAGE_EVIDENCE_DIR", evidence_dir)
    executor = StageExecutor(controller=_FakeController(), config={})
    result = StageResult(stage=2, status="PASS", timestamp=module.iso_now(), evidence={"ok": True})
    executor.write_stage_evidence(2, result)
    out = evidence_dir / "STAGE2_EVIDENCE.json"
    assert out.exists()


def test_advance_if_ready_called_without_human_input(monkeypatch) -> None:
    executor = StageExecutor(controller=_FakeController(), config={})
    monkeypatch.setattr(executor, "get_current_stage", lambda: 8)
    assert executor.advance_if_ready() is False


def test_stage_executor_importable() -> None:
    imported = importlib.import_module("automation.stage_executor")
    assert hasattr(imported, "StageExecutor")
