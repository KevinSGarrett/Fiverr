from __future__ import annotations

from pathlib import Path


def test_jira_client_create_issue_payload_compat(monkeypatch):
    from automation import jira_client

    captured = {}

    def fake_create_issue(project_key, summary, description, issue_type="Bug", labels=None):
        captured.update(
            {
                "project_key": project_key,
                "summary": summary,
                "description": description,
                "issue_type": issue_type,
                "labels": labels,
            }
        )
        return {"key": "SCRUM-1"}

    monkeypatch.setattr(jira_client, "create_issue", fake_create_issue)
    client = jira_client.JiraClient()
    payload = {
        "summary": "Stage 3 smoke story",
        "issuetype": {"name": "Story"},
        "project": {"key": "SCRUM"},
    }
    result = client.create_issue(payload)

    assert result["key"] == "SCRUM-1"
    assert captured["project_key"] == "SCRUM"
    assert captured["issue_type"] == "Story"


def test_merge_gate_check_full_dod_shape():
    from automation.merge_gate import MergeGate

    result = MergeGate().check_full_dod(77)

    assert result["cycle"] == 77
    assert "passed" in result
    assert "checks" in result


def test_post_cycle_bundle_compat_functions():
    from automation.post_cycle_review import (
        generate_post_cycle_github_bundle,
        generate_post_cycle_jira_bundle,
    )

    class FakeJiraClient:
        def board_inventory(self, project_key="SCRUM"):
            return {"total": 7}

    github_bundle = generate_post_cycle_github_bundle(77, "cycle/077/integration", object())
    jira_bundle = generate_post_cycle_jira_bundle(77, FakeJiraClient())

    assert github_bundle["cycle"] == 77
    assert jira_bundle["inventory_total"] == 7


def test_repairloop_handle_writes_incident(monkeypatch, tmp_path):
    import automation.repairloop as repairloop
    from automation.repairloop import RepairLoop

    incidents_dir = tmp_path / "incidents"
    monkeypatch.setattr(repairloop, "REPORTS_DIR", incidents_dir)
    monkeypatch.setattr(repairloop, "notify_blocked", lambda **_kwargs: None)

    trigger = tmp_path / "trigger.json"
    trigger.write_text('{"trigger":"LINT_FAIL","module":"x","cycle":77}', encoding="utf-8")

    result = RepairLoop().handle(str(trigger))

    assert result["status"] == "PLANNED"
    assert Path(result["incident_path"]).exists()
