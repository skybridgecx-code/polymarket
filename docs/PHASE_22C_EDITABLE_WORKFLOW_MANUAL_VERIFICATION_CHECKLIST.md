# Phase 22C Editable Workflow Manual Verification Checklist

## Scope

Manual verification checklist for the local editable operator decision workflow.

This is docs-only. No runtime behavior changes.

## Preconditions

- Repo is on `phase-22c-editable-workflow-manual-verification-checklist`.
- Virtual environment is active.
- You have a valid `OpportunityContextBundle` JSON file.
- You have a writable local artifacts directory.

## Checklist

### 1. Verify repo state

Run:

`git status -sb`

Expected:

- branch is `phase-22c-editable-workflow-manual-verification-checklist`
- no unexpected dirty files before manual verification

### 2. Generate artifacts with review metadata

Run CLI artifact generation with `--initialize-operator-review`.

Expected files:

- `X.json`
- `X.md`
- `X.operator_review.json`

Expected companion metadata:

- `review_status` is `pending`
- `operator_decision` is `null`
- artifact `run_id` matches generated run id

### 3. Launch local operator UI

Set `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT` to the artifact directory and launch the operator UI.

Expected:

- app starts locally
- root page loads
- artifacts root status is configured/readable

### 4. Verify list page

Open `/`.

Expected:

- generated run appears
- review status displays `pending`
- success/failure status remains visible

### 5. Verify detail page

Open `/runs/X`.

Expected:

- artifact detail loads
- operator review metadata section appears
- edit form appears
- fields are prefilled from `X.operator_review.json`

### 6. Submit decided update

Use the edit form to set:

- `review_status`: `decided`
- `operator_decision`: `approve`, `reject`, or `needs_follow_up`
- optional notes
- optional reviewer identity

Expected:

- POST redirects back to detail page
- detail page shows updated values
- `X.operator_review.json` is rewritten
- base `X.json` and `X.md` are not modified

### 7. Submit pending update

Use the edit form to set:

- `review_status`: `pending`
- blank operator decision
- blank notes/reviewer if desired

Expected:

- POST redirects back to detail page
- `operator_decision` becomes `null`
- `decided_at_epoch_ns` becomes `null`
- failure-stage metadata remains preserved for failed runs

### 8. Verify missing metadata error

Generate artifacts without `--initialize-operator-review`, then attempt an update.

Expected:

- update fails with bounded `Review Update Error`
- error mentions `operator_review_metadata_missing`
- no companion file is implicitly created

### 9. Verify malformed metadata error

Corrupt `X.operator_review.json`, then load detail/update.

Expected:

- artifact visibility remains bounded
- malformed metadata is surfaced as an operator error state
- no production or trading behavior occurs

## Validation Commands

Run after manual verification:

`pytest tests/future_system/test_operator_review_models.py tests/future_system/test_operator_review_update_helpers.py tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`

`ruff check src/future_system/operator_review_models src/future_system/review_artifacts src/future_system/cli/review_artifacts.py src/future_system/operator_ui tests/future_system/test_operator_review_models.py tests/future_system/test_operator_review_update_helpers.py tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`

`mypy src/future_system/operator_review_models src/future_system/review_artifacts src/future_system/cli/review_artifacts.py src/future_system/operator_ui`

## Boundaries

- no DB
- no queues/jobs/scheduling
- no notifications/delivery/inbox
- no production trading/execution
- no `src/polymarket_arb/*` integration
