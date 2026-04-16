# Phase 23C List/Detail Page Copy Polish

## Scope

Copy/UX polish for the local operator UI list and detail read surfaces.

## What Changed

- Renamed `Review Artifacts` to `Local Review Runs`.
- Renamed `Review Artifact Detail` to `Local Review Run Detail`.
- Renamed `Run Issues` to `Run File Issues`.
- Renamed `Operator Review Metadata` to `Operator Decision Review`.
- Renamed `Failure Context` to `Failure Explanation`.
- Renamed artifact content headings to `Artifact Evidence`, `Markdown Evidence`, and `JSON Evidence`.
- Improved trigger helper text and empty-list wording.
- Added friendlier display label for `no-review-metadata` as `No review metadata`.

## Boundaries Preserved

- no runtime capability expansion
- no `src/polymarket_arb/*` changes
- no DB
- no queues/jobs/scheduling
- no notifications/delivery
- no production trading/execution

## Validation

- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `mypy src/future_system/operator_ui`

## Result

- `38 passed, 1 warning`
- `ruff`: all checks passed
- `mypy`: success, no issues found in 9 source files
