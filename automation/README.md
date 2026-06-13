# Automation Layer README

This document maps core automation modules to purpose, public surface, and checklist responsibility.

| Module | Purpose | Primary public functions/classes | Checklist IDs |
| --- | --- | --- | --- |
| `ai_cycle_controller.py` | CLI entrypoint coordinating planning, validation, dispatch, review | `main()`, command handlers | STATE, OPS, DISPATCH |
| `config_loader.py` | Loads typed automation configuration | `load_config()` | ENV, OPS |
| `pm_pack_loader.py` | Reads PM_Pack state and references | `load_pm_pack()` | STATE |
| `policy_compiler.py` | Compiles policy snapshots from source docs | `compile_policy()` | BRAIN, STATE |
| `prompt_generator.py` | Generates agent prompts for cycle execution | `generate_prompts()` | DISPATCH, STATE |
| `prompt_validator.py` | Validates prompt quality and policy compliance | `validate_prompts()` | OPS-030, STATE |
| `run_agent_lifecycle.py` | Drives per-agent run lifecycle orchestration | `run_lifecycle()` | DISPATCH |
| `cursor_adapter.py` | Integrates with Cursor agent runtime | `dispatch_cursor()`, `health_check()` | ENV, MODEL |
| `claude_post_cycle_adapter.py` | Integrates Claude PM review path | `run_post_cycle_review()` | POSTCYCLE, MODEL-008 |
| `post_cycle_review.py` | Executes post-cycle review logic | `execute_review()` | POSTCYCLE |
| `merge_gate.py` | Merge readiness gating for PRs | `run()` | GJCI |
| `repair_loop.py` | Controlled repair retries on failures | `run_repair_loop()` | OPS |
| `secret_guard.py` | Scans staged changes for secrets | `scan_staged()` | SEC |
| `freeze_gate.py` | Enforces freeze state controls | `check_freeze_gate()` | STATE, OPS |
| `pm_pack_consistency_audit.py` | Audits PMPack state consistency | `run_audit()` | STATE-016 |
| `check_dev_auto_readiness.py` | Verifies autonomous readiness prerequisites | `check_readiness()` | ENV |

## Notes

- Controller owns git commit/push operations.
- PMPack consistency and model verification are hard governance controls.
- This README intentionally focuses on primary files used in Cycle 075 governance scope.
