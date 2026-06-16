from __future__ import annotations

import json
from pathlib import Path

import automation.ai_cycle_controller as controller
from click.testing import CliRunner


class _GateResult:
    def __init__(self, passed: bool, message: str) -> None:
        self.passed = passed
        self._message = message

    def summary(self) -> str:
        return self._message


def _invoke_stage2(
    tmp_path: Path,
    monkeypatch,
    *,
    model_gate_passed: bool = True,
    pm_pack_audit_passed: bool = True,
    validate_prompts_passed: bool = True,
    manifest_status: str = "READY",
) -> tuple[int, str]:
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(controller, "REPO_ROOT", repo_root)

    manifest_path = repo_root / "PM_Pack/automation/prompt_package_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps({"cycle": "081", "status": manifest_status}),
        encoding="utf-8",
    )
    policy_path = repo_root / "PM_Pack/automation/provider_policy.yml"
    policy_path.write_text(
        json.dumps(
            {
                "global_rules": {
                    "advisory_only_provider_routing": False,
                    "advisory_confirm_mode": True,
                }
            }
        ),
        encoding="utf-8",
    )

    provider_health_path = tmp_path / "provider_health.json"
    provider_health_path.write_text(
        json.dumps({"cursorcli": {"status": "READY"}}),
        encoding="utf-8",
    )
    real_path = Path
    monkeypatch.setattr(
        controller,
        "Path",
        lambda value: provider_health_path
        if value == "C:/AI_Runner/state/provider_health.json"
        else real_path(value),
    )
    monkeypatch.setattr(
        "automation.model_gate.check",
        lambda repo_root, cycle, agent: _GateResult(model_gate_passed, "model gate"),
    )

    def _fake_run_shell(args: list[str]) -> tuple[int, str]:
        joined = " ".join(args)
        if "pm-pack-audit" in joined:
            if pm_pack_audit_passed:
                return (0, "PM_PACK_AUDIT PASS")
            return (1, "PM_PACK_AUDIT BLOCKED")
        if "validate-prompts" in joined:
            if validate_prompts_passed:
                return (0, "PROMPT VALIDATION PASS")
            return (1, "PROMPT VALIDATION FAIL")
        return (0, "PASS")

    monkeypatch.setattr(controller, "_run_shell_command", _fake_run_shell)
    result = CliRunner().invoke(controller.cli, ["stage2-readiness-check"])
    return result.exit_code, result.output


def test_stage2_all_gates_pass(tmp_path: Path, monkeypatch) -> None:
    code, _output = _invoke_stage2(tmp_path, monkeypatch)
    assert code == 0


def test_stage2_model_gate_fail(tmp_path: Path, monkeypatch) -> None:
    code, _output = _invoke_stage2(tmp_path, monkeypatch, model_gate_passed=False)
    assert code == 1


def test_stage2_prompt_package_not_ready(tmp_path: Path, monkeypatch) -> None:
    code, _output = _invoke_stage2(tmp_path, monkeypatch, manifest_status="BLOCKED")
    assert code == 1


def test_stage2_pm_pack_audit_fail(tmp_path: Path, monkeypatch) -> None:
    code, _output = _invoke_stage2(tmp_path, monkeypatch, pm_pack_audit_passed=False)
    assert code == 1
