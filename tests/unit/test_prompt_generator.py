"""Unit tests for prompt_generator.py — real prompt generation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from automation.prompt_generator import AGENT_ROLES, generate_prompt, write_prompts


class TestAgentRoles:
    def test_all_six_agents_defined(self):
        assert set(AGENT_ROLES.keys()) == set("ABECFD")

    def test_each_agent_has_name(self):
        for agent_id, role in AGENT_ROLES.items():
            assert "name" in role, f"Agent {agent_id} missing 'name'"
            assert len(role["name"]) > 5

    def test_each_agent_has_scope(self):
        for agent_id, role in AGENT_ROLES.items():
            assert "scope" in role, f"Agent {agent_id} missing 'scope'"

    def test_each_agent_has_epics(self):
        for agent_id, role in AGENT_ROLES.items():
            assert "epics" in role, f"Agent {agent_id} missing 'epics'"

    def test_agent_d_is_docs_only(self):
        assert AGENT_ROLES["D"].get("docs_only") is True

    def test_agent_e_is_tests_only(self):
        assert AGENT_ROLES["E"].get("tests_only") is True


class TestGeneratePrompt:
    def test_prompt_contains_model_block(self):
        """Generated prompt must have Codex 5.3 model block."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "Codex 5.3" in prompt

    def test_prompt_contains_medium_effort(self):
        """Generated prompt must specify medium effort."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "medium" in prompt.lower()

    def test_prompt_contains_end_of_prompt(self):
        """Generated prompt must have END OF PROMPT exactly once."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        count = prompt.count("END OF PROMPT")
        assert count == 1, f"Expected 1 END OF PROMPT, got {count}"

    def test_prompt_contains_branch(self):
        """Generated prompt must reference the cycle branch."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "cycle/075/integration" in prompt

    def test_prompt_contains_repo_root(self):
        """Generated prompt must reference C:/Fiverr/Fiverr."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "C:/Fiverr/Fiverr" in prompt or "C:\\Fiverr\\Fiverr" in prompt

    def test_prompt_contains_validation_commands(self):
        """Generated prompt must have ruff, mypy, pytest commands."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "ruff" in prompt
        assert "mypy" in prompt
        assert "pytest" in prompt

    def test_prompt_contains_report_path(self):
        """Generated prompt must include report path."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "docs/cycle_reports" in prompt

    def test_prompt_contains_autonomy_rule(self):
        """Generated prompt must have autonomy rule section."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "Autonomy" in prompt or "autonomy" in prompt

    def test_prompt_contains_no_main_guardrail(self):
        """Generated prompt must include no-main push guardrail."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "run-test-001")
        assert "main" in prompt.lower()

    def test_prompt_includes_jira_issues(self):
        """Generated prompt includes Jira issues when provided."""
        issues = [{"key": "SCRUM-100", "summary": "Test story", "status": "In Progress"}]
        prompt = generate_prompt("A", 75, "cycle/075/integration", issues, "test")
        assert "SCRUM-100" in prompt

    def test_prompt_contains_cycle_number(self):
        """Generated prompt must reference the cycle number."""
        prompt = generate_prompt("A", 75, "cycle/075/integration", [], "test")
        assert "075" in prompt


class TestWritePrompts:
    def test_writes_all_agents(self, tmp_path):
        """write_prompts creates one file per agent."""
        agents = ["A", "B", "E", "C", "F", "D"]
        result = write_prompts(75, "cycle/075/integration", "test-run",
                               agents, [], tmp_path)
        assert len(result) == len(agents)
        for _agent_id, path in result.items():
            assert path.exists()
            assert path.stat().st_size > 100

    def test_file_naming_convention(self, tmp_path):
        """Prompt files must follow CYCLE_NNN_AGENT_X_PROMPT.md naming."""
        write_prompts(75, "cycle/075/integration", "test", ["A"], [], tmp_path)
        assert (tmp_path / "CYCLE_075_AGENT_A_PROMPT.md").exists()
