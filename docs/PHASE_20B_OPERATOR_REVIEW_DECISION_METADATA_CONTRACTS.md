# Phase 20B Operator Review Decision Metadata Contracts

## Scope

Phase 20B introduces a bounded contract surface for local operator review decision metadata in `future_system`.

This phase is contract/model/docs/tests focused:

- no DB persistence
- no background jobs/queues/scheduling
- no delivery/inbox mechanisms
- no execution/trading behavior
- no `src/polymarket_arb/*` integration

## Contract Surface Added

- `src/future_system/operator_review_models/models.py`
- `src/future_system/operator_review_models/builder.py`
- `src/future_system/operator_review_models/__init__.py`

Core concepts:

- `OperatorReviewArtifactReference`
- `OperatorReviewDecisionRecord`
- `build_initial_operator_review_decision_record(...)`

## Deterministic Metadata Concepts

The contract provides deterministic, file-safe metadata fields for:

- review status (`pending` | `decided`)
- operator decision (`approve` | `reject` | `needs_follow_up`)
- optional review notes summary
- optional reviewer identity
- optional local-safe epoch-ns timestamps
- optional run flag snapshot from artifact payload

Relationship to existing artifact files:

- references existing run identity (`run_id`, `theme_id`)
- references existing export semantics (`status`, `export_kind`, optional `failure_stage`)
- supports initialization from current artifact JSON payloads

## Backward-Safe Behavior

- review metadata is additive and optional; existing artifact read/list/detail flow is unchanged
- success/failure-stage semantics stay aligned with existing export payload contracts
- failed artifacts require explicit failure stage in the review metadata reference

## Test Coverage Added

- `tests/future_system/test_operator_review_models.py`

Coverage includes:

- valid status/decision combinations
- invalid status/decision and status/failure-stage combinations
- deterministic serialization shape
- optional/backward-safe behavior
- initialization from success/failure artifact payload shapes

## Out Of Scope In 20B

- UI editing or mutable workflow machinery
- persistence backends
- async orchestration
- production-readiness claims

20B is a local contract checkpoint only.
