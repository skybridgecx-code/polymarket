# Phase 19B — Operator UI Artifact Content Polish

## Goal

Polish the operator UI artifact detail surface so review content is easier and safer to inspect.

This phase is about artifact detail presentation only.

19A improved run history, navigation, and safe error handling.
19B should improve how artifact content itself is rendered and organized without changing the underlying generation pipeline.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- any helper/read logic used by the operator UI
- directly relevant tests for the current UI detail surface

## Required deliverable

Build a bounded UI polish pass that:

- improves markdown presentation in the run detail view
- improves JSON readability in the run detail view
- groups metadata into clearer sections
- handles larger artifact content safely and predictably
- preserves explicit success vs failure clarity
- preserves explicit failure stage clarity where applicable:
  - analyst_timeout
  - analyst_transport
  - reasoning_parse
- remains read-only except for the already-existing synchronous trigger flow
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- minimal helper additions strictly needed for safer artifact content rendering and grouping
- minimal route/page/component adjustments strictly needed for detail-view polish
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add background jobs, queues, or scheduling
- add delivery/inbox/notification systems
- add execution/trading behavior
- reimplement generation logic in the UI layer
- add speculative platform architecture beyond this bounded detail-view polish
- allow reads/writes outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded refinement of the current operator UI detail surface.

A good result is:

- clearer metadata grouping in detail view
- more readable markdown section
- cleaner JSON presentation
- safe truncation/collapsing or bounded display behavior for large content
- deterministic tests for rendering/grouping/large-content/error behavior

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
- must group key metadata clearly
- must render markdown content in a cleaner readable way
- must render JSON content in a bounded readable way
- must provide explicit and safe handling for missing/invalid/oversized content
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can inspect artifact content more easily in the detail view
- success and failure content remain clearly distinguishable
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- larger content is handled safely and predictably
- tests cover detail rendering, metadata grouping, and safe large-content/error behavior
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
