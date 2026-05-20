# Release Process
# Fiverr Research System — Versioning, Tagging, and Changelog

---

## Version Numbering

### Scheme: Semantic Versioning (Modified)
```
v{major}.{minor}.{patch}

During development (pre-v1.0.0):
  v0.{epic_number}.{patch}
  
  v0.1.0  — Epic 01 complete (Foundation)
  v0.1.1  — Hotfix to Epic 01
  v0.2.0  — Epic 02 complete (Collection)
  v0.3.0  — Epic 03 complete (Analysis)
  v0.4.0  — Epic 04 complete (Scoring)
  v0.5.0  — Epic 05 complete (Recommendations)
  v0.6.0  — Epic 06 complete (Pricing)
  v0.7.0  — Epic 07 complete (Discovery)
  v0.8.0  — Epic 08 complete (Playbook)
  v0.9.0  — Epic 09 complete (Dashboard)
  v0.10.0 — Epic 10 complete (Integration & Launch)

Production:
  v1.0.0  — First production release (after validation run)
  v1.0.1  — Patch fix
  v1.1.0  — New feature addition
```

---

## Release Types

### 1. Epic Release (v0.X.0)
**When:** After all stories in an epic are merged to develop and integration tests pass.

**Process:**
```
1. Verify all epic stories are merged to develop
   - Check: all issues for the epic are closed
   - Check: no open PRs targeting develop for this epic

2. Run full test suite on develop
   git checkout develop
   git pull origin develop
   pytest tests/ --cov=src --cov-fail-under=80 -v

3. Create release PR: develop → main
   Title: "release: v0.{epic}.0 — Epic {NN}: {Name}"
   Body: 
     ## Release: v0.{epic}.0
     ### Epic {NN}: {Name}
     
     ### Stories Included
     - S{N}.1: {description} (#issue)
     - S{N}.2: {description} (#issue)
     - ...
     
     ### Breaking Changes
     - None / list any
     
     ### Migration Required
     - None / list steps
     
   Labels: type:release, priority:P2-high, scope:epic{NN}-{name}, risk:high

4. Human operator reviews the release PR
   - Verify story list is complete
   - Verify integration tests pass
   - Verify no P1/P2 issues remain open for this epic

5. Squash merge to main

6. Tag the release
   git checkout main
   git pull origin main
   git tag -a v0.{epic}.0 -m "Epic {NN}: {Name}"
   git push origin v0.{epic}.0

7. Create GitHub Release
   - Go to: GitHub → Releases → Draft a new release
   - Tag: v0.{epic}.0
   - Title: "v0.{epic}.0 — Epic {NN}: {Name}"
   - Body: Copy from PR description
   - Mark as: Pre-release (until v1.0.0)

8. Update CHANGELOG.md on develop
   git checkout develop
   git pull origin develop
   # Add release entry to CHANGELOG.md
   git add CHANGELOG.md
   git commit -m "docs: update changelog for v0.{epic}.0"
   git push origin develop
```

### 2. Hotfix Release (v0.X.Y)
**When:** Critical bug found in main that can't wait for next epic release.

**Process:**
```
1. Create hotfix branch from main
   git checkout main
   git pull origin main
   git checkout -b hotfix/description

2. Implement fix with tests

3. Create PR: hotfix → main
   Title: "hotfix: {description}"
   Labels: type:hotfix, priority:P1-critical, risk:critical

4. After merge, tag:
   git tag -a v0.{epic}.{patch+1} -m "Hotfix: {description}"
   git push origin v0.{epic}.{patch+1}

5. Cherry-pick to develop:
   git checkout develop
   git cherry-pick {commit-sha}
   git push origin develop

6. Update CHANGELOG.md
```

### 3. Production Release (v1.0.0)
**When:** All 10 epics complete, first full validation run successful.

**Process:** Same as epic release but:
- More thorough testing (full integration + performance benchmarks)
- Mark as "Latest release" (not pre-release)
- Update README.md with production status
- Archive all pre-release tags

---

## CHANGELOG.md Format

```markdown
# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- ...

### Changed
- ...

### Fixed
- ...

## [v0.2.0] — 2025-XX-XX — Epic 02: Collection Engine

### Added
- Playwright session manager with persistent browser context (S2.1)
- Fiverr CSS selector library with 30+ selectors (S2.2)
- Pacing manager with human-like delays (S2.3)
- Queue processor with priority scheduling (S2.4)
- Checkpoint manager for crash recovery (S2.5)
- Proxy layer with pluggable interface (S2.6)
- 8 collection workflows: keyword expansion, fiverr search, gig detail,
  seller profile, google trends, reddit signals, autocomplete, auto-promotion
  (S2.7 through S2.14)

### Changed
- Updated config schema with collection settings
- Extended Job model with workflow-specific fields

### Fixed
- None

## [v0.1.0] — 2025-XX-XX — Epic 01: Foundation & Infrastructure

### Added
- Project scaffolding with directory structure
- Configuration system with Pydantic v2 models
- 28 SQLAlchemy ORM models
- CLI entry point with Click
- LLM client wrapper with caching
- Structured logging system
- 9-niche seed configuration
```

---

## Release Checklist

### Pre-Release (before creating release PR)
- [ ] All epic stories merged to develop
- [ ] All epic issues closed
- [ ] Full test suite passes on develop
- [ ] Coverage ≥ 80%
- [ ] No open P1/P2 issues for this epic
- [ ] No TODO/FIXME comments from this epic remain
- [ ] Documentation updated for new features

### Release PR
- [ ] PR title follows release convention
- [ ] PR body lists all stories with issue links
- [ ] Breaking changes documented
- [ ] Migration steps documented (if any)
- [ ] Labels applied: type:release, priority, scope, risk:high

### Post-Release
- [ ] Version tag created and pushed
- [ ] GitHub Release created
- [ ] CHANGELOG.md updated on develop
- [ ] Team notified (ChatGPT PM updates project board)
