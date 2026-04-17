# Phase 31A — Run Detail UX Improvement Scope Lock

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-31a-run-detail-ux-improvement-scope-lock`
- Phase: `31A — run detail UX improvement scope lock`
- Source checkpoint: Phase 29E launcher track closeout + Phase 30A launcher smoke validation

## Why This Track Exists
The local operator UI is now:
- shipped
- manually evidenced
- launchable with deterministic tooling
- covered by focused launcher smoke validation

The next bounded product improvement is detail-page comprehension during local operator review/demo use. This phase locks scope only and does not implement UX changes.

## 31A Deliverable Type
- Docs-only scope lock + inventory.
- No implementation changes.
- No runtime behavior changes.

## Proposed Later Improvements (Do Not Implement In 31A)
- clearer artifact root/status context on detail page
- clearer run id / artifact path display
- clearer initialized operator review metadata state
- clearer empty/no review metadata state
- clearer guidance around update form and save outcome
- optional demo-mode context if using generated demo artifacts

## Explicit Out Of Scope
- no `src/polymarket_arb/*`
- no production trading/execution behavior
- no DB/queue/jobs/notifications/scheduling
- no new backend persistence model
- no new external integrations
- no screenshot/evidence modifications

## Later Phase Sequence Recommendation
- **31B:** detail UX inventory + focused rendered-copy/test contract alignment.
- **31C:** small template copy/layout polish on run detail page only.
- **31D:** focused tests for run detail UX expectations and regressions.
- **31E:** closeout doc with validation summary and next-step decision.

## Boundaries Preserved
- Local operator UI track remains local artifact-file workflow only.
- No expansion into production control-plane behavior.
- No implementation in this phase beyond documentation artifacts.
