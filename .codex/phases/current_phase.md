# Phase 21A — Editable Operator Decision Workflow Scope Lock

## Goal

Define a bounded scope lock for the next local-only track: editable operator decisions written to
artifact companion metadata files.

This phase is docs-only.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_20F_DECISION_WORKFLOW_CLOSEOUT_CHECKPOINT.md`
- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`
- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- `docs/PHASE_20B_OPERATOR_REVIEW_DECISION_METADATA_CONTRACTS.md`
- `docs/PHASE_20C_OPERATOR_UI_DECISION_STATUS_RENDERING.md`
- `docs/PHASE_20D_CLI_ARTIFACT_REVIEW_WORKFLOW_ALIGNMENT.md`
- `docs/PHASE_20E_DETERMINISTIC_DECISION_WORKFLOW_TEST_HARDENING.md`

## Required deliverable

Add:

- `docs/PHASE_21A_EDITABLE_OPERATOR_DECISION_WORKFLOW_SCOPE_LOCK.md`

Define the next track clearly:

- local UI form for editing `X.operator_review.json`
- allowed decision fields
- validation rules
- deterministic overwrite/update behavior
- no DB or production workflow
- no trading/execution behavior
- file-based only
- safety constraints for path handling and malformed existing files

Include candidate phases:

- 21B decision update/write helper contracts
- 21C operator UI edit form rendering
- 21D POST handler/update flow
- 21E workflow test hardening
- 21F closeout checkpoint

Keep scope factual and bounded. Do not claim production readiness.

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- touch `src/future_system/*`
- touch `tests/*`
- add features
- add DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic

## Validation

Run:

- `git diff --stat`
- `git diff --name-only`

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
