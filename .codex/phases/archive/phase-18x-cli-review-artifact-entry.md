# Phase 18Y — Operator UI Read Surface

## Goal

Add a bounded read-only operator UI surface for inspecting generated review artifacts.

This phase is about read-only UI inspection only.

18X introduced a bounded CLI entry that can generate review artifacts locally.
18Y should introduce a minimal operator-facing UI that reads existing artifact outputs from a caller-provided/local configured artifacts root and renders them for inspection.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/review_artifacts/*`
- `src/future_system/review_file_writers/*`
- `src/future_system/review_exports/*`
- any existing UI/app/operator surface already present in the repo that is the correct place for a bounded future_system operator screen
- any existing local file-reading helpers or route patterns that are directly relevant

Also read the directly relevant tests before implementing.

## Required deliverable

Build a bounded read-only operator UI surface that:

- lists generated review artifact runs from a local artifacts root
- lets the operator open/select a run
- shows key metadata for the run
- shows success vs failure clearly
- shows explicit failure stage where applicable:
  - analyst_timeout
  - analyst_transport
  - reasoning_parse
- shows markdown output
- shows JSON output or a bounded structured view of it
- is read-only
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal UI/app files strictly needed for a read-only operator surface
- minimal bounded server/read helpers strictly needed to enumerate and read locally written artifact files
- minimal route/page/component additions strictly needed for this screen
- minimal tests strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add run-triggering from the UI
- add scheduling/orchestration
- add database/persistence backends
- add network delivery, notifications, inboxes, or queue systems
- add execution/trading behavior
- re-run runtime/review generation logic from the UI
- add speculative app shell/platform architecture beyond this bounded screen
- allow reading outside the configured/local artifacts root

## Desired shape

Use the repo’s existing UI/app pattern.
Prefer the smallest possible bounded operator surface.

A good result is:

- one page/screen for artifact run listing
- one detail view or split view for a selected run
- small helper(s) for local artifact discovery and reading
- deterministic tests for read/list/render behavior

## Behavioral requirements

The implementation must preserve this contract:

1. Existing artifact files remain the source of truth.
2. UI is read-only and downstream of the artifact-writing flow.
3. UI does not regenerate or mutate artifacts.
4. Success and failure runs remain clearly distinct.
5. Failure-stage identity remains exact.
6. File reading remains bounded to the configured/local artifacts root.
7. UI output remains operator-safe and deterministic.

UI requirements:

- must show `theme_id`
- must show status / failure-stage context
- must show artifact path or run identifier context
- must show markdown content
- must show JSON content or a bounded readable structured rendering
- must fail explicitly and safely on missing/invalid artifact files
- must not invent fake reasoning or fake policy content

## Acceptance criteria

This phase is complete when:

- an operator can open the UI and inspect existing generated review artifacts
- list and detail views are functional and read-only
- success and failure artifact runs are clearly distinguishable
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- file reads stay bounded to the configured/local artifacts root
- tests cover list/detail behavior and failure-file handling
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched UI/read-helper files
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
