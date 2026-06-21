"""Item 5.4 (repo hygiene): correct `git status --porcelain` path parsing.

The previous parse `line.strip().lstrip("?! MAD")` was a character-SET strip that
ate leading filename characters in {?,!,space,M,A,D} (e.g. " M Makefile" ->
"akefile"), and the upstream `.stdout.strip()` destroyed the first line's leading
status column. Either could misclassify a runtime-artifact path as a real dirty
change -> spurious BLOCKED_DIRTY_REPO that stalls the autonomous loop. These tests
pin the fixed-width porcelain-v1 parse (path begins at column 3) and the
artifact-prefix filter that depends on it.
"""
from __future__ import annotations

from automation.ai_cycle_controller import _porcelain_status_path

_ARTIFACT_PREFIXES = (
    "PM_Pack/automation/post_cycle_reviews/",
    "PM_Pack/automation/runs/",
    "PM_Pack/automation/prompts/drafts/",
)


def test_path_starts_at_column_3_not_charset_strip():
    # The headline bug: a filename whose first char is in {M,A,D} must survive.
    assert _porcelain_status_path(" M Makefile") == "Makefile"
    assert _porcelain_status_path(" D Data.txt") == "Data.txt"
    assert _porcelain_status_path("A  Adapter.py") == "Adapter.py"
    assert _porcelain_status_path("MM Models.py") == "Models.py"


def test_all_status_codes_yield_the_path():
    assert _porcelain_status_path("?? new_file.py") == "new_file.py"
    assert _porcelain_status_path(" M src/pipeline/collector.py") == "src/pipeline/collector.py"
    assert _porcelain_status_path("A  tests/unit/test_x.py") == "tests/unit/test_x.py"
    assert _porcelain_status_path(" D docs/old.md") == "docs/old.md"
    assert _porcelain_status_path("!! ignored.log") == "ignored.log"


def test_rename_returns_destination_path():
    assert _porcelain_status_path("R  old/name.py -> new/name.py") == "new/name.py"
    assert _porcelain_status_path("C  a.py -> b.py") == "b.py"


def test_empty_and_short_lines():
    assert _porcelain_status_path("") == ""
    assert _porcelain_status_path("M") == ""
    assert _porcelain_status_path(" M ") == ""


def test_artifact_prefix_filter_with_helper():
    # The dispatch-gate logic: artifact-path lines are filtered out; real changes
    # remain and would block. Verify both directions with realistic porcelain lines
    # (including the leading-space status column the old `.strip()` corrupted).
    porcelain = (
        " M PM_Pack/automation/runs/CYCLE_099/run.json\n"   # artifact -> ignored
        "?? PM_Pack/automation/post_cycle_reviews/r.md\n"    # artifact -> ignored
        " M Makefile\n"                                       # real change -> blocks
        "A  src/pipeline/new.py\n"                            # real change -> blocks
    )
    dirty = [
        line for line in porcelain.splitlines()
        if line.strip() and not any(
            _porcelain_status_path(line).startswith(p) for p in _ARTIFACT_PREFIXES
        )
    ]
    paths = [_porcelain_status_path(line) for line in dirty]
    assert paths == ["Makefile", "src/pipeline/new.py"]
    # The artifact lines did NOT leak into the dirty set (no spurious block).
    assert not any("runs/" in p or "post_cycle_reviews/" in p for p in paths)
