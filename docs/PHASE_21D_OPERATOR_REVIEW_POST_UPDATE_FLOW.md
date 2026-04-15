# Phase 21D Operator Review POST Update Flow

## Scope

Phase 21D adds the bounded local POST/update flow for existing operator review companion metadata files.

## What Changed

- Added `POST /runs/{run_id}/operator-review/update`.
- The route updates an existing `X.operator_review.json` companion file only.
- Update requests use the Phase 21B helper contract.
- Successful updates redirect back to the run detail page.
- Target subdirectory context is preserved when provided.
- Missing companion metadata fails safely with a bounded operator error page.

## Boundaries Preserved

- no DB persistence
- no queues/jobs/scheduling
- no notification/delivery/inbox workflow
- no production execution/trading behavior
- no `src/polymarket_arb/*` integration
- no writes to base artifact markdown/json files

## Validation

- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_update_helpers.py`
- `ruff check src/future_system/operator_ui src/future_system/operator_review_models tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_update_helpers.py`
- `mypy src/future_system/operator_ui src/future_system/operator_review_models`

## Result

- `38 passed, 1 warning`
- `ruff`: all checks passed
- `mypy`: success, no issues found in 13 source files
