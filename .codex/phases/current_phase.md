# Phase 21B — Decision Update/Write Helper Contracts

## Goal

Add deterministic local helper contracts for validating and writing updates to existing
`X.operator_review.json` companion metadata files.

This phase is helper-contract focused (no UI form/POST flow yet).

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_21A_EDITABLE_OPERATOR_DECISION_WORKFLOW_SCOPE_LOCK.md`
- `docs/PHASE_20B_OPERATOR_REVIEW_DECISION_METADATA_CONTRACTS.md`
- `src/future_system/operator_review_models/*`
- `src/future_system/review_artifacts/operator_review_metadata.py`
- `src/future_system/operator_ui/artifact_reads.py`
- `tests/future_system/test_operator_review_models.py`
- `tests/future_system/test_review_artifacts_flow.py`
- `tests/future_system/test_operator_review_workflow_integration.py`

## Required deliverable

Add deterministic update/write helpers for existing companion metadata files.

Suggested module:

- `src/future_system/operator_review_models/updates.py`

Define a bounded update-input contract for editable fields only:

- `review_status`
- `operator_decision`
- `review_notes_summary`
- `reviewer_identity`

Helper behavior must:

- read existing `X.operator_review.json`
- validate existing file as `OperatorReviewDecisionRecord`
- apply editable-field update only
- preserve non-editable/system-owned fields
- write replacement JSON deterministically
- reject missing companion file
- reject malformed companion file
- reject out-of-root paths / unsafe symlink targets
- reject writes when target is not a regular file

Timestamp policy must be explicit and deterministic:

- `pending` clears `operator_decision` and `decided_at_epoch_ns`
- `decided` requires `operator_decision`
- `decided_at_epoch_ns` set/kept by deterministic rule
- `updated_at_epoch_ns` comes from explicit caller-provided timestamp (never wall clock)

## Tests required

Add focused tests for:

- pending update clears decision and decided timestamp
- decided update requires decision
- decided update sets timestamps deterministically from explicit input
- non-editable fields are preserved
- missing/malformed/out-of-root/non-file targets reject safely
- serialized JSON shape is stable

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- add DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic
- add UI form or POST route behavior in 21B

Keep this phase file-based helper contracts only.

## Validation

Run:

- `pytest tests/future_system/test_operator_review_models.py tests/future_system/test_operator_review_update_helpers.py`
- `ruff check src/future_system/operator_review_models tests/future_system/test_operator_review_models.py tests/future_system/test_operator_review_update_helpers.py`
- `mypy src/future_system/operator_review_models`

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
