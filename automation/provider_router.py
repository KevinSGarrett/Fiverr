"""Provider router for policy-driven provider selection and decision artifacts."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from automation.provider_health import ProviderHealth
from automation.provider_task_classifier import classify

POLICY_PATH = Path("PM_Pack/automation/provider_policy.yml")
RUNNER_ROUTER_CONFIG_PATH = Path("C:/AI_Runner/config/provider_router.yaml")
DECISION_DIR = Path("PM_Pack/automation/provider_decisions")


class PolicyLoadError(Exception):
    pass


class ProviderBlockedError(Exception):
    pass


class PolicyViolation(Exception):
    pass


@dataclass(frozen=True)
class ProviderDecision:
    provider: str
    task_type: str
    reason: str
    billing_mode: str
    estimated_cost_usd: float
    policy_ref: str
    decided_at: str


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    issues: list[str]


@dataclass
class ProviderRunResult:
    status: str
    provider: str
    started_at: str | None
    completed_at: str | None
    files_changed: list[str]
    validation_required: bool
    error_message: str | None
    decision_artifact_path: str | None

    @property
    def startedat(self) -> str | None:
        return self.started_at

    @property
    def completedat(self) -> str | None:
        return self.completed_at

    @property
    def fileschanged(self) -> list[str]:
        return self.files_changed

    @property
    def validationrequired(self) -> bool:
        return self.validation_required

    @property
    def errormessage(self) -> str | None:
        return self.error_message

    @property
    def decisionartifactpath(self) -> str | None:
        return self.decision_artifact_path


class ProviderRouter:
    """Policy-aware provider router."""

    def __init__(
        self,
        policy_path: Path | None = None,
        runner_config_path: Path | None = None,
    ) -> None:
        self.policy_path = policy_path or POLICY_PATH
        self.runner_config_path = runner_config_path or RUNNER_ROUTER_CONFIG_PATH
        self.policy: dict[str, Any] | None = None
        self.runner_config: dict[str, Any] = {}
        self.provider_health = ProviderHealth()
        self.advisory_only_mode = True
        self._load_runner_config()
        self._load_policy()

    def _load_runner_config(self) -> None:
        if not self.runner_config_path.exists():
            self.runner_config = {}
            return
        payload = yaml.safe_load(self.runner_config_path.read_text(encoding="utf-8"))
        self.runner_config = payload if isinstance(payload, dict) else {}

    def _load_policy(self) -> None:
        if not self.policy_path.exists():
            self.policy = None
            return
        try:
            payload = yaml.safe_load(self.policy_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PolicyLoadError(f"Malformed provider policy YAML: {exc}") from exc
        if not isinstance(payload, dict):
            raise PolicyLoadError("Malformed provider policy YAML: expected mapping")
        if not self._has_minimum_structure(payload):
            raise PolicyLoadError(
                "Malformed provider policy YAML: providers/routes/global_rules are required"
            )
        self.policy = payload
        global_rules = payload.get("global_rules", {})
        self.advisory_only_mode = bool(global_rules.get("advisory_only_provider_routing", True))

    def _has_minimum_structure(self, payload: dict[str, Any]) -> bool:
        return (
            isinstance(payload.get("providers"), dict)
            and isinstance(payload.get("routes"), dict)
            and isinstance(payload.get("global_rules"), dict)
        )

    def _require_policy(self) -> dict[str, Any]:
        if self.policy is None:
            raise PolicyLoadError("PROVIDER_POLICY_MISSING: cannot route without policy")
        return self.policy

    def _normalize_task_type(self, task_type: str) -> str:
        return task_type.strip().lower().replace("-", "_")

    def _normalize_provider(self, provider: str) -> str:
        return provider.strip().lower().replace("-", "_")

    def _provider_for_decision(self, provider: str) -> str:
        mapping = {
            "cursor_cli": "cursorcli",
            "claude_subscription": "claudesubscription",
            "openai_api": "openaiapi",
            "codex_subscription": "codexsubscription",
            "deterministic_controller": "deterministiccontroller",
            "deterministic_prompt_factory": "deterministicpromptfactory",
            "deterministic_validator": "deterministicvalidator",
            "chatgpt_browser": "chatgptbrowser",
            "chatgpt_browser_automation": "chatgptbrowser",
        }
        normalized = self._normalize_provider(provider)
        return mapping.get(normalized, normalized.replace("_", ""))

    def _provider_for_health(self, provider: str) -> str:
        mapping = {
            "cursorcli": "cursorcli",
            "claudesubscription": "claudesubscription",
            "openaiapi": "openaiapi",
            "codexsubscription": "codexsubscription",
        }
        return mapping.get(self._provider_for_decision(provider), "")

    def _provider_billing_mode(self, provider: str) -> str:
        policy = self._require_policy()
        providers = policy.get("providers", {})
        normalized = self._normalize_provider(provider)
        if isinstance(providers, dict) and normalized in providers and isinstance(providers[normalized], dict):
            return str(providers[normalized].get("billing_mode", "unknown"))
        deterministic = {
            "deterministic_controller": "deterministic",
            "deterministic_prompt_factory": "deterministic",
            "deterministic_validator": "deterministic",
        }
        return deterministic.get(normalized, "unknown")

    def get_primary_route(self, task_type: str) -> str:
        normalized_task = self._normalize_task_type(task_type)
        policy = self._require_policy()
        routes = policy.get("routes", {})
        if not isinstance(routes, dict):
            raise PolicyLoadError("PROVIDER_POLICY_MISSING: cannot route without policy")
        classification = classify(normalized_task)
        route = routes.get(normalized_task, classification.primary_route)
        return str(route)

    def getprimaryroute(self, tasktype: str) -> str:
        return self.get_primary_route(tasktype)

    def select_provider(self, task_type: str, cycle: str = "", agent: str = "") -> ProviderDecision:
        _ = cycle, agent
        self._require_policy()
        normalized_task = self._normalize_task_type(task_type)
        classification = classify(normalized_task)
        route_provider = self.get_primary_route(normalized_task)
        provider_decision_value = self._provider_for_decision(route_provider)

        if (
            provider_decision_value == "chatgptbrowser"
            or normalized_task == "chatgpt_browser_automation"
            or normalized_task == "chatgptbrowserautomation"
        ):
            raise PolicyViolation(
                "NO_BROWSER_AUTOMATION_CHATGPT: provider_policy.yml "
                "no_browser_automation_chatgpt=true"
            )

        if (
            provider_decision_value == "claudesubscription"
            and normalized_task in {"implementation", "repair", "testgeneration", "test_generation"}
        ):
            raise PolicyViolation("CLAUDE_SUBSCRIPTION_CODE_IMPLEMENTATION_BLOCKED")

        health_provider = self._provider_for_health(route_provider)
        health_status = "UNKNOWN"
        if health_provider:
            health_status = self.provider_health.get_status(health_provider)

        reason = (
            f"classified={classification.task_type};primary={classification.primary_route};"
            f"route={route_provider};health={health_status}"
        )
        if self.advisory_only_mode and provider_decision_value not in {
            "deterministiccontroller",
            "deterministicpromptfactory",
            "deterministicvalidator",
        }:
            reason = "ADVISORY_ONLY"

        return ProviderDecision(
            provider=provider_decision_value,
            task_type=normalized_task,
            reason=reason,
            billing_mode=self._provider_billing_mode(route_provider),
            estimated_cost_usd=0.0,
            policy_ref=f"{self.policy_path}",
            decided_at=datetime.now(UTC).isoformat(),
        )

    def selectprovider(self, tasktype: str, cycle: str = "", agent: str = "") -> ProviderDecision:
        return self.select_provider(tasktype, cycle=cycle, agent=agent)

    def write_decision_artifact(self, decision: ProviderDecision, cycle: str = "") -> Path:
        DECISION_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:8]
        path = DECISION_DIR / f"PROVIDER_DECISION_{ts}_{short_id}.json"
        payload = {
            "decisionid": str(uuid.uuid4()),
            "cycle": (cycle or "000").zfill(3),
            "tasktype": decision.task_type,
            "selectedprovider": decision.provider,
            "reason": decision.reason,
            "billingmode": decision.billing_mode,
            "estimatedcostusd": decision.estimated_cost_usd,
            "approvedbypolicy": True,
            "decided_at": decision.decided_at,
            "decidedat": decision.decided_at,
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def writedecisionartifact(self, decision: ProviderDecision, cycle: str = "") -> Path:
        return self.write_decision_artifact(decision, cycle=cycle)

    def validate_policy(self) -> ValidationResult:
        issues: list[str] = []
        payload: dict[str, Any] = {}
        policy = getattr(self, "policy", None)
        if isinstance(policy, dict):
            payload = policy
        else:
            policy_path = getattr(self, "policy_path", POLICY_PATH)
            if not Path(policy_path).exists():
                return ValidationResult(passed=False, issues=["Provider policy file not loaded"])
            parsed = yaml.safe_load(Path(policy_path).read_text(encoding="utf-8"))
            payload = parsed if isinstance(parsed, dict) else {}

        providers = payload.get("providers", {})
        routes = payload.get("routes", {})
        global_rules = payload.get("global_rules", {})

        if not isinstance(providers, dict) or len(providers) < 4:
            issues.append("Missing required providers")
        if not isinstance(routes, dict) or len(routes) < 9:
            issues.append("Missing required routes")
        if global_rules.get("no_browser_automation_chatgpt") is not True:
            issues.append("global_rules.no_browser_automation_chatgpt must be true")
        if "advisory_only_provider_routing" not in global_rules:
            issues.append("global_rules.advisory_only_provider_routing is required")

        return ValidationResult(passed=not issues, issues=issues)

    def validatepolicy(self) -> ValidationResult:
        return self.validate_policy()

    def validate_routes(self) -> bool:
        return self.validate_policy().passed

    def route_dry_run(self, task_type: str, cycle: str = "000") -> dict[str, Any]:
        decision = self.select_provider(task_type=task_type, cycle=cycle)
        artifact_path = self.write_decision_artifact(decision, cycle=cycle)
        payload = asdict(decision)
        provider_alias = {
            "deterministiccontroller": "deterministic_controller",
            "deterministicpromptfactory": "deterministic_prompt_factory",
            "deterministicvalidator": "deterministic_validator",
        }
        payload["provider"] = provider_alias.get(payload["provider"], payload["provider"])
        payload["decision_artifact_path"] = str(artifact_path)
        print(f"DRYRUN: Would route {task_type} to {payload['provider']}. Artifact: {artifact_path}")
        return payload

    def routedry_run(self, tasktype: str, cycle: str = "000") -> dict[str, Any]:
        return self.route_dry_run(tasktype, cycle=cycle)

    def route_dryrun(self, tasktype: str, cycle: str = "000") -> dict[str, Any]:
        return self.route_dry_run(tasktype, cycle=cycle)

    def dispatch(self, task_type: str, cycle: str = "000", agent: str = "") -> ProviderRunResult:
        started_at = datetime.now(UTC).isoformat()
        decision = self.select_provider(task_type=task_type, cycle=cycle, agent=agent)
        artifact_path = self.write_decision_artifact(decision, cycle=cycle)
        if decision.provider == "claudesubscription" and self.advisory_only_mode:
            return ProviderRunResult(
                status="ADVISORYONLYBLOCKED",
                provider=decision.provider,
                started_at=started_at,
                completed_at=datetime.now(UTC).isoformat(),
                files_changed=[],
                validation_required=True,
                error_message="ADVISORY_ONLY_BLOCKED",
                decision_artifact_path=str(artifact_path),
            )
        return ProviderRunResult(
            status="SUCCESS",
            provider=decision.provider,
            started_at=started_at,
            completed_at=datetime.now(UTC).isoformat(),
            files_changed=[],
            validation_required=False,
            error_message=None,
            decision_artifact_path=str(artifact_path),
        )


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Provider router policy validation and dry-run routing.")
    parser.add_argument("--dry-run", action="store_true", help="Route task in dry-run mode.")
    parser.add_argument("--task-type", default="implementation", help="Task type to route.")
    parser.add_argument("--cycle", default="000", help="Cycle id used in decision artifact.")
    args = parser.parse_args()

    router = ProviderRouter()
    if args.dry_run:
        try:
            payload = router.route_dry_run(task_type=args.task_type, cycle=str(args.cycle))
            print(json.dumps(payload, indent=2))
            return 0
        except Exception as exc:
            print(f"ERROR: {exc}")
            return 1
    result = router.validate_policy()
    print(result)
    return 0 if result.passed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate-routes", "dry-run"])
    parser.add_argument("--task-type", default="implementation")
    args = parser.parse_args()

    router = ProviderRouter()
    if args.command == "validate-routes":
        result = router.validate_policy()
        print(result)
        sys.exit(0 if result.passed else 1)

    dry = router.route_dry_run(args.task_type)
    print(dry)
    sys.exit(0)
