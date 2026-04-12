# Phase 18Q — Review Packet Surface

## Goal

Add a bounded operator-review packet surface that converts the structured runtime result envelope from 18P into deterministic review packets suitable for human inspection and later export/artifact work.

This phase is about review-packet construction only.

18P introduced structured success/failure runtime results.
18Q should transform those results into stable, operator-safe review packet models/builders without adding filesystem export, UI, or orchestration.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/runtime/*`
- `src/future_system/live_analyst/*`
- `src/future_system/reasoning_contracts/*`
- `src/future_system/policy_engine/*`

Also read any existing review/packet patterns in the repo that are directly relevant, but do not widen scope or pull `src/polymarket_arb/*` into this phase.

Read the directly relevant runtime tests before implementing.

## Required deliverable

Build a bounded review-packet layer that:

- accepts the structured runtime result envelope from 18P
- produces deterministic operator-review packet model(s) for both success and failure outcomes
- preserves explicit distinction between:
  - successful analysis result
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- exposes a builder/helper entrypoint that converts runtime result -> review packet
- emits deterministic operator-safe summary fields/content suitable for later export/rendering work
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_packets/*` if needed
- or minimal bounded additions under `src/future_system/runtime/*` if the repo shape strongly prefers that
- new review packet models/builders/helpers strictly needed for this surface
- minimal test fixtures/additions strictly needed for deterministic tests

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add filesystem writing or artifact export
- add database or persistence work
- add scheduling/orchestration
- add execution or order placement behavior
- add UI
- change policy logic
- change reasoning schema contracts
- collapse failure stages into a generic bucket
- add speculative “reporting platform” architecture
- add transport/retry logic here

## Desired shape

Prefer a small dedicated review packet surface, for example:

- `src/future_system/review_packets/__init__.py`
- `src/future_system/review_packets/models.py`
- `src/future_system/review_packets/builder.py`

Or a minimal equivalent if the repo’s existing patterns strongly suggest a smaller shape.

Tests should stay narrow and deterministic.

## Behavioral requirements

The implementation must preserve this contract:

1. Runtime remains the source of truth for analysis success/failure.
2. Review packet layer is downstream of runtime result construction.
3. Review packet construction does not re-run policy or reasoning logic.
4. Success review packets may include validated reasoning/policy/result summaries.
5. Failure review packets must not invent fake reasoning output or fake policy output.
6. Failure review packets must preserve exact failure stage identity.
7. Review packet content remains deterministic and operator-safe.

Review packet requirements:

- must include `theme_id`
- must include explicit packet/result status
- must include packet kind/type that distinguishes success vs failure review packets
- must include explicit failure stage on failure packets
- must include deterministic summary text
- must include `run_flags`
- success packets should include the bounded success details already available from runtime output
- failure packets should include only safe, real failure details already available from runtime failure output

The builder/entrypoint should make it easy for later phases to consume review packets without needing to know runtime exception details.

## Acceptance criteria

This phase is complete when:

- callers can convert the 18P runtime result envelope into deterministic review packets
- success and failure review packets are explicit and structurally distinct
- failure review packets explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- no fake reasoning/policy output is introduced on failures
- tests cover success plus each expected failure stage
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `review_packets` and/or `runtime` files
- touched tests

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
