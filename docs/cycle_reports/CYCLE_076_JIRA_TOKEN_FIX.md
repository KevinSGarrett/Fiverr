# Cycle 076 Jira Token Fix

## Root Cause
`JIRA_API_TOKEN` was read indirectly via `get_secret()`, but there was no explicit validation or actionable error at Jira client initialization time. When the token was missing (or blank) in `C:\AI_Runner\secrets\runner.env`, Jira flows failed later with generic auth failures instead of a clear runner-env-path error.

## Fix Applied
- Added explicit credential validation in `automation/jira_client.py`:
  - `JiraClient.__init__()` now validates Jira credentials up front.
  - Missing `JIRA_API_TOKEN` now raises a clear `ValueError` including the expected runner env path.
  - Missing `JIRA_EMAIL` now raises a clear `ValueError` including the expected runner env path.
- Added runner-env diagnostics in `automation/config_loader.py`:
  - DEBUG log when `JIRA_API_TOKEN` is successfully loaded.
  - ERROR log when `runner.env` is missing.
  - ERROR log when `JIRA_API_TOKEN` is absent from `runner.env`.
  - Added UTF-8 encoding in config file reads for deterministic parsing.

## Files Modified
- `automation/config_loader.py`
- `automation/jira_client.py`
- `tests/unit/test_jira_client.py`

## Test Added
- `test_jira_client_raises_clear_error_when_token_missing`
- `test_jira_client_initializes_when_token_present`

## Verification
Run:

`.venv\Scripts\python.exe -m pytest tests/unit/test_jira_client.py -v --tb=short`

Expected:
- Missing token scenario raises `ValueError` containing `JIRA_API_TOKEN is missing`.
- Present token scenario initializes `JiraClient` successfully.
