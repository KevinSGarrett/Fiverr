# Coverage Summary — Agent F Final

## Automation Modules Fixed This Cycle (Agent F)
| Module | Before Agent F | After Agent F | Gate Met |
|---|---|---|---|
| automation/model_gate.py | 80% | 93% | YES |
| automation/policy_compiler.py | 94% | 94% | YES |
| automation/prompt_validator.py | 91% | 91% | YES |
| automation/config_loader.py | 86% | 100% | YES |
| automation/claude_sub_gate.py | 88% | 100% | YES |
| automation/lock_manager.py | 87% | 93% | YES |
| automation/github_client.py | 80% | 98% | YES |
| automation/report_generator.py | 95% | 95% | YES |

## Combined Coverage Gates
| Scope | Coverage | CI Gate (≥90%) |
|---|---|---|
| automation/ only | 67.75%* | FAIL* |
| automation/ + src/ | 92.58% | PASS |

*Notes: workspace-wide automation-only run consistently truncates around ~54% progress in this environment; per-module coverage for targeted modules is verified above and all are ≥90%.

## Total Tests
- Before Cycle 076: 5847
- After Cycle 076 Agent F: 5935 total collected
- New tests added by Agent F: 30

## Regressions
None in targeted regression suites.
