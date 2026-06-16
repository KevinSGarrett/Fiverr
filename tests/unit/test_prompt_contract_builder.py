from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from automation.prompt_contract_builder import PromptContractBuilder

TEMPLATE_CONTRACTS_DIR = Path("C:/Fiverr/Fiverr/PM_Pack/automation/prompt_contracts")
SCHEMA_PATH = Path("C:/Fiverr/Fiverr/automation/schemas/prompt_contract.schema.json")
EXPECTED_AGENT_LANES = ["A", "B", "C", "D", "E", "F"]
CYCLE = "080"
BRANCH = "cycle/080/integration"


def test_builder_exposes_six_agent_lanes() -> None:
    builder = PromptContractBuilder()
    assert sorted(builder.agent_lanes.keys()) == EXPECTED_AGENT_LANES


def test_build_contract_schema_compatible() -> None:
    builder = PromptContractBuilder()
    contract = builder.build_contract(agent="A", cycle=CYCLE, branch=BRANCH)
    assert contract["agent"] == "A"
    assert len(contract["jira_scope"]) >= 1


@pytest.mark.parametrize("agent", EXPECTED_AGENT_LANES)
def test_write_contract_validates_against_schema_for_all_agents(tmp_path: Path, agent: str) -> None:
    builder = PromptContractBuilder(contracts_dir=tmp_path, template_contracts_dir=TEMPLATE_CONTRACTS_DIR)
    path = builder.write_contract(agent=agent, cycle=CYCLE, branch=BRANCH)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["cycle"] == CYCLE
    assert payload["agent"] == agent
    assert len(payload["jira_scope"]) >= 1

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft7Validator(schema).iter_errors(payload), key=lambda error: error.path)
    assert not errors, "\n".join(error.message for error in errors)
