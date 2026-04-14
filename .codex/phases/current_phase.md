# Phase 20E — Deterministic Decision Workflow Test Hardening

## Goal

Harden deterministic tests across the full local operator review decision metadata path introduced
in 20B–20D.

Focus is tests/docs with local artifact-file workflow invariants locked end-to-end.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`
- `docs/PHASE_20B_OPERATOR_REVIEW_DECISION_METADATA_CONTRACTS.md`
- `docs/PHASE_20C_OPERATOR_UI_DECISION_STATUS_RENDERING.md`
- `docs/PHASE_20D_CLI_ARTIFACT_REVIEW_WORKFLOW_ALIGNMENT.md`
- `src/future_system/operator_review_models/*`
- `src/future_system/review_artifacts/operator_review_metadata.py`
- `src/future_system/review_artifacts/flow.py`
- `src/future_system/cli/review_artifacts.py`
- `src/future_system/operator_ui/artifact_reads.py`
- `tests/future_system/test_operator_review_models.py`
- `tests/future_system/test_review_artifacts_flow.py`
- `tests/future_system/test_review_cli_review_artifacts.py`
- `tests/future_system/test_operator_ui_review_artifacts.py`
- `tests/future_system/test_operator_ui_integration_flows.py`

## Required deliverable

Add/expand deterministic tests to lock the end-to-end local decision metadata workflow:

- CLI with `--initialize-operator-review` writes companion metadata
- operator UI list/detail render initialized metadata as `pending`
- failed artifact initialized metadata preserves `failure_stage` through CLI -> file -> UI
- default path still writes no companion metadata
- existing companion metadata no-overwrite behavior remains preserved
- malformed companion metadata remains bounded/non-fatal
- out-of-root metadata read/write safety behavior does not regress

Prefer one integration-style test module when cleaner:

- `tests/future_system/test_operator_review_workflow_integration.py`

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- add DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic
- add UI editing/write flow
- widen scope beyond deterministic local decision workflow test hardening

Avoid production code changes unless a tiny non-behavioral test seam is absolutely required.

## Validation

Run:

- `pytest tests/future_system/test_operator_review_models.py tests/future_system/test_review_artifacts_flow.py tests/future_system/test_review_cli_review_artifacts.py tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_ui_integration_flows.py tests/future_system/test_operator_review_workflow_integration.py`
- `ruff check src/future_system/operator_review_models src/future_system/review_artifacts src/future_system/cli/review_artifacts.py src/future_system/operator_ui tests/future_system/test_operator_review_models.py tests/future_system/test_review_artifacts_flow.py tests/future_system/test_review_cli_review_artifacts.py tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_ui_integration_flows.py tests/future_system/test_operator_review_workflow_integration.py`
- `mypy src/future_system/operator_review_models src/future_system/review_artifacts src/future_system/cli/review_artifacts.py src/future_system/operator_ui`

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
