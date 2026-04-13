# Phase 20A — Future System Next-Track Scope Lock

## Goal

Define a strict scope lock for the next `future_system` track after the completed local operator UI/review artifact checkpoint.

This phase is docs-only.

## Read first

- `.codex/phases/current_phase.md`
- `docs/PHASE_19Q_OPERATOR_UI_TRACK_CLOSEOUT.md`
- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- `docs/PHASE_19O_OPERATOR_UI_MANUAL_VERIFICATION_CHECKPOINT.md`

## Required deliverable

Add:

- `docs/PHASE_20A_FUTURE_SYSTEM_NEXT_TRACK_SCOPE_LOCK.md`

The scope-lock doc must define:

- current repository checkpoint context
- what Phase 18O–19Q completed
- what the next track should focus on
- recommended next track name
- allowed work
- forbidden work
- acceptance criteria
- validation expectations
- first 3–5 candidate phases after 20A

Recommended next-track direction:

- `future_system operator decision/review workflow hardening`

## Hard constraints

Do not:

- touch `src/polymarket_arb/*`
- touch `src/future_system/*`
- touch `tests/*`
- add features
- add DB/jobs/queues/scheduling/delivery/inbox/execution/trading logic
- claim production readiness

## Validation

Run:

- `git diff --stat`
- `git diff --name-only`

## Required Codex return format

Return:

1. concise summary
2. exact files changed
3. validation output
4. risks/deferred items
5. do not commit unless asked
