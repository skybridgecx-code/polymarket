# Phase 21B Decision Update/Write Helper Contracts

## Scope

Phase 21B adds deterministic local helper contracts for updating existing operator review
companion metadata files (`X.operator_review.json`).

This phase is helper-model/tests/docs only:

- no UI form rendering
- no POST route wiring
- no DB persistence
- no queues/jobs/scheduling
- no delivery/inbox infrastructure
- no execution/trading behavior
- no `src/polymarket_arb/*` changes

## Helper Surface Added

- `src/future_system/operator_review_models/updates.py`

Core additions:

- `OperatorReviewDecisionUpdateInput`
- `apply_operator_review_decision_update(...)`
- `update_existing_operator_review_metadata_companion(...)`
- `render_operator_review_decision_record_json(...)`

## Editable-Field Update Contract

Editable fields accepted in updates:

- `review_status`
- `operator_decision`
- `review_notes_summary`
- `reviewer_identity`
- explicit caller-provided `updated_at_epoch_ns`

System-owned fields are preserved from existing metadata:

- `record_kind`, `record_version`
- `artifact` reference block
- `run_flags_snapshot`

## Deterministic Timestamp Policy

- when `review_status` is set to `pending`:
  - `operator_decision` is cleared
  - `decided_at_epoch_ns` is cleared
- when `review_status` is set to `decided`:
  - `operator_decision` is required
  - `decided_at_epoch_ns` is kept if already present
  - otherwise `decided_at_epoch_ns` is set to `updated_at_epoch_ns`
- `updated_at_epoch_ns` is never derived from wall clock; caller must provide it explicitly

## File Safety / Path Boundaries

Update helper behavior is bounded:

- target must be under explicit `target_directory` bounds
- missing companion file is rejected
- malformed existing companion metadata is rejected
- out-of-root resolved paths (including unsafe symlink targets) are rejected
- non-file targets are rejected
- replacement file content is rendered with deterministic sorted JSON shape

## Tests Added

- `tests/future_system/test_operator_review_update_helpers.py`

Coverage includes:

- pending update clearing decision/decided timestamp
- decided update requiring decision
- deterministic decided-at/updated-at behavior from explicit input
- preservation of non-editable/system-owned fields
- missing/malformed/out-of-root/non-file rejection behavior
- stable deterministic serialized JSON shape

## Local Checkpoint

21B is a local deterministic helper-contract checkpoint for editable decision metadata updates.
It does not add UI edit flow or production workflow behavior.
