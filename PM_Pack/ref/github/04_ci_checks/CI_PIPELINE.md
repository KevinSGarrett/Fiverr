# CI/CD Pipeline
# Fiverr Research System — GitHub Actions Workflows

---

## Pipeline Architecture

```
On PR (to develop or main):
  ├── ci.yml
  │   ├── lint (Ruff)
  │   ├── type-check (Mypy)
  │   └── test (Pytest + coverage)
  ├── pr-checks.yml
  │   ├── validate-title
  │   ├── validate-labels
  │   ├── validate-size
  │   ├── validate-description
  │   └── suggest-risk
  └── security.yml
      ├── secret-scan
      └── dependency-check

On push to main:
  └── release.yml
      ├── tag-version
      └── generate-changelog

On schedule (daily):
  └── stale.yml
      └── mark-stale-prs-and-issues
```

---

## Workflow 1: ci.yml (Main CI Pipeline)

**Triggers:** Pull request to `develop` or `main`, push to `develop`
**Required for merge:** YES — all 3 jobs must pass

### Job: `lint`
```yaml
name: CI
on:
  pull_request:
    branches: [develop, main]
  push:
    branches: [develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install Ruff
        run: pip install ruff
      - name: Run Ruff linter
        run: ruff check src/ tests/ --output-format=github
      - name: Run Ruff formatter check
        run: ruff format src/ tests/ --check
```

### Job: `type-check`
```yaml
  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install mypy
      - name: Run Mypy
        run: mypy src/ --ignore-missing-imports --strict
```

### Job: `test`
```yaml
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=src \
            --cov-report=xml \
            --cov-report=term-missing \
            --cov-fail-under=80 \
            -v
      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage.xml
```

---

## Workflow 2: pr-checks.yml (PR Validation)

**Triggers:** Pull request opened, edited, labeled, unlabeled, synchronize
**Required for merge:** YES

### Checks Performed:

**1. Title Validation**
- Matches regex: `^(feat|fix|refactor|test|docs|chore|style|perf|ci|build|release|hotfix|revert)(\([a-z0-9-]+\))?: .+$`
- Total length ≤ 72 characters
- Fail with clear error message showing expected format

**2. Description Validation**
- PR body is not empty
- PR body has ≥ 50 characters (more than just the template headers)
- Contains "## What" section (from template)

**3. Label Validation**
- Has exactly 1 `type:*` label
- Has exactly 1 `priority:*` label
- Has at least 1 `scope:*` label
- Has exactly 1 `risk:*` label
- Post comment listing missing required labels

**4. Size Calculation & Label**
- Count additions + deletions (excluding exempted files)
- Remove any existing `size:*` labels
- Apply correct `size:*` label
- If `size:XXL` → post warning comment + block merge unless `override:large-pr` present

**5. Risk Suggestion**
- Analyze changed file paths
- Post comment suggesting risk level if no `risk:*` label present

---

## Workflow 3: security.yml (Security Scanning)

**Triggers:** Pull request to `develop` or `main`
**Required for merge:** NO (advisory, but failures flagged)

### Checks:
**1. Secret Scanning**
```yaml
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for secrets
        run: |
          # Check for common secret patterns
          if grep -rn "sk-[a-zA-Z0-9]" src/ tests/ --include="*.py"; then
            echo "::error::Potential OpenAI API key found in source code"
            exit 1
          fi
          if grep -rn "password\s*=" src/ tests/ --include="*.py" | grep -v "test\|mock\|example"; then
            echo "::error::Potential hardcoded password found"
            exit 1
          fi
```

**2. Dependency Vulnerability Check**
```yaml
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install pip-audit
        run: pip install pip-audit
      - name: Audit dependencies
        run: pip-audit -r requirements.txt
```

---

## Workflow 4: release.yml

**Triggers:** Push to `main` (after release PR merge)
**Purpose:** Auto-tag releases

```yaml
on:
  push:
    branches: [main]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Get version from latest commit message
        id: version
        run: |
          # Extract version from release commit message
          MSG=$(git log -1 --pretty=%B)
          # Expect format: "release: epic XX ..."
          echo "message=$MSG" >> $GITHUB_OUTPUT
      - name: Create GitHub Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: auto  # Version determined by commit
          release_name: ${{ steps.version.outputs.message }}
          draft: false
          prerelease: true
```

---

## Workflow 5: stale.yml

**Triggers:** Daily schedule (cron)
**Purpose:** Mark stale PRs and issues

```yaml
on:
  schedule:
    - cron: '0 9 * * *'  # 9 AM UTC daily

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/stale@v9
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          stale-pr-message: 'This PR has been inactive for 3 days. Please update, reduce scope, or close.'
          stale-pr-label: 'status:stale'
          days-before-pr-stale: 3
          days-before-pr-close: 7
          stale-issue-message: 'This issue has been inactive for 7 days.'
          stale-issue-label: 'status:stale'
          days-before-issue-stale: 7
          days-before-issue-close: 30
          exempt-pr-labels: 'status:blocked,status:on-hold'
          exempt-issue-labels: 'issue:epic,status:blocked'
```

---

## CI Performance Budget

| Job | Target Duration | Hard Limit |
|---|---|---|
| lint | < 30 seconds | 2 minutes |
| type-check | < 2 minutes | 5 minutes |
| test | < 5 minutes | 10 minutes |
| pr-checks | < 1 minute | 3 minutes |
| security | < 2 minutes | 5 minutes |
| **Total pipeline** | **< 10 minutes** | **20 minutes** |
