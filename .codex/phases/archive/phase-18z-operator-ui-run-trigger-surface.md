# Phase 18Z — Operator UI Run Trigger Surface

## Goal

Add a bounded operator UI trigger surface that lets an operator start the existing review-artifact generation flow from the UI and then inspect the resulting run.

This phase is about synchronous UI-triggered run invocation only.

18Y introduced a read-only operator UI for existing artifact runs.
18W/18X already provide bounded top-level generation entrypoints.

18Z should connect those so the operator can start a run from the UI without adding background jobs, scheduling, or broader application infrastructure.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- `src/future_system/review_entrypoints/*`
- `src/future_system/cli/*` if directly relevant
- any existing route/form handling patterns already used by the repo’s UI surface

Also read the directly relevant tests before implementing.

## Required deliverable

Build a bounded operator UI trigger surface that:

- presents a small run form/input surface
- accepts a caller-provided context source
- accepts or derives a bounded target directory under the configured/local artifacts root
- invokes the existing top-level review artifact flow synchronously
- surfaces deterministic operator-safe run result feedback
- lets the operator open or land on the resulting run detail view
- preserves explicit distinction between:
  - success
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions under `src/future_system/operator_ui/*`
- minimal helper additions strictly needed for safe target-directory derivation and synchronous invocation
- minimal route/page/component additions strictly needed for this run-trigger screen/flow
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add background jobs, workers, queues, or scheduling
- add database/persistence backends
- add delivery/inbox/notification systems
- add execution/trading behavior
- add speculative multi-user/app-platform architecture
- allow writes outside the configured/local artifacts root
- bypass the existing 18W/18X bounded flow with duplicated logic

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded addition to the current operator UI surface.

A good result is:

- one run form/view
- one submit path
- one safe handoff into the existing flow
- redirect or link to the created run detail
- deterministic tests for form submit, success, and failure cases

## Behavioral requirements

The implementation must preserve this contract:

1. Existing top-level review artifact entry flow remains the source of truth for generation behavior.
2. UI trigger layer is only a bounded synchronous invocation surface.
3. Generated artifact files remain rooted under the configured/local artifacts root.
4. Success and failure results remain clearly distinct.
5. Failure-stage identity remains exact.
6. UI remains operator-safe and deterministic.
7. No run-generation logic is reimplemented in the UI layer.

UI trigger requirements:

- must accept explicit context source input
- must keep target path bounded under the artifacts root
- must surface `theme_id`
- must surface status / failure-stage context
- must provide a clear way to inspect the resulting run
- must fail explicitly and safely on invalid inputs
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can trigger a run from the UI and generate local review artifacts synchronously
- the UI can navigate to or reveal the resulting run detail
- success and failure outcomes are preserved cleanly
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- writes stay bounded to the configured/local artifacts root
- tests cover trigger success, trigger failure, invalid input, and run-detail handoff behavior
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
