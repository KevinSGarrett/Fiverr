# Issue Templates
# Fiverr Research System — 5 GitHub Issue Templates

---

## Overview

All issue templates are placed in `.github/ISSUE_TEMPLATE/` as YAML form files.
GitHub renders them as structured forms when creating a new issue.

---

## Template 1: Bug Report (`bug_report.yml`)

```yaml
name: Bug Report
description: Report a bug or unexpected behavior
title: "[BUG] "
labels: ["issue:bug", "priority:P3-medium"]
body:
  - type: markdown
    attributes:
      value: |
        ## Bug Report
        Please fill out the sections below so the agent can reproduce and fix the issue.

  - type: input
    id: summary
    attributes:
      label: Summary
      description: One-line description of the bug
      placeholder: "Gig detail workflow crashes on gigs without package pricing"
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      description: Exact steps to trigger the bug
      placeholder: |
        1. Run `python run.py --mode full --niche "prd-ai-saas"`
        2. Wait for gig detail stage (Stage 5)
        3. Observe crash on gig ID xyz123
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should happen?
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happens? Include error messages or stack traces.
    validations:
      required: true

  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options:
        - "P1 — Blocks all work / production broken"
        - "P2 — Blocks current epic progress"
        - "P3 — Important but not blocking"
        - "P4 — Minor / cosmetic"
    validations:
      required: true

  - type: dropdown
    id: epic
    attributes:
      label: Affected Epic
      options:
        - "Epic 01 — Foundation"
        - "Epic 02 — Collection"
        - "Epic 03 — Analysis"
        - "Epic 04 — Scoring"
        - "Epic 05 — Recommendations"
        - "Epic 06 — Pricing"
        - "Epic 07 — Discovery"
        - "Epic 08 — Playbook"
        - "Epic 09 — Dashboard"
        - "Epic 10 — Integration"
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant Logs / Screenshots
      description: Paste error output, stack traces, or screenshots
      render: shell

  - type: textarea
    id: context
    attributes:
      label: Additional Context
      description: Any other information (config values, data state, environment)
```

---

## Template 2: Feature Request (`feature_request.yml`)

```yaml
name: Feature Request
description: Suggest a new feature or enhancement
title: "[FEATURE] "
labels: ["issue:enhancement", "priority:P3-medium"]
body:
  - type: textarea
    id: description
    attributes:
      label: Feature Description
      description: What feature do you want and why?
      placeholder: "Add a CSV export option for the opportunity rankings page..."
    validations:
      required: true

  - type: textarea
    id: use_case
    attributes:
      label: Use Case
      description: Who benefits and how will it be used?
    validations:
      required: true

  - type: textarea
    id: acceptance
    attributes:
      label: Acceptance Criteria
      description: How do we know this is done?
      placeholder: |
        - [ ] CSV export button on opportunities page
        - [ ] Exports all visible columns with current filters
        - [ ] File named with timestamp
    validations:
      required: true

  - type: dropdown
    id: epic
    attributes:
      label: Target Epic
      options:
        - "Epic 01 — Foundation"
        - "Epic 02 — Collection"
        - "Epic 03 — Analysis"
        - "Epic 04 — Scoring"
        - "Epic 05 — Recommendations"
        - "Epic 06 — Pricing"
        - "Epic 07 — Discovery"
        - "Epic 08 — Playbook"
        - "Epic 09 — Dashboard"
        - "Epic 10 — Integration"
        - "New / Cross-cutting"
    validations:
      required: true

  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives Considered
      description: Any other approaches you thought about?
```

---

## Template 3: Implementation Task (`task.yml`)

```yaml
name: Implementation Task
description: A specific development task (story or sub-task)
title: "[TASK] "
labels: ["issue:task", "priority:P3-medium"]
body:
  - type: input
    id: story_id
    attributes:
      label: Story / Task ID
      description: Reference from the To-Do epic file (e.g., S1.2, T1.2.3)
      placeholder: "S4.1 or T4.1.1"
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Task Description
      description: What needs to be implemented?
    validations:
      required: true

  - type: textarea
    id: acceptance
    attributes:
      label: Definition of Done
      description: Copy from the DOD file or write specific acceptance criteria
      placeholder: |
        - [ ] DemandScoreCalculator class created in src/scoring/demand.py
        - [ ] Accepts KeywordScoreInput, returns DemandScore (0-100)
        - [ ] All 4 components implemented per DEMAND_SCORE.md
        - [ ] Unit tests with ≥90% coverage on this module
    validations:
      required: true

  - type: dropdown
    id: epic
    attributes:
      label: Epic
      options:
        - "Epic 01 — Foundation"
        - "Epic 02 — Collection"
        - "Epic 03 — Analysis"
        - "Epic 04 — Scoring"
        - "Epic 05 — Recommendations"
        - "Epic 06 — Pricing"
        - "Epic 07 — Discovery"
        - "Epic 08 — Playbook"
        - "Epic 09 — Dashboard"
        - "Epic 10 — Integration"
    validations:
      required: true

  - type: dropdown
    id: agent
    attributes:
      label: Assigned Agent
      options:
        - "Agent 1 — Infrastructure"
        - "Agent 2 — Collection"
        - "Agent 3 — Analysis/Scoring"
        - "Agent 4 — Dashboard/UX"
        - "Unassigned"
    validations:
      required: true

  - type: textarea
    id: spec_refs
    attributes:
      label: Spec References
      description: Which project-pack documents define the requirements?
      placeholder: |
        - project-pack/05_scoring/DEMAND_SCORE.md (Section 3-5)
        - project-pack/05_scoring/SCORING_SYSTEM.md (weight profiles)

  - type: textarea
    id: dependencies
    attributes:
      label: Dependencies / Blockers
      description: List any issues or stories that must be completed first
      placeholder: "Depends on #12 (database models)"
```

---

## Template 4: Epic Tracker (`epic.yml`)

```yaml
name: Epic Tracker
description: Track progress of an entire epic
title: "[EPIC] "
labels: ["issue:epic", "priority:P2-high"]
body:
  - type: input
    id: epic_number
    attributes:
      label: Epic Number
      placeholder: "01"
    validations:
      required: true

  - type: input
    id: epic_name
    attributes:
      label: Epic Name
      placeholder: "Foundation & Infrastructure"
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Epic Description
      description: High-level summary of what this epic delivers
    validations:
      required: true

  - type: textarea
    id: stories
    attributes:
      label: Stories Checklist
      description: List all stories with issue links (update as issues are created)
      placeholder: |
        - [ ] #XX S1.1 — Project Scaffolding
        - [ ] #XX S1.2 — Configuration System
        - [ ] #XX S1.3 — Database Models
        - [ ] #XX S1.4 — CLI Entry Point
        - [ ] #XX S1.5 — LLM Client
        - [ ] #XX S1.6 — Shared Utilities
        - [ ] #XX S1.7 — Seed Data
    validations:
      required: true

  - type: textarea
    id: completion_criteria
    attributes:
      label: Epic Completion Criteria
      description: When is this epic done?
      placeholder: |
        - [ ] All stories merged to develop
        - [ ] Integration tests pass
        - [ ] Release PR merged to main
        - [ ] Tagged as v0.1.0
    validations:
      required: true
```

---

## Template 5: Spike / Research (`spike.yml`)

```yaml
name: Spike / Research
description: Time-boxed research or investigation task
title: "[SPIKE] "
labels: ["issue:spike", "type:spike", "priority:P3-medium"]
body:
  - type: textarea
    id: question
    attributes:
      label: Research Question
      description: What are we trying to learn or decide?
      placeholder: "Can we use Playwright's route interception to cache Fiverr API responses?"
    validations:
      required: true

  - type: input
    id: timebox
    attributes:
      label: Time Box
      description: Maximum time to spend before reporting findings
      placeholder: "4 hours"
    validations:
      required: true

  - type: textarea
    id: approach
    attributes:
      label: Investigation Approach
      description: How will the agent investigate this?
      placeholder: |
        1. Read Playwright route interception docs
        2. Build minimal proof-of-concept
        3. Test with 3 Fiverr search pages
        4. Measure response times with and without cache

  - type: textarea
    id: deliverables
    attributes:
      label: Expected Deliverables
      description: What should the spike produce?
      placeholder: |
        - Written findings in a comment on this issue
        - Go/No-Go recommendation
        - If Go: prototype code in a branch
    validations:
      required: true

  - type: dropdown
    id: epic
    attributes:
      label: Related Epic
      options:
        - "Epic 01 — Foundation"
        - "Epic 02 — Collection"
        - "Epic 03 — Analysis"
        - "Epic 04 — Scoring"
        - "Epic 05 — Recommendations"
        - "Epic 06 — Pricing"
        - "Epic 07 — Discovery"
        - "Epic 08 — Playbook"
        - "Epic 09 — Dashboard"
        - "Epic 10 — Integration"
        - "Cross-cutting"
    validations:
      required: true
```
