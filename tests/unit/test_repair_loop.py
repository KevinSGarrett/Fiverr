"""Unit tests for repair_loop.py — failure classification and prompt generation."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))


class TestClassifyFailure:
    """_classify_failure correctly identifies failure types from error messages."""

    def test_lint(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["ruff check error"]) == "lint"

    def test_lint_uppercase(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["Ruff FAIL: F401"]) == "lint"

    def test_typecheck(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["mypy error found"]) == "typecheck"

    def test_test(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["pytest FAILED"]) == "test"

    def test_report(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["Required report not found"]) == "report"

    def test_ownership(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["ownership violation"]) == "ownership"

    def test_general_fallback(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure(["something else entirely"]) == "general"

    def test_empty_errors(self):
        from automation.repair_loop import _classify_failure
        assert _classify_failure([]) == "general"


class TestGenerateRepairPrompt:
    def test_repair_prompt_has_required_sections(self):
        """Repair prompt must have END OF PROMPT, model block, validation commands."""
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt(
            agent_id="A", cycle=75,
            errors=["ruff check failed: E501"],
            failure_type="lint",
            attempt=1,
        )
        assert "END OF PROMPT" in prompt
        assert "Codex 5.3" in prompt
        assert "medium" in prompt.lower()
        assert "git commit" in prompt.lower() or "commit" in prompt.lower()

    def test_repair_prompt_includes_errors(self):
        """Repair prompt must include the specific error messages."""
        from automation.repair_loop import _generate_repair_prompt
        errors = ["ruff: line 42 E501 too long", "ruff: line 55 F401 import unused"]
        prompt = _generate_repair_prompt("A", 75, errors, "lint", 1)
        assert "ruff: line 42" in prompt or "E501" in prompt

    def test_repair_prompt_includes_attempt_number(self):
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt("B", 75, ["error"], "test", 2)
        assert "2" in prompt
        assert "attempt" in prompt.lower() or "Attempt" in prompt

    def test_repair_prompt_includes_agent_and_cycle(self):
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt("C", 75, ["error"], "test", 1)
        assert "Agent C" in prompt or "AGENT_C" in prompt or "Agent C" in prompt
        assert "075" in prompt or "75" in prompt

    def test_repair_prompt_includes_branch(self):
        from automation.repair_loop import _generate_repair_prompt
        prompt = _generate_repair_prompt("D", 75, ["error"], "report", 1)
        assert "cycle/075/integration" in prompt


class TestRepairResult:
    def test_result_dataclass(self):
        from automation.repair_loop import RepairResult
        r = RepairResult(agent="A", cycle=75, attempt=1, status="REPAIRED")
        assert r.agent == "A"
        assert r.cycle == 75
        assert r.attempt == 1
        assert r.status == "REPAIRED"

    def test_result_defaults(self):
        from automation.repair_loop import RepairResult
        r = RepairResult(agent="A", cycle=75, attempt=1, status="FAILED")
        assert r.errors_in == []
        assert r.errors_out == []
        assert r.repair_prompt_path == ""
        assert r.commit_sha == ""


class TestMaxAttempts:
    def test_max_attempts_constant(self):
        """MAX_REPAIR_ATTEMPTS must be 3."""
        from automation.repair_loop import MAX_REPAIR_ATTEMPTS
        assert MAX_REPAIR_ATTEMPTS == 3
