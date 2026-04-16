# Phase 23A Operator UI Copy/UX Polish Scope Lock

## Repo / Branch / Phase

- Repo: `polymarket-arb`
- Branch: `phase-23a-operator-ui-copy-ux-polish-scope-lock`
- Source checkpoint: `phase-22e-editable-workflow-verification-closeout`
- Phase: `23A — operator UI copy/UX polish scope lock`

## Objective

Define a bounded UI polish track for the local `future_system` operator UI.

The goal is to make the existing local operator workflow clearer, safer, and easier to use without adding new runtime capabilities.

## Baseline Entering 23A

Current shipped local workflow includes:

- CLI artifact generation
- optional `X.operator_review.json` initialization
- operator UI list/detail pages
- review metadata rendering
- editable operator review form
- POST update flow for existing companion metadata
- deterministic metadata rewrite
- integration tests
- runbook/manual verification/troubleshooting docs

## Allowed Work

- copy polish in `src/future_system/operator_ui/*`
- local UI label/help text improvements
- clearer empty states and error messages
- clearer review-status/decision wording
- minor layout/template polish if bounded
- focused tests for changed rendered text/behavior
- docs updates if wording changes affect operator runbook

## Forbidden Work

- no `src/polymarket_arb/*` changes
- no DB persistence
- no queues/jobs/scheduling
- no notifications/delivery/inbox
- no production trading/execution behavior
- no new agent behavior
- no new background processing
- no new data model fields unless separately scoped

## Candidate Phases After 23A

1. **23B — Operator UI Copy Inventory**  
   Review current list/detail/edit/error copy and document exact copy changes.

2. **23C — List/Detail Page Copy Polish**  
   Improve headings, labels, helper text, and empty/error states for read-only surfaces.

3. **23D — Editable Decision Form Copy Polish**  
   Improve edit-form guidance, validation wording, and update success/error language.

4. **23E — Copy/UX Test Hardening**  
   Lock important rendered copy and boundaries with focused tests.

5. **23F — UI Copy/UX Closeout**  
   Document final behavior, validation, and remaining boundaries.

## Acceptance Criteria

The track is complete when:

- operator UI text is clearer and more consistent
- decision/update actions are easier to understand
- error states explain what happened and what to do next
- no runtime scope is expanded
- validation remains green

## Decision Gate

Proceed to 23B only if the goal remains copy/UX polish. Any new runtime behavior requires a fresh scope lock.
