from __future__ import annotations

from pathlib import Path

import yaml


def test_no_advisory_confirm_mode_in_policy() -> None:
    policy_path = Path("C:/Fiverr/Fiverr/PM_Pack/automation/provider_policy.yml")
    payload = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    global_rules = payload.get("global_rules", {})
    assert not bool(global_rules.get("advisory_confirm_mode", False))


def test_no_advisory_only_routing_in_policy() -> None:
    policy_path = Path("C:/Fiverr/Fiverr/PM_Pack/automation/provider_policy.yml")
    payload = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    global_rules = payload.get("global_rules", {})
    assert bool(global_rules.get("advisory_only_provider_routing", True)) is False


def test_no_input_calls_in_lifecycle() -> None:
    source = Path("C:/Fiverr/Fiverr/automation/run_agent_lifecycle.py").read_text(encoding="utf-8")
    assert "input(" not in source


def test_no_human_pause_in_controller() -> None:
    source = Path("C:/Fiverr/Fiverr/automation/ai_cycle_controller.py").read_text(encoding="utf-8")
    assert "contact Kevin" not in source


def test_post_cycle_review_has_no_blocking_exit() -> None:
    source = Path("C:/Fiverr/Fiverr/automation/post_cycle_review.py").read_text(encoding="utf-8")
    assert "sys.exit(1)" not in source
    assert "human required" not in source.lower()
