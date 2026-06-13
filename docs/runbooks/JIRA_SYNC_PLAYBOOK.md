# Jira Sync Playbook

## Purpose

This runbook defines the safe process for Jira synchronization during cycle operations, including credential verification, issue discovery, transition execution, and evidence comments. It exists to prevent accidental transitions on incorrect issues and to keep DOD evidence auditable.

## Preflight

Load runner secrets and confirm `JIRA_API_TOKEN` is present before any write operations. Run a read-only query first to verify connectivity and project visibility. Never start with bulk transitions; always identify target keys explicitly and validate summary text and status.

## Safe Transition Procedure

Build a candidate issue list using deterministic queries. For each issue, log key, summary, and status before transition. Apply transition ID only after matching the issue to cycle evidence. After transition, re-read status and post a concise evidence comment referencing the exact report file used for completion proof.

## Commenting Standards

Comments should include what changed, why transition is valid, and where evidence is stored. Avoid vague “done” comments without artifacts. If required issue keys are missing or return 404, stop and document the mismatch rather than guessing alternative keys.

## Failure Handling

If API calls return authorization or not-found errors, capture HTTP code and endpoint. Validate base URL and account scope. If issue keys are not present in the active project, document it in cycle evidence and do not force transitions. This protects workflow integrity and prevents false completion claims.

## Audit Trail

Store all transition and comment outcomes in the cycle Jira sync report. A complete audit trail includes attempted keys, responses, final status, and unresolved blockers.
