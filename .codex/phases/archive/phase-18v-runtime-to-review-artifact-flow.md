# Phase 18V — Runtime-to-Review Artifact Flow

## Goal

Add a bounded end-to-end artifact flow that takes a structured runtime result and produces written local review artifact files through the existing review bundle, export, and file-writer layers.

This phase is about composition and flow wiring only.

18P introduced structured runtime results.
18Q introduced review packets.
18R introduced renderers.
18S introduced review bundles.
18T introduced export payloads.
18U introduced bounded local file writing.

18V should compose those layers into one small end-to-end artifact flow without adding new delivery systems, persistence backends, UI, or orchestration.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/runtime/*`
- `src/future_system/review_packets/*`
- `src/future_system/review_renderers/*`
- `src/future_system/review_bundles/*`
- `src/future_system/review_exports/*`
- `src/future_system/review_file_writers/*`

Also read the directly relevant tests for those layers before implementing.

## Required deliverable

Build a bounded flow layer that:

- accepts an 18P runtime result envelope
- derives the 18S review bundle
- derives the 18T export payload package
- writes artifacts through the 18U file-writer boundary into a caller-provided target directory
- returns a structured end-to-end artifact flow result/model
- supports both success and expected failure outcomes
- preserves explicit distinction between:
  - success
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_artifacts/*`
- minimal helper/model additions strictly needed for end-to-end flow composition
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add network delivery, email, notifications, queues, or inbox/reporting systems
- add scheduling/orchestration beyond this single synchronous composition flow
- add UI
- add execution/trading behavior
- re-run runtime, reasoning, or policy logic inside this layer
- change semantics of review bundle/export/writer layers beyond minimal bounded integration support
- write outside the caller-provided target directory
- add speculative job-runner or artifact-registry architecture

## Desired shape

Prefer a small dedicated composition surface, for example:

- `src/future_system/review_artifacts/__init__.py`
- `src/future_system/review_artifacts/models.py`
- `src/future_system/review_artifacts/flow.py`

Tests should stay narrow and deterministic and should use temp directories only.

## Behavioral requirements

The implementation must preserve this contract:

1. Runtime result remains the source of truth for success/failure.
2. Review bundle builder remains the source of bundle construction.
3. Export layer remains the source of export payload construction.
4. File-writer layer remains the source of local file writing.
5. This layer is only a bounded synchronous composition flow across those existing components.
6. Success and failure outcomes remain structurally distinct or explicitly typed.
7. Failure-stage identity remains exact.
8. Output remains deterministic and operator-safe.

Artifact flow requirements:

- must include `theme_id`
- must include flow status / kind
- must include the runtime result envelope or a bounded reference to it
- must include the derived review bundle or bounded reference to it
- must include the derived export payload package or bounded reference to it
- must include the file-writer result
- must include `run_flags`
- failure outcomes must include explicit failure stage
- success outcomes may include bounded success details already present upstream
- failure outcomes must not invent fake reasoning or fake policy content

Expose a small entrypoint such as:

- `build_and_write_review_artifacts(...)`

or a similarly small bounded equivalent.

A good result model may include, at minimum:

- theme_id
- target directory
- runtime result reference
- review bundle reference
- export payload reference
- file write result
- status / failure stage context

## Acceptance criteria

This phase is complete when:

- callers can pass an 18P runtime result envelope and a target directory and receive deterministic written review artifacts through the composed flow
- flow includes bundle construction, export payload construction, and local file writing
- success and failure outcomes are preserved cleanly
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- flow stays bounded to caller-provided local filesystem targets only
- tests cover success plus each expected failure stage, using temp directories
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `review_artifacts` files
- any touched tests

Use:

- `pytest`
- `ruff check`
- `mypy`

## Required Codex return format

Return only:

1. concise summary
2. exact files created/modified
3. exact validation commands run
4. exact validation results
5. deviations from spec
6. explicit note whether `src/polymarket_arb/*` was untouched
