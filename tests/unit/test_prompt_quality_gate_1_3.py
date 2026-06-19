"""ITEM 1.3 — prompt quality gate ENFORCES (fail-closed on degenerate prompts).

These tests pin the promotion of PQ-6 (code-block ratio), PQ-7a (unique-word
ratio), PQ-7b (authored-task ratio), the word floor, and the PQ-0..5 section
gates from warnings to HARD ERRORS, plus env-tunability of the floors.

Positive calibration uses the synthetic known-good prompt in _prompt_fixtures —
proving the gate is calibrated (reject degenerate, accept genuinely rich), not
a blanket "reject all".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parent))

from _prompt_fixtures import build_known_good_prompt, build_marginal_word_floor_prompt

from automation.prompt_validator import validate


def _write(tmp_path: Path, content: str, cycle: int = 75, agent: str = "A") -> Path:
    p = tmp_path / f"CYCLE_{cycle:03d}_AGENT_{agent}_PROMPT.md"
    p.write_text(content, encoding="utf-8")
    return p


# Header lines that satisfy the REQUIRED_ERRORS content gates so that a test
# isolating one quality floor does not also trip unrelated required-content
# errors. (PQ-0..5 + model block + markers + commands.)
_GOOD_HEADER = (
    "=" * 68 + "\n"
    "AGENT A -- CYCLE 075 PROMPT\n"
    + "=" * 68 + "\n\n"
    "## 0. Model Policy / PQ-0 Identity\n"
    "- Model: Codex 5.3\n- Effort: medium\n"
    "- Auto model selection: DISABLED\n"
    "## 1. PQ-1 Project Context\nBranch: cycle/075/integration  Repo: C:/Fiverr/Fiverr\n"
    "## 2. PQ-2 Your Role / File Ownership\nfile ownership: src/pipeline\n"
    "## 3. PQ-3 Git Instructions\nwork on branch cycle/075/integration\n"
    "## 4. PQ-4 Autonomy Rule\nAutonomy rule: proceed autonomously\n"
    "## 5. PQ-5 Jira Scope\nSCRUM-100 in scope\n"
    "docs/cycle_reports/CYCLE_075 report path\n"
    "python -m ruff check  python -m mypy src  python -m pytest\n"
    "END OF PROMPT\n"
)


def _degenerate_cycle083_style(n_tasks: int = 100, n_code: int = 2) -> str:
    """Mimic CYCLE_083: many templated tasks, almost no code blocks."""
    parts = [_GOOD_HEADER]
    parts.append("## 6. Tasks\n")
    for i in range(1, n_tasks + 1):
        parts.append(
            f"### Task {i}: Implement core logic for [FIVERR-E6] Story {i}\n"
            "Implement the story acceptance criteria as described in the spec.\n"
        )
    # Add exactly n_code stray code fences somewhere (the CYCLE_083 pattern: ~2).
    for j in range(n_code):
        parts.append(f"```\necho placeholder {j}\n```\n")
    return "\n".join(parts)


def test_degenerate_prompt_fails(tmp_path):
    """100 tasks + 2 code blocks (CYCLE_083 style) → FAIL with a PQ-6 error.

    Negative reproduction: this used to PASS-with-warnings.
    """
    prompt = _degenerate_cycle083_style(n_tasks=100, n_code=2)
    f = _write(tmp_path, prompt)
    result = validate(f, "A", 75)
    assert result.passed is False
    assert any(e.startswith("PQ-6") for e in result.errors), (
        f"Expected a PQ-6 error. Errors: {result.errors}"
    )


def test_zero_codeblock_many_tasks_fails(tmp_path):
    """55 tasks, 0 code blocks → explicit egregious ERROR."""
    parts = [_GOOD_HEADER, "## 6. Tasks\n"]
    for i in range(1, 56):
        parts.append(f"### Task {i}: Do work item {i}\nProse only, no code.\n")
    f = _write(tmp_path, "\n".join(parts))
    result = validate(f, "A", 75)
    assert result.passed is False
    assert any("PQ-6" in e and "ZERO code blocks" in e for e in result.errors), (
        f"Expected zero-codeblock PQ-6 error. Errors: {result.errors}"
    )


def test_known_good_prompt_passes(tmp_path):
    """The synthetic known-good prompt → passes with no PQ errors."""
    prompt = build_known_good_prompt(cycle=75, agent="A", tasks=60)
    f = _write(tmp_path, prompt)
    result = validate(f, "A", 75)
    assert result.passed is True, f"Known-good prompt must pass. Errors: {result.errors}"
    assert not any(e.startswith(("PQ-6", "PQ-7")) for e in result.errors)
    assert not any("Word floor" in e for e in result.errors)


def test_floors_env_tunable(tmp_path, monkeypatch):
    """Lowering a floor via env lets a marginal prompt pass; default rejects it.

    The marginal prompt clears the task/code-ratio/authored/unique floors but
    lands below the 6000 default word floor — i.e. it fails ONLY on the word
    floor by default, and passes once PROMPT_MIN_WORD_COUNT is lowered.
    """
    marginal = build_marginal_word_floor_prompt(cycle=75, agent="A")
    f = _write(tmp_path, marginal)

    # Default: rejected on the word floor.
    monkeypatch.delenv("PROMPT_MIN_WORD_COUNT", raising=False)
    default_result = validate(f, "A", 75)
    assert default_result.passed is False
    assert any("Word floor" in e for e in default_result.errors), (
        f"Marginal prompt should fail word floor by default. Errors: {default_result.errors}"
    )

    # Tuned down: the same prompt now clears the (lowered) word floor.
    monkeypatch.setenv("PROMPT_MIN_WORD_COUNT", "500")
    tuned_result = validate(f, "A", 75)
    assert tuned_result.passed is True, (
        f"Lowering PROMPT_MIN_WORD_COUNT should let the marginal prompt pass. "
        f"Errors: {tuned_result.errors}"
    )


def test_missing_section_is_error(tmp_path):
    """A prompt missing a PQ-0..5 section → ERROR (was a warning)."""
    # Start from the known-good prompt and strip the PQ-3 section marker.
    prompt = build_known_good_prompt(cycle=75, agent="A", tasks=60)
    # Remove the PQ-3 heading + its alias keywords so the gate cannot match.
    broken = prompt.replace("## 3. PQ-3 Git Instructions", "## 3. Repository Notes")
    broken = broken.replace("git instructions", "repository notes")
    f = _write(tmp_path, broken)
    result = validate(f, "A", 75)
    assert result.passed is False
    assert any(e.startswith("PQ gate missing: PQ-3") for e in result.errors), (
        f"Expected a PQ-3 missing-section error. Errors: {result.errors}"
    )
