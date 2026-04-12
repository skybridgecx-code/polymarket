# Phase 18S — Review Bundle Surface

## Goal

Add a bounded in-memory review bundle surface that composes the existing runtime result, review packet, and rendered review outputs into one deterministic bundle for downstream operator handling and later export work.

This phase is about in-memory bundle construction only.

18P introduced structured runtime results.
18Q introduced structured review packets.
18R introduced deterministic text/markdown rendering.

18S should combine those layers into one stable review bundle without adding filesystem export, UI, persistence, or orchestration.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/runtime/*`
- `src/future_system/review_packets/*`
- `src/future_system/review_renderers/*`

Also read the directly relevant tests for those layers before implementing.

## Required deliverable

Build a bounded review bundle layer that:

- accepts the structured runtime result envelope from 18P
- derives the review packet using the 18Q builder
- derives deterministic text and markdown renderings using the 18R renderer
- returns a single deterministic in-memory review bundle model
- supports both success and expected failure outcomes
- preserves explicit distinction between:
  - success
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- exposes a small builder entrypoint for callers
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_bundles/*`
- minimal helper/model additions strictly needed for the bundle surface
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add filesystem writing or export jobs
- add database/persistence work
- add scheduling/orchestration
- add UI
- add execution/trading behavior
- change runtime, policy, reasoning, review packet, or renderer semantics beyond minimal bounded integration support
- collapse failure stages into generic bundle status
- add speculative queue/inbox/reporting architecture

## Desired shape

Prefer a small dedicated bundle surface, for example:

- `src/future_system/review_bundles/__init__.py`
- `src/future_system/review_bundles/models.py`
- `src/future_system/review_bundles/builder.py`

Tests should stay narrow and deterministic.

## Behavioral requirements

The implementation must preserve this contract:

1. Runtime result remains the source of truth for success/failure outcome.
2. Review packet remains the structured review representation.
3. Renderer remains the source of text/markdown rendering.
4. Review bundle is a pure composition layer downstream of those components.
5. Review bundle construction does not re-run runtime, reasoning, or policy logic.
6. Success and failure bundles remain structurally distinct or explicitly typed.
7. Failure bundles preserve exact failure-stage identity.
8. Bundle content remains deterministic and operator-safe.

Review bundle requirements:

- must include `theme_id`
- must include bundle status / kind
- must include the original runtime result envelope or a bounded reference to it
- must include the derived review packet
- must include rendered plain text output
- must include rendered markdown output
- must include `run_flags`
- failure bundles must include explicit failure stage
- success bundles may include bounded success details already present in upstream models
- failure bundles must not invent fake reasoning or fake policy content

Expose a small entrypoint such as:

- `build_review_bundle(...)`

or a similarly small bounded equivalent.

## Acceptance criteria

This phase is complete when:

- callers can convert an 18P runtime result envelope into a deterministic review bundle
- the bundle contains runtime result, review packet, text rendering, and markdown rendering
- success and failure outcomes are preserved cleanly
- failure bundles explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- no filesystem writing, DB work, UI work, or orchestration is added
- tests cover success plus each expected failure stage
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `review_bundles` files
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
