from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, ValidationError, validate

REPO_ROOT = Path(__file__).resolve().parents[2]
AUTOMATION_SCHEMAS = REPO_ROOT / "automation" / "schemas"
CATALOG_DIR = REPO_ROOT / "PM_Pack" / "automation"


def _load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def test_dod_catalog_validates_against_schema() -> None:
    schema = _load_json(AUTOMATION_SCHEMAS / "dod_catalog.schema.json")
    instance = _load_json(CATALOG_DIR / "dod_catalog.json")
    validate(instance=instance, schema=schema)


def test_project_plan_catalog_validates() -> None:
    schema = _load_json(AUTOMATION_SCHEMAS / "project_plan_catalog.schema.json")
    instance = _load_json(CATALOG_DIR / "project_plan_catalog.json")
    validate(instance=instance, schema=schema)


def test_todo_epic_catalog_validates() -> None:
    schema = _load_json(AUTOMATION_SCHEMAS / "todo_epic_catalog.schema.json")
    instance = _load_json(CATALOG_DIR / "todo_epic_catalog.json")
    validate(instance=instance, schema=schema)


def test_github_governance_catalog_validates() -> None:
    schema = _load_json(AUTOMATION_SCHEMAS / "github_governance_catalog.schema.json")
    instance = _load_json(CATALOG_DIR / "github_governance_catalog.json")
    validate(instance=instance, schema=schema)


def test_all_catalog_schemas_are_valid_json_schema() -> None:
    for schema_name in [
        "dod_catalog.schema.json",
        "project_plan_catalog.schema.json",
        "todo_epic_catalog.schema.json",
        "github_governance_catalog.schema.json",
    ]:
        Draft7Validator.check_schema(_load_json(AUTOMATION_SCHEMAS / schema_name))


def test_dod_catalog_invalid_item_fails_schema() -> None:
    schema = _load_json(AUTOMATION_SCHEMAS / "dod_catalog.schema.json")
    invalid_instance = [
        {
            "filename": "DOD_EPIC_11.md",
            "source_path": "PM_Pack/ref/dod/DOD_EPIC_11.md",
            "epic_id": "EPIC-11",
        }
    ]
    with pytest.raises(ValidationError):
        validate(instance=invalid_instance, schema=schema)
