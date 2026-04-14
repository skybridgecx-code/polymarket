# Phase 20D CLI/Artifact Review Workflow Alignment

## Scope

Phase 20D aligns local artifact generation with the operator review metadata contract by adding an
explicit opt-in path to initialize companion operator review metadata files.

This phase remains local and artifact-file based:

- no DB persistence
- no queues/jobs/scheduling
- no delivery/inbox wiring
- no execution/trading logic
- no UI edit/write flow

## Companion Metadata Initialization Convention

For generated artifact run id `X`, opt-in initialization writes:

- `X.operator_review.json`

The companion payload is initialized as:

- `record_kind=operator_review_decision_record`
- `record_version=1`
- `review_status=pending`
- artifact reference derived from generated export payload + run id

For failed artifacts, initialized metadata preserves:

- `artifact.status=failed`
- `artifact.failure_stage=<generated failure stage>`

## CLI Integration

The CLI now supports an explicit opt-in flag:

- `--initialize-operator-review`

Default behavior remains unchanged:

- CLI still writes only markdown/json review artifacts unless opt-in is provided.

## Safety Behavior

- companion writes are bounded to the explicit target directory
- existing companion metadata files are not overwritten silently
- overwrite attempts return a deterministic validation error

## Tests Added/Updated

- `tests/future_system/test_review_artifacts_flow.py`
- `tests/future_system/test_review_cli_review_artifacts.py`

Coverage includes:

- default no companion metadata write
- opt-in pending companion metadata creation
- failure-stage preservation for initialized failed metadata
- no silent overwrite for existing companion metadata
- bounded path/write behavior

## Local Checkpoint

20D is a local workflow-alignment checkpoint that keeps artifact-file boundaries intact and does
not change non-opt-in generation behavior.
