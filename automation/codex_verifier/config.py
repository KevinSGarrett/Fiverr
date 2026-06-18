"""
config.py -- ICV configuration loader.

ICV-CONFIG-1: Reads PM_Pack/automation/codex_verifier.yml + env overrides.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path("C:/Fiverr/Fiverr")
DEFAULT_CONFIG_PATH = REPO_ROOT / "PM_Pack/automation/codex_verifier.yml"


@dataclass
class ICVConfig:
    enabled: bool = True
    max_attempts: int = 3                 # hard cap on repair loops per agent
    wall_clock_max_minutes: float = 30.0  # hard cap on total ICV time per agent
    openai_model: str = "o3-mini"         # reasoning model for verification
    openai_budget_usd: float = 2.0        # per-agent ICV budget (from overall $10/day cap)
    min_completion_score: float = 0.80    # threshold for VERIFIED_PASS
    deterministic_only_fallback: bool = True  # fall back to det-only if LLM unavailable
    heartbeat_interval_s: float = 30.0
    skip_if_no_commit: bool = False       # if True, skip ICV when agent made no commit
    require_contract: bool = False        # if True, SKIPPED_DISABLED when no contract found
    log_level: str = "INFO"

    # Env var overrides applied in __post_init__
    def __post_init__(self) -> None:
        if os.environ.get("ICV_DISABLED", "").lower() in ("1", "true", "yes"):
            self.enabled = False
        if os.environ.get("ICV_MAX_ATTEMPTS"):
            try:
                self.max_attempts = int(os.environ["ICV_MAX_ATTEMPTS"])
            except ValueError:
                pass
        if os.environ.get("ICV_OPENAI_MODEL"):
            self.openai_model = os.environ["ICV_OPENAI_MODEL"]
        if os.environ.get("PYTEST_CURRENT_TEST"):
            # In test mode: disable LLM calls, cap at 1 attempt
            self.openai_budget_usd = 0.0
            self.max_attempts = 1
            self.deterministic_only_fallback = True


def load_config(config_path: Path | None = None) -> ICVConfig:
    """Load ICV config from YAML file; missing file returns defaults."""
    path = config_path or DEFAULT_CONFIG_PATH
    cfg = ICVConfig()
    if not path.exists():
        return cfg
    try:
        import yaml
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        icv_data = data.get("codex_verifier", data)  # support both nested and flat
        if isinstance(icv_data, dict):
            for key, val in icv_data.items():
                if hasattr(cfg, key):
                    setattr(cfg, key, val)
    except Exception:
        pass  # config errors -> use defaults
    cfg.__post_init__()  # re-apply env overrides
    return cfg
