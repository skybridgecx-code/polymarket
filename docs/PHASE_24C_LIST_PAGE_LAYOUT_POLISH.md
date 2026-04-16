# Phase 24C List Page Layout Polish

## Scope

Layout/accessibility polish for the local operator UI list page.

## What Changed

- Added a caption to the local review runs table.
- Added a caption to the run file issues table.
- Added `aria-describedby` relationships for trigger form controls:
  - `context_source`
  - `target_subdirectory`
  - `analyst_mode`
- Added `role="alert"` to trigger error messaging.
- Added focused rendered-structure assertions.

## Boundaries Preserved

- no runtime capability expansion
- no POST/update behavior changes
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

- `39 passed, 1 warning`
- `ruff`: all checks passed
- `mypy`: success, no issues found in 9 source files
