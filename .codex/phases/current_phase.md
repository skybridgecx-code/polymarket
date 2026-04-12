# Phase 18O — Live Analyst Adapter Boundary

## Goal

Add a bounded live analyst transport layer under `src/future_system/live_analyst/` that lets the existing 18N dry-run runtime call a real model boundary while preserving the current deterministic flow:

- deterministic context assembly stays upstream
- reasoning parsing/validation stays mandatory
- deterministic policy stays downstream

This phase is about the analyst transport boundary only.

## Read first

Before changing code, read the existing implementations for:

- `src/future_system/runtime/*`
- `src/future_system/reasoning_contracts/*`
- `src/future_system/policy_engine/*`

Also read any directly relevant tests for 18L, 18M, and 18N before implementing.

## Required deliverable

Build a bounded `src/future_system/live_analyst/` module that:

- implements the runtime analyst protocol through a real model-call transport boundary
- accepts either a `ReasoningInputPacket` or an already-rendered prompt packet/string from the existing reasoning layer
- returns model-like output that is still forced through the existing reasoning parser/validator
- enforces explicit timeout handling
- enforces explicit clean failure behavior
- is covered with mocked, deterministic unit tests only

## Scope allowed

Allowed work in this phase:

- new files under `src/future_system/live_analyst/`
- minimal runtime wiring needed so runtime can swap stub analyst vs live analyst without rewriting core logic
- minimal shared types, request/response metadata, or error classes strictly needed for this boundary
- minimal new test fixtures strictly needed for mocked unit tests

## Hard constraints

Do not:

- modify anything under `src/polymarket_arb/*`
- add scheduling
- add execution or trading behavior
- add persistence or database work
- add UI
- bypass the existing reasoning parser/validator
- let live analyst code make policy decisions
- silently fall back to stub outputs on transport/parser failure
- widen into orchestration/retry systems beyond a single clear timeout/failure boundary
- introduce speculative architecture outside this boundary

Prefer existing dependencies or stdlib.
Do not add a new third-party package unless it is clearly necessary and there is no simpler bounded option.

## Suggested file shape

Expected shape, adjusted only if the repo’s existing patterns strongly suggest a small variation:

- `src/future_system/live_analyst/__init__.py`
- `src/future_system/live_analyst/adapter.py` or `client.py`
- `src/future_system/live_analyst/models.py` only if needed
- `src/future_system/live_analyst/errors.py` only if needed

Tests should cover:

- successful response path
- malformed transport response
- timeout path
- reasoning parser/validation failure path

## Behavioral requirements

The implementation must preserve this contract:

1. Runtime prepares deterministic context and prompt input using the existing reasoning layer.
2. Live analyst boundary performs the transport/model call.
3. Raw returned content goes through the existing reasoning parse/validation path.
4. Only validated reasoning output proceeds downstream.
5. Transport failures and parser failures remain distinguishable.

Specific requirements:

- expose a clean call surface that runtime can depend on
- timeout failures must raise an explicit live-analyst timeout error
- malformed or incomplete transport responses must raise an explicit live-analyst response/transport error
- parser/validation failures must remain explicit and distinct from transport failures
- no fake/default reasoning output may be injected on failure
- runtime must be able to use either the existing stub analyst or the new live analyst boundary with minimal wiring

## Acceptance criteria

This phase is complete when:

- runtime can swap stub analyst for live analyst boundary without a core-logic rewrite
- live analyst output still must pass through the existing `ReasoningOutputPacket` parsing/validation path
- timeout, malformed response, and parser-failure behavior are explicit and test-covered
- tests are mocked and deterministic
- `src/polymarket_arb/*` remains untouched

## Validation

Run narrow validation only.

At minimum, run the smallest reasonable set covering:

- new `live_analyst` module files
- any minimally touched runtime files
- new/updated unit tests

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
