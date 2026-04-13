# Phase 18X — CLI Review Artifact Entry

## Goal

Add a bounded CLI entry that invokes the 18W runtime-entry-to-artifact flow and writes local review artifacts from a caller-provided context source and target directory.

This phase is about CLI wiring only.

18W introduced a top-level Python entrypoint for:
- context bundle
- analyst
- target directory
-> runtime result construction
-> artifact flow
-> local written review artifacts

18X should expose that capability through a small local CLI surface without adding UI, services, scheduling, or delivery systems.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/review_entrypoints/*`
- `src/future_system/runtime/*`
- any existing CLI modules/patterns already present in `src/future_system/*`
- any fixture-loading helpers already used by runtime/review tests if directly relevant

Also read the directly relevant tests before implementing.

## Required deliverable

Build a bounded CLI entry that:

- accepts a caller-provided context source
- accepts a caller-provided target directory
- invokes the 18W entrypoint
- writes review artifacts locally through the existing stack
- returns/prints deterministic operator-safe summary output
- supports both success and expected failure outcomes
- preserves explicit distinction between:
  - success
  - analyst timeout failure
  - analyst transport failure
  - reasoning parse failure
- is covered with deterministic tests only

## Scope allowed

Allowed work in this phase:

- minimal bounded CLI files under `src/future_system/cli/*` or a similarly small existing CLI surface if the repo already has one
- minimal helper/model additions strictly needed for CLI argument parsing and invocation
- minimal test additions strictly needed for deterministic coverage

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add UI
- add database/persistence backends
- add network delivery, email, notifications, queues, or inbox/reporting systems
- add scheduling/orchestration beyond one synchronous CLI invocation
- add execution/trading behavior
- re-run reasoning/policy logic outside the existing 18W entrypoint
- introduce broad application/framework scaffolding
- write outside the caller-provided target directory
- add speculative config/platform architecture

## Desired shape

Prefer a very small CLI surface, for example:

- `src/future_system/cli/__init__.py`
- `src/future_system/cli/review_artifacts.py`

or minimal additions to an existing CLI module if that is clearly the repo pattern.

Tests should stay narrow and deterministic and use temp directories / fixture inputs only.

## Behavioral requirements

The implementation must preserve this contract:

1. 18W entrypoint remains the source of truth for top-level flow behavior.
2. CLI layer is only a bounded invocation + argument parsing + deterministic summary layer.
3. CLI invocation does not change runtime/artifact semantics.
4. Success and failure outcomes remain structurally distinct.
5. Failure-stage identity remains exact.
6. Local writes remain bounded to the caller-provided target directory.
7. Printed/returned CLI output remains deterministic and operator-safe.

CLI requirements:

- must accept an explicit input/context source argument
- must accept an explicit target directory argument
- must invoke the 18W entrypoint
- must surface theme_id
- must surface status / failure stage context
- must surface written artifact path information
- must not invent fake reasoning or fake policy content
- must fail explicitly on invalid inputs rather than silently substituting defaults

Prefer a small entry such as:

- `python -m future_system.cli.review_artifacts ...`

or a similarly bounded equivalent consistent with existing repo patterns.

## Acceptance criteria

This phase is complete when:

- callers can invoke a local CLI with context source + target directory and receive deterministic written review artifacts
- CLI output is deterministic and operator-safe
- success and failure outcomes are preserved cleanly
- failure outputs explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- writes stay bounded to caller-provided local filesystem targets only
- tests cover success plus each expected failure stage
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched CLI files
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
