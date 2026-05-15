# PM CORRECTIVE RULES — CYCLE 006

## Trigger
Cycle 005 governance work was merged, but a valid Codex thread from PR #4 remained unresolved/outdated and the underlying defect still existed on `develop`. Live GitHub also showed Codecov patch status, while project coverage status was not clearly visible.

## Permanent Rule
Outdated Codex review threads are not automatically ignorable. The Integration/GitHub Steward must review every Codex thread, including outdated threads, and determine whether the underlying issue still exists in the current target branch. If the issue still exists, it is a blocker until fixed or explicitly deferred by PM/operator approval.

## Codecov Rule
Local coverage >=90% is necessary but not sufficient. PRs must also surface required GitHub/Codecov statuses. If Codecov project coverage status is missing, the PR is blocked unless PM/operator grants a documented temporary exception.

## PM Pack Rule
Every PM cycle handoff must include the updated PM Pack zip and the full cycle response/prompts artifact.
