# Test File Verification

| Test File | Exists | Command | Result | Notes |
|---|---|---|---|---|
| `tests/unit/test_lock_manager.py` | YES | `python -m pytest tests/unit/test_lock_manager.py -v --tb=short` | PASS | 10 passed |
| `tests/unit/test_drift_detector.py` | YES | `python -m pytest tests/unit/test_drift_detector.py -v --tb=short` | PASS | 6 passed |
| `tests/unit/test_state_writer.py` | YES | `python -m pytest tests/unit/test_state_writer.py -v --tb=short` | PASS | 5 passed |
| `tests/unit/test_notification_router.py` | YES | `python -m pytest tests/unit/test_notification_router.py -v --tb=short` | PASS | 5 passed |
| `tests/unit/test_post_cycle_review.py` | YES | `python -m pytest tests/unit/test_post_cycle_review.py -v --tb=short` | PASS | 8 passed |
| `tests/unit/test_github_client.py` | YES | `python -m pytest tests/unit/test_github_client.py -v --tb=short` | PASS | 6 passed |
| `tests/unit/test_merge_gate.py` | YES | `python -m pytest tests/unit/test_merge_gate.py -v --tb=short` | PASS | 16 passed |
| `tests/unit/test_jira_client.py` | YES | `python -m pytest tests/unit/test_jira_client.py -v --tb=short` | PASS | 7 passed |
| `tests/unit/test_repair_loop.py` | YES | `python -m pytest tests/unit/test_repair_loop.py -v --tb=short` | PASS | 22 passed |
| `tests/unit/test_run_agent_lifecycle.py` | YES | `python -m pytest tests/unit/test_run_agent_lifecycle.py -v --tb=short` | PASS | 14 passed |
