"""Additional orchestrator metadata contract tests for integration handoff."""

from __future__ import annotations

import pytest
import src.orchestrator as orchestrator


def test_build_phase2_smoke_metadata_contains_required_contract_fields() -> None:
    metadata = orchestrator.build_phase2_smoke_metadata()

    assert metadata["phase"] == "phase2-smoke"
    assert metadata["jira_mapping_required"] is True
    assert metadata["codex_disposition_required"] is True
    assert metadata["expected_gates"] == [
        "CI / Lint, Typecheck, Tests, and Gates",
        "codecov/project",
        "codecov/patch",
    ]


def test_build_phase2_smoke_metadata_is_deterministic() -> None:
    assert orchestrator.build_phase2_smoke_metadata() == orchestrator.build_phase2_smoke_metadata()


def test_run_phase2_smoke_prints_metadata_contract(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class _FakeLoader:
        def __init__(self, _config_path: str) -> None:
            pass

        def load(self) -> object:
            return object()

    monkeypatch.setattr(orchestrator.importlib, "import_module", lambda _name: object())
    monkeypatch.setattr(orchestrator, "ConfigLoader", _FakeLoader)

    assert orchestrator.run_phase2_smoke(config_path="config.yaml") == 0
    output = capsys.readouterr().out
    assert "Phase2 smoke metadata:" in output
    assert '"jira_mapping_required": true' in output
    assert '"codex_disposition_required": true' in output
