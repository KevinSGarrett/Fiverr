# CYCLE 082 — Agent E: Live data validation, external signal collection, evidence files
Generated: 2026-06-16T03:48:17.748545+00:00
Cycle: 082
Agent: E
Branch: cycle/082/integration
Repo Root: C:/Fiverr/Fiverr

## MODEL POLICY — MANDATORY
Worker: Cursor CLI
Model: codex-5.3
Effort: medium
Auto: DISABLED
Fallback: DISABLED

## GIT RULES — MANDATORY
You MUST NOT run any write-side Git command or PR merge command.
Controller owns all git operations.

## AUTONOMY RULE
Complete all assigned tasks autonomously without confirmation prompts unless a hard blocker appears.

## ALLOWED PATHS
- docs/cycle_reports/**
- data/evidence/**
- scripts/validation/**

## BLOCKED PATHS
- src/**
- tests/**
- config.yaml

## JIRA SCOPE
### SCRUM-256: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Six contract JSON files are created in PM_Pack/automation/prompt_contracts/
- All contracts validate against prompt_contract.schema.json
Definition of Done:
- Contract generation for A/B/E/C/F/D completes successfully
- Schema validation command exits zero for all contracts
Files or modules:
- PM_Pack/automation/prompt_contracts/
- automation/schemas/prompt_contract.schema.json

### SCRUM-257: PROMPTFACTORY-012 add prompt lineage metadata
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Each contract includes source lineage entries
- Lineage references Jira keys and PM_Pack catalogs
Definition of Done:
- Lineage is present for all six agents
- Lineage report captures source resolution evidence
Files or modules:
- PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json
- PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md

### SCRUM-258: PROMPTFACTORY-015 create Cycle 079 validation report artifact
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- Validation report JSON exists in prompts/validated
- Per-agent PASS/FAIL/WARN and gate checks are recorded
Definition of Done:
- validate-prompts evidence is captured into report
- Report includes generation timestamp and summary status
Files or modules:
- PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json

### SCRUM-259: PROMPTFACTORY-030/031 contract README and prompt factory chain docs
Status: In Progress
Priority: Medium
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- prompt_contracts/README.md explains schema and generation flow
- PROMPT_FACTORY_CHAIN.md documents the artifact lifecycle
Definition of Done:
- Both documentation artifacts exist with correct chain details
- Dispatch source of truth in prompts/validated is documented
Files or modules:
- PM_Pack/automation/prompt_contracts/README.md
- docs/architecture/PROMPT_FACTORY_CHAIN.md

### SCRUM-260: REFCAT freshness rebuild and strict verification
Status: In Progress
Priority: High
Spec path: PM_Pack/ref/project_plan/13_Cycle_013_Execution_Protocol.md
Acceptance Criteria:
- All four ref catalogs are rebuilt fresh
- verify --strict exits zero and brain-check has no stale warnings
Definition of Done:
- Catalog counts meet strict minimum thresholds
- BRAIN_REGISTRY freshness constraints are confirmed
Files or modules:
- automation/ref_catalog_builder.py
- PM_Pack/automation/project_plan_catalog.json
- PM_Pack/automation/dod_catalog.json
- PM_Pack/automation/todo_epic_catalog.json
- PM_Pack/automation/github_governance_catalog.json
- PM_Pack/automation/BRAIN_REGISTRY.yml


## TASKS
### Task 1: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — Review specification and acceptance requirements
- Jira key: SCRUM-256
- Description: Agent E executes 'Review specification and acceptance requirements' for SCRUM-256, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 2: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — Implement routing and control logic
- Jira key: SCRUM-256
- Description: Agent E executes 'Implement routing and control logic' for SCRUM-256, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 3: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — Verify acceptance criteria coverage
- Jira key: SCRUM-256
- Description: Agent E executes 'Verify acceptance criteria coverage' for SCRUM-256, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 4: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — Write and run focused unit validation checks
- Jira key: SCRUM-256
- Description: Agent E executes 'Write and run focused unit validation checks' for SCRUM-256, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 5: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — Verify definition-of-done artifacts
- Jira key: SCRUM-256
- Description: Agent E executes 'Verify definition-of-done artifacts' for SCRUM-256, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 6: PROMPTFACTORY-010 generate six Cycle 079 prompt contracts — Run full validation command set
- Jira key: SCRUM-256
- Description: Agent E executes 'Run full validation command set' for SCRUM-256, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/, automation/schemas/prompt_contract.schema.json
- Validation: Record command outputs and state transition evidence.

### Task 7: PROMPTFACTORY-012 add prompt lineage metadata — Review specification and acceptance requirements
- Jira key: SCRUM-257
- Description: Agent E executes 'Review specification and acceptance requirements' for SCRUM-257, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Record command outputs and state transition evidence.

### Task 8: PROMPTFACTORY-012 add prompt lineage metadata — Implement routing and control logic
- Jira key: SCRUM-257
- Description: Agent E executes 'Implement routing and control logic' for SCRUM-257, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Record command outputs and state transition evidence.

### Task 9: PROMPTFACTORY-012 add prompt lineage metadata — Verify acceptance criteria coverage
- Jira key: SCRUM-257
- Description: Agent E executes 'Verify acceptance criteria coverage' for SCRUM-257, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Record command outputs and state transition evidence.

### Task 10: PROMPTFACTORY-012 add prompt lineage metadata — Write and run focused unit validation checks
- Jira key: SCRUM-257
- Description: Agent E executes 'Write and run focused unit validation checks' for SCRUM-257, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Record command outputs and state transition evidence.

### Task 11: PROMPTFACTORY-012 add prompt lineage metadata — Verify definition-of-done artifacts
- Jira key: SCRUM-257
- Description: Agent E executes 'Verify definition-of-done artifacts' for SCRUM-257, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Record command outputs and state transition evidence.

### Task 12: PROMPTFACTORY-012 add prompt lineage metadata — Run full validation command set
- Jira key: SCRUM-257
- Description: Agent E executes 'Run full validation command set' for SCRUM-257, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/CYCLE_079_*.contract.json, PM_Pack/automation/prompt_contracts/CYCLE_079_LINEAGE_REPORT.md
- Validation: Record command outputs and state transition evidence.

### Task 13: PROMPTFACTORY-015 create Cycle 079 validation report artifact — Review specification and acceptance requirements
- Jira key: SCRUM-258
- Description: Agent E executes 'Review specification and acceptance requirements' for SCRUM-258, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Record command outputs and state transition evidence.

### Task 14: PROMPTFACTORY-015 create Cycle 079 validation report artifact — Implement routing and control logic
- Jira key: SCRUM-258
- Description: Agent E executes 'Implement routing and control logic' for SCRUM-258, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Record command outputs and state transition evidence.

### Task 15: PROMPTFACTORY-015 create Cycle 079 validation report artifact — Verify acceptance criteria coverage
- Jira key: SCRUM-258
- Description: Agent E executes 'Verify acceptance criteria coverage' for SCRUM-258, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Record command outputs and state transition evidence.

### Task 16: PROMPTFACTORY-015 create Cycle 079 validation report artifact — Write and run focused unit validation checks
- Jira key: SCRUM-258
- Description: Agent E executes 'Write and run focused unit validation checks' for SCRUM-258, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Record command outputs and state transition evidence.

### Task 17: PROMPTFACTORY-015 create Cycle 079 validation report artifact — Verify definition-of-done artifacts
- Jira key: SCRUM-258
- Description: Agent E executes 'Verify definition-of-done artifacts' for SCRUM-258, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Record command outputs and state transition evidence.

### Task 18: PROMPTFACTORY-015 create Cycle 079 validation report artifact — Run full validation command set
- Jira key: SCRUM-258
- Description: Agent E executes 'Run full validation command set' for SCRUM-258, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompts/validated/CYCLE_079_VALIDATION_REPORT.json
- Validation: Record command outputs and state transition evidence.

### Task 19: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — Review specification and acceptance requirements
- Jira key: SCRUM-259
- Description: Agent E executes 'Review specification and acceptance requirements' for SCRUM-259, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Record command outputs and state transition evidence.

### Task 20: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — Implement routing and control logic
- Jira key: SCRUM-259
- Description: Agent E executes 'Implement routing and control logic' for SCRUM-259, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Record command outputs and state transition evidence.

### Task 21: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — Verify acceptance criteria coverage
- Jira key: SCRUM-259
- Description: Agent E executes 'Verify acceptance criteria coverage' for SCRUM-259, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Record command outputs and state transition evidence.

### Task 22: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — Write and run focused unit validation checks
- Jira key: SCRUM-259
- Description: Agent E executes 'Write and run focused unit validation checks' for SCRUM-259, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Record command outputs and state transition evidence.

### Task 23: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — Verify definition-of-done artifacts
- Jira key: SCRUM-259
- Description: Agent E executes 'Verify definition-of-done artifacts' for SCRUM-259, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Record command outputs and state transition evidence.

### Task 24: PROMPTFACTORY-030/031 contract README and prompt factory chain docs — Run full validation command set
- Jira key: SCRUM-259
- Description: Agent E executes 'Run full validation command set' for SCRUM-259, records evidence, and updates implementation notes for downstream agents.
- Files: PM_Pack/automation/prompt_contracts/README.md, docs/architecture/PROMPT_FACTORY_CHAIN.md
- Validation: Record command outputs and state transition evidence.

### Task 25: REFCAT freshness rebuild and strict verification — Review specification and acceptance requirements
- Jira key: SCRUM-260
- Description: Agent E executes 'Review specification and acceptance requirements' for SCRUM-260, records evidence, and updates implementation notes for downstream agents.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Record command outputs and state transition evidence.

### Task 26: REFCAT freshness rebuild and strict verification — Implement routing and control logic
- Jira key: SCRUM-260
- Description: Agent E executes 'Implement routing and control logic' for SCRUM-260, records evidence, and updates implementation notes for downstream agents.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Record command outputs and state transition evidence.

### Task 27: REFCAT freshness rebuild and strict verification — Verify acceptance criteria coverage
- Jira key: SCRUM-260
- Description: Agent E executes 'Verify acceptance criteria coverage' for SCRUM-260, records evidence, and updates implementation notes for downstream agents.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Record command outputs and state transition evidence.

### Task 28: REFCAT freshness rebuild and strict verification — Write and run focused unit validation checks
- Jira key: SCRUM-260
- Description: Agent E executes 'Write and run focused unit validation checks' for SCRUM-260, records evidence, and updates implementation notes for downstream agents.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Record command outputs and state transition evidence.

### Task 29: REFCAT freshness rebuild and strict verification — Verify definition-of-done artifacts
- Jira key: SCRUM-260
- Description: Agent E executes 'Verify definition-of-done artifacts' for SCRUM-260, records evidence, and updates implementation notes for downstream agents.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Record command outputs and state transition evidence.

### Task 30: REFCAT freshness rebuild and strict verification — Run full validation command set
- Jira key: SCRUM-260
- Description: Agent E executes 'Run full validation command set' for SCRUM-260, records evidence, and updates implementation notes for downstream agents.
- Files: automation/ref_catalog_builder.py, PM_Pack/automation/project_plan_catalog.json, PM_Pack/automation/dod_catalog.json, PM_Pack/automation/todo_epic_catalog.json, PM_Pack/automation/github_governance_catalog.json, PM_Pack/automation/BRAIN_REGISTRY.yml
- Validation: Record command outputs and state transition evidence.

### Task 31: General quality gate execution
- Jira key: SCRUM-256
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 32: General quality gate execution
- Jira key: SCRUM-257
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 33: General quality gate execution
- Jira key: SCRUM-258
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 34: General quality gate execution
- Jira key: SCRUM-259
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 35: General quality gate execution
- Jira key: SCRUM-260
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 36: General quality gate execution
- Jira key: SCRUM-256
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 37: General quality gate execution
- Jira key: SCRUM-257
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 38: General quality gate execution
- Jira key: SCRUM-258
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 39: General quality gate execution
- Jira key: SCRUM-259
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 40: General quality gate execution
- Jira key: SCRUM-260
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 41: General quality gate execution
- Jira key: SCRUM-256
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 42: General quality gate execution
- Jira key: SCRUM-257
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 43: General quality gate execution
- Jira key: SCRUM-258
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 44: General quality gate execution
- Jira key: SCRUM-259
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 45: General quality gate execution
- Jira key: SCRUM-260
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 46: General quality gate execution
- Jira key: SCRUM-256
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 47: General quality gate execution
- Jira key: SCRUM-257
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 48: General quality gate execution
- Jira key: SCRUM-258
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 49: General quality gate execution
- Jira key: SCRUM-259
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 50: General quality gate execution
- Jira key: SCRUM-260
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 51: General quality gate execution
- Jira key: SCRUM-256
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 52: General quality gate execution
- Jira key: SCRUM-257
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 53: General quality gate execution
- Jira key: SCRUM-258
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 54: General quality gate execution
- Jira key: SCRUM-259
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

### Task 55: General quality gate execution
- Jira key: SCRUM-260
- Description: Run ruff, mypy, pytest, schema checks, and reporting validation to maintain regression safety while finalizing delivery artifacts.
- Files: (none)
- Validation: ruff + mypy + pytest + jsonschema + report update

## REQUIRED VALIDATION STEPS
- python automation/ai_cycle_controller.py brain-check
- python automation/ai_cycle_controller.py validate-prompts --cycle 080
- mypy src/ automation/ --ignore-missing-imports

## FINAL REPORT REQUIREMENT
Write final report to docs/cycle_reports/CYCLE_082_AGENT_E.md.

## STOP CONDITIONS
- Stop immediately if secrets/credentials are exposed in outputs or artifacts.
- Stop if any blocked path must be modified to complete a task.
- Stop if FC-1 (frozen/autonomy block) is triggered by policy or state.
- Stop before attempting write-side Git operations.

ADDITIONAL TASKS — Checklist Completion (Items with no prior coverage)
Task 56: EXPORT-001 — Create automation/export_sanitizer_verify.py
Create the module automation/export_sanitizer_verify.py. It must export:
class ExportSecretError(Exception) — carries offending_paths: list[str]
def verify_staged_files(staged_files: list[str]) -> None — raises ExportSecretError if any path matches: *.env, runner.env, *.credentials, *.pem, *.key, any name containing _TOKEN or secret (case-insensitive)
def verify_zip(zip_path: Path) -> None — opens ZIP, runs same check on all member names, raises ExportSecretError if any match Clean input → returns None silently. Add if __name__ == "__main__": import sys; verify_zip(Path(sys.argv[1])) CLI entrypoint. Run python -c "from automation.export_sanitizer_verify import verify_staged_files, verify_zip, ExportSecretError; verify_staged_files([]); print('export_sanitizer_verify OK')". Must exit 0.
Task 57: BRAIN-021 — Complete post_cycle_review.py fact collection
Open automation/post_cycle_review.py. Locate or create _verify_github_facts(self) -> dict: must call subprocess.run(["gh","pr","list","--state","merged","--limit","5","--json","number,title,mergedAt"]), parse JSON, return {"merged_prs": [...], "collected_at": ISO}. Write result to PM_Pack/automation/post_cycle_reviews/current_run/github_verification.json (create dirs). Handle subprocess errors gracefully — on CalledProcessError or FileNotFoundError return {"merged_prs":[], "error":"gh_unavailable"}. Wire this into collect_facts().
Task 58: POSTCYCLE-010/011 — Complete Jira closeout facts
In automation/post_cycle_review.py, add _verify_jira_facts(self) -> dict: queries Jira for Done stories in the current cycle using jira_client.search_issues(f"project=SCRUM AND status=Done AND sprint in openSprints()"), returns {"done_stories": [list of keys], "collected_at": ISO}. On JiraAuthError or ConnectionError: return {"done_stories": [], "auth_error": "JIRA_AUTH_FAILED"} — never raises. Wire into collect_facts(). Write result to PM_Pack/automation/post_cycle_reviews/current_run/jira_verification.json. Run python -c "from automation.post_cycle_review import PostCycleReview; r=PostCycleReview(); print('PostCycleReview importable')". Must exit 0.
Task 59: MODEL-014 — Add model verification section to daily report
Open automation/report_generator.py. Add _get_model_status_section(self) -> str: reads C:\AI_Runner\state\cursor_model_state.json (and claude_model_state.json if it exists). Computes age in days from verified_at. Returns a formatted markdown block: `## Model Verification Status
Cursor: {model} | effort: {effort} | age: {N} days | expires: {date}
Claude: {model} | effort: {effort} | billing: {billingmode}. Wire intogeneratedailyreport(). Runpython automation/aicycle_controller.py daily-report 2>&1 | grep -i model` — must show at least one model line.
Task 60: GJCI-031 — Add CI timing benchmark to daily report
In automation/report_generator.py, add _get_ci_timing_section(self) -> str: runs subprocess.run(["gh","run","list","--workflow=ci.yml","--limit","5","--json","conclusion,createdAt,updatedAt"]), parses the JSON, computes average duration in seconds, returns `## CI Timing
Last 5 runs avg: {N}s | last run: {conclusion} ({duration}s). Handle gh unavailable gracefully. Wire intogeneratedailyreport()`. Document the output.
Task 61: PASS4-P1-010 — Health check ORANGE on stale heartbeat
Create C:\AI_Runner\scripts\health_check.ps1 if it doesn't already exist. The script must:
Read C:\AI_Runner\state\heartbeat.json — get last_seen timestamp
Compute age in minutes: (Get-Date) - [datetime]::Parse($heartbeat.last_seen)
If age > 120 minutes AND controller_state.json status is ACTIVE: write RED and exit 2
If age > 30 minutes AND controller_state.json status is ACTIVE: write ORANGE and exit 1
Otherwise: write GREEN and exit 0 Document the script. Verify it exists at the correct path.
Task 62: STATE-010 — Implement local notification logging on BLOCKED severity
Open automation/notification_router.py (create if not exists). Implement class NotificationRouter with:
send_local_notification(self, message: str, channel: str, severity: str) -> None: writes local jsonl entries, no external network calls.
route_notification(self, severity: str, message: str, context: dict) -> None: calls send_local_notification only when severity in ('BLOCKED', 'RED', 'CRITICAL'). Run python -c "from automation.notification_router import NotificationRouter; r=NotificationRouter(); r.route_notification('INFO','test',{}); print('NotificationRouter OK')". Must not crash.
Task 63: Run ruff + mypy on all new Agent B files
Run ruff check automation/export_sanitizer_verify.py automation/post_cycle_review.py automation/report_generator.py automation/notification_router.py --output-format=concise. Must exit 0. Run mypy automation/export_sanitizer_verify.py automation/notification_router.py --ignore-missing-imports --no-error-summary. Must exit 0. Document any type issues found and fixed.

END OF PROMPT
