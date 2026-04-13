# Phase 19A — Operator UI Run History and Navigation Hardening

## Goal

Harden the operator UI so existing generated runs are easier and safer to inspect and navigate.

This phase is about UI usability and resilience only.

18Y introduced read-only artifact inspection.
18Z introduced synchronous run triggering from the UI.

19A should improve run history presentation, status clarity, navigation, and safe error handling without changing the core generation pipeline.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- any helper/read logic used by the operator UI
- directly relevant tests for the current UI read/trigger surface

## Required deliverable

Build a bounded UI hardening pass that:

- improves run list ordering and labeling
- makes success vs failure visually/textually clearer
- shows explicit failure stage clearly where applicable:
  - analyst_timeout
  - analyst_transport
  - reasoning_parse
- improves navigation between:
  - run list
  - selected run detail
  - newly created run result
- handles missing/invalid artifact files more clearly and safely
- remains read-only except for the already-existing synchronous trigger flow
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- minimal helper additions strictly needed for ordering, labels, and safer read states
- minimal route/page/component adjustments strictly needed for navigation hardening
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add background jobs, queues, or scheduling
- add delivery/inbox/notification systems
- add execution/trading behavior
- reimplement generation logic in the UI layer
- add speculative app/platform architecture beyond this bounded hardening pass
- allow reads/writes outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded refinement of the current operator UI surface.

A good result is:

- clearer run list rows/cards
- stronger badges/labels for success vs failure
- clearer detail headers and back-navigation
- explicit safe empty/missing/error states
- deterministic tests for ordering, labels, and invalid/missing-file behavior

## Behavioral requirements

The implementation must preserve this contract:

1. Existing artifact files remain the source of truth.
2. UI remains downstream of the existing generation flow.
3. UI does not regenerate or mutate artifacts outside the existing trigger flow.
4. Success and failure runs remain clearly distinct.
5. Failure-stage identity remains exact.
6. Reads/writes remain bounded to the configured/local artifacts root.
7. UI output remains operator-safe and deterministic.

UI requirements:

- must show `theme_id`
- must show status / failure-stage context clearly
- must improve run identification in the list/history view
- must provide clear navigation between list and detail
- must provide explicit and safe missing/invalid-file states
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can more easily browse prior runs and open details
- success and failure runs are more clearly distinguishable in the UI
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- navigation between list, detail, and triggered runs is cleaner
- missing/invalid artifact states are handled safely and clearly
- tests cover ordering/navigation/error-state behavior
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
