# Phase 20B — Operator Review Decision Metadata Contracts

## Goal

Define a bounded, deterministic contract for operator review decision/status metadata that can live alongside existing review artifacts as file-based local data.

This phase should prioritize models/contracts/docs/tests with no runtime behavior expansion.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`
- `docs/PHASE_19Q_OPERATOR_UI_TRACK_CLOSEOUT.md`
- `src/future_system/review_exports/*`
- `src/future_system/review_file_writers/*`
- `src/future_system/operator_ui/*`
- `tests/future_system/test_operator_ui_integration_flows.py`
- relevant future_system models/tests for export payload and artifact-read semantics

## Required deliverable

Build a scoped contract surface for operator review decision/status metadata, for example under:

- `src/future_system/operator_review_models/*`

The contract should cover deterministic artifact-file-based concepts such as:

- review status
- operator decision
- optional review notes summary
- local-safe identity/timestamp fields only when explicitly provided
- backward-safe relationship to existing artifact payloads

Add focused deterministic tests for:

- valid statuses/decisions
- serialization shape
- backward-safe optional behavior
- no DB/network/runtime execution coupling

Optional but encouraged:

- short phase doc summarizing the contract

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- introduce DB/queues/background jobs/scheduling/delivery/inbox/execution/trading logic
- widen scope into mutable workflow machinery or UI editing
- claim final operator workflow completion in this phase

## Validation

Run narrow validation on touched surfaces:

- `pytest` on touched future_system tests
- `ruff check` on touched files
- `mypy` on touched future_system modules

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
