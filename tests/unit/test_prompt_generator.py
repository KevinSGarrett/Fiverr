"""Unit tests for prompt_generator.py — V5 corrected version."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from automation.prompt_generator import (
    TASK_FLOOR,
    _load_agent_lanes,
    generate_prompt,
    write_prompts,
)


class TestAgentLanes:
    def test_all_six_agents_loaded(self):
        """All six agent lanes must be defined in agent_lanes.yml."""
        lanes = _load_agent_lanes()
        lane_ids = set(lanes.get("lanes", {}).keys())
        assert set("ABECFD") == lane_ids

    def test_each_lane_has_description(self):
        lanes = _load_agent_lanes()
        for agent_id, lane in lanes.get("lanes", {}).items():
            assert "description" in lane, f"Agent {agent_id} missing description"

    def test_each_lane_has_role(self):
        lanes = _load_agent_lanes()
        for agent_id, lane in lanes.get("lanes", {}).items():
            assert "role" in lane, f"Agent {agent_id} missing role"

    def test_each_lane_has_owns(self):
        lanes = _load_agent_lanes()
        for agent_id, lane in lanes.get("lanes", {}).items():
            assert "owns" in lane, f"Agent {agent_id} missing owns"

    def test_agent_d_role(self):
        lanes = _load_agent_lanes()
        d = lanes["lanes"]["D"]
        assert "pr" in d.get("role", "").lower() or "steward" in d.get("role", "").lower() \
            or "merge" in d.get("description", "").lower()

    def test_agent_e_wait_for_b(self):
        lanes = _load_agent_lanes()
        e = lanes["lanes"]["E"]
        assert e.get("wait_for_b_first_commit") is True


class TestTaskFloor:
    def test_task_floor_is_15(self):
        # Recalibrated 2026-06-23 (55 -> 15); see AGENT_TASK_FLOOR_ENFORCEMENT.md.
        assert TASK_FLOOR == 15


class TestGeneratePrompt:
    def test_prompt_contains_model_block(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "Codex 5.3" in prompt

    def test_prompt_contains_medium_effort(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "medium" in prompt.lower()

    def test_prompt_contains_end_of_prompt(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        count = prompt.count("END OF PROMPT")
        assert count == 1, f"Expected 1 END OF PROMPT, got {count}"

    def test_prompt_contains_branch(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "cycle/075/integration" in prompt

    def test_prompt_contains_repo_root(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "C:\\Fiverr\\Fiverr" in prompt or "C:/Fiverr/Fiverr" in prompt

    def test_prompt_contains_validation_commands(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "ruff" in prompt
        assert "mypy" in prompt
        assert "pytest" in prompt

    def test_prompt_contains_report_path(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "docs/cycle_reports" in prompt

    def test_prompt_contains_autonomy_rule(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "autonomy" in prompt.lower() or "Autonomy" in prompt

    def test_prompt_contains_no_git_commit_instruction(self):
        """V5-007: prompts must not tell agents to git commit."""
        for agent_id in "ABECFD":
            prompt = generate_prompt(
                agent_id, 75, "cycle/075/integration",
                [{"key": "SCRUM-100", "summary": "Test story",
                  "status": "In Progress", "priority": "Medium"}] * 15,
                "run-test"
            )
            # Should not contain actual git commit commands as instructions
            # (may contain "do NOT git commit" which is fine)
            lines = prompt.splitlines()
            for line in lines:
                line_stripped = line.strip()
                if line_stripped.startswith("git commit") or line_stripped.startswith("git add"):
                    pytest.fail(
                        f"Agent {agent_id} prompt contains git commit/add command: {line!r}"
                    )

    def test_prompt_includes_jira_issues(self):
        issues = [{"key": "SCRUM-100", "summary": "Test story",
                   "status": "In Progress", "priority": "Medium"}]
        prompt = generate_prompt("A", 75, "cycle/075/integration", issues, "test")
        assert "SCRUM-100" in prompt

    def test_prompt_contains_cycle_number(self):
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "test")
        assert "075" in prompt

    def test_prompt_contains_do_not_commit_instruction(self):
        """Prompt must tell agents NOT to commit — controller owns git."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "test")
        assert "DO NOT" in prompt or "do not" in prompt.lower()
        assert "git" in prompt.lower()


class TestWritePrompts:
    def test_writes_all_agents(self, tmp_path):
        agents = ["A", "B", "E", "C", "F", "D"]
        issues = [
            {"key": f"SCRUM-{100 + i}", "summary": f"Story {i} test implementation",
             "status": "In Progress", "priority": "Medium"}
            for i in range(20)  # 20 issues to generate enough tasks
        ]
        result = write_prompts(75, "cycle/075/integration", "test-run",
                               agents, issues, tmp_path)
        assert len(result) == len(agents)
        for _agent_id, path in result.items():
            assert path.exists()
            assert path.stat().st_size > 100

    def test_file_naming_convention(self, tmp_path):
        """Prompt files must follow CYCLE_NNN_AGENT_X_PROMPT.md naming."""
        issues = [
            {"key": f"SCRUM-{100 + i}", "summary": f"Story {i}",
             "status": "In Progress", "priority": "Medium"}
            for i in range(20)
        ]
        write_prompts(75, "cycle/075/integration", "test", ["A"], issues, tmp_path)
        assert (tmp_path / "CYCLE_075_AGENT_A_PROMPT.md").exists()

    def test_raises_planning_incomplete_without_issues(self, tmp_path):
        """write_prompts raises RuntimeError with PLANNING_INCOMPLETE if no Jira issues."""
        with pytest.raises(RuntimeError, match="PLANNING_INCOMPLETE"):
            write_prompts(75, "cycle/075/integration", "test", ["A"], [], tmp_path)
