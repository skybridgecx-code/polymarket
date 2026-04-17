# Phase 32A — Local Review Runs List/Create UX Scope Lock

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-32a-list-create-ux-scope-lock`
- Phase: `32A — local review runs list/create UX scope lock`
- Source checkpoint: `31E — run detail UX track closeout`

## Why This Track Exists
The local operator UI launcher/tooling is stable and the run detail UX track is complete.  
The next bounded product improvement is list-page and create-form comprehension for local operators and demos.

This phase locks scope and inventory only. No implementation is included in 32A.

## 32A Deliverable Type
- Docs-only scope lock + inventory.
- No runtime behavior changes.
- No test or screenshot changes.

## Proposed Later Improvements (Do Not Implement In 32A)
- clearer `Local Review Runs` list page intro
- clearer artifact root/configured directory status explanation
- clearer `Create Local Review Run` guidance
- clearer `Context Source JSON Path` guidance
- clearer `Target Subdirectory` guidance
- clearer `Analyst Mode` guidance
- clearer `Run Analysis` result expectations
- clearer trigger error guidance
- clearer empty/no-runs state

## Explicit Out Of Scope
- no `src/polymarket_arb/*`
- no production trading/execution behavior
- no DB/queue/jobs/notifications/scheduling
- no new backend persistence model
- no new external integrations
- no screenshot/evidence modifications

## Recommended Later Phase Sequence
- **32B:** list/create UX contract tests
- **32C:** list/create template copy/layout polish
- **32D:** manual smoke checklist
- **32E:** closeout

## Boundaries Preserved
- Local artifact-file workflow remains the only operator UI scope.
- No expansion into production control-plane behavior.
- No implementation changes in this phase beyond documentation artifacts.
