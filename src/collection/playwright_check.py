"""Safe Playwright availability checks without side effects."""

import importlib

INSTALL_COMMAND = "playwright install chromium"


def check_playwright_chromium_available() -> dict[str, object]:
    """Report whether Playwright is importable for local Chromium use.

    This helper never installs browsers, runs shell commands, or launches a browser.
    It only returns operator guidance.
    """
    try:
        importlib.import_module("playwright")
    except Exception as exc:  # pragma: no cover - exercised via monkeypatch in tests
        return {
            "available": False,
            "needs_install": True,
            "command": INSTALL_COMMAND,
            "message": (
                "Playwright is not importable in this environment. "
                f"Run `{INSTALL_COMMAND}` after installing dependencies. "
                f"Import error: {exc.__class__.__name__}"
            ),
        }

    return {
        "available": True,
        "needs_install": False,
        "command": INSTALL_COMMAND,
        "message": "Playwright package is importable. Chromium install can be verified by the operator.",
    }
