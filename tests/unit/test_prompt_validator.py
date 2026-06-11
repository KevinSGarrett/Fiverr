"""Unit tests for prompt_validator.py — HARDENED gates."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from automation.prompt_validator import validate, validate_all


def _make_valid_prompt(cycle: int = 75, agent: str = "A", tasks: int = 55) -> str:
    """Build a minimal valid prompt that passes all gates."""
    task_lines = []
    for i in range(1, tasks + 1):
        task_lines.append(f"### Task {i}: SCRUM-{1000 + i} task description")
        task_lines.append("")

    return f"""{'=' * 68}
AGENT {agent} -- CYCLE {cycle:03d} PROMPT
{'=' * 68}

## 0. Model Policy (MANDATORY -- do not override)

- **Model:** Codex 5.3
- **Effort:** medium
- **Auto model selection:** DISABLED -- use only Codex 5.3
- **Fallback model:** DISABLED

## 1. Identity

You are Agent {agent} for Cycle {cycle:03d}.

## 2. Project Context

- Branch: `cycle/{cycle:03d}/integration`
- Repo: C:/Fiverr/Fiverr
- Cycle: {cycle:03d}

## 3. Your Role

File scope: src/pipeline

## 4. Git Instructions

Work on branch: cycle/{cycle:03d}/integration

## 5. Autonomy Rule

Proceed autonomously without confirmation.

## 6. Jira Scope

| Jira Key | Summary | Status |
| SCRUM-100 | Example story | In Progress |

## 7. Tasks

{chr(10).join(task_lines)}

## 8. Validation Steps

Run these commands:

```bash
python -m ruff check src/ --output-format=text
python -m mypy src/ --ignore-missing-imports
python -m pytest tests/ -q
```

## 9. Files Summary

| Action | File |
| CREATE | src/example.py |

## 10. Commit Instructions

```bash
git add .
git commit -m "feat(cycle-{cycle:03d}): [Agent {agent}] description"
```

## 11. Report Requirements

Write to: docs/cycle_reports/CYCLE_{cycle:03d}_AGENT_{agent}.md

Include AGENT_COMPLETE on the final line.

## 12. Branch Guardrails

- Do NOT push directly to `main`
- Do NOT force-push to any branch

{'=' * 68}
END OF PROMPT -- AGENT {agent} CYCLE {cycle:03d}
{'=' * 68}
"""


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
