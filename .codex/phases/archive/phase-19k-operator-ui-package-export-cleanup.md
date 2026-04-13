# Phase 19K — Operator UI Package/Export Cleanup

## Goal

Clean up the `operator_ui` package structure so exports and import paths are easier to maintain without changing behavior.

This phase is about bounded package/export cleanup only.

18Y–19J established the operator UI read, trigger, detail, helper extraction, template extraction, styling cleanup, route cleanup, and app-wiring cleanup flows.
19K should improve package ergonomics and internal structure while preserving current operator-visible behavior.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- current `__init__.py` exports and import paths across the operator UI package
- directly relevant tests for the current UI surface

## Required deliverable

Build a bounded cleanup pass that:

- cleans up `operator_ui` exports where appropriate
- reduces awkward import paths across operator UI modules where appropriate
- centralizes public package entrypoints where appropriate
- preserves existing list/detail/trigger behavior
- preserves current success/failure and failure-stage rendering behavior
- keeps reads/writes bounded to the configured/local artifacts root
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- small package export/helper adjustments if clearly justified
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

Use the repo’s existing package pattern.
Prefer the smallest possible bounded refactor.

A good result is:

- cleaner `operator_ui/__init__.py`
- cleaner internal imports
- clearer public package entrypoints
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

## Acceptance criteria

This phase is complete when:

- the operator UI package/export structure is cleaner and easier to consume
- current UI behavior remains intact for valid and invalid root/artifact states
- success and failure outputs still clearly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- tests cover unchanged behavior after the cleanup
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
