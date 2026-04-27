# Phase 36A — Packaging Entrypoint Scope Lock

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-36a-packaging-entrypoint-scope-lock`
- Phase: `36A — packaging entrypoint scope lock`
- Source checkpoint: `main` after Phase 35F

## Why this phase exists
The bounded review outcome packaging flow now exists and is tested, but it does not yet have an operator-facing entrypoint.

The next product step is to decide how an operator should trigger packaging in a way that is:
- deterministic
- easy to test
- aligned with the current local artifact-file workflow

This phase is docs-only.

## Decision
First entrypoint should be:
- CLI first
- UI later only if still needed

## Why CLI first
CLI-first is the best next step because it is:
- smaller than UI integration
- easier to validate locally
- easier to test deterministically
- aligned with the existing local review/demo workflow
- less risky than adding new operator page actions immediately

## In scope
- define the first packaging entrypoint
- define operator inputs
- define expected outputs
- define failure handling expectations
- define recommended later phase sequence

## Out of scope
- no runtime code changes
- no UI template changes
- no test changes
- no `src/polymarket_arb/*` changes
- no DB, queue, scheduling, notification, inbox, or background-job work
- no remote delivery or external integrations
- no production trading or execution behavior

## Proposed CLI entrypoint shape
A future CLI entrypoint should accept:
- run id
- artifacts root
- optional package target root

It should produce:
- `<target_root>/<run_id>.package/`
  - `handoff_summary.md`
  - `handoff_payload.json`

## Expected operator-visible behavior
The CLI should clearly report:
- which run is being packaged
- where it read artifacts from
- where the package was written
- which files were created
- why packaging failed, if it fails

## Expected failure handling
The future CLI should fail clearly when:
- run artifacts are missing
- companion review metadata is missing
- companion review metadata is invalid
- review state is inconsistent
- target path is invalid

## Recommended later sequence
- 36B CLI packaging contract and command shape
- 36C CLI implementation bootstrap
- 36D focused tests and manual smoke
- 36E closeout

## Exit criteria
- first entrypoint direction is explicit
- operator inputs and outputs are explicit
- failure handling expectations are explicit
- later phase sequence is explicit
- no runtime behavior has changed
