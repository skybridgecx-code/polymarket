# Phase 24A Operator UI Layout/Accessibility Scope Lock

## Repo / Branch / Phase

- Repo: `polymarket-arb`
- Branch: `phase-24a-operator-ui-layout-accessibility-scope-lock`
- Source checkpoint: `phase-23f-ui-copy-ux-closeout`
- Phase: `24A — operator UI layout/accessibility scope lock`

## Objective

Define a bounded polish track for the local `future_system` operator UI layout and accessibility.

The goal is to make the existing local operator workflow easier to scan and use without adding runtime capabilities.

## Baseline Entering 24A

Current shipped local workflow includes:

- CLI artifact generation
- optional `X.operator_review.json` initialization
- local operator UI list/detail pages
- operator decision metadata rendering
- editable decision form
- POST update flow for existing companion metadata
- deterministic metadata rewrite
- copy/UX polish and copy contract tests
- runbook/manual verification/troubleshooting docs

## Allowed Work

- local UI layout polish in `src/future_system/operator_ui/*`
- accessible label/help text improvements
- heading hierarchy cleanup
- table scanability improvements
- form grouping and guidance improvements
- error-page readability improvements
- focused tests for rendered structure/copy where useful
- docs updates if operator behavior/readability changes

## Forbidden Work

- no `src/polymarket_arb/*` changes
- no DB persistence
- no queues/jobs/scheduling
- no notifications/delivery/inbox
- no production trading/execution behavior
- no new agent behavior
- no new background processing
- no new data model fields unless separately scoped
- no runtime capability expansion

## Candidate Phases After 24A

1. **24B — Layout/Accessibility Inventory**  
   Review current rendered HTML structure, headings, tables, forms, and error pages.

2. **24C — List Page Layout Polish**  
   Improve run-list table scanability, root status, trigger form grouping, and empty states.

3. **24D — Detail/Edit Page Layout Polish**  
   Improve detail page sections, decision review readability, and edit-form grouping.

4. **24E — Accessibility/Test Hardening**  
   Add focused tests for important structure, labels, and preserved copy.

5. **24F — Layout/Accessibility Closeout**  
   Document final behavior, validation, and remaining boundaries.

## Acceptance Criteria

The track is complete when:

- UI is easier to scan locally
- form controls have clear labels/help text
- important sections are easier to navigate
- error states remain bounded and understandable
- no runtime scope is expanded
- validation remains green

## Decision Gate

Proceed to 24B only if the goal remains layout/accessibility polish. Any new runtime behavior requires a fresh scope lock.
