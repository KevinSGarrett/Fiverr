"""ITEM D-7 — brain-check content validation + audit cross-source cycle agreement.

brain-check gates `plan-cycle --live`; before this, it was existence-only (a file
that exists but is empty/stub/unparseable still PASSed) and the consistency audit
silently reported consensus when cycle sources were off by one (82 != 83). A false
green here would poison the milestone observation.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from automation import pm_pack_consistency_audit as audit
from automation import pm_pack_loader as loader


# ── _brain_file_content_ok (pure) ─────────────────────────────────────────────
def test_content_ok_real_file(tmp_path):
    p = tmp_path / "doc.md"
    p.write_text("# Real brain doc\nwith genuine content.\n", encoding="utf-8")
    ok, _ = loader._brain_file_content_ok(p)
    assert ok is True


def test_content_ok_empty_fails(tmp_path):
    p = tmp_path / "empty.md"
    p.write_text("   \n\t\n", encoding="utf-8")
    ok, why = loader._brain_file_content_ok(p)
    assert ok is False and "empty" in why


def test_content_ok_stub_fails(tmp_path):
    p = tmp_path / "stub.md"
    p.write_text("# Header\n[STUB - populate later]\n", encoding="utf-8")
    ok, why = loader._brain_file_content_ok(p)
    assert ok is False and "stub" in why.lower()


def test_content_ok_invalid_json_fails(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("{not valid json,,,", encoding="utf-8")
    ok, why = loader._brain_file_content_ok(p)
    assert ok is False and "JSON" in why


def test_content_ok_invalid_yaml_fails(tmp_path):
    p = tmp_path / "x.yml"
    p.write_text("a:\n  - b\n  c: : :\n", encoding="utf-8")
    ok, why = loader._brain_file_content_ok(p)
    assert ok is False and "YAML" in why


def test_content_ok_valid_json_passes(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"a": 1}), encoding="utf-8")
    assert loader._brain_file_content_ok(p)[0] is True


def test_content_ok_binary_empty_fails(tmp_path):
    p = tmp_path / "b.db"
    p.write_bytes(b"")
    assert loader._brain_file_content_ok(p)[0] is False


def test_content_ok_binary_nonempty_passes(tmp_path):
    p = tmp_path / "b.db"
    p.write_bytes(b"\x00\x01\x02")
    assert loader._brain_file_content_ok(p)[0] is True


# ── brain_check end-to-end: empty load_order file FAILS (not PASS) ─────────────
def _seed_registry(repo: Path, files: dict[str, str]):
    reg = repo / "PM_Pack/automation/BRAIN_REGISTRY.yml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    rels = []
    for rel, content in files.items():
        f = repo / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
        rels.append(rel)
    reg.write_text(yaml.safe_dump({"load_order": {"core": rels}}), encoding="utf-8")


def test_brain_check_flags_empty_load_order_file(tmp_path):
    _seed_registry(tmp_path, {
        "PM_Pack/good.md": "# Real content here\n",
        "PM_Pack/bad.md": "  \n",  # empty -> must FAIL
    })
    res = loader.brain_check(tmp_path)
    assert any("good.md" in p for p in res.passed)
    assert any("bad.md" in f and "INVALID" in f for f in res.failed)
    assert res.ok is False  # an invalid brain file fails the whole check


def test_brain_check_passes_when_all_real(tmp_path):
    # Content validation must PASS real files (res.ok also depends on other
    # full-brain checks beyond D-7, so assert the content-validation specifics).
    _seed_registry(tmp_path, {
        "PM_Pack/a.md": "# A real\n", "PM_Pack/b.md": "# B real\n",
    })
    res = loader.brain_check(tmp_path)
    assert any("a.md" in p for p in res.passed)
    assert any("b.md" in p for p in res.passed)
    assert not any("INVALID" in f for f in res.failed)  # no content-validation failure


# ── audit: cross-source cycle agreement (no false consensus) ──────────────────
def _seed_audit(repo: Path, runner: Path, policy_cycle, ctrl_cycle):
    snap = repo / "PM_Pack/automation/current_policy_snapshot.json"
    snap.parent.mkdir(parents=True, exist_ok=True)
    snap.write_text(json.dumps({"cycle_current": policy_cycle,
                                "last_completed_cycle": policy_cycle}), encoding="utf-8")
    cs = runner / "state/controller_state.json"
    cs.parent.mkdir(parents=True, exist_ok=True)
    cs.write_text(json.dumps({"active_cycle": ctrl_cycle, "status": "IDLE"}), encoding="utf-8")


def test_audit_offbyone_is_flagged_not_silent_consensus(tmp_path):
    repo, runner = tmp_path / "repo", tmp_path / "runner"
    _seed_audit(repo, runner, policy_cycle=82, ctrl_cycle=83)
    res = audit.run_audit(repo_root=repo, runner_root=runner)
    assert any("CYCLESOURCESDISAGREE" in w for w in res.warnings), res.warnings
    # off-by-one is a warning, not a hard block
    assert not any(c.code == "CYCLESOURCESDISAGREE" for c in res.conflicts)


def test_audit_large_cycle_gap_blocks(tmp_path):
    repo, runner = tmp_path / "repo", tmp_path / "runner"
    _seed_audit(repo, runner, policy_cycle=82, ctrl_cycle=86)  # spread 4 > 2
    res = audit.run_audit(repo_root=repo, runner_root=runner)
    assert res.passed is False
    assert any(c.code == "CYCLESOURCESDISAGREE" and c.severity == "BLOCKING"
               for c in res.conflicts)


def test_audit_agreement_no_disagree_warning(tmp_path):
    repo, runner = tmp_path / "repo", tmp_path / "runner"
    _seed_audit(repo, runner, policy_cycle=83, ctrl_cycle=83)
    res = audit.run_audit(repo_root=repo, runner_root=runner)
    assert not any("CYCLESOURCESDISAGREE" in w for w in res.warnings)
    assert "All state files agree" in res.summary()  # genuine consensus


def test_audit_summary_does_not_advertise_consensus_on_warning(tmp_path):
    # Codex P2: an off-by-one passes (non-blocking) but the summary must NOT say
    # "all agree" — it must surface the non-consensus so plan-cycle isn't misled.
    repo, runner = tmp_path / "repo", tmp_path / "runner"
    _seed_audit(repo, runner, policy_cycle=82, ctrl_cycle=83)
    res = audit.run_audit(repo_root=repo, runner_root=runner)
    s = res.summary()
    assert "All state files agree" not in s
    assert "do NOT fully agree" in s
