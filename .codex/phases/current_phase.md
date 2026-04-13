# Phase 18U — Review Bundle File Writer Boundary

## Goal

Add a bounded file-writer layer that takes the 18T review export payloads and writes deterministic local files to a controlled output target.

This phase is about filesystem writing only.

18T introduced deterministic export payloads.
18U should add a small local file-writing boundary without introducing delivery, persistence backends, UI, or orchestration.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/review_exports/*`
- `src/future_system/review_bundles/*`
- any directly relevant existing local artifact/file-writing helpers already present in the repo, if any

Also read the directly relevant tests for the export layer before implementing.

## Required deliverable

Build a bounded file-writer layer that:

- accepts the 18T export payload package
- writes deterministic local files for at least:
  - markdown output
  - JSON output
- writes only into an explicitly provided target directory
- returns a structured file-write result/model describing what was written
- preserves explicit distinction between:
  - success exports
  - analyst timeout failure exports
  - analyst transport failure exports
  - reasoning parse failure exports
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new bounded files under `src/future_system/review_file_writers/*`
- minimal helper/model additions strictly needed for local file writing
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add database/persistence backends
- add network delivery, email, notifications, or inbox/reporting systems
- add scheduling/orchestration
- add UI
- add execution/trading behavior
- change review export semantics beyond minimal bounded writer support
- write outside the caller-provided target directory
- introduce unsafe path behavior or implicit global output locations
- add speculative artifact registry architecture

## Desired shape

Prefer a small dedicated file-writer surface, for example:

- `src/future_system/review_file_writers/__init__.py`
- `src/future_system/review_file_writers/models.py`
- `src/future_system/review_file_writers/writer.py`

Tests should stay narrow and deterministic and should use temp directories only.

## Behavioral requirements

The implementation must preserve this contract:

1. Review export payloads remain the source of truth for written content.
2. File-writer layer is downstream of export payload construction.
3. File writing does not re-run runtime, reasoning, policy, review packet, rendering, bundle, or export logic.
4. Files written must be deterministic in content and naming.
5. Writer must operate only inside an explicitly provided target directory.
6. Writer result must clearly describe what files were written.
7. The writer must remain local-only and side-effect-bounded.

File-writer requirements:

- must write at least one markdown file and one JSON file
- must include `theme_id` in deterministic filenames or directory layout
- must produce stable naming for success vs failure outputs
- must preserve explicit failure-stage identity in the written content and/or metadata when applicable
- must return structured metadata describing paths written
- must not invent fake reasoning or fake policy content
- must fail explicitly on invalid target directory inputs rather than silently choosing another location

Expose a small entrypoint such as:

- `write_review_export_files(...)`

or a similarly small bounded equivalent.

A good result model may include, at minimum:

- target directory
- written markdown file path
- written JSON file path
- theme_id
- export status / failure stage context

## Acceptance criteria

This phase is complete when:

- callers can pass an 18T export payload package and a target directory and receive deterministic written local files
- markdown and JSON files are both written
- success and failure exports are preserved cleanly
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- writer stays bounded to caller-provided local filesystem targets only
- tests cover success plus each expected failure stage, using temp directories
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `review_file_writers` files
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
