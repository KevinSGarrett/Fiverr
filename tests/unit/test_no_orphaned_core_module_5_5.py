"""Item 5.5-T3 — "no orphaned core module" guard.

The runner accreted multiple implementations per concern; several `automation/`
modules exist but are imported by NOTHING in the live path — the "looks built but
isn't wired" illusion-of-completeness this item targets. This guard makes that
state EXPLICIT and prevents silent drift: every top-level `automation/*.py` module
must be either (a) imported somewhere under `automation/`, (b) a known ENTRYPOINT
(run directly as a CLI / scheduled task / CI step), or (c) listed in
DEFERRED_ORPHANS (tracked for the 5.5 wire-or-delete decision).

A NEW orphan that is none of these fails the test, forcing a conscious choice:
wire it, delete it, or track it. Deleting the existing orphans is deferred to a
careful per-module review (some are intended future wiring); the spec explicitly
permits "mark DEFERRED w/ tracking item" — this allowlist IS that tracking item.

Analysis date: 2026-06-21 (static + dynamic + string import scan).
"""
from __future__ import annotations

import re
from pathlib import Path

_AUTOMATION = Path(__file__).resolve().parents[2] / "automation"

# Modules run DIRECTLY (CLI / scheduled task / CI step), so zero importers is correct
# and expected — they are entrypoints, not orphaned library code.
_ENTRYPOINTS = {
    "ai_cycle_controller",      # the CLI + continuous driver (host/start_controller.ps1)
    "codex_review_gate",        # CI step (.github/workflows/ci.yml)
    "repo_janitor",             # scheduled task "AI Runner Repo Janitor"
    "check_dev_auto_readiness",  # operator CLI
    "prompt_renderer",          # operator CLI
    "ref_catalog_builder",      # operator CLI
}

# Exist but imported by NOTHING in the live path as of the analysis date. Tracked for
# the 5.5 wire-or-delete decision (deletion deferred — needs per-module review).
_DEFERRED_ORPHANS = {
    "failure_classifier",
    "git_adapter",
    "github_client",
    "lock_manager",
    "model_verifier",
    "pm_pack_state_updater",
    "prompt_contract_builder",
    "prompt_generator",
    "prompt_promotion",
    "scorecard_calculator",
    "validation_runner",
}

_IMPORT_RE = re.compile(
    r"from\s+automation\.(\w+)"
    r"|from\s+automation\s+import\s+([\w,\s]+?)(?:\n|$|#)"
    r"|import\s+automation\.(\w+)"
)


def _top_level_modules() -> set[str]:
    return {p.stem for p in _AUTOMATION.glob("*.py") if p.stem != "__init__"}


def _imported_module_names() -> set[str]:
    """Top-level automation module names imported anywhere under automation/ (any depth)."""
    imported: set[str] = set()
    for py in _AUTOMATION.rglob("*.py"):
        text = py.read_text(encoding="utf-8", errors="replace")
        for m in _IMPORT_RE.finditer(text):
            if m.group(1):
                imported.add(m.group(1))
            if m.group(3):
                imported.add(m.group(3))
            if m.group(2):
                for name in m.group(2).split(","):
                    nm = name.strip().split(" as ")[0].strip()
                    if nm and nm.isidentifier():
                        imported.add(nm)
    return imported


def _computed_orphans() -> set[str]:
    modules = _top_level_modules()
    imported = _imported_module_names()
    return {m for m in modules if m not in imported and m not in _ENTRYPOINTS}


def test_no_unaccounted_orphan_core_module():
    unaccounted = _computed_orphans() - _DEFERRED_ORPHANS
    assert not unaccounted, (
        "New orphaned automation/ module(s) with zero importers in the live path: "
        f"{sorted(unaccounted)}.\nWire it into the live loop, delete it, mark it an "
        "ENTRYPOINT (if run directly), or add it to _DEFERRED_ORPHANS with a tracking note."
    )


def test_deferred_orphans_and_entrypoints_still_exist():
    # Keep the allowlists honest: a stale entry (module wired+deleted, or renamed)
    # should be pruned so the guard reflects reality.
    for m in _DEFERRED_ORPHANS | _ENTRYPOINTS:
        assert (_AUTOMATION / f"{m}.py").exists(), (
            f"'{m}' is allowlisted but automation/{m}.py no longer exists — "
            "remove it from the _DEFERRED_ORPHANS/_ENTRYPOINTS set."
        )


def test_wired_core_modules_are_actually_imported():
    # Positive guard: the implementations the live loop DOES use must stay wired.
    imported = _imported_module_names()
    for m in ("pr_builder", "repair_loop", "jira_client", "merge_gate",
              "post_cycle_review", "prompt_validator", "claude_prompt_creator",
              "run_agent_lifecycle", "required_checks"):
        assert m in imported, f"core module '{m}' is no longer imported by the live path"
