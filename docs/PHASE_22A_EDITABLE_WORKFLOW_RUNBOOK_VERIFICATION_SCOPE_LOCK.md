# Phase 22A Editable Workflow Runbook Verification Scope Lock

## Repo / Branch / Phase

- Repo: `polymarket-arb`
- Branch: `phase-22a-editable-workflow-runbook-verification-scope-lock`
- Phase: `22A — editable workflow runbook verification scope lock`
- Source checkpoint: `phase-21f-editable-decision-workflow-closeout`

## Objective

Create a bounded docs/manual-verification track for the shipped local editable operator decision workflow.

The goal is not to add features. The goal is to make the local workflow easy to run, verify, troubleshoot, and hand off.

## Baseline Entering 22A

The current local workflow supports:

- CLI artifact generation
- optional `--initialize-operator-review`
- companion `X.operator_review.json` metadata
- operator UI list/detail pages
- edit form rendering
- POST update flow for existing companion metadata
- deterministic companion metadata rewrite
- integration test coverage

## Allowed Work

- Update `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- Add manual verification checklists
- Add local operator step-by-step workflows
- Add troubleshooting notes for editable decision updates
- Add docs-only phase checkpoints

## Forbidden Work

- no `src/polymarket_arb/*` changes
- no `src/future_system/*` behavior changes
- no tests changed unless a later explicit verification phase allows docs/test alignment only
- no DB
- no queues/jobs/scheduling
- no notifications/delivery/inbox
- no production trading/execution
- no product integration claims

## Candidate Phases After 22A

1. **22B — Editable Workflow Runbook Polish**  
   Update the local runbook with exact editable-decision workflow steps.

2. **22C — Manual Verification Checklist**  
   Add a checklist for CLI generation, metadata initialization, UI edit, POST update, and error states.

3. **22D — Troubleshooting / Operator Recovery Notes**  
   Document missing metadata, malformed metadata, failed updates, and target subdirectory cases.

4. **22E — Final Manual Verification Checkpoint**  
   Record final validation/manual verification commands and boundaries.

## Acceptance Criteria

The track is complete when an operator can:

- generate artifacts locally
- initialize review metadata
- launch UI
- inspect run detail
- update review decision fields
- verify the companion JSON changed
- recover from missing/malformed metadata errors
- understand that no production execution/trading behavior is involved

## Decision Gate

Before 22B, continue only if the goal remains docs/manual-verification polish. Any new runtime behavior requires a fresh scope lock.
