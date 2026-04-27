# Phase 36C — CLI Packaging Implementation

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-36c-cli-packaging-implementation`
- Phase: `36C — CLI packaging implementation`
- Source checkpoint: `phase-36b-cli-packaging-contract`

## Purpose
This phase implements the first operator-facing CLI entrypoint for the bounded local review outcome packaging flow.

## What was added
- `src/future_system/cli/review_outcome_package.py`
- focused CLI tests in:
  - `tests/future_system/test_review_outcome_package_cli.py`

## Behavior
The CLI:
- accepts `--run-id`
- accepts `--artifacts-root`
- accepts optional `--target-root`
- resolves reviewed run artifacts from the artifacts root
- calls the existing local packaging module
- prints created package paths on success
- prints a clear operator-facing error and returns non-zero on failure

## Boundaries preserved
- local artifact-file workflow only
- no UI changes
- no remote delivery
- no DB, queue, scheduling, notification, inbox, or background-job work
- no `src/polymarket_arb/*` changes
- no production trading or execution behavior

## Validation
Run:
- `pytest tests/future_system/test_review_outcome_package_cli.py tests/future_system/test_operator_review_outcome_packaging.py tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `ruff check src/future_system tests/future_system/test_review_outcome_package_cli.py tests/future_system/test_operator_review_outcome_packaging.py tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `mypy src/future_system`

## Expected next step
- add manual smoke coverage for the CLI entrypoint
- then close out the CLI packaging entrypoint track
