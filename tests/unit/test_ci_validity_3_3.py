"""Tests for ITEM 3.3 -- close CI validity holes.

Green CI must mean the loop-critical core is actually tested. These tests assert:
  * .github/workflows/ci.yml no longer --ignores the loop-critical modules that
    CAN run on ubuntu-hosted CI (queue_processor, collection_orchestrator,
    openai_api_adapter).
  * The Cursor-CLI-dependent modules (cursor_adapter, prompt_generator,
    prompt_contract_builder) ARE still ignored on ubuntu-hosted CI -- they
    require the Cursor binary (Windows self-hosted runner only) -- and the
    ignore carries a documented reason so it is not mistaken for a coverage hole.
  * automation/post_cycle_review.py (the live post-agent gate) keeps the same
    ignore set as CI.
  * automation/adapters/openai_api_adapter.py no longer hardcodes a C:/AI_Runner
    literal (it resolves runner paths via automation.runner_paths, which the test
    write-guard honours).
  * host/set_branch_protection.ps1 uses the correct token env vars, the EXACT
    required status contexts GitHub reports, the canonical repo owner, and is
    guarded (default dry-run).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Loop-critical modules that run on a Python-only host -- these MUST be exercised
# by ubuntu-hosted CI + the post-cycle gate (un-ignored after item 3.3).
UBUNTU_PORTABLE_IGNORES = (
    "--ignore=tests/unit/test_queue_processor.py",
    "--ignore=tests/unit/test_collection_orchestrator.py",
    "--ignore=tests/unit/test_openai_api_adapter.py",
)

# Loop-critical modules that require the Cursor CLI binary (Windows self-hosted
# runner only). They CANNOT run on ubuntu-hosted CI, so they stay ignored there
# and are covered on the self-hosted runner (runner-smoke.yml). The ignore must
# be accompanied by a documented reason -- see the "Cursor CLI" rationale.
CURSOR_DEPENDENT_IGNORES = (
    "--ignore=tests/unit/test_cursor_adapter.py",
    "--ignore=tests/unit/test_prompt_generator.py",
    "--ignore=tests/unit/test_prompt_contract_builder.py",
)


def test_ci_does_not_ignore_ubuntu_portable_modules() -> None:
    ci_yml = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for ignore in UBUNTU_PORTABLE_IGNORES:
        assert ignore not in ci_yml, f"ci.yml still ignores loop-critical module: {ignore}"
    # Stale ignore for a module that does not exist must be gone too.
    assert "--ignore=tests/unit/test_ai_cycle_controller_coverage.py" not in ci_yml


def test_ci_ignores_cursor_dependent_modules_with_reason() -> None:
    """Cursor-CLI-dependent modules stay ignored on ubuntu CI -- but the ignore
    must be documented so it is not mistaken for an unexplained coverage hole."""
    ci_yml = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for ignore in CURSOR_DEPENDENT_IGNORES:
        assert ignore in ci_yml, (
            f"ci.yml must ignore Cursor-CLI-dependent module on ubuntu: {ignore}"
        )
    # The ignore must carry a rationale referencing the Cursor CLI requirement.
    assert "Cursor CLI" in ci_yml, "ci.yml ignore of Cursor modules must be documented"


def test_post_cycle_gate_matches_ci_ignores() -> None:
    review = (REPO_ROOT / "automation" / "post_cycle_review.py").read_text(encoding="utf-8")
    # Ubuntu-portable modules un-ignored in the live gate too.
    for ignore in UBUNTU_PORTABLE_IGNORES:
        assert ignore not in review, (
            f"post_cycle_review.py still ignores loop-critical module: {ignore}"
        )
    # Cursor-dependent modules ignored to mirror CI exactly.
    for ignore in CURSOR_DEPENDENT_IGNORES:
        assert ignore in review, (
            f"post_cycle_review.py must mirror CI's Cursor-CLI ignore: {ignore}"
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

    # Required status contexts -- the EXACT check-run names GitHub reports
    # (verified live): CI jobs are namespaced "CI / <job>"; the security.yml and
    # pr-checks.yml jobs report as bare job names.
    for context in (
        "CI / lint",
        "CI / type-check",
        "CI / tests-coverage",
        "CI / smoke-gates",
        "CI / codex-review-gate",
        "Secret Scan",
        "Dependency Audit",
        "Validate PR",
    ):
        assert context in text, f"branch-protection script missing required context: {context}"

    # The earlier WRONG context strings (workflow names, not job names) must be
    # gone from the required-contexts array.
    assert '"Security"' not in text, "stale wrong context 'Security' must be removed"
    assert '"PR Checks"' not in text, "stale wrong context 'PR Checks' must be removed"

    # Canonical repo owner (the real remote), not the bogus default.
    assert "KevinSGarrett" in text
    assert '"scentiment"' not in text, "stale wrong owner default must be removed"

    # Must be guarded: default dry-run, only applies with -Execute.
    assert "-Execute" in text
    assert "$Execute" in text
    assert "DRY-RUN" in text
