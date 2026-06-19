"""Unit tests for prompt_validator.py — HARDENED gates.

Item 1.3 promoted PQ-6/PQ-7a/PQ-7b/word-floor/PQ-0..5 from warnings to hard
errors. The legacy ``_make_valid_prompt`` helper produced a substance-poor
prompt (55 templated task headers, ~2 code blocks, <6000 words) that PASSED
under the old warn-only gate but is exactly the degenerate shape the gate now
fails. It therefore delegates to the genuinely-rich synthetic fixture in
``_prompt_fixtures.build_known_good_prompt`` — the calibrated positive case.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parent))

from _prompt_fixtures import build_known_good_prompt

from automation.prompt_validator import validate, validate_all


def _make_valid_prompt(cycle: int = 75, agent: str = "A", tasks: int = 55) -> str:
    """Build a genuinely-rich prompt that passes all (now-enforced) gates.

    Delegates to the shared known-good fixture so the positive case stays
    calibrated against the fail-closed quality floors.
    """
    return build_known_good_prompt(cycle=cycle, agent=agent, tasks=tasks)


class TestValidatePass:
    def test_valid_prompt_passes(self, tmp_path):
        prompt = _make_valid_prompt()
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert result.passed, f"Valid prompt should pass. Errors: {result.errors}"

    def test_task_count_detected(self, tmp_path):
        prompt = _make_valid_prompt(tasks=55)
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert result.task_count >= 55

    def test_end_of_prompt_exactly_once(self, tmp_path):
        prompt = _make_valid_prompt()
        assert prompt.count("END OF PROMPT") == 1
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert result.end_of_prompt_count == 1


class TestValidateFail:
    def test_stub_prompt_fails(self, tmp_path):
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text("[STUB - populate from PM_Pack]\n\nBranch: cycle/075/integration\n")
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("stub" in e.lower() or "Stub" in e for e in result.errors)

    def test_missing_file_fails(self, tmp_path):
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("does not exist" in e for e in result.errors)

    def test_task_floor_violation_fails(self, tmp_path):
        prompt = _make_valid_prompt(tasks=10)  # below 55 floor
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("Task floor" in e or "task" in e.lower() for e in result.errors)

    def test_missing_end_of_prompt_fails(self, tmp_path):
        prompt = _make_valid_prompt().replace("END OF PROMPT", "")
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("END OF PROMPT" in e for e in result.errors)

    def test_double_end_of_prompt_fails(self, tmp_path):
        prompt = _make_valid_prompt() + "\nEND OF PROMPT -- extra\n"
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("END OF PROMPT" in e for e in result.errors)

    def test_missing_codex_model_block_fails(self, tmp_path):
        prompt = _make_valid_prompt().replace("Codex 5.3", "gpt-4")
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("Codex 5.3" in e or "model" in e.lower() for e in result.errors)

    def test_missing_jira_key_fails(self, tmp_path):
        prompt = _make_valid_prompt().replace("SCRUM-", "STORY-")
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert not result.passed

    def test_push_to_main_safety_gate(self, tmp_path):
        prompt = _make_valid_prompt() + "\ngit push origin main\n"
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 75)
        assert not result.passed
        assert any("main" in e.lower() for e in result.errors)

    def test_cycle_mismatch_fails(self, tmp_path):
        prompt = _make_valid_prompt(cycle=75)
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text(prompt)
        result = validate(f, "A", 99)  # wrong cycle
        assert not result.passed
        assert any("mismatch" in e.lower() or "cycle" in e.lower() for e in result.errors)

    def test_short_prompt_fails(self, tmp_path):
        f = tmp_path / "CYCLE_075_AGENT_A_PROMPT.md"
        f.write_text("\n".join([f"line {i}" for i in range(10)]))
        result = validate(f, "A", 75)
        assert not result.passed


class TestValidateAll:
    def test_validate_all_missing_files(self, tmp_path):
        results = validate_all(tmp_path, 75, ["A", "B"])
        assert "A" in results
        assert "B" in results
        assert not results["A"].passed
        assert not results["B"].passed

    def test_validate_all_returns_all_agents(self, tmp_path):
        agents = ["A", "B", "E", "C", "F", "D"]
        results = validate_all(tmp_path, 75, agents)
        assert set(results.keys()) == set(agents)
