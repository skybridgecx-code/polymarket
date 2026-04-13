# Phase 20C Operator UI Decision/Status Rendering

## Scope

Phase 20C adds read-only operator review decision/status rendering to the local `future_system`
operator UI when companion metadata files are present.

This phase stays local and artifact-file based:

- no DB persistence
- no queues/jobs/scheduling
- no delivery/inbox wiring
- no execution/trading logic
- no UI edit/write flow

## Companion Metadata Convention

For artifact run id `X`, the UI now looks for an optional companion metadata file:

- `X.operator_review.json`

Discovery is bounded to the configured artifacts root.

If companion metadata is missing:

- list/detail rendering continues normally
- review status is shown as `no-review-metadata`

If companion metadata is malformed:

- artifact list/detail still render
- bounded issue context is surfaced without breaking artifact display

## Rendering Surface Added

List view now includes review status per run:

- `pending`
- `decided`
- `no-review-metadata`

Detail view now includes an **Operator Review Metadata** section with:

- review status
- operator decision
- review notes summary
- reviewer identity
- decided/updated epoch-ns timestamps when present

Existing success/failure-stage rendering remains unchanged.

## Safety Boundaries

- no required dependency on decision metadata for existing artifacts
- malformed companion metadata is bounded and non-fatal for artifact display
- companion metadata path resolution is bounded under artifacts root

## Tests Added/Updated

- `tests/future_system/test_operator_ui_review_artifacts.py`

Coverage includes:

- no companion metadata
- valid pending metadata
- valid decided metadata
- malformed metadata
- out-of-root companion metadata path attempt (bounded)

## Local Checkpoint

20C is a local operator UI read-only rendering checkpoint, not a production-readiness claim.
