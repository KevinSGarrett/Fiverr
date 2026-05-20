# PM REPLY CHECKLIST
# The PM MUST pass ALL items before sending a reply. If ANY item fails, fix before sending.

---

## Section 1: Structure (6 gates)
- [ ] Reply contains CYCLE HEADER with cycle number and date
- [ ] Reply contains REVIEW SECTION for previous agent work (or "Cycle 001 — no prior work")
- [ ] Reply contains JIRA UPDATE SECTION with all ticket changes
- [ ] Reply contains 4 AGENT PROMPTS (Agent A, B, C, D)
- [ ] Reply contains GITHUB OPERATOR WORKFLOW with exact push/PR/merge/main-promotion instructions
- [ ] Reply contains STATE UPDATE summary
- [ ] Reply contains NEXT CYCLE PREVIEW (what the next cycle will focus on)

## Section 2: Agent Prompts (11 gates)
- [ ] All 4 agent prompts follow PROMPT_TEMPLATE.md format exactly
- [ ] All 4 agent prompts are >=6,000 words each unless both waivers are present; target 8,000-12,000 words each
- [ ] All 4 agent prompts include exact branch name: cycle/{NNN}/integration
- [ ] All 4 agent prompts include file paths for ALL files to create/modify
- [ ] All 4 agent prompts include spec references (project-pack path)
- [ ] All 4 agent prompts include DOD criteria from DOD files
- [ ] All 4 agent prompts include specific test requirements with descriptions
- [ ] No two agents have overlapping file assignments
- [ ] Dependency order is respected
- [ ] Each agent has >=20 substantive tasks assigned (target 24-32, max 40); any exception has explicit TASK-COUNT WAIVER and PROMPT-DETAIL WAIVER
- [ ] No prohibited patterns used (see PROMPT_RULES.md)
- [ ] Jira responsibility is explicit in each prompt and follows CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md
- [ ] Every task embeds exact Jira key(s), AC bullets, and DoD bullets
- [ ] Prompt includes final report path and stop conditions

## Section 3: Jira (5 gates)
- [ ] All tasks worked on this cycle have updated Jira status
- [ ] All completed tasks have Jira comments with cycle #, agent, branch
- [ ] Any new issues discovered have new Jira tickets created
- [ ] Epic tracker tickets have updated progress percentages
- [ ] No Jira ticket left in intermediate state from prior cycles
- [ ] PM response includes board audit findings or explicit scope-limit rationale
- [ ] Governance/cycle ticket updates do not replace product-story updates

## Section 4: Review (4 gates — when reviewing prior work)
- [ ] Each agent's work reviewed against their DOD criteria
- [ ] Confidence scores assigned (0-100) per agent
- [ ] Any rework needed captured as tasks for this or next cycle
- [ ] QA gates checklist run for each agent

## Section 5: State (4 gates)
- [ ] STATE_SNAPSHOT.md changes documented
- [ ] EPIC_STATUS_TRACKER.md updated
- [ ] CYCLE_LOG entry prepared for 10_cycle_log/
- [ ] HYDRATION_HEADER.md updated if focus area changed

## Section 6: GitHub / PR / Main Governance (7 gates)
- [ ] Cycle reply states agents do NOT push directly to main
- [ ] Cycle reply states agents usually do not push at all; human operator pushes one cycle branch after all agent commits
- [ ] Cycle reply includes exact `git push -u origin cycle/{NNN}/integration` command
- [ ] Cycle reply includes exact PR source/target: `cycle/{NNN}/integration` -> `develop`
- [ ] Cycle reply includes PR title and body template
- [ ] Cycle reply states squash merge to `develop` only after CI/review gates pass
- [ ] Cycle reply states `main` is promoted only by approved release PR from `develop` after release gates pass
- [ ] Cycle reply confirms uncommitted local work has been checked against live PR scope

## Section 7: Completeness (4 gates)
- [ ] No placeholder text ("TBD", "TODO", "fill in later", "same as before")
- [ ] No vague instructions ("do the usual", "handle it", "implement the system")
- [ ] All file paths are absolute (starting from src/ or tests/)
- [ ] All spec references use full relative path from ref/

---

## Total Gates: 42
## Pass Threshold: ALL must be checked
## If ANY gate fails: Fix before sending reply


## Cycle 001 Corrective Gate

Before sending any future cycle reply, the PM must ask: “Would Kevin reasonably consider these Cursor prompts high-detail, high-substance, and long enough for autonomous execution?” If no, regenerate the prompts. Passing the mechanical checklist is not enough.
