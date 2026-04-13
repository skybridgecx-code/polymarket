# Phase 19D — Operator UI Run-Input UX Polish

## Goal

Polish the operator UI run-input surface so it is clearer, safer, and easier to use without changing the underlying generation pipeline.

This phase is about run-input UX only.

18Z introduced synchronous run triggering from the UI.
19A/19B/19C improved navigation, artifact presentation, and artifacts-root safety.

19D should improve the operator-facing run form and submit experience while preserving the existing bounded generation flow.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- any helper/read logic used by the operator UI
- directly relevant tests for the current UI trigger surface

## Required deliverable

Build a bounded UI polish pass that:

- improves run form labels and help text
- improves invalid-input messaging
- introduces safer default target-subdirectory behavior under the bounded artifacts root
- makes submit/result handoff clearer after a run is triggered
- preserves explicit success vs failure clarity
- preserves explicit failure-stage clarity where applicable:
  - analyst_timeout
  - analyst_transport
  - reasoning_parse
- remains bounded to the configured/local artifacts root
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- minimal helper additions strictly needed for safer target-subdirectory derivation and clearer form messaging
- minimal route/page/component adjustments strictly needed for trigger-form UX
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add background jobs, queues, or scheduling
- add delivery/inbox/notification systems
- add execution/trading behavior
- reimplement generation logic in the UI layer
- add speculative product/platform architecture beyond this bounded UX pass
- allow reads/writes outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded refinement of the current operator UI trigger surface.

A good result is:

- clearer context-source and target-directory inputs
- safer default target-subdirectory behavior
- better inline error/help text
- clearer success/failure handoff after submit
- deterministic tests for valid submit, invalid submit, default-subdirectory behavior, and handoff rendering

## Behavioral requirements

The implementation must preserve this contract:

1. Existing top-level generation flow remains the source of truth.
2. UI remains a bounded synchronous invocation surface.
3. UI does not reimplement generation logic.
4. Success and failure results remain clearly distinct.
5. Failure-stage identity remains exact.
6. Reads/writes remain bounded to the configured/local artifacts root.
7. UI output remains operator-safe and deterministic.

UI requirements:

- must accept explicit context source input
- must provide safer target-subdirectory behavior under the bounded root
- must make invalid input errors clearer
- must surface `theme_id`
- must surface status / failure-stage context clearly after submit
- must provide a clear way to inspect the resulting run
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can trigger runs more safely and clearly from the UI
- invalid inputs are handled with clearer messages
- default target-subdirectory behavior is safer and bounded
- success and failure handoff after submit is clearer
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- tests cover input/help/error/default/handoff behavior
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
