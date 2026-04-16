# Phase 25A — Local Operator UI Evidence / Smoke-Capture Scope Lock

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-25a-local-operator-ui-evidence-scope-lock`
- Phase: `25A — local operator UI evidence / smoke-capture scope lock`
- Source checkpoint: `phase-24f-layout-accessibility-closeout`

## Why this phase exists
Phases 20A–24F delivered the local operator review workflow, editable decision flow, supporting docs, copy polish, and layout/accessibility polish for the `future_system` local operator UI track.

This phase does **not** expand product behavior. It locks the final evidence-oriented scope for manual smoke capture and release-style verification artifacts so the shipped operator UI track can be documented cleanly.

## In scope
- Define the evidence capture goals for the local operator UI track.
- Define the manual smoke walkthrough surfaces that should be captured.
- Define the screenshot/evidence artifact list.
- Define the release-style checklist items that verify shipped behavior.
- Keep the scope limited to docs/evidence planning only.

## Out of scope
- No runtime code changes.
- No template/UI wording changes.
- No test changes.
- No changes under `src/polymarket_arb/*`.
- No DB, queue, scheduling, notification, inbox, or background-job work.
- No production trading or execution work.
- No new product capabilities beyond the existing local artifact-file workflow.

## Existing shipped behavior this phase assumes
- Local review run list/detail pages exist.
- Operator decision review metadata renders in the detail page.
- Editable decision form exists and persists updates through the local companion metadata workflow.
- Copy polish from 23A–23F is already shipped.
- Layout/accessibility polish from 24A–24F is already shipped.
- Validation baseline at close of 24F:
  - `pytest tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
  - `ruff check src/future_system/operator_ui tests/future_system/test_operator_ui_review_artifacts.py tests/future_system/test_operator_review_workflow_integration.py`
  - `mypy src/future_system/operator_ui`

## Planned evidence areas for later phases
- List page screenshot/evidence capture.
- Detail page screenshot/evidence capture.
- Update Decision form screenshot/evidence capture.
- Empty/missing metadata state capture where applicable.
- Trigger/create flow smoke evidence where applicable.
- Final manual verification and release-style checklist alignment.

## Deliverable for 25A
- A locked scope document for the evidence/smoke-capture track only.

## Exit criteria
- Scope is explicitly documented.
- Boundaries are explicit.
- No runtime behavior is changed.
- The next phase can proceed with evidence inventory/capture planning without reopening UI implementation scope.
