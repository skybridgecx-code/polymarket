# Phase 14I — Replay Harness Variance Normalization

## Current Repo Truth

- the frozen baseline branch remains trusted and separate
- `src/polymarket_arb/` remains no-touch for this implementation branch
- the implementation branch currently contains only non-live future-system review
  support layers:
  - observability and audit foundation
  - review packet builder
  - evidence evaluator
  - deficiency summarizer
  - recommendations
  - review bundles
  - review reports
  - replay review harness
- no live-capable behavior exists on this branch
- no venue-facing actions are allowed on this branch

## Accepted 14H Harness-Local Variance

Phase 14H introduced one bounded harness-local variance:

- a replay-scenario field named `packet_adjustment`
- one accepted adjustment value:
  - `DROP_TRACE_COVERAGE`

That adjustment is applied only after raw observability inputs have already been
assembled into a single review packet. It exists solely so the replay harness can
exercise downstream traceability checks while keeping the scenario inside the
single-packet contract required by the harness.

This is the only accepted variance from pure raw-input replay fidelity in Phase 14H.

## Why The Variance Was Accepted

The variance was accepted as a contained exception rather than rejected as scope
drift because:

- the existing review packet builder groups raw inputs by `correlation_id`
- a raw-input traceability-deficient scenario that introduces mismatched
  `correlation_id` values naturally splits into multiple packets
- the Phase 14H harness was explicitly scoped to replay one bounded scenario into
  one bounded review result
- changing the packet-builder semantics to force a single packet would have been a
  redesign of an existing review component, which Phase 14H did not authorize
- broadening the harness to multi-packet replay would also have been a larger design
  move than Phase 14H allowed

Accepting one narrow post-packet adjustment was therefore the smallest available
exception that preserved:

- existing review-component semantics
- the single-packet replay contract
- the non-live, in-memory-only boundary

## Corrected Forward Interpretation

Harness-local adjustments are not a new default pattern.

They are allowed only when all of the following are true:

- the harness phase is explicitly bounded to exercise already-existing downstream
  review semantics
- the desired deficient condition cannot be represented through raw inputs without
  changing the semantics of an existing review component
- the adjustment is applied only after the existing component under test has already
  produced its normal upstream output
- the adjustment is local to the harness and deterministic
- the adjustment does not add new evaluation logic, automation, runtime wiring, or
  broader scenario orchestration
- the adjustment is documented explicitly as an exception in branch history

Harness-local adjustments are not allowed when they would:

- become the normal way of expressing scenarios
- hide a component-semantics problem that should instead be fixed in a narrowly
  approved cleanup phase
- widen replay from a bounded single-result harness into a larger orchestration or
  comparison system

## Forward Decision Fork

Phase 14H remains accepted. No code rollback is required.

The next real code move should choose one of two narrow directions:

### Option A — Raw-Input Replay Fidelity Cleanup

Purpose:

- remove the need for the accepted harness-local traceability adjustment

Boundary:

- a narrow semantics-cleanup phase only
- focused on whether traceability-deficient replay can be represented from raw
  inputs while still preserving the accepted review-component boundaries

Why choose it:

- if the priority is cleaner replay semantics and less harness-local exception

What it must not become:

- a redesign of the full review stack
- a multi-packet orchestration layer
- a broader replay/comparison system

### Option B — Scenario-Pack Expansion Under Current Harness Rules

Purpose:

- keep the current harness rules intact and add more bounded scenarios under the
  documented exception policy

Boundary:

- no semantics cleanup first
- continue to treat the 14H traceability adjustment as an allowed contained
  exception

Why choose it:

- if the priority is broader scenario coverage without changing accepted replay
  semantics yet

What it must not become:

- silent growth of multiple ad hoc adjustments
- an implicit redefinition of raw-input replay fidelity
- a broader operator or automation surface

## Phase 14I Outcome

This phase records the accepted 14H variance without rewriting history.

It does not:

- change code
- change tests
- reinterpret 14H as a mistake requiring rollback
- choose the next code path in advance

It does:

- preserve a truthful branch record
- make the accepted-exception status explicit
- define the forward rule for harness-local adjustments
- frame the next implementation decision cleanly
