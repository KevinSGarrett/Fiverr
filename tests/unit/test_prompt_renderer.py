from __future__ import annotations

from pathlib import Path

import pytest
from automation.prompt_renderer import DEFAULT_DRAFTS_DIR, PromptRenderer, render_with_overrides
from automation.prompt_validator import validate


def _contract(story_count: int = 3) -> dict[str, object]:
    stories = []
    for idx in range(1, story_count + 1):
        stories.append(
            {
                "key": f"SCRUM-{500 + idx}",
                "summary": f"Coverage story {idx}",
                "status": "TODO",
                "priority": "HIGH",
                "acceptancecriteria": [f"AC {idx}a", f"AC {idx}b"],
                "definitionofdone": [f"DoD {idx}a", f"DoD {idx}b"],
                "projectplanpath": f"PM_Pack/ref/project_plan/epic_{idx}.md",
                "filesormodules": [f"tests/unit/file_{idx}.py"],
            }
        )
    return {
        "cycle": "080",
        "agent": "F",
        "agentlane": "Test Coverage / Regression Suite / ADR Coverage",
        "branch": "cycle/080/integration",
        "modelpolicy": {"worker": "Cursor CLI", "model": "codex-5.3", "effort": "medium"},
        "jirascope": stories,
        "allowedpaths": ["tests/unit/test_prompt_renderer.py"],
        "blockedpaths": ["src/"],
        "validationcommands": [
            "ruff check tests/ --output-format=concise",
            "mypy src/ automation/ --ignore-missing-imports --no-error-summary",
            "pytest tests/unit/test_prompt_renderer.py -q",
        ],
        "finalreportpath": "docs/cycle_reports/CYCLE_080_AGENT_F.md",
        "builtat": "2026-06-15T11:20:00Z",
        "contractversion": "1.0.0",
    }


def test_render_returns_string_with_end_of_prompt() -> None:
    rendered = PromptRenderer().render(_contract())
    assert isinstance(rendered, str)
    assert "END OF PROMPT" in rendered


def test_render_contains_at_least_55_task_markers() -> None:
    rendered = PromptRenderer().render(_contract())
    assert rendered.count("### Task ") >= 55


def test_render_includes_git_rules_block() -> None:
    rendered = PromptRenderer().render(_contract())
    assert "GIT RULES — MANDATORY" in rendered


def test_render_includes_autonomy_rule_block() -> None:
    rendered = PromptRenderer().render(_contract())
    assert "AUTONOMY RULE" in rendered


def test_render_includes_all_jira_scope_story_keys() -> None:
    contract = _contract(story_count=5)
    rendered = PromptRenderer().render(contract)
    for story in contract["jirascope"]:
        assert story["key"] in rendered


def test_renderer_raises_filenotfound_when_template_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        PromptRenderer(template_path=tmp_path / "PROMPT_TEMPLATE.md")


def test_render_to_draft_creates_file_in_drafts_directory() -> None:
    renderer = PromptRenderer()
    draft_path = renderer.render_to_draft(_contract())
    assert draft_path.exists()
    assert draft_path.parent == DEFAULT_DRAFTS_DIR


def test_render_to_draft_file_contains_end_of_prompt() -> None:
    draft_path = PromptRenderer().render_to_draft(_contract())
    assert "END OF PROMPT" in draft_path.read_text(encoding="utf-8")


def test_render_to_draft_file_contains_at_least_55_task_markers() -> None:
    draft_path = PromptRenderer().render_to_draft(_contract())
    assert draft_path.read_text(encoding="utf-8").count("### Task ") >= 55


def test_render_to_draft_returns_expected_path_object() -> None:
    renderer = PromptRenderer()
    contract = _contract()
    expected = DEFAULT_DRAFTS_DIR / "CYCLE_080_AGENT_F_DRAFT.md"
    result = renderer.render_to_draft(contract)
    assert result == expected


def test_rendered_draft_passes_prompt_validator_integration() -> None:
    draft_path = PromptRenderer().render_to_draft(_contract())
    prompt_path = DEFAULT_DRAFTS_DIR / "CYCLE_080_AGENT_F_PROMPT.md"
    prompt_path.write_text(draft_path.read_text(encoding="utf-8"), encoding="utf-8")
    result = validate(prompt_path=prompt_path, agent="F", cycle=80)
    assert result.passed is True


def test_render_with_overrides_appends_extra_tasks() -> None:
    rendered = render_with_overrides(
        _contract(),
        extra_tasks=[
            {
                "title": "Extra regression slice",
                "jira_key": "SCRUM-999",
                "description": "Add one more check",
                "files": ["tests/unit/test_prompt_renderer.py"],
                "validation": "pytest tests/unit/test_prompt_renderer.py -q",
            }
        ],
    )
    assert "Extra regression slice" in rendered
    assert "SCRUM-999" in rendered


def test_render_with_overrides_custom_stop_conditions() -> None:
    rendered = render_with_overrides(
        _contract(),
        stop_conditions=["Stop when contract is invalid.", "Stop before blocked paths."],
    )
    assert "Stop when contract is invalid." in rendered
    assert "Stop before blocked paths." in rendered
    assert "Stop immediately if secrets/credentials are exposed" not in rendered


def test_render_with_overrides_total_tasks_still_55plus() -> None:
    rendered = render_with_overrides(
        _contract(),
        extra_tasks=[{"title": "Extra 1"}, {"title": "Extra 2"}],
    )
    assert rendered.count("### Task ") >= 55


def test_render_with_empty_jira_scope() -> None:
    contract = _contract()
    contract["jirascope"] = []
    rendered = render_with_overrides(contract)
    assert "No Jira stories assigned" in rendered
    assert rendered.count("### Task ") >= 55
