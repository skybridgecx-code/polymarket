# Phase 20A Future System Next-Track Scope Lock

## Repo Checkpoint

- Repo: `polymarket-arb`
- Branch at scope lock creation: `phase-20a-future-system-next-track-scope-lock`
- Prior completed checkpoint: `phase-19q-operator-ui-track-closeout`
- Checkpoint status: local operator-readiness checkpoint for `future_system` operator UI/review artifacts; not a production-readiness claim

## What Phase 18O–19Q Completed

The completed track delivered a bounded local `future_system` operator workflow including:

- runtime/result envelope and review packet/render/bundle/export surfaces
- deterministic local artifact writing and runtime-to-artifact flow
- `future_system` CLI review artifact entrypoint
- local operator UI list/detail/read flow
- synchronous trigger flow with explicit failure-stage identity:
  - `analyst_timeout`
  - `analyst_transport`
  - `reasoning_parse`
- app entry/export/mount cleanup
- local runbook + manual verification checkpoint docs
- integration-flow test hardening for key shipped behavior

## Recommended Next Track

Recommended name:

- `future_system operator decision/review workflow hardening`

Primary focus:

- improve local operator review workflow after artifacts are generated
- add explicit review status/decision metadata only when file-artifact based
- keep all workflow behavior local and deterministic
- preserve current bounded operator safety constraints

## Allowed Work (Next Track)

- `future_system`-scoped docs/models/builders/rendering/UI refinements for local operator review workflow
- artifact-file based review status/decision metadata additions
- deterministic local-only tests and test coverage expansion
- bounded refactors that improve maintainability without widening runtime scope

## Forbidden Work (Next Track)

- any changes under `src/polymarket_arb/*` unless a separate explicit scope-lock phase approves it
- DB persistence layers
- queues/background workers/schedulers
- notification/delivery/inbox infrastructure
- execution/trading/order placement behavior
- production orchestration claims or production-readiness claims

## Acceptance Criteria (Next Track Scope)

The next track should be considered complete only when:

- local operator decision/review workflow is clearer and better structured than 19Q baseline
- any new review decision/status metadata remains artifact-file based and deterministic
- existing success/failure-stage semantics remain preserved
- local-only boundaries remain intact (no DB/queues/jobs/scheduling/delivery/execution)
- documentation and tests reflect shipped behavior accurately

## Validation Expectations (Next Track)

For each phase in the next track:

- keep validation narrow and phase-bounded
- run targeted `pytest` for touched future_system/operator-ui/review tests
- run `ruff check` and `mypy` for touched `future_system` surface
- explicitly report changed files and confirm whether `src/polymarket_arb/*` remains untouched

For scope-lock checkpoints:

- include `git diff --stat` and `git diff --name-only`
- avoid code changes unless that checkpoint explicitly allows them

## Candidate Phases After 20A

1. **20B — Operator Review Decision Metadata Contracts**  
   Define bounded artifact-file decision/status schema additions (if needed) with strict backward-safe semantics.

2. **20C — Operator UI Decision/Status Rendering Surface**  
   Surface decision/status metadata in list/detail templates without changing non-local behavior.

3. **20D — CLI/Artifact Review Workflow Alignment**  
   Align CLI-produced artifacts and UI-consumed artifacts around decision/review workflow expectations.

4. **20E — Deterministic Decision Workflow Test Hardening**  
   Add integration-style tests locking in decision/review workflow invariants and edge cases.

5. **20F — Track Verification + Closeout Checkpoint**  
   Produce manual verification notes, runbook polish, and final local-readiness closeout for the new track.

## Decision Gate

Before starting 20B, explicitly choose one:

1. Merge 19Q/20A as a stable checkpoint and stop.
2. Start the new bounded track above with a fresh phase-by-phase scope lock, keeping `src/polymarket_arb/*` out of scope unless explicitly authorized later.
