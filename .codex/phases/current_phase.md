# Phase 19P — Operator UI Integration-Flow Test Hardening

## Goal

Add bounded integration-style tests that lock in the currently shipped operator UI read/trigger/detail and mount behavior without introducing runtime behavior changes.

This phase is primarily tests plus phase-file update.

## Read first

Before implementing, read:

- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- `src/future_system/operator_ui/app_entry.py`
- `src/future_system/operator_ui/review_artifacts.py`
- `src/future_system/operator_ui/route_handlers.py`
- `src/future_system/operator_ui/app_wiring.py`
- `tests/future_system/test_operator_ui_review_artifacts.py`
- `tests/future_system/test_operator_ui_app_entry.py`
- `tests/future_system/test_operator_ui_app_wiring.py`

## Required deliverable

Build a bounded integration-flow test pass that covers:

- `create_operator_ui_app` exposing shipped routes
- `mount_operator_ui_app` default-path mounting behavior
- `GET /` root/list rendering for configured readable root
- `POST /runs/trigger` redirect/handoff into `GET /runs/{run_id}`
- detail visibility for success and failure-stage outcomes
- default trigger target subdirectory (`operator_runs`)
- top-level list visibility behavior for triggered subdirectory runs
- bounded root-status messaging for not-configured/missing/invalid roots

## Scope allowed

Allowed work in this phase:

- update this phase file
- add one bounded integration-style operator UI test module
- minimal test-only helper additions in that new test module

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic
- change shipped behavior unless a tiny non-behavioral testability seam is required
- drift beyond operator UI integration-flow hardening

## Validation

Run exactly:

- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_ui_app_wiring.py tests/future_system/test_operator_ui_package_exports.py tests/future_system/test_operator_ui_app_entry.py tests/future_system/test_operator_ui_integration_flows.py`
- `ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_ui_app_wiring.py tests/future_system/test_operator_ui_package_exports.py tests/future_system/test_operator_ui_app_entry.py tests/future_system/test_operator_ui_integration_flows.py`
- `mypy src/future_system/operator_ui`

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. any risks/deferred items
5. do not commit unless asked
