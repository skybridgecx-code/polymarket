# Phase 19N — Operator UI Local Runbook and Docs

## Goal

Document the local operator UI setup and usage flow so operators can reliably launch, configure, and inspect artifacts without changing code behavior.

This phase is about documentation only.

18X established CLI artifact generation.
18Y–19M established the local operator UI read/trigger/detail surface and cleaned its internal structure.

19N should produce a bounded local runbook/doc update for the operator UI and its surrounding local workflow.

## Read first

Before changing docs, read the existing implementations for:

- `src/future_system/operator_ui/*`
- `src/future_system/cli/*`
- any existing docs/runbooks/README files already covering local usage
- directly relevant tests only as needed to confirm the documented flow

## Required deliverable

Build a bounded documentation pass that:

- explains how to launch the operator UI locally
- explains the local artifacts root assumption/configuration
- explains how CLI-generated artifacts and UI-inspected artifacts relate
- explains the existing UI trigger flow at a high level
- explains expected local success/failure states and safe troubleshooting steps
- keeps documentation grounded in shipped behavior only
- does not change code behavior

## Scope allowed

Allowed work in this phase:

- minimal bounded documentation additions/updates
- one or more docs files/runbook updates if clearly justified
- minimal README updates if appropriate

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- change runtime behavior
- add new features
- add speculative future architecture as if it already exists
- document workflows that are not actually supported
- widen scope beyond local operator UI / artifact workflow docs

## Desired shape

Prefer the smallest possible bounded doc update.

A good result is:

- one clear local runbook doc for operator UI usage
- or one focused README/doc section update if the repo already has the right place
- explicit launch/config/usage/troubleshooting sections
- wording grounded in current code truth

## Behavioral requirements

The documentation must preserve this contract:

1. Existing artifact files remain the source of truth.
2. UI remains downstream of the existing generation flow.
3. UI trigger flow remains synchronous/local.
4. Reads/writes remain bounded to the configured/local artifacts root.
5. Success and failure states are described accurately and conservatively.

## Acceptance criteria

This phase is complete when:

- a local operator can read the docs and understand how to:
  - launch the operator UI
  - configure the artifacts root
  - generate artifacts locally
  - inspect them in the UI
- the docs describe valid and invalid root/artifact states clearly
- the docs do not claim unsupported behavior
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum:
- validate any touched markdown/docs formatting if there is an existing lightweight doc check
- otherwise just report exact files changed and confirm no code paths changed

## Required Codex return format

Return only:

1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched
