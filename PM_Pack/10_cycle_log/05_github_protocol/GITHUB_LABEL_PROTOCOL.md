# GITHUB LABEL PROTOCOL
# Added: Cycle 019

---

## Current Status

61 labels are deployed on KevinSGarrett/Fiverr as of Cycle 019. All 44 spec-defined labels plus 17 operational labels are active.

---

## Applying Labels to PRs

Every PR must have at minimum:
- One `type:*` label
- One `priority:*` label
- One `scope:*` label
- One `agent:*` label

Add labels before or immediately after opening the PR. The pr-checks.yml workflow may read label state.

### Command Line
```bash
gh pr edit {NUMBER} --add-label "type:feature,priority:P3-medium,scope:epic02,agent:2-collection"
```

---

## Applying Labels to Issues

Same rules apply. Use Jira for detailed tracking; GitHub labels are for triage and filtering.

---

## Deploying New Labels

If a new label needs to be added to the 61-label set:

```bash
gh label create "new-label-name" --color "hex-color" --description "Description" --repo KevinSGarrett/Fiverr
```

Then update `ref/github/10_repo_files/.github/labels.json` and `ref/github/03_labels/LABEL_TAXONOMY.md`.

---

## Full Label Reference

See `ref/github/03_labels/LABEL_TAXONOMY.md` for complete taxonomy with colors and descriptions.
