# Phase 23D Editable Decision Form Copy Polish

## Scope

Copy/UX polish for the editable operator decision form and update-error surfaces.

## What Changed

- Renamed `Operator Review Edit Form` to `Update Operator Decision`.
- Renamed form labels from review metadata language to decision-focused language.
- Improved edit-form intro copy to explain local companion-file updates.
- Clarified pending vs decided decision behavior.
- Changed submit button copy to `Save Local Decision`.
- Changed update error title from `Review Update Error` to `Decision Update Error`.
- Improved missing-metadata guidance for runs without companion review metadata.
- Updated tests to lock the new rendered copy.

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
