# Phase 18W — Runtime Entry-to-Artifact Entry Flow

## Goal

Add a bounded top-level entry flow that starts from the actual runtime result entrypoint and produces written local review artifacts through the existing artifact flow.

This phase is about top-level composition only.

18P introduced the runtime result entrypoint.
18V introduced the runtime-result-to-review-artifact composition flow.

18W should connect those layers so a caller with a context bundle, analyst, and target directory can invoke one small entrypoint and receive the final artifact result.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/runtime/*`
- `src/future_system/review_artifacts/*`
- `src/future_system/review_bundles/*`
- `src/future_system/review_exports/*`
- `src/future_system/review_file_writers/*`

Also read the directly relevant tests for the runtime and review artifact flow before implementing.

## Required deliverable

Build a bounded top-level entry flow that:

- accepts:
  - context bundle
  - runtime analyst
  - caller-provided target directory
- invokes the 18P runtime result entrypoint
- invokes the 18V review artifact flow
- returns a structured end-to-end entry result/model
- supports both success and expected failure outcomes
- preserves explicit distinction between:
  - success
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_entrypoints/*`
- or minimal bounded additions under `src/future_system/review_artifacts/*` if the repo shape strongly prefers that
- minimal helper/model additions strictly needed for the top-level composition entrypoint
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add network delivery, email, notifications, queues, or inbox/reporting systems
- add scheduling/orchestration beyond this single synchronous top-level flow
- add UI
- add execution/trading behavior
- re-run reasoning or policy logic outside the existing runtime entrypoint
- change semantics of runtime result, bundle, export, writer, or artifact-flow layers beyond minimal bounded integration support
- write outside the caller-provided target directory
- add speculative service/application framework architecture

## Desired shape

Prefer a small dedicated entry surface, for example:

- `src/future_system/review_entrypoints/__init__.py`
- `src/future_system/review_entrypoints/models.py`
- `src/future_system/review_entrypoints/entry.py`

Tests should stay narrow and deterministic and should use temp directories only.

## Behavioral requirements

The implementation must preserve this contract:

1. Runtime result entrypoint remains the source of truth for runtime success/failure.
2. Review artifact flow remains the source of downstream artifact construction/writing.
3. This layer is only a bounded synchronous entry composition across those existing components.
4. Success and failure outcomes remain structurally distinct or explicitly typed.
5. Failure-stage identity remains exact.
6. Output remains deterministic and operator-safe.
7. Local writes remain bounded to the caller-provided target directory.

Entry flow requirements:

- must include `theme_id`
- must include entry status / kind
- must include the runtime result envelope or a bounded reference to it
- must include the review artifact flow result
- must include `run_flags`
- failure outcomes must include explicit failure stage
- success outcomes may include bounded success details already present upstream
- failure outcomes must not invent fake reasoning or fake policy content

Expose a small entrypoint such as:

- `run_analysis_and_write_review_artifacts(...)`

or a similarly small bounded equivalent.

A good result model may include, at minimum:

- theme_id
- target directory
- runtime result reference
- artifact flow result
- status / failure stage context

## Acceptance criteria

This phase is complete when:

- callers can pass a context bundle, analyst, and target directory and receive deterministic written review artifacts through the composed top-level entrypoint
- flow includes runtime result construction and artifact writing
- success and failure outcomes are preserved cleanly
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- writes stay bounded to caller-provided local filesystem targets only
- tests cover success plus each expected failure stage, using temp directories
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `review_entrypoints` and/or `review_artifacts` files
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
