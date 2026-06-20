"""Tests for ITEM 3.3 -- close CI validity holes.

Green CI must mean the loop-critical core is actually tested. These tests assert:
  * .github/workflows/ci.yml no longer --ignores the loop-critical test modules.
  * automation/post_cycle_review.py (the live post-agent gate) matches CI's
    ignore set -- it does not ignore the same loop-critical modules.
  * automation/adapters/openai_api_adapter.py no longer hardcodes a C:/AI_Runner
    literal (it resolves runner paths via automation.runner_paths, which the test
    write-guard honours).
  * host/set_branch_protection.ps1 uses the correct token env vars and required
    status contexts, and is guarded (default dry-run).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# The loop-critical test modules that MUST be exercised by CI + the post-cycle
# gate (no longer ignored after item 3.3).
LOOP_CRITICAL_IGNORES = (
    "--ignore=tests/unit/test_cursor_adapter.py",
    "--ignore=tests/unit/test_prompt_generator.py",
    "--ignore=tests/unit/test_prompt_contract_builder.py",
    "--ignore=tests/unit/test_queue_processor.py",
    "--ignore=tests/unit/test_collection_orchestrator.py",
    "--ignore=tests/unit/test_openai_api_adapter.py",
)


def test_ci_does_not_ignore_loop_critical_modules() -> None:
    ci_yml = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for ignore in LOOP_CRITICAL_IGNORES:
        assert ignore not in ci_yml, f"ci.yml still ignores loop-critical module: {ignore}"
    # Stale ignore for a module that does not exist must be gone too.
    assert "--ignore=tests/unit/test_ai_cycle_controller_coverage.py" not in ci_yml


def test_post_cycle_gate_matches_ci_ignores() -> None:
    review = (REPO_ROOT / "automation" / "post_cycle_review.py").read_text(encoding="utf-8")
    for ignore in LOOP_CRITICAL_IGNORES:
        assert ignore not in review, (
            f"post_cycle_review.py still ignores loop-critical module: {ignore}"
        )


def test_openai_adapter_uses_runner_paths() -> None:
    src = (REPO_ROOT / "automation" / "adapters" / "openai_api_adapter.py").read_text(
        encoding="utf-8"
    )
    # No hardcoded live-runner-root literal must remain in the module.
    assert "C:/AI_Runner" not in src
    assert "C:\\AI_Runner" not in src
    assert r"C:\AI_Runner" not in src
    # It must resolve runner paths via the single source of truth.
    assert "runner_paths" in src


def test_branch_protection_script_uses_correct_token_and_contexts() -> None:
    script_path = REPO_ROOT / "host" / "set_branch_protection.ps1"
    assert script_path.exists(), "host/set_branch_protection.ps1 must exist"
    text = script_path.read_text(encoding="utf-8")

    # Correct token env vars -- and NOT the bogus GITHUB_AUTOMATION_TOKEN.
    assert "GH_TOKEN" in text
    assert "GH_AUTOMATION_TOKEN" in text
    assert "GITHUB_AUTOMATION_TOKEN" not in text

    # Required status contexts (the workflows that exist).
    for context in (
        "CI / lint",
        "CI / type-check",
        "CI / tests-coverage",
        "CI / smoke-gates",
        "CI / codex-review-gate",
        "Security",
        "PR Checks",
    ):
        assert context in text, f"branch-protection script missing required context: {context}"

    # Must be guarded: default dry-run, only applies with -Execute.
    assert "-Execute" in text
    assert "$Execute" in text
    assert "DRY-RUN" in text
