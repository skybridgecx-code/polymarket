# vNext Design Track

## Purpose

This document starts a separate design track for what comes after the frozen baseline.

It is design-only. It does not change the shipped system, operator surface, or trust boundary of the current baseline.

## What Stays Frozen

The current baseline remains the trusted shipped system:

- read-only Polymarket ingestion
- fee-aware opportunity scanning
- wallet seed discovery and wallet activity ingestion
- lead/lag copier detection
- read-only FastAPI operator API
- bounded refresh orchestration with checkpointing
- paper-trade planning and simulation
- post-simulation policy decisions
- review packets and replay evaluation
- operator runbook, workflow examples, checklists, failure-mode guidance, and operator validation

That baseline is still not:

- a live trading system
- an auth system
- a private key system
- an order submission system

## Why A Separate vNext Track Exists

The frozen baseline is valuable because it is bounded, inspectable, and trusted. Future work should not blur that trust boundary by mixing speculative live-capable design into the shipped operator surface.

The vNext track exists to:

- preserve the current baseline as the stable reference point
- define future boundaries before implementation starts
- make promotion criteria explicit before any live-capable work is considered
- reduce the risk of accidental scope drift from read-only research into unsafe execution behavior

## Phased Roadmap

The vNext track should stay short, gated, and operator/risk-aware. The phases below are design phases first. Implementation should not begin until a later phase explicitly permits it.

### Phase 13B

Objective:

- define the bounded vNext roadmap and decision gates

Why it exists:

- future work needs explicit gates before design can turn into implementation

What it would change:

- design documents only

What it must not change:

- the frozen baseline
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior
- live trading behavior

Validation required before moving on:

- docs review confirms the phased path is bounded and explicit
- the frozen baseline docs remain untouched unless a later phase explicitly authorizes cross-references

Decision gate to unlock the next phase:

- the future-phase sequence is specific enough that each later phase can be approved or rejected independently

### Phase 14

Objective:

- design the promotion gate from the frozen baseline to stricter operator release discipline

Why it exists:

- the current baseline is validated, but promotion criteria for any tighter execution-adjacent environment are not yet formalized

What it would change:

- operator release criteria
- promotion thresholds
- documented go/no-go rules for advancing beyond the frozen baseline

What it must not change:

- execution behavior
- auth boundaries
- order placement boundaries
- live-capable system behavior

Validation required before moving on:

- explicit promotion criteria are documented
- rejection criteria for unsafe promotion are documented
- operator validation execution requirements are concrete and reviewable

Decision gate to unlock the next phase:

- approval that promotion criteria are complete enough to support execution-boundary design without weakening the frozen baseline

### Phase 15

Objective:

- design the live-capable execution boundary as a separate system surface

Why it exists:

- the current paper-trade path must not be allowed to drift directly into live execution

What it would change:

- architecture-level boundary definitions between simulation and any future order-intent or execution system
- explicit module and responsibility separation for a future live-capable track

What it must not change:

- paper-trade formulas
- policy formulas
- read-only baseline services
- any live behavior in the current repo

Validation required before moving on:

- explicit non-reuse rules are documented for paper-trade code paths
- live-capable boundary diagrams and control points are documented
- auth, signing, and order submission remain out of scope in this phase

Decision gate to unlock the next phase:

- approval that the execution boundary is clear enough to support risk/control design without collapsing trust boundaries

### Phase 16

Objective:

- design the risk and portfolio control layer for any future live-capable system

Why it exists:

- no live-capable design should proceed without controls that are broader than per-trade simulation logic

What it would change:

- design for exposure controls
- control hierarchy for kill switches and circuit breakers
- operator approval and escalation boundaries

What it must not change:

- current baseline policy behavior
- current checkpoint model
- current paper-trade outputs

Validation required before moving on:

- portfolio-level controls are documented
- failure containment rules are documented
- operator override and approval semantics are documented as design only

Decision gate to unlock the next phase:

- approval that the risk/control layer is complete enough to support reconciliation and recovery design

### Phase 17

Objective:

- design reconciliation, failure recovery, and stricter pre-live testing stages

Why it exists:

- any future live-capable system would need explicit state recovery, reconciliation, and forward-testing stages before real order submission is even considered

What it would change:

- design for reconciliation checkpoints
- failure classification
- recovery workflows
- staged progression from stricter testing to any later approval request

What it must not change:

- current baseline behavior
- current read-only operator surface
- live trading boundaries

Validation required before moving on:

- reconciliation flows are documented
- failure recovery responsibilities are documented
- stricter testing stages are documented with explicit stop conditions

Decision gate to unlock any later implementation phase:

- separate approval that the design track is complete enough to justify discussing implementation
- separate approval that live-capable work is allowed at all

## Decision Gates

The phases above are intentionally serial:

1. promotion gate design
2. live-capable execution boundary design
3. risk and portfolio control design
4. reconciliation and stricter pre-live testing design

No later phase should start until the prior phase has an explicit approval decision. No phase in this document authorizes implementation by default.

## Candidate Future Design Areas

### Operator Validation Promotion Gate

Design goal:

- define what must pass before the baseline can be promoted from documented operator validation to stricter execution-adjacent testing

Likely scope:

- stricter acceptance gates
- promotion criteria for fixtures, replay, and checkpoint verification
- explicit failure thresholds for operator release confidence

### Live-Capable Execution Design Boundary

Design goal:

- define a hard separation between the current paper-trade path and any future live-capable execution path

Likely scope:

- explicit module boundary between simulation and any future order-intent layer
- non-goals around direct reuse of paper-trade services for live execution
- review points before auth, signing, or order placement are even discussed

### Risk And Portfolio Control Layer

Design goal:

- define the control plane that would have to exist before any live-capable behavior could be considered

Likely scope:

- exposure limits
- circuit-breaker hierarchy
- portfolio-level guardrails
- operator approval boundaries

### Reconciliation And Failure Recovery

Design goal:

- define how a future live-capable system would detect and reconcile drift, partial failures, or inconsistent external state

Likely scope:

- reconciliation checkpoints
- failure classification
- replay and recovery boundaries
- operator-visible recovery states

### Promotion Path From Simulation To Stricter Testing

Design goal:

- define the staged path from read-only simulation to more demanding verification environments without jumping directly to live behavior

Likely scope:

- simulation hardening
- deterministic acceptance promotion
- stricter integration-style testing
- explicit go/no-go gates between stages

## Risks Of Prematurely Going Live

The main risks are structural, not cosmetic:

- paper-trade success can be mistaken for execution readiness
- current checkpointing and validation are operator-safe for a read-only system, not a full live control plane
- policy decisions on simulated rows do not replace real exposure management
- replay and review are useful audit tools, but they are not execution reconciliation
- adding live behavior too early would collapse boundaries that are currently clear and defensible

## Recommended Order Of Future Work

1. complete design-only promotion gating
2. complete design-only live-capable execution boundary work
3. complete design-only risk and portfolio control work
4. complete design-only reconciliation and stricter testing work
5. require separate approval before any implementation phase is even proposed

## Explicit Non-Goals For Phase 13B

This design track does not add:

- Python changes
- route changes
- new CLI commands
- scoring changes
- policy changes
- live trading behavior
- auth or private key handling
- UI work
- implementation of the future system
- broad roadmap expansion beyond this design outline

## Phase Boundary

This branch adds a design track only. The current baseline remains the trusted shipped system until a later phase explicitly changes that status.

Promotion to anything live-capable requires separate approval, tighter controls, and stricter validation than anything described in the frozen baseline.
