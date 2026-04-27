# Phase 35A — Operator Workflow Expansion Scope Lock

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-35a-operator-workflow-expansion-scope-lock`
- Phase: `35A — operator workflow expansion scope lock`
- Source checkpoint: `main` after Phase 34E

## Why this phase exists
The current `future_system` local operator UI is now:
- launchable
- validated
- documented
- polished for list/create and detail flows
- supported by smoke checklists and reliability docs

What is still missing is the next real product workflow after local review.

This phase does not implement that workflow. It defines the bounded scope for what the next operator-facing capability should be.

## Candidate next workflow areas
This phase allows evaluation of later work in one of these areas:
- post-review operator action flow
- explicit review outcome packaging / export flow
- runtime/demo failure recovery flow
- onboarding / first-run operator packaging flow
- broader operator handoff workflow after decision update

## In scope
- define the next operator workflow candidates
- define which one should become the next product track
- define boundaries and non-goals
- define recommended phase sequence for the chosen workflow

## Out of scope
- no runtime code changes
- no UI template changes
- no test changes
- no `src/polymarket_arb/*` changes
- no DB, queue, scheduling, notification, inbox, or background-job work
- no production trading or execution behavior
- no screenshot/evidence modifications

## Recommended evaluation criteria
Use these criteria to choose the next track:
- operator value
- implementation boundedness
- fit with existing local artifact-file workflow
- clarity of inputs and outputs
- low ambiguity
- strong manual testability

## Expected deliverable
A bounded direction for the next real product workflow track after the current local review/demo slice.

## Suggested later phase sequence
- 35B workflow inventory / contract definition
- 35C implementation bootstrap
- 35D focused tests
- 35E manual smoke / closeout

## Exit criteria
- next workflow candidates are clearly defined
- boundaries are explicit
- a recommended next product direction is stated
- no runtime behavior has changed
