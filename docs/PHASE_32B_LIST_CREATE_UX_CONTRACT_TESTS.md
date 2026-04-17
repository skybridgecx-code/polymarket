# Phase 32B — List/Create UX Contract Tests

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-32b-list-create-ux-contract-tests`
- Phase: `32B — list/create UX contract tests`
- Source checkpoint: `32A — local review runs list/create UX scope lock`

## Purpose
Phase 32B adds focused contract coverage for the shipped local operator UI list page and create-run form before later template polish in 32C.

The goal is to lock meaningful operator-facing list/create labels, sections, form fields, and error recovery context without brittle full-page snapshots.

## What Tests Were Added
Added focused list/create UX contract tests in `tests/future_system/test_operator_ui_review_artifacts.py`:

- `test_operator_ui_list_create_contract_core_sections_and_fields`
  - locks core list/create visibility and form field presence:
    - `Local Review Runs`
    - `Create Local Review Run`
    - `Artifacts Root Status` / `Configured Value`
    - `Context Source JSON Path` + `name="context_source"`
    - `Target Subdirectory` + `name="target_subdirectory"`
    - `Analyst Mode` + `name="analyst_mode"`
    - `Run Analysis`
    - runs-table caption when runs exist

- `test_operator_ui_list_create_contract_empty_state_when_no_runs`
  - locks empty state with no runs discovered:
    - `No local review runs found.`
    - list/create context still visible

- `test_operator_ui_list_create_contract_trigger_error_preserves_recovery_context`
  - locks trigger error clarity and recovery context:
    - `Trigger Error`
    - `Invalid trigger input:`
    - `role="alert"`
    - list/create headings and form fields still present for operator recovery

## Why This Protects 32C
These contracts preserve key operator-facing list/create behavior so 32C copy/layout polish can be made safely without regressing:

- primary page/context labels
- create form field identifiers
- empty-state discoverability
- runs-table visibility
- trigger error clarity and recoverability

## Boundaries Preserved
- No runtime UI/template implementation changes.
- No changes under `src/polymarket_arb/*`.
- No evidence screenshot changes.
- No DB, queue, job, notification, scheduling, production-trading, or execution behavior changes.
- No browser/e2e dependency added.

## Validation Commands / Results
Run:
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `mypy src/future_system/operator_ui`

Results:
- `pytest ...`: `45 passed, 1 warning`
- `ruff check ...`: passed (`All checks passed!`)
- `mypy src/future_system/operator_ui`: passed (`Success: no issues found in 9 source files`)

Known warning:
- `PendingDeprecationWarning` from `starlette.formparsers`.
