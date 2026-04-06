# Phase 14A — First Candidate Implementation Branch Scope Lock

## Purpose

This document locks the exact scope of the first approved implementation candidate for
the separate implementation branch. It governs Phase 14B, which is the single narrow
code phase immediately following this bootstrap.

This document does not authorize implementation beyond the Phase 13L candidate.
It does not authorize live behavior, auth, signing, order submission, or any
execution-capable surface.

---

## Current Repo Truth

- Trusted frozen baseline: branch `phase-9-policy-and-guardrail-layer`
- Frozen baseline module tree: `src/polymarket_arb/` — all files in this tree are
  no-touch for this branch
- vNext design track: complete through Phase 13O on
  `phase-13a-vnext-design-track-bootstrap` (head `99a0dba`)
- Current implementation branch: `phase-14a-first-candidate-implementation-bootstrap`,
  forked from that head
- Design phases completed: 13B through 13O
- Implementation authorized: Phase 13L first candidate only — non-live observability
  and audit foundation

No live behavior exists on this branch. No implementation has begun. This document
is the first act on this branch.

---

## Exact First Approved Candidate (from Phase 13L)

Extracted verbatim from `docs/VNEXT_DESIGN_TRACK.md` § "The Narrowest Acceptable
First Candidate":

> At criteria level only, the narrowest acceptable first implementation candidate is:
>
> - a future-system observability and audit foundation that remains non-live, separate
>   from the frozen baseline, and incapable of emitting venue-facing actions

### What It May Touch (from Phase 13L)

- structured event definitions for future critical decision paths
- correlation and traceability primitives for future-system records
- immutable audit-record boundaries for future approvals, control actions, and
  recovery-relevant state changes
- bounded review-oriented telemetry contracts for a future non-live system
- non-live validation hooks needed to prove that the future observability surface is
  attributable and reconstructible

It may exist only outside the frozen baseline repo and only as a control-supporting
foundation for later non-live work.

### What It Must Not Touch (from Phase 13L)

- the frozen baseline repo or its current CLI, API, services, or models
- auth, signing, credentials, or private key handling
- order-intent creation, order submission, cancelation, replace logic, or venue adapters
- live position mutation or exposure mutation
- risk-control decisions beyond recording future-system facts
- reconciliation actions beyond future auditability and traceability contracts
- strategy logic, scoring logic, or portfolio allocation logic
- UI surfaces or background worker expansion

---

## Minimum Allowed File Touch Set for Phase 14B

Phase 14B may create only the following new files. No existing file may be modified.

### New source files (outside `src/polymarket_arb/`)

```
src/future_system/__init__.py
src/future_system/observability/__init__.py
src/future_system/observability/events.py
src/future_system/observability/audit.py
src/future_system/observability/correlation.py
```

Responsibilities by file:

- `events.py`: defines structured, typed event records for future critical decision
  paths (approval events, control events, recovery-relevant state changes); no live
  emission, no network calls, no venue references
- `audit.py`: defines immutable audit-record contracts with explicit field boundaries
  for future-system attribution (who acted, what was decided, when, under what
  authority); no live persistence, no external calls
- `correlation.py`: defines correlation key types and traceability primitives that
  connect future decision, control, and recovery records; no live state, no side
  effects

All three modules must be pure data-definition modules: Pydantic models or typed
dataclasses only. No I/O, no HTTP clients, no database connections, no file writes.

### New test files

```
tests/future_system/__init__.py
tests/future_system/test_observability_boundary.py
```

`test_observability_boundary.py` must verify:

- all event types carry a required correlation key field
- all audit records carry required attribution fields (actor, action, authority,
  timestamp)
- no event type or audit record imports from `src/polymarket_arb/`
- no event type or audit record carries any field that names a venue, order, position,
  credential, or live state concept
- all record types are instantiable from pure in-memory fixtures with no network
  calls, no file I/O, and no external dependencies

These are structural boundary checks, not integration tests.

### New documentation file

```
docs/PHASE_14B_IMPLEMENTATION_LOG.md
```

This file must be created by Phase 14B after its code work is complete. It must
record:

- which files were created
- what each module's top-level exports are
- which test checks passed
- which no-touch boundaries were verified to be unbroken
- any unresolved questions or deferred items discovered during implementation

Phase 14B must not begin without this scope lock. Phase 14B must not close without
producing this log.

### No other files

Phase 14B must not create or modify any file not listed above. Any file outside this
set is a scope violation and triggers immediate halt.

---

## Explicit Non-Goals for Phase 14B

Phase 14B must not:

- modify any file under `src/polymarket_arb/`
- modify `BASELINE.md`, `CODEX_HANDOFF.md`, `ARCHITECTURE.md`, `README.md`,
  `ROADMAP.md`, `docs/OPERATOR_RUNBOOK.md`, `docs/OPERATOR_VALIDATION.md`
- add CLI commands, API routes, or operator-visible surfaces
- add live emission, network calls, HTTP clients, or database connections to any
  new module
- implement governance enforcement, risk/control enforcement, or reconciliation
  automation
- implement portfolio allocation, order-intent logic, or venue adapters
- add auth, credential handling, signing, or private key logic
- implement anything corresponding to Phase 14 or later in the vNext design track
  (live-capable system surface, portfolio-governance integration, forward-testing design)
- widen the candidate scope based on implementation convenience
- merge or depend on the frozen baseline module tree

---

## Exact Validation Commands for Phase 14B

After Phase 14B completes its code work and before any commit is made, the following
commands must all pass cleanly:

```bash
# 1. Confirm no frozen baseline files were modified
git diff --name-only HEAD | grep "src/polymarket_arb" && echo "VIOLATION: baseline touched" || echo "OK: baseline clean"

# 2. Confirm only allowed files were added
git diff --name-only HEAD

# 3. Run full baseline validation (must stay green)
source .venv/bin/activate && make validate

# 4. Run new future_system tests in isolation
source .venv/bin/activate && python -m pytest tests/future_system/ -v

# 5. Confirm no imports from polymarket_arb in new modules
grep -r "from polymarket_arb\|import polymarket_arb" src/future_system/ && echo "VIOLATION: cross-import" || echo "OK: no cross-imports"

# 6. Confirm no live or venue references in new modules
grep -rE "order|venue|sign|auth|credential|key|submit|position|live" src/future_system/ --include="*.py" | grep -v "^Binary\|#" | grep -v "test_" && echo "REVIEW: potential scope drift" || echo "OK: no live references"
```

All six checks must pass before Phase 14B closes. Commands 3 and 4 must both show
zero failures. Commands 5 and 6 must both show "OK" or produce no output.

---

## Exact Halt Conditions for Phase 14B

Phase 14B must halt immediately and seek supervisor and reviewer reauthorization if
any of the following is detected:

- any file under `src/polymarket_arb/` appears in `git diff --name-only`
- any new module imports from `polymarket_arb`
- any new module contains a field or type name referencing a venue, order, credential,
  position, auth flow, or signing operation
- any new module contains I/O: file writes, HTTP calls, database connections, or
  environment variable reads for secrets
- `make validate` produces any failure (ruff, mypy, or pytest)
- `tests/future_system/` tests fail for any reason other than a missing dependency
  that is itself within the allowed scope
- a file outside the minimum allowed touch set is created or modified
- the implementation log reveals that a no-touch boundary was crossed during
  implementation

A halt means: stop, do not commit, record the finding in a note, return to this
scope lock document, and report to supervisor and reviewer before proceeding.

---

## Supervisor and Reviewer Gating

Before Phase 14B begins writing any code:

1. supervisor and reviewer must confirm this scope lock document is complete,
   accurate, and consistent with Phase 13L and Phase 13O
2. supervisor and reviewer must confirm the branch lineage is correct
   (forked from `99a0dba` on `phase-13a-vnext-design-track-bootstrap`)
3. supervisor and reviewer must confirm the minimum file touch set is the narrowest
   acceptable scope for the Phase 13L candidate
4. supervisor and reviewer must issue explicit written authorization to begin Phase 14B

Phase 14B does not begin until that authorization is recorded.

---

## Phase Boundary

This document completes Phase 14A. It does not begin Phase 14B.

Phase 14B begins only after supervisor and reviewer authorization. Phase 14B is
complete only when all validation commands pass and the implementation log exists.

The frozen baseline remains trusted and separate throughout.
