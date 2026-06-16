"""Codex CLI subscription adapter for autonomous runner dispatch."""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ProviderRunResult:
    provider: str
    agent: str
    cycle: str
    status: str
    agent_complete: bool
    duration_seconds: float
    run_dir: Path
    output_excerpt: str
    errors: list[str]


class AdapterBlockedError(RuntimeError):
    """Raised when preflight checks block codex subscription dispatch."""


class CodexSubscriptionAdapter:
    """Run validated prompts through Codex CLI authenticated by ChatGPT subscription."""

    CLI_COMMAND = "codex"
    STATE_PATH = Path(r"C:\AI_Runner\state\codex_subscription_state.json")

    def preflight(self, prompt_path: Path, cycle: str, agent: str) -> None:
        _ = cycle, agent
        if os.environ.get("OPENAI_API_KEY"):
            raise AdapterBlockedError(
                "OPENAI_API_KEY is set. Codex subscription lane requires ChatGPT subscription login."
            )
        version_probe = subprocess.run(
            [self.CLI_COMMAND, "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if version_probe.returncode != 0:
            raise AdapterBlockedError(
                "codex CLI not found. Install: npm install -g @openai/codex, then run codex login."
            )
        if not self.STATE_PATH.exists():
            raise AdapterBlockedError(f"codex_subscription_state.json missing at {self.STATE_PATH}.")
        state = json.loads(self.STATE_PATH.read_text(encoding="utf-8"))
        if state.get("billing_mode") != "chatgpt_subscription_only":
            raise AdapterBlockedError(
                f"codex billing_mode is {state.get('billing_mode')!r}, expected chatgpt_subscription_only."
            )
        if state.get("api_key_present", True):
            raise AdapterBlockedError("codex subscription state indicates api_key_present=true.")
        normalized_prompt = str(prompt_path).replace("\\", "/").lower()
        if "/drafts/" in normalized_prompt or "drafts" in normalized_prompt:
            raise AdapterBlockedError(f"Codex lane rejected draft prompt path: {prompt_path}")

    def run_agent(self, prompt_path: Path, cycle: str, agent: str) -> ProviderRunResult:
        self.preflight(prompt_path, cycle, agent)
        run_dir = Path(fr"C:\AI_Runner\runs\CYCLE_{cycle}\codex_{agent}")
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt_copy = run_dir / f"CODEX_{cycle}_{agent}_PROMPT.txt"
        prompt_copy.write_text(prompt_path.read_text(encoding="utf-8"), encoding="utf-8")

        start = time.time()
        errors: list[str] = []
        output = ""
        try:
            result = subprocess.run(
                [self.CLI_COMMAND, "--file", str(prompt_copy)],
                cwd=Path(r"C:\Fiverr\Fiverr"),
                capture_output=True,
                text=True,
                timeout=3600,
                check=False,
            )
            output = (result.stdout or "") + (result.stderr or "")
        except subprocess.TimeoutExpired:
            output = "TIMEOUT after 3600s"
            errors.append("Codex CLI timed out after 3600 seconds")
        duration = time.time() - start

        (run_dir / "codex_output.txt").write_text(output, encoding="utf-8")
        agent_complete = "AGENT_COMPLETE" in output
        if not agent_complete:
            errors.append("AGENT_COMPLETE not found in output")
        status = "SUCCESS" if agent_complete else "FAIL"
        return ProviderRunResult(
            provider="codex_subscription",
            agent=agent,
            cycle=cycle,
            status=status,
            agent_complete=agent_complete,
            duration_seconds=duration,
            run_dir=run_dir,
            output_excerpt=output[:500],
            errors=errors,
        )
