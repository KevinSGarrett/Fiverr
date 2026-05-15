# PR Checks — Detailed Validation Rules
# Fiverr Research System

---

## Overview

The `pr-checks.yml` workflow runs on every PR event (opened, edited, labeled, unlabeled, synchronize) and validates 5 areas. ALL checks must pass for the PR to be mergeable.

---

## Check 1: Title Validation

### Rules
| Rule | Requirement | Failure Message |
|---|---|---|
| Format | Must match `^(feat\|fix\|refactor\|test\|docs\|chore\|style\|perf\|ci\|build\|release\|hotfix\|revert)(\([a-z0-9-]+\))?: .+$` | "PR title must follow conventional format: type(scope): description" |
| Length | Total ≤ 72 characters | "PR title exceeds 72 characters (currently {n})" |
| Case | Type and scope must be lowercase | "PR title type and scope must be lowercase" |
| Description start | First character of description must be lowercase (except proper nouns) | "Description should start with lowercase verb" |
| No period | Must not end with `.` | "PR title should not end with a period" |

### Implementation
```yaml
- name: Validate PR Title
  uses: actions/github-script@v7
  with:
    script: |
      const title = context.payload.pull_request.title;
      const pattern = /^(feat|fix|refactor|test|docs|chore|style|perf|ci|build|release|hotfix|revert)(\([a-z0-9-]+\))?: .+$/;
      const errors = [];
      
      if (!pattern.test(title)) {
        errors.push('PR title must follow: type(scope): description');
      }
      if (title.length > 72) {
        errors.push(`PR title is ${title.length} chars (max 72)`);
      }
      if (title.endsWith('.')) {
        errors.push('PR title should not end with a period');
      }
      
      if (errors.length > 0) {
        core.setFailed(errors.join('\n'));
      }
```

---

## Check 2: Description Validation

### Rules
| Rule | Requirement | Failure Message |
|---|---|---|
| Not empty | PR body must not be null/empty | "PR description is empty — use the PR template" |
| Minimum length | Body ≥ 50 characters (excluding template headers) | "PR description too short (min 50 chars of actual content)" |
| Has What section | Body must contain `## What` | "PR description missing '## What' section" |
| Has Why section | Body must contain `## Why` | "PR description missing '## Why' section" |
| Has checklist | Body must contain at least one `- [x]` or `- [ ]` | "PR description missing checklist items" |

### Implementation
```yaml
- name: Validate PR Description
  uses: actions/github-script@v7
  with:
    script: |
      const body = context.payload.pull_request.body || '';
      const errors = [];
      
      if (body.trim().length === 0) {
        errors.push('PR description is empty — use the PR template');
      } else {
        // Strip markdown headers to measure actual content
        const content = body.replace(/^##.*$/gm, '').replace(/^-\s*\[.\]\s*/gm, '').trim();
        if (content.length < 50) {
          errors.push(`PR description too short (${content.length} chars, min 50)`);
        }
        if (!body.includes('## What')) {
          errors.push("Missing '## What' section");
        }
        if (!body.includes('## Why')) {
          errors.push("Missing '## Why' section");
        }
        if (!/- \[[ x]\]/.test(body)) {
          errors.push('Missing checklist items');
        }
      }
      
      if (errors.length > 0) {
        core.setFailed(errors.join('\n'));
      }
```

---

## Check 3: Label Validation

### Required Label Groups
| Category | Prefix | Exactly | Minimum | Failure Message |
|---|---|---|---|---|
| Type | `type:` | 1 | — | "Exactly 1 type label required (found {n})" |
| Priority | `priority:` | 1 | — | "Exactly 1 priority label required (found {n})" |
| Scope | `scope:` | — | 1 | "At least 1 scope label required" |
| Risk | `risk:` | 1 | — | "Exactly 1 risk label required (found {n})" |

### Type-Title Consistency
The type label must match the PR title prefix:

| Title Prefix | Required Label |
|---|---|
| `feat(...)` | `type:feature` |
| `fix(...)` | `type:fix` |
| `refactor(...)` | `type:refactor` |
| `test(...)` | `type:test` |
| `docs(...)` | `type:docs` |
| `chore(...)` | `type:chore` |
| `style(...)` | `type:style` |
| `perf(...)` | `type:perf` |
| `ci(...)` or `ci:` | `type:chore` |
| `release(...)` | `type:release` |
| `hotfix(...)` | `type:hotfix` |

If mismatched: "Type label 'type:feature' doesn't match title prefix 'fix'"

### Implementation
```yaml
- name: Validate Labels
  uses: actions/github-script@v7
  with:
    script: |
      const labels = context.payload.pull_request.labels.map(l => l.name);
      const errors = [];
      
      const typeLabels = labels.filter(l => l.startsWith('type:'));
      const priorityLabels = labels.filter(l => l.startsWith('priority:'));
      const scopeLabels = labels.filter(l => l.startsWith('scope:'));
      const riskLabels = labels.filter(l => l.startsWith('risk:'));
      
      if (typeLabels.length !== 1) errors.push(`Exactly 1 type label required (found ${typeLabels.length})`);
      if (priorityLabels.length !== 1) errors.push(`Exactly 1 priority label required (found ${priorityLabels.length})`);
      if (scopeLabels.length < 1) errors.push('At least 1 scope label required');
      if (riskLabels.length !== 1) errors.push(`Exactly 1 risk label required (found ${riskLabels.length})`);
      
      if (errors.length > 0) {
        core.setFailed(errors.join('\n'));
      }
```

---

## Check 4: Size Calculation & Labeling

### Line Count Logic
```
total_changes = additions + deletions

Excluded files (not counted):
  - *.lock
  - tests/fixtures/**/*.json
  - data/seeds/**/*.yaml
  - **/__init__.py (if empty or import-only)
  - *.md (documentation PRs)
  - *.j2 (template files — tracked separately)
```

### Size Thresholds
| Range | Label Applied | PR Comment |
|---|---|---|
| 1-10 | `size:XS` | None |
| 11-50 | `size:S` | None |
| 51-200 | `size:M` | None |
| 201-500 | `size:L` | "⚠️ Large PR — consider splitting if possible" |
| 501-1000 | `size:XL` | "⚠️ XL PR — strongly consider splitting" |
| 1000+ | `size:XXL` | "🛑 XXL PR — must split or add `override:large-pr` label" |

### XXL Blocking Logic
If `size:XXL` is applied AND `override:large-pr` label is NOT present:
- CI check **fails** with message: "PR exceeds 1000 lines. Split into smaller PRs or add `override:large-pr` label with justification."
- If `override:large-pr` IS present: CI passes with warning comment

### Implementation
```yaml
- name: Calculate PR Size
  uses: actions/github-script@v7
  with:
    script: |
      const { data: files } = await github.rest.pulls.listFiles({
        owner: context.repo.owner,
        repo: context.repo.repo,
        pull_number: context.payload.pull_request.number,
        per_page: 300
      });
      
      const excluded = /(\\.lock$|fixtures\/.*\\.json$|seeds\/.*\\.yaml$|__init__\\.py$|\\.md$|\\.j2$)/;
      let totalChanges = 0;
      
      for (const file of files) {
        if (!excluded.test(file.filename)) {
          totalChanges += file.additions + file.deletions;
        }
      }
      
      let sizeLabel;
      if (totalChanges <= 10) sizeLabel = 'size:XS';
      else if (totalChanges <= 50) sizeLabel = 'size:S';
      else if (totalChanges <= 200) sizeLabel = 'size:M';
      else if (totalChanges <= 500) sizeLabel = 'size:L';
      else if (totalChanges <= 1000) sizeLabel = 'size:XL';
      else sizeLabel = 'size:XXL';
      
      // Remove old size labels and apply new
      const currentLabels = context.payload.pull_request.labels.map(l => l.name);
      for (const label of currentLabels) {
        if (label.startsWith('size:')) {
          await github.rest.issues.removeLabel({
            owner: context.repo.owner,
            repo: context.repo.repo,
            issue_number: context.payload.pull_request.number,
            name: label
          });
        }
      }
      
      await github.rest.issues.addLabels({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: context.payload.pull_request.number,
        labels: [sizeLabel]
      });
      
      // Block XXL without override
      if (sizeLabel === 'size:XXL' && !currentLabels.includes('override:large-pr')) {
        core.setFailed(`PR has ${totalChanges} lines changed (XXL). Split or add override:large-pr label.`);
      }
```

---

## Check 5: Risk Suggestion

### File-to-Risk Mapping
| Files Changed | Suggested Risk | Reason |
|---|---|---|
| `src/models/database.py`, `src/models/base.py` | `risk:critical` | Core database layer |
| `src/models/*.py` (new/altered columns) | `risk:critical` | Schema changes affect all downstream |
| `src/orchestrator.py` | `risk:critical` | Master pipeline coordinator |
| `alembic/**`, migration files | `risk:critical` | Database migrations |
| `src/collection/session_manager.py` | `risk:high` | Browser session core |
| `src/collection/workflows/*.py` | `risk:high` | Data collection logic |
| `src/scoring/*.py` | `risk:high` | Score formulas affect all rankings |
| `src/llm/prompts/*.j2` | `risk:high` | LLM prompt changes affect recommendations |
| `src/llm/client.py` | `risk:high` | LLM integration core |
| `src/analysis/*.py` | `risk:medium` | Analysis within established patterns |
| `src/pricing/*.py` | `risk:medium` | Pricing logic |
| `src/discovery/*.py` | `risk:medium` | Discovery engine |
| `src/dashboard/**` | `risk:medium` | UI changes, no data impact |
| `src/playbook/**` | `risk:medium` | Output generation |
| `tests/**` | `risk:low` | Tests only |
| `docs/**`, `*.md` | `risk:low` | Documentation only |
| `.github/**` | `risk:low` | CI/config changes |
| `config.yaml`, `.env.example` | `risk:low` | Config template |

### Behavior
- If no `risk:*` label is present, CI posts a comment with the suggested risk level based on files changed
- The comment is advisory — the agent must add the label manually
- If multiple risk levels apply (e.g., editing both models and tests), suggest the **highest** risk level
- CI does NOT fail for missing risk label (that's handled by Check 3: Label Validation)
