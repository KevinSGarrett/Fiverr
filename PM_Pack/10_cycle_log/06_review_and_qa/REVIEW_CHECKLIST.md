# REVIEW CHECKLIST
# What the PM checks for EACH agent's work every cycle (25 checks per agent)

---

## Per-Agent Review (run for Agent A, B, C, D separately)

### Code Existence (5 checks)
- [ ] All files listed in the prompt's FILES CREATED table actually exist
- [ ] All files are in the correct directories per DIRECTORY_STRUCTURE.md
- [ ] All __init__.py files updated to export new classes/functions
- [ ] No extra unexpected files created outside the assigned scope
- [ ] File naming follows snake_case convention per .cursorrules

### Code Quality (6 checks)
- [ ] Ruff lint passes with zero errors: ruff check src/{agent_dirs}/
- [ ] Mypy type check passes: mypy src/{agent_dirs}/ --ignore-missing-imports
- [ ] No hardcoded values that should come from config.yaml
- [ ] No print() statements (use logging)
- [ ] No TODO/FIXME/HACK comments left in production code
- [ ] Imports are clean (no unused imports, correct paths)

### Spec Compliance (4 checks)
- [ ] Implementation matches the spec document referenced in the prompt
- [ ] All fields/columns/parameters match SCHEMA.md / FIELD_CATALOG.md
- [ ] Method signatures match what the spec describes
- [ ] Edge cases from the spec are handled

### Test Coverage (5 checks)
- [ ] All required tests from the prompt exist
- [ ] Tests actually test meaningful behavior (not trivial assertions)
- [ ] Edge case tests exist (null input, empty data, missing fields)
- [ ] Error handling tests exist (invalid input, DB errors, API failures)
- [ ] Tests pass: pytest tests/unit/test_{module}.py -v -> all green

### Integration (3 checks)
- [ ] New code doesn't break existing code (no import errors across modules)
- [ ] New code integrates with existing models/config/utils correctly
- [ ] Database models can be created and queried (for model-related tasks)

### Documentation (2 checks)
- [ ] Docstrings on all public classes and methods
- [ ] Complex logic has inline comments explaining why (not what)

---

## Total checks per agent: 25
## Pass threshold: ALL must be checked for confidence >= 80
