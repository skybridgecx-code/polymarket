# Phase 31B — Run Detail UX Contract Tests

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-31b-run-detail-ux-contract-tests`
- Phase: `31B — run detail UX contract tests`
- Source checkpoint: `phase-31a-run-detail-ux-improvement-scope-lock`

## Purpose
Phase 31B adds focused contract coverage for the shipped `future_system` local operator UI run detail page before later UX/template polish.

The goal is to protect important operator-facing labels, sections, and states while avoiding brittle full-page HTML snapshots.

## What changed
Added focused run detail UX tests covering:

- Detail page title:
  - `Local Review Run Detail`
- Navigation:
  - `Back to local review runs`
- Operator review section:
  - `Operator Decision Review`
- Populated metadata state:
  - existing companion review metadata renders
  - update form is available
- Empty/no metadata state:
  - `No review metadata`
  - decision form unavailable message
- Editable form contract:
  - `Update Decision`
  - `Save Local Decision`
  - `Decision Notes`
  - `Reviewer`
  - `name="review_notes_summary"`
  - `name="reviewer_identity"`
- Artifact/run context:
  - `Artifact Paths`
  - `Markdown Path`
  - `JSON Path`
  - `Decision Metadata Path`
  - run id visible
- Error state:
  - missing run returns clear `Run Read Error`
  - includes `artifact_run_not_found: json file is missing.`
  - preserves back link

## Files changed
- `tests/future_system/test_operator_ui_review_artifacts.py`
- `.codex/phases/current_phase.md`
- `docs/PHASE_31B_RUN_DETAIL_UX_CONTRACT_TESTS.md`

## Boundaries preserved
- No runtime UI/template implementation changes.
- No changes under `src/polymarket_arb/*`.
- No evidence screenshot changes.
- No DB, queue, job, notification, scheduling, production-trading, or execution behavior.
- No browser/e2e dependency added.

## Why this protects 31C
These tests lock the key user-facing contracts that later run-detail UX polish should preserve or intentionally update:
- core page title/navigation
- review metadata visibility
- empty metadata state
- edit form availability
- form field names
- artifact path context
- missing-run error clarity

## Validation
Run:
- `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
- `mypy src/future_system/operator_ui`

Known warning:
- `PendingDeprecationWarning` from `starlette.formparsers`
