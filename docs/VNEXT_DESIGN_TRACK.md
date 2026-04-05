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

1. strengthen operator validation execution against the frozen baseline
2. define the promotion gate from read-only validation to stricter testing
3. define the live-capable execution boundary as a separate design surface
4. define risk and portfolio controls before any auth or signing discussion
5. define reconciliation and failure recovery before any real order submission path
6. only then consider whether a later phase should permit live-capable implementation work

## Explicit Non-Goals For Phase 13A

This phase does not add:

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
