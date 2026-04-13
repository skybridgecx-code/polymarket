# Phase 19C — Operator UI Configuration and Root-Path Hardening

## Goal

Harden the operator UI around artifacts-root configuration so the operator can clearly understand whether the local artifact root is configured and readable, and the system fails safely when it is not.

This phase is about configuration visibility and local root-path safety only.

19A improved run history and navigation.
19B improved artifact content presentation.
19C should improve the operator UI’s handling of the configured/local artifacts root without changing the generation pipeline.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/operator_ui/*`
- any helper/read logic used by the operator UI
- any existing configuration/env handling already used for the artifacts root
- directly relevant tests for the current UI surface

## Required deliverable

Build a bounded UI/config hardening pass that:

- makes configured artifacts-root status clearer
- clearly distinguishes:
  - configured and readable
  - configured but missing
  - configured but unreadable/invalid
  - not configured
- keeps file reads/writes bounded to the configured/local artifacts root
- provides safe, operator-readable UI messaging for invalid/missing/unreadable root states
- preserves existing run list/detail/trigger behavior when the root is valid
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded additions/modifications under `src/future_system/operator_ui/*`
- minimal helper additions strictly needed for root-path validation and safe status reporting
- minimal route/page/component adjustments strictly needed for configuration-status rendering
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add background jobs, queues, or scheduling
- add delivery/inbox/notification systems
- add execution/trading behavior
- reimplement generation logic in the UI layer
- add speculative config/platform architecture beyond this bounded hardening pass
- allow reads/writes outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded refinement of the current operator UI surface.

A good result is:

- a clear configuration-status section/banner
- explicit safe UI states for missing/invalid/unreadable root
- preserved normal behavior when the root is valid
- deterministic tests for configured/unconfigured/invalid root behavior

## Behavioral requirements

The implementation must preserve this contract:

1. Existing artifact files remain the source of truth.
2. UI remains downstream of the existing generation flow.
3. UI does not regenerate or mutate artifacts outside the existing trigger flow.
4. Success and failure runs remain clearly distinct.
5. Failure-stage identity remains exact.
6. Reads/writes remain bounded to the configured/local artifacts root.
7. UI output remains operator-safe and deterministic.
8. Configuration problems are surfaced clearly and safely.

UI/config requirements:

- must make the current artifacts-root state visible
- must provide explicit and safe messaging for missing/invalid/unreadable root states
- must preserve normal list/detail/trigger behavior when the root is valid
- must fail explicitly and safely on invalid root usage
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can tell whether the artifacts root is configured and usable
- invalid/missing/unreadable root states are handled safely and clearly
- normal UI behavior remains intact when the root is valid
- reads/writes stay bounded to the configured/local artifacts root
- tests cover configured, missing, invalid, and unreadable-root behavior
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
