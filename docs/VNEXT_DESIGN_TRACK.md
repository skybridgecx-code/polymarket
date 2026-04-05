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

### Phase 13D

Objective:

- define the future risk/control layer that would govern any later execution-capable system outside the frozen baseline

Why it exists:

- a future execution-capable system cannot be considered safe unless a separate control layer defines hard limits, escalation rules, and permission boundaries before any autonomous or operator-assisted action is allowed

What it would change:

- design documents only
- explicit ownership for a future risk/control layer
- explicit control responsibilities, input contracts, permitted decisions, and prerequisites for any later implementation

What it must not change:

- the frozen baseline repo
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior in the frozen baseline
- live trading behavior

Validation required before moving on:

- control ownership and non-goals are explicit
- the design distinguishes containment and permissioning from strategy selection
- the design does not assign live control responsibilities back into the frozen baseline repo

Decision gate to unlock the next phase:

- approval that the risk/control layer is complete enough to support later reconciliation and stricter testing design without inventing live behavior

### Phase 13E

Objective:

- define the future reconciliation and failure-recovery layer that would be required for any later execution-capable system outside the frozen baseline

Why it exists:

- no execution-capable system is trustworthy unless it can detect divergence, classify failures, recover in bounded ways, and preserve an audit trail under degraded conditions

What it would change:

- design documents only
- explicit ownership for a future reconciliation and failure-recovery layer
- explicit failure classes, recovery properties, input contracts, permitted recovery actions, and prerequisites for any later implementation

What it must not change:

- the frozen baseline repo
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior in the frozen baseline
- live trading behavior

Validation required before moving on:

- failure classes and recovery responsibilities are explicit
- idempotency, replayability, audit logging, retry boundaries, and manual intervention triggers are documented
- the design does not treat checkpointing, replay, or paper-trade review artifacts in the frozen baseline as if they were already a live reconciliation system

Decision gate to unlock the next phase:

- approval that reconciliation and failure-recovery design is complete enough to support later promotion-gate and stricter testing design without inventing live behavior

### Phase 13F

Objective:

- define the staged promotion path and pre-live validation gates that would be required before any future live-capable implementation is even proposed

Why it exists:

- promotion from the frozen baseline into execution-adjacent work must be earned through concrete evidence, not assumed from design completeness or paper-trade results

What it would change:

- design documents only
- explicit validation stages
- explicit evidence requirements, stop conditions, rollback triggers, and prohibited actions at each stage

What it must not change:

- the frozen baseline repo
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior in the frozen baseline
- live trading behavior

Validation required before moving on:

- staged promotion requirements are concrete enough to reject unsafe advancement
- every stage has explicit required evidence and rollback triggers
- shadow-mode or dry-run stages remain explicitly non-live in this design phase

Decision gate to unlock the next phase:

- approval that the promotion path is concrete enough to govern future-system design and later implementation gating without weakening the frozen baseline boundary

### Phase 13G

Objective:

- define the data, telemetry, audit, and observability boundaries that a future execution-capable system would require before implementation could move forward

Why it exists:

- observability in a future execution-capable system is not a debugging convenience; it is part of the control surface required to reconstruct critical decisions, bound automation, and support operator, risk, and reconciliation workflows

What it would change:

- design documents only
- explicit telemetry, audit, event, metric, and traceability requirements
- explicit minimum observability requirements before any later implementation phase can be considered

What it must not change:

- the frozen baseline repo
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior in the frozen baseline
- live trading behavior

Validation required before moving on:

- critical future-system decision paths are explicitly observable and reconstructible on paper
- minimum telemetry, audit, and correlation requirements are concrete enough to reject under-instrumented implementation work
- the design keeps future observability outside the frozen baseline rather than quietly widening current operator surfaces

Decision gate to unlock the next phase:

- approval that the observability boundary is complete enough to support future-system surface design and later implementation gating without weakening the frozen baseline trust boundary

### Phase 13H

Objective:

- define the future portfolio and capital-allocation layer that would sit outside the frozen baseline and govern capital usage across strategies and opportunity groups

Why it exists:

- a future execution-capable system would need an explicit layer that decides how much capital can be allocated, where it can be allocated, how competing intents are resolved, and when de-allocation or rebalance pressure must override strategy appetite

What it would change:

- design documents only
- explicit portfolio and capital-allocation ownership
- explicit allocation, exposure-budgeting, limit, netting, and conflict-resolution rules at design level

What it must not change:

- the frozen baseline repo
- Python behavior
- routes
- CLI commands
- scoring logic
- policy behavior in the frozen baseline
- live trading behavior

Validation required before moving on:

- capital-allocation authority and non-goals are explicit
- portfolio-level and strategy-level limit boundaries are concrete enough to reject under-specified implementation work
- the design keeps portfolio allocation outside the frozen baseline rather than reinterpreting paper-trade artifacts as live capital controls

Decision gate to unlock the next phase:

- approval that the portfolio and capital-allocation boundary is complete enough to support future-system surface design and later implementation gating without weakening the frozen baseline trust boundary

### Phase 14

Objective:

- design the live-capable system surface that would exist outside the frozen baseline boundary once promotion gates and control layers are already defined

Why it exists:

- once the boundary, control, recovery, and promotion layers are defined, the future execution-capable system still needs its own owned surface and responsibilities

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

- approval that the separate future system surface is clear enough to support later detailed portfolio-control integration without collapsing trust boundaries

### Phase 15

Objective:

- refine portfolio-governance sequencing and cross-component integration detail for any future live-capable system

Why it exists:

- once portfolio allocation ownership is defined, the future system still needs a narrower design for how allocation decisions, escalation sequencing, and cross-component control interactions fit around that owned layer

What it would change:

- limit evaluation order across scopes
- escalation sequencing between allocation pressure, automated holds, kill switches, and operator approval boundaries
- cross-component handoff rules between strategy intents, portfolio controls, and future execution services

What it must not change:

- current baseline policy behavior
- current checkpoint model
- current paper-trade outputs

Validation required before moving on:

- portfolio-level allocation and control interactions are documented
- capital-governance escalation rules are documented
- operator override and approval semantics remain documented as design only

Decision gate to unlock the next phase:

- approval that the control layer is detailed enough to support stricter forward-testing design and eventual implementation gating

### Phase 16

Objective:

- design stricter pre-live testing and forward-testing stages after the control and recovery layers are already defined

Why it exists:

- any future live-capable system would still require explicit staged testing after the control and reconciliation layers are defined, because implementation should not move directly from design approval to unrestricted execution-adjacent behavior

What it would change:

- staged progression from stricter integration-style testing to later approval requests
- stop conditions for forward-testing stages
- promotion boundaries between progressively stricter non-live or tightly controlled test environments

What it must not change:

- current baseline policy behavior
- current checkpoint model
- current paper-trade outputs

Validation required before moving on:

- stricter testing stages are documented with explicit stop conditions
- stage-exit requirements are documented
- forward-testing boundaries remain explicitly separate from live order submission approval

Decision gate to unlock the next phase:

- separate approval that the design track is complete enough to justify discussing implementation
- separate approval that live-capable work is allowed at all

## Decision Gates

The phases above are intentionally serial:

1. execution-boundary design
2. risk/control-layer design
3. reconciliation and failure-recovery design
4. promotion-gate and pre-live validation design
5. data and observability boundary design
6. portfolio and capital-allocation design
7. separate live-capable system surface design
8. detailed portfolio-control integration design
9. stricter pre-live testing design

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

## Risk And Control Layer

### Purpose Of This Layer

This layer exists to decide whether a future execution-capable system is permitted to act, at what size, under what limits, and under what escalation conditions. It is a control and containment layer, not a strategy engine and not a venue-execution engine.

### Why It Must Be Separate From The Frozen Baseline

The frozen baseline is intentionally limited to read-only analytics, paper-trade simulation, policy decisions on simulated rows, review, and operator inspection. A future risk/control layer would govern real external consequences. Collapsing those responsibilities into the baseline would weaken the current trust boundary and create pressure to reinterpret simulation-time artifacts as live controls.

### Responsibilities A Future Risk/Control Layer Would Own

The future layer would own:

- position sizing authority
- exposure caps across market, strategy, venue, and portfolio scopes
- concentration limits
- market disable switches
- strategy disable switches
- circuit-breaker hierarchy
- kill-switch boundaries
- operator escalation and approval boundaries
- manual override approval paths
- promotion gates from simulation to stricter testing or later execution-adjacent stages

This layer would decide whether a future execution-capable system may proceed, must be held, must be reduced, or must be stopped.

### Required Inputs To This Layer

The future layer may consume only explicit, reviewable inputs such as:

- baseline research outputs and paper-trade artifacts
- operator-approved configuration and limit definitions
- live position and exposure state from a separate future execution-capable system
- venue health and reconciliation state
- portfolio-level capital allocation state
- operator approvals, denials, and emergency stop signals
- promotion-stage status for non-live testing environments

This layer should not depend on hidden heuristics or implicit operator memory.

### Permitted Outputs And Decisions

The future layer may emit only bounded control decisions such as:

- allow or disallow a class of actions
- maximum permitted size or notional
- exposure reduction requirements
- market disable or strategy disable decisions
- circuit-breaker activation
- kill-switch activation
- escalation requirement for human review
- promotion approval or promotion denial for stricter testing stages

Every emitted decision must be bounded, logged, attributable, and reversible through an explicit control path where appropriate.

### What It Must Not Be Allowed To Do Without Separate Controls

The future risk/control layer must not be allowed to:

- generate trading ideas or optimize strategy logic
- bypass auth, signing, or execution approval boundaries
- submit orders directly unless a separate future design explicitly authorizes that architecture
- rewrite venue reconciliation truth
- suppress or erase failure records
- apply manual overrides without operator attribution and explicit scope limits
- expand limits automatically without a separate approved rule and audit path

### Guardrails And Non-Goals

- this is not a strategy-optimization layer
- this is not the live execution engine
- this is not a replacement for venue reconciliation
- this is not a reason to widen the frozen baseline repo
- every autonomous decision must have limits, logs, and override paths
- every override path must be attributable and bounded

### Prerequisites Before Any Risk/Control Implementation

Before implementation of any future risk/control layer is allowed, all of the following must be true:

- the execution boundary is approved
- the future execution-capable system boundary is approved
- limit scopes and control hierarchy are documented
- manual override and kill-switch authority are documented
- promotion gates for stricter non-live testing are documented
- reconciliation and failure-recovery expectations are documented enough that controls can react to them
- separate approval is granted to move from design-only work into implementation work

### Risks Of Under-Designing This Layer

- sizing and exposure decisions could become inconsistent across components
- kill switches and circuit breakers could conflict or fail open
- manual overrides could become informal and unauditable
- simulated policy behavior could be misused as if it were a portfolio control plane
- a future execution-capable system could take actions without clear authority, limits, or escalation paths
- operator confidence would degrade because no single layer would clearly own containment

## Reconciliation And Failure Recovery

### Purpose Of This Layer

This layer exists to preserve correctness under failure. It would detect whether internal state and external venue state diverge, classify what kind of failure occurred, and choose bounded recovery paths that preserve auditability. This is not a convenience feature. It is a correctness and containment layer for a future execution-capable system.

### Why It Must Be Separate From The Frozen Baseline

The frozen baseline has bounded checkpointing, replay, and review artifacts for a read-only and paper-trade system. Those features are useful for operator inspection, but they are not a live reconciliation control plane. A future reconciliation layer would govern recovery after real external side effects, so it must remain outside the frozen baseline repo and outside the current paper-trade path.

### Failure Classes The Future System Must Handle

At minimum, the future layer would need explicit handling for:

- partial fills
- duplicate submits
- missing acknowledgements
- stale internal state
- disconnect and reconnect gaps
- state divergence between internal records and venue state
- delayed external data
- missing external data
- conflicting execution events received out of order
- retries that risk creating duplicate external effects

### Responsibilities The Reconciliation Layer Would Own

The future layer would own:

- detection of state divergence
- classification of failure modes
- reconciliation checkpoints
- idempotency enforcement for recovery paths
- bounded replay and replay verification
- retry eligibility decisions and retry suppression rules
- manual intervention triggers when automated recovery is no longer trustworthy
- audit logging for every recovery-relevant state transition

This layer would answer questions such as: what happened, what is known, what is uncertain, what can be retried safely, and when must automation stop and escalate.

### Required Inputs, Records, And Checkpoints

The future layer may consume only explicit, reviewable records such as:

- internal order-intent and execution-attempt records from a separate future execution-capable system
- venue acknowledgements, rejects, cancels, and fill events
- live position and exposure state
- reconnect and session-gap records
- reconciliation checkpoints and checkpoint timestamps
- operator intervention records
- retry-attempt history
- immutable audit logs for externally visible actions

It should require durable identifiers, stable correlation keys, and explicit checkpoint boundaries before any automated recovery path is allowed.

### Required Recovery Properties

Any future implementation would need to preserve all of the following:

- idempotency expectations for retried or resumed actions
- replayability of recovery analysis from recorded facts
- audit logging for every automated and manual recovery decision
- reconciliation checkpoints that make known-vs-unknown state explicit
- retry boundaries that prevent unbounded loops or duplicate external effects
- manual intervention triggers when confidence drops below a defined threshold

Every retry path must be bounded. Every recovery path must preserve auditability. Every automated recovery action must have limits and a manual fallback.

### Permitted Outputs, Decisions, And Actions

The future layer may emit only bounded recovery outputs such as:

- reconciled or unreconciled status
- known-safe retry eligibility
- automation stop decisions
- escalation requirements for human review
- state divergence classifications
- checkpoint advancement or checkpoint freeze decisions
- recovery notes and audit records

It may direct a separate future execution-capable system to pause, retry within bounds, or require manual review. It must not silently rewrite history or claim certainty it does not have.

### What It Must Not Be Allowed To Do Without Separate Controls

The future reconciliation layer must not be allowed to:

- create new strategy logic
- expand exposure limits
- bypass risk/control decisions
- bypass auth, signing, or execution approval boundaries
- retry indefinitely
- erase or rewrite audit history
- self-clear material divergence without explicit bounded rules
- continue automated recovery after a manual-intervention threshold is crossed

### Guardrails And Non-Goals

- this is not a venue adapter
- this is not a trading strategy layer
- this is not a replacement for risk/control
- this is not a reason to widen the frozen baseline repo
- every recovery action must be attributable
- every ambiguous state must remain explicit until resolved

### Prerequisites Before Any Reconciliation Implementation

Before implementation of any future reconciliation or failure-recovery layer is allowed, all of the following must be true:

- the execution boundary is approved
- the risk/control layer is approved
- the future execution-capable system surface is documented
- durable identifiers and correlation requirements are documented
- retry ceilings and manual intervention thresholds are documented
- audit-log and checkpoint requirements are documented
- separate approval is granted to move from design-only work into implementation work

### Risks Of Under-Designing Reconciliation And Recovery

- duplicate external actions could be triggered during retries
- internal state could drift from venue truth without detection
- partial failures could be misclassified as success or harmless delay
- operators could lose the ability to reconstruct what actually happened
- manual intervention could happen too late because automated recovery remained active too long
- incident response would be slowed by ambiguous ownership and missing checkpoints

## Promotion And Pre-Live Validation

### Purpose Of This Section

This section defines how future work would earn the right to advance from the frozen baseline into stricter testing stages. It exists to make promotion evidence explicit before any live-capable implementation is even proposed.

### Why Staged Promotion Is Required

The frozen baseline is trusted because it is bounded, read-only, and inspectable. A future system would introduce materially different failure modes, permissions, and external consequences. That step cannot be justified by intuition, isolated demos, or paper-trade success alone. Promotion must be staged, evidence-backed, and reversible.

### Proposed Validation Stages

The future promotion path would remain non-live unless a later phase explicitly changes that boundary. At minimum, the stages would be:

1. fixture-backed verification
2. deterministic replay validation
3. stricter paper-trade or simulation validation
4. shadow-mode or dry-run validation in a still-non-live environment

### Gate Criteria For Each Stage

#### Stage 1: Fixture-Backed Verification

Required evidence:

- deterministic fixtures cover expected success, rejection, and failure-containment paths
- output contracts remain stable and reviewable
- acceptance checks are repeatable without uncontrolled network dependence

Stop conditions and rollback triggers:

- fixture drift becomes unexplained
- deterministic checks stop being reproducible
- critical rejected or weak paths are no longer explicit

#### Stage 2: Deterministic Replay Validation

Required evidence:

- replay artifacts can reconstruct decisions and mismatches from recorded facts
- divergence cases are observable and attributable
- replay-based failure classification is stable enough to support operator review

Stop conditions and rollback triggers:

- replay cannot explain discrepancies consistently
- key failure classes cannot be replayed from retained records
- auditability weakens under edge-case scenarios

#### Stage 3: Stricter Paper-Trade Or Simulation Validation

Required evidence:

- simulation-stage controls, rejection paths, and policy decisions remain explicit under higher-stress scenarios
- promotion metrics are defined and reviewed rather than improvised
- operator review packets remain sufficient to explain why a candidate stage result was allowed, held, or denied

Stop conditions and rollback triggers:

- policy or simulation outputs become hard to interpret
- review or replay artifacts stop supporting reliable operator judgment
- simulated edge or fill assumptions begin to drive promotion without enough evidence

#### Stage 4: Shadow-Mode Or Dry-Run Validation

Required evidence:

- the future system can produce proposed decisions without creating live side effects
- proposed actions can be compared against external reality without order placement
- reconciliation, control, and promotion evidence remain reviewable under real-time conditions

Stop conditions and rollback triggers:

- shadow-mode outputs cannot be reconciled reliably
- operator review becomes too ambiguous to approve advancement
- dry-run behavior suggests pressure to bypass non-live boundaries

### What Must Remain Prohibited Until Those Gates Are Passed

Until the gates above are passed and separately approved:

- no live order submission
- no auth or private key handling in the frozen baseline repo
- no widening of current CLI or API surfaces into execution behavior
- no reinterpretation of paper-trade results as executable orders
- no use of review or replay artifacts as substitutes for live reconciliation controls

### Minimum Evidence Before Any Live-Capable Proposal

Before any live-capable proposal can even be brought forward, the minimum evidence set would include:

- stable fixture-backed verification coverage
- deterministic replay evidence for core mismatch and failure classes
- reviewed paper-trade and policy evidence under stricter scenarios
- documented control, reconciliation, and promotion stop conditions
- operator-reviewed shadow-mode or dry-run evidence that remains explicitly non-live
- explicit approval that the design track has satisfied its pre-implementation evidence burden

### Risks Of Skipping Stages

- implementation pressure would outrun evidence
- paper-trade success could be mistaken for execution readiness
- failure recovery and control designs would be tested too late
- rollback conditions would be improvised during incidents instead of defined in advance
- operator trust in the frozen baseline boundary would erode

## Data, Audit, And Observability

### Purpose Of This Section

This section defines the future telemetry, audit, event, metric, and traceability surfaces required for any execution-capable system. The goal is to ensure that critical actions, decisions, failures, and overrides would be reconstructible rather than inferred after the fact.

### Why Observability Must Be Designed Before Implementation

In a future execution-capable system, observability is part of correctness and control, not just troubleshooting. If critical actions cannot be attributed, correlated, and reviewed under failure, then risk controls, reconciliation, and operator approvals would all be weaker than they appear on paper.

### Required Event, Log, And Metric Surfaces

At minimum, a future execution-capable system would need explicit surfaces for:

- decision events for control, approval, hold, deny, disable, and escalation paths
- order-intent and execution-attempt events
- venue acknowledgement, reject, cancel, and fill events
- reconciliation state changes and divergence classifications
- retry and recovery actions
- operator intervention and manual override events
- kill-switch and circuit-breaker activations
- portfolio and exposure state changes
- system health metrics, latency metrics, and queue/backlog pressure metrics
- structured error events for external dependency failures

These surfaces should be structured and queryable rather than dependent on ad hoc plain-text logs.

### Audit And Traceability Requirements

Any future system would need:

- durable identifiers for actions, attempts, and related external events
- correlation IDs that connect decision, execution, recovery, and operator-review paths
- immutable audit records for materially important state transitions
- explicit attribution for automated decisions and human overrides
- timestamped records with enough context to reconstruct who decided what, when, and why
- traceability from upstream research artifact to downstream proposed or attempted action

Every critical decision path in a future system should be reconstructible.

### What Operators, Risk Controls, And Reconciliation Would Need To Observe

Operators would need visibility into:

- current control state
- escalations, disables, and unresolved ambiguities
- current recovery status and blocked actions

Risk/control layers would need visibility into:

- live exposure state
- pending actions
- failed or ambiguous actions
- override and kill-switch activity

Reconciliation layers would need visibility into:

- venue truth versus internal state
- checkpoint progress
- retry eligibility
- unresolved divergence and stale-state conditions

### Retention, Correlation, And Review Expectations

At design level, the future system would need:

- retention long enough to support incident review and replay-backed investigation
- correlation across decision, control, execution, and recovery events
- reviewable event histories that survive reconnects, retries, and partial failures
- bounded summarization layers that do not replace raw audit records

Retention policy details do not need to be implemented in this phase, but the requirement for reviewable historical traces must be explicit before implementation work begins.

### Minimum Observability Requirements Before Implementation

Before any future implementation could move forward, the minimum observability set would include:

- structured event surfaces for critical state transitions
- correlation IDs across control, execution, and recovery paths
- immutable audit records for high-risk decisions and overrides
- metrics for health, latency, queueing, and failure pressure
- traceability from upstream research artifacts into downstream decision paths
- operator-review visibility for blocked, held, denied, retried, and escalated states

### What Must Remain Outside The Frozen Baseline

The frozen baseline must not be widened to become the observability system for a future execution-capable stack. That future observability surface belongs outside the current read-only repo because it would need to observe live-capable decisions, retries, external effects, and operator interventions that do not exist in the baseline.

### Guardrails And Non-Goals

- this is not a dashboard design phase
- this is not a data-warehouse implementation phase
- this is not a reason to widen the frozen baseline CLI or API
- this is not permission to add background telemetry systems now
- every autonomous future action must be attributable, bounded, and reviewable
- observability must support control and correctness, not just post hoc debugging

### Risks Of Under-Designing Telemetry And Observability

- critical decisions would become hard to reconstruct
- operators could lose confidence in what the system actually did
- risk and reconciliation layers would act on incomplete or ambiguous facts
- retries and overrides could become unauditable
- incidents would take longer to classify and contain

## Portfolio And Capital Allocation

### Purpose Of This Section

This section defines the future portfolio and capital-allocation layer that would decide how capital is budgeted, constrained, netted, and reallocated across strategies, markets, events, and themes in any later execution-capable system.

### Why This Layer Must Be Separate From The Frozen Baseline

The frozen baseline can score opportunities, simulate plans, and emit policy decisions on simulated rows, but it does not own live capital, real exposure, or cross-strategy portfolio tradeoffs. A future capital-allocation layer would govern scarce capital and materially constrain external actions, so it must remain outside the frozen baseline repo and outside the current paper-trade path.

### What This Layer Would Own

The future layer would own:

- capital allocation across strategies and opportunity groups
- exposure budgeting across portfolio, strategy, market, event, and theme scopes
- gross exposure limits
- net exposure limits
- concentration limits across markets, events, and themes
- conflict resolution between competing strategy intents
- design-level netting and offset recognition rules
- rebalance and de-allocation triggers
- capital reservation and release rules

This layer would decide what fraction of available capital may be committed, where it may be committed, and when existing allocations must be reduced or blocked.

### Capital Allocation And Exposure Budgeting Responsibilities

At design level, the future layer would need explicit rules for:

- how capital is partitioned across strategies or opportunity groups
- how unused capital becomes available for reallocation
- how exposure budgets are enforced before additional intent is approved
- how gross and net exposures are measured consistently across scopes
- how strategy-level limits interact with portfolio-level ceilings

The layer must make allocation pressure explicit rather than letting each strategy assume independent capital availability.

### Concentration Limits And Conflict Resolution

The future layer would need explicit handling for:

- concentration limits across highly related markets
- concentration limits across events with shared drivers
- concentration limits across themes or narratives
- competing strategy intents that target overlapping exposure
- conflicts between a high-conviction strategy and a tighter portfolio-level cap

Conflict resolution must be rule-based and reviewable. It cannot rely on whichever strategy reaches the system first.

### Netting And Offset Recognition

At design level, the future layer would need explicit rules for:

- when exposures are considered offsetting
- when apparent offsets should not be treated as true netting
- how partially overlapping exposures are counted
- how offset recognition interacts with gross limits, net limits, and concentration limits

Netting rules must stay conservative enough that false offsets do not hide actual portfolio risk.

### Rebalance And De-Allocation Triggers

The future layer would need explicit rebalance or de-allocation triggers such as:

- breach or near-breach of gross or net exposure budgets
- concentration thresholds
- operator-imposed reductions
- kill-switch or circuit-breaker pressure from other control layers
- loss of confidence in a strategy, market, or venue state
- unresolved reconciliation ambiguity that makes current allocations unsafe

Any rebalance or de-allocation action would need to remain bounded, attributable, and reviewable.

### Inputs This Layer May Consume

The future layer may consume only explicit, reviewable inputs such as:

- upstream research outputs and grouped opportunity artifacts
- future strategy-intent proposals from a separate execution-capable system
- current portfolio and exposure state
- concentration and theme-mapping definitions
- recognized offset and netting rules
- risk-control states such as holds, disables, and kill switches
- reconciliation states that make some capital unavailable or uncertain
- operator approvals, denials, or temporary overrides

### Bounded Decisions This Layer May Emit

The future layer may emit only bounded allocation decisions such as:

- maximum capital or notional available to a strategy or opportunity group
- approval, reduction, or denial of additional allocation
- allocation freezes for specific strategies, markets, events, or themes
- forced de-allocation or rebalance requirements
- recognition or non-recognition of allowed offsets under predefined rules
- escalation requirements when conflicts cannot be resolved automatically

Every emitted decision must be attributable, bounded, and reviewable.

### What It Must Not Be Allowed To Do Without Separate Controls

The future portfolio layer must not be allowed to:

- generate strategy ideas
- bypass risk-control decisions
- bypass auth, signing, or execution approval boundaries
- expand portfolio limits automatically without explicit approved rules
- assume netting where the rule set is incomplete
- allocate capital based on hidden heuristics without auditability
- treat simulated paper-trade performance as sufficient evidence for live allocation

### Prerequisites Before Any Implementation Is Allowed

Before implementation of any future portfolio and capital-allocation layer is allowed, all of the following must be true:

- the execution boundary is approved
- the risk/control layer is approved
- the reconciliation layer is approved
- promotion and pre-live validation gates are approved
- observability and audit requirements are approved
- portfolio scopes, limit definitions, and netting rules are documented
- override and escalation authority are documented
- separate approval is granted to move from design-only work into implementation work

### Risks Of Under-Designing Portfolio Allocation And Exposure Control

- multiple strategies could unknowingly compete for the same scarce capital
- gross and net exposure could drift beyond intended limits
- false offset recognition could hide correlated risk
- concentration could build across related markets or themes without clear visibility
- de-allocation pressure could arrive too late because no rule owned it
- operator review would weaken because capital decisions would appear discretionary rather than rule-based

## Recommended Order Of Future Work

1. finish the execution-boundary definition
2. define the risk/control layer and its authority boundaries
3. define reconciliation and failure-recovery ownership and limits
4. define promotion gates and pre-live validation evidence for stricter non-live testing
5. define the data, audit, and observability boundary for the future system
6. define the portfolio and capital-allocation boundary for the future system
7. define the separate future execution-capable system surface
8. define detailed portfolio-governance integration for that future system
9. define stricter forward-testing boundaries before any implementation phase is proposed

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

### Data And Observability Boundary

Design goal:

- define the event, metric, audit, and traceability surfaces required so a future execution-capable system can be reviewed, controlled, and reconciled under failure

Likely scope:

- structured event taxonomy
- audit trail requirements
- correlation and retention expectations
- minimum observability gates before implementation

### Portfolio And Capital Allocation

Design goal:

- define how a future system would allocate scarce capital, budget exposure, recognize offsets conservatively, and resolve conflicts between competing strategy intents

Likely scope:

- portfolio and strategy allocation boundaries
- gross and net exposure budgeting
- concentration limits
- conflict-resolution rules
- rebalance and de-allocation triggers

## Risks Of Prematurely Going Live

The main risks are structural, not cosmetic:

- paper-trade success can be mistaken for execution readiness
- current checkpointing and validation are operator-safe for a read-only system, not a full live control plane
- policy decisions on simulated rows do not replace real exposure management
- replay and review are useful audit tools, but they are not execution reconciliation
- adding live behavior too early would collapse boundaries that are currently clear and defensible

## Explicit Non-Goals For Phase 13H

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
