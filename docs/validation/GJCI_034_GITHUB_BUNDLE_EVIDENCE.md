# GJCI_034_GITHUB_BUNDLE_EVIDENCE

## Prompt-Specified API Check

- Requested command:
  - `generate_post_cycle_github_bundle(...)`
- Result: **FAIL**
  - `ImportError: cannot import name 'generate_post_cycle_github_bundle' from 'automation.post_cycle_review'`

## Available Post-Cycle Data Collection

- Executed available function:
  - `from automation.post_cycle_review import collect_facts, ReviewMode`
  - `collect_facts(77, ReviewMode.POST_AGENT, None)`
- Output:
  - `total_keys=24`
  - key sample:
    - `agent_reports_present`
    - `ci_passed`
    - `codecov_project`
    - `codecov_patch`
    - `develop_sha`
    - `head_sha`
    - `local_ruff`
    - `local_mypy`

## Verdict

- **PARTIAL** — post-cycle fact bundle is available via `collect_facts`, but prompt-specified GitHub bundle function does not exist in this branch.
