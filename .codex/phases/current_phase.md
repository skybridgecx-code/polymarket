# Phase 20D — CLI/Artifact Review Workflow Alignment

## Goal

Align CLI/local artifact generation with the operator review metadata contract by adding an
explicit opt-in path that initializes companion operator review metadata files next to generated
artifacts.

Default behavior must remain unchanged.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`
- `docs/PHASE_20B_OPERATOR_REVIEW_DECISION_METADATA_CONTRACTS.md`
- `docs/PHASE_20C_OPERATOR_UI_DECISION_STATUS_RENDERING.md`
- `src/future_system/operator_review_models/*`
- `src/future_system/review_artifacts/*`
- `src/future_system/review_entrypoints/*`
- `src/future_system/cli/review_artifacts.py`
- `src/future_system/operator_ui/artifact_reads.py`
- `tests/future_system/test_operator_review_models.py`
- relevant tests for `review_artifacts` / `review_entrypoints` / CLI surfaces

## Required deliverable

Add deterministic helper support so generated artifact run id `X` can also initialize:

- `X.operator_review.json`

Initialized companion metadata must:

- validate as `OperatorReviewDecisionRecord`
- be initialized as `review_status="pending"`
- derive from existing artifact payload + run id
- write only under explicit target directory bounds
- avoid silent overwrite (must be explicit and tested if allowed)

Wire this through generation path with explicit opt-in:

- CLI flag: `--initialize-operator-review`
- default remains no companion metadata writes

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- add DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic
- add UI editing/write flow
- widen scope beyond local artifact-file workflow alignment

## Tests required

Add deterministic tests for:

- default CLI/artifact path does not write companion review metadata
- opt-in writes valid pending companion metadata
- existing companion metadata is not silently overwritten
- failed artifacts preserve `failure_stage` in initialized review metadata
- no writes outside target directory

## Validation

Run:

- `pytest` on touched `future_system` tests
- `ruff check` on touched files
- `mypy` on touched `future_system` modules

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
