# Phase 18R — Review Packet Renderer Surface

## Goal

Add a bounded renderer surface that converts 18Q review packets into deterministic operator-facing text/markdown renderings for inspection and later export work.

This phase is about rendering only.

18Q created structured success/failure review packets.
18R should render those packets into stable human-readable outputs without introducing file writing, UI, or orchestration.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/review_packets/*`
- `src/future_system/runtime/*`
- any directly relevant summary/helper code already used by runtime or review packet layers

Also read the directly relevant review packet tests before implementing.

## Required deliverable

Build a bounded renderer layer that:

- accepts the 18Q review packet models
- produces deterministic operator-safe rendered output
- supports at least:
  - plain text rendering
  - markdown rendering
- preserves explicit distinction between:
  - success review packet
  - analyst timeout failure review packet
  - analyst transport failure review packet
  - reasoning parse failure review packet
- exposes a small builder/renderer entrypoint that callers can use without knowing packet internals
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_renderers/*`
- or minimal bounded additions under `src/future_system/review_packets/*` if the repo shape strongly prefers that
- minimal helper/model additions strictly needed for rendering
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add filesystem writing or export jobs
- add database/persistence work
- add scheduling/orchestration
- add UI
- add execution/trading behavior
- change runtime, policy, or reasoning logic
- change review packet meaning/structure beyond minimal bounded rendering support
- collapse failure stages into generic text
- add speculative reporting/inbox architecture

## Desired shape

Prefer a small dedicated rendering surface, for example:

- `src/future_system/review_renderers/__init__.py`
- `src/future_system/review_renderers/renderer.py`

Optionally add a small models/helpers file only if clearly necessary.

Tests should stay narrow and deterministic.

## Behavioral requirements

The implementation must preserve this contract:

1. Review packets remain the source of truth for operator review content.
2. Renderer layer is downstream of review packet construction.
3. Rendering does not re-run reasoning, runtime, or policy logic.
4. Text and markdown outputs must be deterministic.
5. Success and failure renderings must remain structurally distinct.
6. Failure renderings must preserve exact failure-stage identity.
7. Rendered output must remain operator-safe and based only on real packet contents.

Renderer requirements:

- must include `theme_id`
- must include packet kind/status
- must include deterministic summary text
- must include `run_flags`
- failure renderings must include explicit failure stage
- success renderings may include bounded reasoning/policy/result fields already present in the review packet
- failure renderings must not invent fake reasoning or fake policy content
- markdown output should be stable and readable, not styled for any UI framework

Expose a small entrypoint such as:

- render_review_packet(...)
- render_review_packet_markdown(...)
- render_review_packet_text(...)

or a similarly small bounded equivalent.

## Acceptance criteria

This phase is complete when:

- callers can render 18Q review packets into deterministic plain text and markdown
- success and failure renderings are explicit and structurally distinct
- failure renderings explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- no filesystem writing or UI work is added
- tests cover success plus each expected failure stage in at least one rendering format, and confirm stable rendering behavior
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched renderer/review packet files
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
