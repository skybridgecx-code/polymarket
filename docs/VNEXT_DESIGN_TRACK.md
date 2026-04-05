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

### Phase 13C

Objective:

- define the execution boundary between the frozen baseline repo and any future execution-capable system

Why it exists:

- the current repo already contains execution research and paper-trade simulation, which creates a real risk of accidental scope drift if future live-capable work is not kept separate

What it would change:

- design documents only
- explicit ownership split between the frozen baseline and any later execution-capable system
- explicit prerequisites that must be satisfied before implementation of any execution-capable system is even discussable

What it must not change:

- the frozen baseline repo
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior
- live trading behavior

Validation required before moving on:

- the execution boundary is documented in a way that makes ownership, non-reuse rules, and trust boundaries explicit
- the baseline repo is still described as read-only plus simulation/review only
- no document in the frozen baseline is rewritten to imply that execution-capable behavior is already planned into the shipped system

Decision gate to unlock the next phase:

- approval that the boundary is explicit enough that later risk/control design can assume a separate execution-capable system rather than a baseline repo extension

### Phase 14

Objective:

- design the promotion gate from the frozen baseline to stricter operator release discipline

Why it exists:

- the current baseline is validated, but promotion criteria for any tighter execution-adjacent environment are not yet formalized

What it would change:

- operator release criteria
- promotion thresholds
- documented go/no-go rules for advancing the frozen baseline into stricter testing and review discipline, not into live execution

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

- approval that promotion criteria are complete enough to support later risk/control design without weakening the frozen baseline

### Phase 15

Objective:

- design the live-capable system surface that would exist outside the frozen baseline boundary

Why it exists:

- once the boundary is defined, the future execution-capable system still needs its own owned surface and responsibilities

What it would change:

- system-level responsibilities for any future order-intent, auth, signing, routing, and execution state handling
- explicit handoff points from baseline research outputs into a separate future system

What it must not change:

- paper-trade formulas
- policy formulas
- read-only baseline services
- any live behavior in the current repo

Validation required before moving on:

- explicit ownership for future execution responsibilities is documented
- auth, signing, and order submission remain out of scope in this phase
- no future system responsibility is assigned back into the frozen baseline repo

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

1. execution-boundary design
2. promotion gate design
3. separate live-capable system surface design
4. risk and portfolio control design
5. reconciliation and stricter pre-live testing design

No later phase should start until the prior phase has an explicit approval decision. No phase in this document authorizes implementation by default.

## Execution Boundary

### Purpose Of This Boundary

The boundary exists to prevent a dangerous category error: treating a trusted read-only research repo as the natural place to add live-capable execution. That would collapse inspection, simulation, and execution into one surface and weaken every control boundary the frozen baseline currently relies on.

### What Must Remain Inside The Frozen Baseline Repo

The baseline repo keeps ownership of:

- read-only public data ingestion
- deterministic normalization
- opportunity scanning
- wallet ingestion and relationship scoring
- paper-trade planning and simulation
- post-simulation policy decisions on simulated rows
- review packets and replay evaluation
- operator documentation, checkpoint inspection, and operator validation

The baseline repo remains a research and operator-inspection system. It may continue to produce candidate opportunities, simulated plans, simulated outcomes, and audit artifacts. It must not become an execution runtime.

### What Must Remain Outside The Frozen Baseline Repo

The baseline repo must not take ownership of:

- exchange or venue authentication
- private key custody or signing
- order-intent creation for live venues
- order submission, cancelation, or replace behavior
- execution-state reconciliation against external fills or balances
- portfolio state mutation
- live exposure management
- autonomous live control loops

These responsibilities belong outside the frozen baseline because they cross the line from read-only research into systems that can create irreversible external effects.

### What A Future Execution-Capable System Would Own

If a future system is ever approved, that separate system would own:

- auth and credential handling
- key management and signing boundaries
- order-intent lifecycle
- order submission and execution acknowledgements
- venue reconciliation
- live position and exposure state
- portfolio and capital controls
- failure recovery for live external actions

The baseline repo could at most provide upstream research artifacts or operator-reviewed signals to that future system. It would not own the live control plane.

### Boundary Rules Between The Two

- the baseline repo may publish read-only analytics outputs and simulated research outputs only
- no live-capable code path may be added by extending `paper-trade` directly
- no auth, signing, or order-routing logic may be placed into current clients, services, routes, or CLI commands
- no policy or checkpoint model in the baseline should be rebranded as a live risk or reconciliation system
- any future execution-capable system must consume clearly defined outputs from the baseline rather than reaching into internal baseline modules opportunistically
- rejected and weak baseline outputs must remain explicit and must not be reinterpreted as executable orders

### Prerequisites Before Any Execution-Capable Implementation

Before any execution-capable implementation is allowed, all of the following must be true:

- the execution boundary is explicitly approved
- a separate future system surface is explicitly approved
- risk and portfolio controls are designed and reviewed
- reconciliation and failure-recovery design is complete
- stricter pre-live validation and forward-testing stages are defined
- separate approval is granted to move from design-only work into implementation work

### Risks Of Violating The Boundary

- operator trust in the frozen baseline would be weakened
- simulated success could be confused with execution readiness
- live side effects could be introduced into code paths that were validated only as read-only or paper-trade research
- review, replay, and checkpoint artifacts could be mistaken for live reconciliation controls even though they were never designed for that role
- future incident response would be harder because ownership would be split across a mixed research/execution codebase

## Recommended Order Of Future Work

1. finish the execution-boundary definition
2. define promotion gates for stricter non-live testing and operator release discipline
3. define the separate future execution-capable system surface
4. define risk and portfolio control ownership for that separate system
5. define reconciliation, failure recovery, and stricter pre-live testing before any implementation phase is proposed

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

## Explicit Non-Goals For Phase 13C

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
