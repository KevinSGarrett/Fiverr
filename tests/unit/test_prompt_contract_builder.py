from __future__ import annotations

import json
import subprocess

from automation.prompt_contract_builder import PromptContractBuilder


def test_builder_exposes_six_agent_lanes() -> None:
    builder = PromptContractBuilder()
    assert sorted(builder.agent_lanes.keys()) == ["A", "B", "C", "D", "E", "F"]


def test_build_contract_schema_compatible() -> None:
    builder = PromptContractBuilder()
    contract = builder.build_contract(agent="A", cycle="080", branch="cycle/080/integration")
    assert contract["agent"] == "A"
    assert len(contract["jira_scope"]) >= 1


def test_write_contract_validates_against_schema(tmp_path) -> None:
    builder = PromptContractBuilder(contracts_dir=tmp_path)
    path = builder.write_contract(agent="B", cycle="080", branch="cycle/080/integration")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["cycle"] == "080"

    schema_path = "automation/schemas/prompt_contract.schema.json"
    cmd = ["python", "-m", "jsonschema", schema_path, "--instance", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
