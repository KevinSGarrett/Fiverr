from __future__ import annotations

import json
from pathlib import Path

from automation.ref_catalog_builder import OUT_DIR, REPO_ROOT, build_catalogs, verify_catalogs


def test_build_catalogs_writes_expected_catalogs() -> None:
    payloads = build_catalogs()
    names = {str(item["catalog"]) for item in payloads}
    assert "pm_pack_ref" in names
    assert "pm_pack_automation" in names
    assert "docs_architecture" in names
    assert "cycle_reports" in names


def test_verify_catalogs_strict_passes_after_build() -> None:
    build_catalogs()
    ok, issues = verify_catalogs(strict=True)
    assert ok is True
    assert issues == []


def test_project_plan_catalog_has_at_least_80_entries() -> None:
    build_catalogs()
    payload = json.loads(OUT_DIR.joinpath("pm_pack_ref.json").read_text(encoding="utf-8"))
    assert payload["entry_count"] >= 80


def test_dod_catalog_has_10_entries() -> None:
    build_catalogs()
    payload = json.loads(OUT_DIR.joinpath("pm_pack_ref.json").read_text(encoding="utf-8"))
    dod_entries = [entry for entry in payload["entries"] if "dod" in entry.lower()]
    assert len(dod_entries) >= 10


def test_dod_entries_have_non_empty_criteria_lists() -> None:
    build_catalogs()
    payload = json.loads(OUT_DIR.joinpath("pm_pack_ref.json").read_text(encoding="utf-8"))
    dod_entries = [Path(entry) for entry in payload["entries"] if "dod" in entry.lower()][:10]
    assert dod_entries
    for rel_path in dod_entries:
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        bullet_lines = [line for line in text.splitlines() if line.strip().startswith("-")]
        assert bullet_lines
