# Phase 18P — Runtime Result Surface

## Goal

Add a bounded operator-safe result layer for the dry-run analysis runtime so the system can return deterministic success/failure packets without forcing callers to infer meaning from exceptions alone.

This phase is about the runtime result boundary only.

18O added a live analyst transport boundary and explicit timeout / transport / parser-failure handling.
18P should convert those runtime outcomes into stable, structured result packets suitable for operator review and later artifact/export work.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/runtime/*`
- `src/future_system/live_analyst/*`
- `src/future_system/reasoning_contracts/*`
- `src/future_system/policy_engine/*`

Also read the directly relevant runtime and live-analyst tests before implementing.

## Required deliverable

Build a bounded runtime result surface that:

- preserves the existing successful `AnalysisRunPacket` path
- introduces explicit structured failure packet/model(s) for runtime failures
- introduces a top-level result envelope / union that can represent either success or failure deterministically
- adds a wrapper entrypoint that returns the structured result envelope instead of raising for expected runtime-stage failures
- preserves explicit distinction between:
  - analyst timeout
  - analyst transport failure
  - reasoning parse/validation failure
- emits deterministic operator-safe summary text/fields for both success and failure cases
- is covered with deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- minimal additions under `src/future_system/runtime/*`
- new runtime result/failure models if needed
- minimal summary/helper additions strictly needed for this result surface
- minimal test fixture additions strictly needed for deterministic tests

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add persistence, database, or filesystem artifact writing
- add scheduling
- add execution or order placement behavior
- add retries/backoff loops
- add UI
- change policy scoring logic
- change reasoning schema contracts
- blur failure-stage distinctions into a generic error bucket
- remove the existing exception-raising pipeline if other code already depends on it
- introduce speculative orchestration architecture

## Desired shape

Prefer extending the existing runtime package rather than creating a broad new subsystem.

Likely shape:

- extend `src/future_system/runtime/models.py`
- minimally update `src/future_system/runtime/runner.py`
- minimally update `src/future_system/runtime/summary.py`
- add tests in `tests/future_system/test_runtime_runner.py`
- add a dedicated runtime result test file only if clearly needed

## Behavioral requirements

The implementation must preserve this contract:

1. Existing success path still yields `AnalysisRunPacket`.
2. Existing strict pipeline logic remains intact.
3. New wrapper/result entrypoint returns a deterministic structured result envelope.
4. Expected runtime-stage failures become structured failure packets in that wrapper/result entrypoint.
5. Failure packets preserve exact stage identity and run flags.
6. Success and failure summaries remain operator-readable and deterministic.

Failure packet/result requirements:

- must include `theme_id`
- must include `status`
- must include explicit `failure_stage`
- must include `run_flags`
- must include a deterministic summary string
- must not include fake reasoning output or fake policy output
- must distinguish expected runtime-stage failures from unexpected programming errors

Error handling requirements:

- expected runtime-stage failures:
  - analyst timeout
  - analyst transport failure
  - reasoning parse failure
  should map to structured failure results in the new wrapper/result entrypoint

- unexpected exceptions should remain explicit and should not be silently converted into a normal-looking success or generic safe placeholder

## Acceptance criteria

This phase is complete when:

- callers can use a new runtime result entrypoint and receive either a success packet or a structured failure packet deterministically
- success packets preserve the existing `AnalysisRunPacket`
- failure packets explicitly distinguish:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- summaries for both success and failure are deterministic and operator-safe
- tests cover success plus each expected failure stage
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- touched `runtime` files
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
