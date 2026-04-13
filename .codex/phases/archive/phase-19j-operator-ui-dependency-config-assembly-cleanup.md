# Phase 19J — Operator UI Dependency and Config Assembly Cleanup

## Goal

Clean up operator UI app wiring so dependency/config assembly is easier to maintain without changing behavior.

This phase is about bounded app-factory/config cleanup only.

18Y–19I established the operator UI read, trigger, history, detail, helper extraction, template extraction, styling cleanup, and route-module cleanup flows.
19J should improve app wiring structure and maintainability while preserving current operator-visible behavior.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- the current app factory/config/dependency assembly in `review_artifacts.py`
- directly relevant tests for the current UI list/detail/trigger/root-state surface

## Required deliverable

Build a bounded cleanup pass that:

- extracts app wiring/dependency assembly into smaller focused helper(s) or module(s) where appropriate
- centralizes config/default handling for the operator UI app where appropriate
- keeps app factory code focused on assembly rather than inline setup detail
- preserves existing list/detail/trigger behavior
- preserves current success/failure and failure-stage rendering behavior
- keeps reads/writes bounded to the configured/local artifacts root
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- creation of small config/dependency helper modules/files if clearly justified
- minimal test updates strictly needed to preserve and verify unchanged behavior

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add background jobs, queues, or scheduling
- add delivery/inbox/notification systems
- add execution/trading behavior
- change the underlying generation pipeline
- widen scope into UI redesign or new features
- allow reads/writes outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded refactor.

A good result is:

- smaller/more focused `review_artifacts.py`
- one or more small helper modules for app wiring/config/default assembly
- unchanged route behavior
- deterministic tests proving behavior stayed intact

## Behavioral requirements

The implementation must preserve this contract:

1. Existing artifact files remain the source of truth.
2. UI remains downstream of the existing generation flow.
3. UI does not regenerate or mutate artifacts outside the existing trigger flow.
4. Success and failure results remain clearly distinct.
5. Failure-stage identity remains exact.
6. Reads/writes remain bounded to the configured/local artifacts root.
7. Operator-visible behavior remains materially unchanged except for safe cleanup side effects.

UI/cleanup requirements:

- must preserve `theme_id` visibility
- must preserve status / failure-stage context
- must preserve run list/detail/trigger behavior
- must preserve safe missing/invalid/unreadable root handling
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- the operator UI dependency/config assembly is cleaner and more modular
- current UI behavior remains intact for valid and invalid root/artifact states
- success and failure outputs still clearly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- tests cover unchanged list/detail/trigger/root-state behavior after the cleanup
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched operator UI files
- touched tests

Use the repo’s normal validation commands for the touched UI surface, plus targeted tests.

## Required Codex return format

Return only:

1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched
