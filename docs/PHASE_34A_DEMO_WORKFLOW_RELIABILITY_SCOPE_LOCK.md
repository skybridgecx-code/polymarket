# Phase 34A — Demo Workflow Reliability Scope Lock

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-34a-demo-workflow-reliability-scope-lock`
- Phase: `34A — future_system demo workflow reliability scope lock`
- Source checkpoint: launcher tooling + runbook/UX tracks through Phase 33A

## Why This Reliability Track Exists
The local operator UI flow is now polished, documented, launchable, and validated.  
The next bounded product improvement is reliability: auditing the full local demo workflow end-to-end and identifying friction or brittleness before implementation changes.

Phase 34A is docs-only scope lock and inventory. No implementation changes are included.

## Demo Workflow Surfaces To Evaluate
- launcher syntax and preflight checks
- prepare-only artifact generation
- context bundle generation from fixture input
- review artifact generation
- companion operator review metadata initialization
- port handling
- cleanup behavior
- list page navigation
- detail page navigation
- update decision flow

## Proposed Later Improvements (Do Not Implement In 34A)
- clearer launcher stdout summaries
- stronger generated artifact verification
- better failure messages for missing dependency / invalid fixture / missing artifact root
- optional no-browser CLI smoke check
- optional demo workflow status file under `.tmp` only

## Explicit Out Of Scope
- no `src/polymarket_arb/*`
- no production trading/execution behavior
- no DB/queue/jobs/notifications/scheduling
- no new backend persistence model
- no external integrations
- no committed evidence screenshot changes

## Recommended Later Sequence
- **34B:** reliability contract/validation script hardening
- **34C:** launcher output/failure-message polish
- **34D:** end-to-end prepare/update smoke checklist
- **34E:** closeout

## Boundaries Preserved
- Local artifact-file workflow remains the only scope.
- No runtime behavior changes in this phase.
- No tests, screenshots, or evidence artifacts changed in this phase.
