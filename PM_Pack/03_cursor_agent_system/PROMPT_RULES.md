# PROMPT RULES — Preventing Shallow Cursor Prompts

Version: Cycle 012 governance correction

---

## Minimum Requirements Per Cursor-Agent Prompt

| Metric | Minimum | Target | Maximum |
|---|---:|---:|---:|
| Total word count per agent prompt | 6,000 | 8,000-12,000 | No hard cap if organized |
| Substantive tasks per prompt | 20 | 24-32 | 40 |
| Words per substantive task | 150 | 250-500 | No hard cap |
| Tests/validation expectations per task | 2 | 3-6 | As needed |
| Jira keys per task | 1 | 1-3 | As needed |
| AC/DoD references per task | 1 | 1-3 | As needed |
| Files listed | Every file touched | Every file touched | Required |

## Binding Prompt-Quality Rules

Every normal cycle must produce long-form, self-contained Cursor prompts. Each prompt must be detailed enough that a Cursor agent can execute without PM follow-up for missing scope.

A prompt is rejected if:

1. it contains fewer than 20 substantive tasks and lacks both required waivers;
2. it fails to include exact Jira keys;
3. it fails to embed exact AC/DoD bullets in each task;
4. it fails to specify whether the agent must perform Jira operations;
5. it fails to include branch, commit, PR, CI, Codecov, and Codex expectations;
6. it omits local validation commands;
7. it omits final report requirements and path;
8. it omits file ownership boundaries;
9. it instructs the agent to push to main;
10. it relies on vague instructions such as "continue", "as needed", or "same as before";
11. it plans from Git/PR deltas before Jira board issue selection.

## Required Cursor-Agent Jira Statement

Every prompt must contain this exact section:

> Jira access: You are allowed to use the connected Jira board when this prompt explicitly assigns Jira work to you. You may read Jira issues, inspect statuses, create issues, update issue fields when appropriate, add comments, transition issues, and maintain Jira mapping evidence. You must follow the PM-defined Jira AC/DoD rules. Do not mark a broad product story Done unless the full source DoD is met. For partial work, use In Progress or In Review as instructed.

## Prompt Generation Checklist (Required)

Before release, every prompt must explicitly include:

1. exact Jira issue keys in scope;
2. exact AC bullets per task;
3. exact DoD bullets per task;
4. exact files (or Jira-only scope);
5. required validation/tests per task;
6. final report file path;
7. stop conditions;
8. branch and PR target expectations (`develop` target only).

## Prompt Rejection Checklist (Shallow Prompt Gate)

Reject the prompt immediately if any of the following is true:

1. fewer than 6,000 words without both waivers;
2. fewer than 20 substantive tasks without both waivers;
3. Jira keys listed only in a header but not mapped per task;
4. AC/DoD listed at top-level but not embedded per task;
5. file list is broad/non-specific;
6. tests are generic ("run tests") instead of explicit commands;
7. Jira language is vague ("update relevant tickets", "handle Jira as needed");
8. final report requirements are missing;
9. no board-audit expectation or no documented scope-limit rationale.

## Required Structure for Every Agent Prompt

1. Mission.
2. Branch and repo context.
3. Jira authority statement.
4. Jira issues and AC/DoD bullets.
5. File ownership boundaries.
6. Non-overlap constraints.
7. 20-40 numbered substantive tasks.
8. Validation commands.
9. Jira update instructions.
10. Git commit instructions.
11. Final report path.
12. Stop conditions.
13. Done criteria.

## No Shallow Prompt Rule

A prompt that merely lists high-level goals is invalid. A prompt must explain implementation intent, quality gates, Jira evidence, and success criteria for every assigned task.
