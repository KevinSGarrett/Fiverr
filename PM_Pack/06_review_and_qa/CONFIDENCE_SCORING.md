# CONFIDENCE SCORING SYSTEM

---

## Scoring Rubric (0-100)

| Score Range | Label | Meaning |
|---|---|---|
| 90-100 | Excellent | All checks pass, code is clean, tests comprehensive |
| 80-89 | Good | Minor issues only, all core functionality works |
| 70-79 | Acceptable | Some issues need fixing, but foundation is solid |
| 60-69 | Needs Work | Significant issues, rework required next cycle |
| 50-59 | Poor | Major gaps, substantial rework needed |
| 0-49 | Failed | Work is unusable, must redo from scratch |

## Scoring Components

| Component | Weight | What It Measures |
|---|---|---|
| File completeness | 20% | All specified files exist at correct paths |
| Spec compliance | 25% | Implementation matches referenced spec docs |
| Test quality | 20% | Tests exist, are meaningful, and pass |
| Code quality | 15% | Lint clean, type-safe, well-structured |
| Integration | 10% | Works with existing codebase, no breaks |
| Documentation | 10% | Docstrings, comments on complex logic |

## Calculation
confidence = (file_score * 0.20) + (spec_score * 0.25) + (test_score * 0.20) + (quality_score * 0.15) + (integration_score * 0.10) + (docs_score * 0.10)

## Threshold Actions

| Confidence | PM Action |
|---|---|
| >= 90 | Mark all tasks Done, no rework needed |
| 80-89 | Mark tasks Done, note minor improvements for later |
| 70-79 | Mark tasks Done with caveats, create improvement tasks |
| 60-69 | Mark tasks In Review, create rework tasks for next cycle |
| < 60 | Mark tasks Failed, reassign with more detailed prompt |

## Per-Cycle Requirement
- PM MUST assign confidence score for EACH agent (4 scores per cycle)
- Scores recorded in CYCLE_LOG entry
- If any agent < 80, PM must explain why and define rework scope
