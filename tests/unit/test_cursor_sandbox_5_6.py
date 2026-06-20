"""ITEM 5.6 — Cursor blast-radius: control-plane protected-path guard.

An autonomous Cursor agent builds the Fiverr product (src/, tests/, docs/,
PM_Pack content). It must NEVER modify the runner's control plane — the CI
workflows, the scheduled driver, its own ownership lanes, the validators/merge
gate — because doing so would let it weaken the very gates that constrain it.
This guard rejects such changes regardless of the agent's lane.

(The OS-level out-of-repo write confinement is the separate DoD-RW step.)
"""
from __future__ import annotations

from automation import run_agent_lifecycle as ral


# ── _is_protected_path ────────────────────────────────────────────────────────
def test_protected_paths_detected():
    for p in (
        ".github/workflows/ci.yml",
        ".github/workflows/security.yml",
        "automation/merge_gate.py",
        "automation/prompt_validator.py",
        "automation/run_agent_lifecycle.py",
        "host/start_controller.ps1",
        "host/set_branch_protection.ps1",
        "PM_Pack/automation/agent_lanes.yml",
        "PM_Pack/automation/merge_policy.yml",
        "PM_Pack/automation/provider_policy.yml",       # Codex P1: provider/cost/git policy
        "PM_Pack/automation/current_policy_snapshot.json",  # compiled policy snapshot
    ):
        assert ral._is_protected_path(p) is True, p


def test_product_paths_not_protected():
    for p in (
        "src/collection/fiverr_selectors.py",
        "tests/unit/test_foo.py",
        "docs/cycle_reports/CYCLE_085_AGENT_B.md",
        "PM_Pack/07_hydration/HYDRATION_HEADER.md",
        "pyproject.toml",
        ".github/ISSUE_TEMPLATE/bug.md",  # not under workflows/
        # runtime-artifact subdirs the runner itself writes are NOT protected:
        "PM_Pack/automation/runs/CYCLE_085/agent_runs/B/rec.json",
        "PM_Pack/automation/prompts/CYCLE_085_AGENT_B_PROMPT.md",
        "PM_Pack/automation/post_cycle_reviews/cycle_085.json",
    ):
        assert ral._is_protected_path(p) is False, p


def test_protected_path_backslash_normalized():
    assert ral._is_protected_path("automation\\merge_gate.py") is True
    assert ral._is_protected_path(".\\automation/cursor_adapter.py") is True


# ── _check_ownership enforces protected paths regardless of lane ───────────────
def test_agent_b_blocked_from_control_plane():
    # Agent B owns src/ + tests/ — a control-plane change is still a violation.
    v = ral._check_ownership("B", ["src/x.py", ".github/workflows/ci.yml",
                                   "automation/merge_gate.py"])
    assert ".github/workflows/ci.yml" in v
    assert "automation/merge_gate.py" in v
    assert "src/x.py" not in v


def test_protected_overrides_an_allowing_lane():
    # Even an agent whose lane nominally ALLOWS .github/** cannot touch the CI
    # gate definitions — protected paths are checked first and win.
    v = ral._check_ownership("A", [".github/workflows/ci.yml"])
    assert ".github/workflows/ci.yml" in v


def test_agent_cannot_widen_own_lane():
    # An agent must not edit the ownership definition itself.
    v = ral._check_ownership("B", ["PM_Pack/automation/agent_lanes.yml"])
    assert "PM_Pack/automation/agent_lanes.yml" in v


def test_clean_product_change_passes_ownership():
    v = ral._check_ownership("B", ["src/foo.py", "tests/unit/test_foo.py"])
    assert v == []
