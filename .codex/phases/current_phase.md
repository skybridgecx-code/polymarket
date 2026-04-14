# Phase 20F — Decision Workflow Closeout Checkpoint

## Goal

Close out the Phase 20A–20F `future_system` operator decision/review workflow hardening track
as a local artifact-file-based readiness checkpoint.

This phase is documentation/manual-verification only.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`
- `docs/PHASE_20B_OPERATOR_REVIEW_DECISION_METADATA_CONTRACTS.md`
- `docs/PHASE_20C_OPERATOR_UI_DECISION_STATUS_RENDERING.md`
- `docs/PHASE_20D_CLI_ARTIFACT_REVIEW_WORKFLOW_ALIGNMENT.md`
- `docs/PHASE_20E_DETERMINISTIC_DECISION_WORKFLOW_TEST_HARDENING.md`
- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`

## Required deliverable

Add:

- `docs/PHASE_20F_DECISION_WORKFLOW_CLOSEOUT_CHECKPOINT.md`

The closeout checkpoint must capture:

- repo/branch/phase context
- what Phase 20A–20F delivered
- current local workflow
  - artifact generation
  - optional `--initialize-operator-review`
  - companion `X.operator_review.json`
  - UI read-only list/detail rendering
  - no-overwrite behavior
  - failure-stage preservation
- explicit out-of-scope boundaries
  - UI edit/write decisions
  - DB persistence
  - queues/jobs/scheduling
  - notifications/delivery
  - production trading/execution
  - `src/polymarket_arb` integration
- safety boundaries
- final validation commands
- recommended next decision:
  - stop/keep checkpoint or start a new bounded track

If runbook wording needs tiny docs-only polish for final workflow clarity, update it; otherwise
leave it unchanged.

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
