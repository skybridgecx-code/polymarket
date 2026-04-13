# Phase 19E — Operator UI Run-Detail and Status Polish

## Goal

Polish the operator UI run-detail surface so run outcomes are clearer and easier to inspect after trigger and navigation flows.

This phase is about run-detail/status UX only.

18Z introduced synchronous run triggering from the UI.
19A/19B/19C/19D improved history, artifact presentation, root-path safety, and run-input UX.

19E should improve detail-page status clarity and post-trigger outcome presentation while preserving the existing bounded generation flow.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- any helper/read logic used by the operator UI
- directly relevant tests for the current UI detail and trigger surface

## Required deliverable

Build a bounded UI polish pass that:

- improves trigger-result summaries on run detail pages
- improves success/failure status hierarchy and labeling
- makes failure-stage context clearer where applicable:
  - analyst_timeout
  - analyst_transport
  - reasoning_parse
- makes target-subdirectory and artifact path visibility clearer
- tightens empty/error states around newly created or partially readable runs
- remains read-only except for the already-existing synchronous trigger flow
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- minimal helper additions strictly needed for clearer status/detail rendering
- minimal route/page/component adjustments strictly needed for detail-page polish
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add background jobs, queues, or scheduling
- add delivery/inbox/notification systems
- add execution/trading behavior
- reimplement generation logic in the UI layer
- add speculative platform architecture beyond this bounded UX pass
- allow reads/writes outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded refinement of the current operator UI detail surface.

A good result is:

- clearer post-trigger status summary block
- stronger success/failure/failure-stage labels
- clearer artifact location/subdirectory context
- safer partial/missing-run states
- deterministic tests for detail rendering, status hierarchy, and error-state behavior

## Behavioral requirements

The implementation must preserve this contract:

1. Existing generation flow remains the source of truth.
2. UI remains a bounded synchronous invocation + inspection surface.
3. UI does not reimplement generation logic.
4. Success and failure results remain clearly distinct.
5. Failure-stage identity remains exact.
6. Reads/writes remain bounded to the configured/local artifacts root.
7. UI output remains operator-safe and deterministic.

UI requirements:

- must show `theme_id`
- must show status / failure-stage context clearly
- must make post-trigger result context easier to scan
- must make target-subdirectory / artifact path context clearer
- must provide explicit safe handling for empty/partial/missing detail states
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can understand run outcome more quickly from the detail page
- success and failure detail states are more clearly distinguishable
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- target-subdirectory and artifact path context are clearer
- empty/partial/missing detail states are handled safely and clearly
- tests cover detail/status/error-state behavior
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
