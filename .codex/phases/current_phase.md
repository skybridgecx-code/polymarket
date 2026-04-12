# Phase 18T — Review Bundle Export Surface

## Goal

Add a bounded export surface that converts the 18S in-memory review bundle into deterministic export payloads suitable for later file-writing, delivery, or API response work.

This phase is about export payload construction only.

18S introduced a deterministic in-memory review bundle.
18T should transform that bundle into stable exportable payloads without adding filesystem writing, persistence, UI, or orchestration.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/review_bundles/*`
- `src/future_system/review_packets/*`
- `src/future_system/review_renderers/*`
- any directly relevant runtime/result models that flow into the bundle

Also read the directly relevant tests for those layers before implementing.

## Required deliverable

Build a bounded export layer that:

- accepts the 18S review bundle
- produces deterministic export payload models for at least:
  - structured JSON-ready payload
  - markdown document payload
- preserves explicit distinction between:
  - success
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- exposes a small builder/entrypoint for callers
- returns payloads only, without writing them anywhere
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_exports/*`
- minimal helper/model additions strictly needed for export payload construction
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add filesystem writing
- add database/persistence work
- add scheduling/orchestration
- add UI
- add execution/trading behavior
- change runtime, review packet, renderer, or review bundle semantics beyond minimal bounded export support
- collapse failure stages into generic export status
- add speculative notification/inbox/reporting infrastructure

## Desired shape

Prefer a small dedicated export surface, for example:

- `src/future_system/review_exports/__init__.py`
- `src/future_system/review_exports/models.py`
- `src/future_system/review_exports/builder.py`

Tests should stay narrow and deterministic.

## Behavioral requirements

The implementation must preserve this contract:

1. Review bundle remains the source of truth for export construction.
2. Export layer is downstream of review bundle construction.
3. Export construction does not re-run runtime, reasoning, policy, review packet, or rendering logic.
4. Export payloads must be deterministic and operator-safe.
5. Success and failure exports must remain structurally distinct or explicitly typed.
6. Failure exports must preserve exact failure-stage identity.
7. Export layer returns payloads only, not side effects.

Export payload requirements:

- must include `theme_id`
- must include export kind/type
- must include bundle status / packet kind context
- must include deterministic plain text and/or markdown content where appropriate
- must include a structured JSON-ready representation
- must include `run_flags`
- failure exports must include explicit failure stage
- success exports may include bounded success details already present in upstream bundle content
- failure exports must not invent fake reasoning or fake policy content

Expose a small entrypoint such as:

- `build_review_export_payloads(...)`

or a similarly small bounded equivalent.

A good outcome is a model that contains, at minimum:

- a JSON-ready export payload
- a markdown export payload
- minimal metadata describing the export package

## Acceptance criteria

This phase is complete when:

- callers can convert an 18S review bundle into deterministic export payloads
- exports include a JSON-ready structured payload and a markdown payload
- success and failure outcomes are preserved cleanly
- failure exports explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- no filesystem writing, DB work, UI work, or orchestration is added
- tests cover success plus each expected failure stage
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `review_exports` files
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
