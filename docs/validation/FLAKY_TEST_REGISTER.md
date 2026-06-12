# Flaky Test Register

- Updated at (UTC): 2026-06-12T03:28:36.163306+00:00
- Scope: 10 additional iterations for each validation command from Task 4.

| Command | Runs | PASS | FAIL | Flaky? | Notes |
|---|---:|---:|---:|---|---|
| Ruff | 10 | 0 | 10 | NO | Consistent deterministic failure pattern across repeats. |
| Mypy | 10 | 0 | 10 | NO | Consistent deterministic failure pattern across repeats. |
| Pytest+coverage | 10 | 0 | 10 | NO | Consistent deterministic failure pattern across repeats. |
| Brain-check | 10 | 10 | 0 | NO | Consistent pass across repeats. |
| PM-pack-audit | 10 | 10 | 0 | NO | Consistent pass across repeats. |
| Baseline DB check | 10 | 10 | 0 | NO | Consistent pass across repeats. |
| Scrapfly check | 10 | 10 | 0 | NO | Consistent pass across repeats. |

## Summary

- No intermittent pass/fail mixing was observed in this repeated run set.
- Ruff failed consistently due unsupported `--output-format=text` flag usage.
- Mypy failed consistently due existing `unused-ignore` findings.
- Pytest executed consistently but failed coverage threshold gate (<90%).
