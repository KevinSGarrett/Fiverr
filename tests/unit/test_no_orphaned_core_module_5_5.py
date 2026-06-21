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

import ast
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

def _top_level_modules() -> set[str]:
    return {p.stem for p in _AUTOMATION.glob("*.py") if p.stem != "__init__"}


def _imported_module_names() -> set[str]:
    """Top-level automation module names REALLY imported anywhere under automation/.

    Codex review (#128): parse the AST, not raw text — the repo keeps prompt snippets
    containing `from automation.X import ...` inside string/docstring bodies, and a
    raw-text scan would count those as imports, letting a real orphan hide behind a
    text mention. ast.walk also catches deferred (function-level) imports. Relative
    intra-package imports (`from . import X`, `from .X import ...`) are handled too.
    """
    imported: set[str] = set()
    for py in _AUTOMATION.rglob("*.py"):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="replace"),
                             filename=str(py))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if node.level:  # relative: from . import X  /  from .X[.sub] import ...
                    if mod:
                        imported.add(mod.split(".", 1)[0])
                    else:
                        for alias in node.names:
                            imported.add(alias.name)
                elif mod == "automation":           # from automation import X, Y
                    for alias in node.names:
                        imported.add(alias.name)
                elif mod.startswith("automation."):  # from automation.X[.sub] import ...
                    imported.add(mod.split(".", 2)[1])
            elif isinstance(node, ast.Import):
                for alias in node.names:             # import automation.X[.sub]
                    if alias.name.startswith("automation."):
                        imported.add(alias.name.split(".", 2)[1])
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


def test_allowlisted_modules_still_exist():
    # Keep the allowlists honest: a stale entry (module deleted or renamed) must be pruned.
    for m in _DEFERRED_ORPHANS | _ENTRYPOINTS:
        assert (_AUTOMATION / f"{m}.py").exists(), (
            f"'{m}' is allowlisted but automation/{m}.py no longer exists — "
            "remove it from the _DEFERRED_ORPHANS/_ENTRYPOINTS set."
        )


def test_deferred_orphans_are_still_orphaned():
    # Codex review (#128): force pruning. If a deferred module gets WIRED (a real
    # import added), it drops out of _computed_orphans() and this fails — requiring it
    # to be removed from _DEFERRED_ORPHANS. That prevents a stale allowlist from hiding
    # a later re-orphaning. Combined with the no-unaccounted test, this pins
    # _DEFERRED_ORPHANS == _computed_orphans() exactly (no drift in either direction).
    now_wired = sorted(_DEFERRED_ORPHANS - _computed_orphans())
    assert not now_wired, (
        f"Deferred orphan(s) are now wired into the live path: {now_wired}. "
        "Remove them from _DEFERRED_ORPHANS (they are accounted for by a real import)."
    )


def test_wired_core_modules_are_actually_imported():
    # Positive guard: the implementations the live loop DOES use must stay wired.
    imported = _imported_module_names()
    for m in ("pr_builder", "repair_loop", "jira_client", "merge_gate",
              "post_cycle_review", "prompt_validator", "claude_prompt_creator",
              "run_agent_lifecycle", "required_checks"):
        assert m in imported, f"core module '{m}' is no longer imported by the live path"
