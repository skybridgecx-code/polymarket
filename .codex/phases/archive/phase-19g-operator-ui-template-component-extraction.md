# Phase 19G — Operator UI Template/Component Extraction

## Goal

Extract the growing HTML/rendering blocks out of the operator UI route/module so the UI surface is easier to maintain without changing behavior.

This phase is about bounded rendering refactor/cleanup only.

18Y–19F established the operator UI read, trigger, history, detail, root-status, and helper extraction flows.
19G should improve rendering structure and maintainability while preserving current operator-visible behavior.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- any rendering/template logic currently embedded in `review_artifacts.py`
- directly relevant tests for the current UI list/detail/trigger surface

## Required deliverable

Build a bounded cleanup pass that:

- extracts repeated or large HTML/rendering blocks into bounded helper(s)
- extracts repeated status/badge/section rendering where appropriate
- keeps route handlers focused on request/response flow instead of large inline rendering blocks
- preserves existing list/detail/trigger behavior
- preserves current success/failure and failure-stage rendering behavior
- keeps reads/writes bounded to the configured/local artifacts root
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- creation of small rendering helper modules/files if clearly justified
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
- one or more small helper modules for HTML/rendering sections
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

- the operator UI rendering logic is cleaner and more modular
- current UI behavior remains intact for valid and invalid root/artifact states
- success and failure outputs still clearly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- tests cover unchanged list/detail/trigger/root-state behavior after the refactor
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
