"""Generate cycle prompt contracts from lane and catalog metadata."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from automation.jira_spec_mapper import JiraSpecMapper

REPO_ROOT = Path(__file__).resolve().parents[1]
PM_AUTOMATION_DIR = REPO_ROOT / "PM_Pack" / "automation"
CONTRACTS_DIR = PM_AUTOMATION_DIR / "prompt_contracts"
AGENT_LANES_PATH = PM_AUTOMATION_DIR / "agent_lanes.yml"


class PlanningIncompleteError(RuntimeError):
    """Raised when contract stories are missing AC/DoD data."""


class PromptContractBuilder:
    """Build cycle contracts with canonical and compatibility keys."""

    def __init__(
        self,
        contracts_dir: Path | None = None,
        template_contracts_dir: Path | None = None,
        agent_lanes_path: Path | None = None,
        mapper: JiraSpecMapper | None = None,
    ) -> None:
        self.contracts_dir = contracts_dir or CONTRACTS_DIR
        self.template_contracts_dir = template_contracts_dir or CONTRACTS_DIR
        self.agent_lanes_path = agent_lanes_path or AGENT_LANES_PATH
        self.mapper = mapper or JiraSpecMapper()
        self.agent_lanes = self._load_agent_lanes()

    def _load_agent_lanes(self) -> dict[str, dict[str, Any]]:
        payload = yaml.safe_load(self.agent_lanes_path.read_text(encoding="utf-8")) or {}
        lanes = payload.get("lanes", {})
        if not isinstance(lanes, dict):
            return {}
        return {str(key): value for key, value in lanes.items() if isinstance(value, dict)}

    def _load_template_story_scope(self, agent: str) -> list[dict[str, Any]]:
        template_path = self.template_contracts_dir / f"CYCLE_079_AGENT_{agent}.contract.json"
        if not template_path.exists():
            return []
        payload = json.loads(template_path.read_text(encoding="utf-8"))
        stories = payload.get("jirascope", payload.get("jira_scope", []))
        return [story for story in stories if isinstance(story, dict)]

    def _normalize_story(self, story: dict[str, Any]) -> dict[str, Any]:
        ac = story.get("acceptancecriteria", story.get("acceptance_criteria", [])) or []
        dod = story.get("definitionofdone", story.get("definition_of_done", [])) or []
        path = story.get(
            "projectplanpath",
            story.get("project_plan_path", "PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md"),
        )
        files = story.get("filesormodules", story.get("files_or_modules", [])) or []
        return {
            "key": story.get("key", "SCRUM-000"),
            "summary": story.get("summary", "Cycle scope item"),
            "status": story.get("status", "To Do"),
            "priority": story.get("priority", "Medium"),
            "acceptance_criteria": [str(item) for item in ac],
            "definition_of_done": [str(item) for item in dod],
            "project_plan_path": str(path),
            "files_or_modules": [str(item) for item in files],
            "acceptancecriteria": [str(item) for item in ac],
            "definitionofdone": [str(item) for item in dod],
            "projectplanpath": str(path),
            "filesormodules": [str(item) for item in files],
        }

    def build_contract(self, agent: str, cycle: str, branch: str) -> dict[str, Any]:
        if agent not in self.agent_lanes:
            raise KeyError(f"Unknown agent lane: {agent}")

        stories = [self._normalize_story(story) for story in self._load_template_story_scope(agent)]
        if not stories:
            raise PlanningIncompleteError(f"No stories available for agent {agent}")
        for story in stories:
            if len(story["acceptance_criteria"]) == 0 or len(story["definition_of_done"]) == 0:
                raise PlanningIncompleteError(
                    f"{story['key']} missing AC/DoD for agent {agent}"
                )

        lane = self.agent_lanes[agent]
        lane_desc = str(lane.get("description", f"Agent {agent} lane"))
        allowed = [str(item) for item in lane.get("owns", [])]
        blocked = [str(item) for item in lane.get("prohibited", lane.get("prohibited_without_explicit_task", []))]

        sources = [
            "PM_Pack/automation/project_plan_catalog.json",
            "PM_Pack/automation/dod_catalog.json",
            "PM_Pack/automation/todo_epic_catalog.json",
            "PM_Pack/automation/github_governance_catalog.json",
            "PM_Pack/automation/agent_lanes.yml",
            *[str(story["key"]) for story in stories],
        ]

        built_at = datetime.now(UTC).isoformat()
        model_policy = {
            "worker": "Cursor CLI",
            "model": "codex-5.3",
            "effort": "medium",
            "auto": False,
            "fallback": False,
        }

        contract = {
            "cycle": cycle,
            "agent": agent,
            "agent_lane": lane_desc,
            "agentlane": lane_desc,
            "branch": branch,
            "model_policy": model_policy,
            "modelpolicy": {**model_policy, "auto_model_selection": "DISABLED"},
            "jira_scope": stories,
            "jirascope": stories,
            "allowed_paths": allowed,
            "allowedpaths": allowed,
            "blocked_paths": blocked,
            "blockedpaths": blocked,
            "validation_commands": [
                "python automation/ai_cycle_controller.py brain-check",
                "python automation/ai_cycle_controller.py validate-prompts --cycle 080",
            ],
            "validationcommands": [
                "python automation/ai_cycle_controller.py brain-check",
                "python automation/ai_cycle_controller.py validate-prompts --cycle 080",
            ],
            "final_report_path": f"docs/cycle_reports/CYCLE_{cycle}_AGENT_{agent}.md",
            "finalreportpath": f"docs/cycle_reports/CYCLE_{cycle}_AGENT_{agent}.md",
            "built_at": built_at,
            "builtat": built_at,
            "contract_version": "1.0.0",
            "contractversion": "1.0.0",
            "metadata": {
                "sources_used": sources,
                "sourcesused": sources,
                "catalog_counts": self.mapper.catalog_counts(),
            },
        }
        return contract

    def write_contract(self, agent: str, cycle: str, branch: str) -> Path:
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        contract = self.build_contract(agent=agent, cycle=cycle, branch=branch)
        path = self.contracts_dir / f"CYCLE_{cycle}_AGENT_{agent}.contract.json"
        path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
        return path
