from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from automation import ref_catalog_builder


def test_build_project_plan_catalog_returns_entries(tmp_path: Path) -> None:
    ref_dir = tmp_path / "PM_Pack/ref/project_plan/01_vision"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "PRODUCT_VISION.md").write_text(
        "# Product Vision\nSCRUM-1\nEPIC_01\nS1.1\nsrc/models/base.py\n",
        encoding="utf-8",
    )
    catalog = ref_catalog_builder.build_project_plan_catalog(
        ref_dir=tmp_path / "PM_Pack/ref",
        output_path=tmp_path / "project_plan_catalog.json",
    )
    assert len(catalog["entries"]) == 1


def test_build_dod_catalog_has_10_entries(tmp_path: Path) -> None:
    catalog = ref_catalog_builder.build_dod_catalog(
        output_path=tmp_path / "dod_catalog.json"
    )
    assert len(catalog["entries"]) == 10


def test_build_todo_catalog_has_11_entries(tmp_path: Path) -> None:
    catalog = ref_catalog_builder.build_todo_catalog(
        output_path=tmp_path / "todo_epic_catalog.json"
    )
    assert len(catalog["entries"]) == 11


def test_catalog_entries_have_required_fields(tmp_path: Path) -> None:
    project_dir = tmp_path / "PM_Pack/ref/project_plan"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "sample.md").write_text("# Sample\n", encoding="utf-8")
    catalog = ref_catalog_builder.build_project_plan_catalog(
        ref_dir=tmp_path / "PM_Pack/ref",
        output_path=tmp_path / "project_plan_catalog.json",
    )
    entry = catalog["entries"][0]
    assert "source_path" in entry
    assert "title" in entry


def test_verify_fails_when_catalog_missing(tmp_path: Path) -> None:
    assert ref_catalog_builder.verify(strict=True, catalog_dir=tmp_path) is False


def test_verify_fails_when_catalog_stale(tmp_path: Path) -> None:
    stale_payload = {
        "generated_at": (datetime.now(UTC) - timedelta(hours=49)).isoformat(),
        "entries": [{} for _ in range(80)],
    }
    (tmp_path / "project_plan_catalog.json").write_text(json.dumps(stale_payload), encoding="utf-8")
    stale_payload["entries"] = [{} for _ in range(10)]
    (tmp_path / "dod_catalog.json").write_text(json.dumps(stale_payload), encoding="utf-8")
    (tmp_path / "todo_epic_catalog.json").write_text(json.dumps(stale_payload), encoding="utf-8")
    stale_payload["entries"] = [{} for _ in range(40)]
    (tmp_path / "github_governance_catalog.json").write_text(json.dumps(stale_payload), encoding="utf-8")
    assert ref_catalog_builder.verify(strict=False, catalog_dir=tmp_path) is False


def test_jira_keys_extracted_from_project_plan_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "PM_Pack/ref/project_plan"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "sample.md").write_text("# Sample\nSCRUM-123\n", encoding="utf-8")
    catalog = ref_catalog_builder.build_project_plan_catalog(
        ref_dir=tmp_path / "PM_Pack/ref",
        output_path=tmp_path / "project_plan_catalog.json",
    )
    assert catalog["entries"][0]["jira_keys"] == ["SCRUM-123"]


def test_zip_files_handled_as_archive_type(tmp_path: Path) -> None:
    project_dir = tmp_path / "PM_Pack/ref/project_plan"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project_plan.zip").write_bytes(b"PK\x03\x04")
    catalog = ref_catalog_builder.build_project_plan_catalog(
        ref_dir=tmp_path / "PM_Pack/ref",
        output_path=tmp_path / "project_plan_catalog.json",
    )
    assert catalog["entries"][0]["type"] == "archive"


def test_build_all_catalogs_returns_counts(tmp_path: Path) -> None:
    ref_root = tmp_path / "PM_Pack/ref"
    (ref_root / "project_plan").mkdir(parents=True, exist_ok=True)
    (ref_root / "dod").mkdir(parents=True, exist_ok=True)
    (ref_root / "todo").mkdir(parents=True, exist_ok=True)
    (ref_root / "github/01_branching").mkdir(parents=True, exist_ok=True)
    (ref_root / "project_plan/sample.md").write_text("# One\n", encoding="utf-8")
    (ref_root / "dod/DOD_EPIC_01.md").write_text("# DOD\n## Criteria\n- x\n", encoding="utf-8")
    (ref_root / "todo/EPIC_01_A.md").write_text("- [ ] one\n- [x] two\n", encoding="utf-8")
    (ref_root / "github/01_branching/RULES.md").write_text("# Rules\n", encoding="utf-8")
    counts = ref_catalog_builder.build_all_catalogs(
        ref_dir=ref_root,
        catalog_dir=tmp_path / "PM_Pack/automation",
    )
    assert counts["project_plan_catalog"] == 1
    assert counts["dod_catalog"] == 1
    assert counts["todo_epic_catalog"] == 1
    assert counts["github_governance_catalog"] == 1


def test_build_dod_catalog_extracts_criteria_and_validation_commands(tmp_path: Path) -> None:
    dod_dir = tmp_path / "PM_Pack/ref/dod"
    dod_dir.mkdir(parents=True, exist_ok=True)
    (dod_dir / "DOD_EPIC_07.md").write_text(
        "# Epic Seven\n## Definition of Done\n- ship feature\n## Validation\n```bash\npytest tests/unit/\nruff check automation/\npython -m json.tool payload.json\n```\n",
        encoding="utf-8",
    )
    catalog = ref_catalog_builder.build_dod_catalog(
        ref_dir=tmp_path / "PM_Pack/ref",
        output_path=tmp_path / "dod_catalog.json",
    )
    entry = catalog["entries"][0]
    assert entry["epic_id"] == "EPIC_07"
    assert entry["criteria"] == ["ship feature"]
    assert entry["validation_commands"] == [
        "pytest tests/unit/",
        "ruff check automation/",
        "python -m json.tool payload.json",
    ]


def test_build_github_catalog_extracts_category_and_summary(tmp_path: Path) -> None:
    github_dir = tmp_path / "PM_Pack/ref/github/02_pr_policy"
    github_dir.mkdir(parents=True, exist_ok=True)
    (github_dir / "PR_POLICY.md").write_text("# PR Policy\nBody", encoding="utf-8")
    catalog = ref_catalog_builder.build_github_catalog(
        ref_dir=tmp_path / "PM_Pack/ref",
        output_path=tmp_path / "github_catalog.json",
    )
    assert catalog["entries"][0]["category"] == "02_pr_policy"
    assert catalog["entries"][0]["title"] == "PR Policy"
    assert catalog["entries"][0]["summary"].startswith("# PR Policy")


def test_verify_fails_for_bad_json_and_shape(tmp_path: Path) -> None:
    (tmp_path / "project_plan_catalog.json").write_text("{bad", encoding="utf-8")
    assert ref_catalog_builder.verify(catalog_dir=tmp_path) is False

    payload = {"generated_at": "2026-06-13T00:00:00+00:00", "entries": "bad"}
    (tmp_path / "project_plan_catalog.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "dod_catalog.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "todo_epic_catalog.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "github_governance_catalog.json").write_text(json.dumps(payload), encoding="utf-8")
    assert ref_catalog_builder.verify(catalog_dir=tmp_path) is False


def test_helper_extract_and_parse_functions_cover_edges() -> None:
    assert ref_catalog_builder._extract_title("body only") == ""
    assert ref_catalog_builder._extract_wave("no wave") is None
    assert ref_catalog_builder._parse_iso(None) is None
    assert ref_catalog_builder._parse_iso("bad-date") is None
    naive = ref_catalog_builder._parse_iso("2026-06-13T12:00:00")
    assert naive is not None


def test_to_repo_relative_falls_back_for_external_path() -> None:
    external = Path("D:/external/file.md")
    assert ref_catalog_builder._to_repo_relative(external).endswith("file.md")
