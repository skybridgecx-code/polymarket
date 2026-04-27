# Phase 35C — Review Outcome Packaging Shape Choice

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-35c-review-outcome-packaging-shape-choice`
- Phase: `35C — review outcome packaging shape choice`
- Source checkpoint: `main` after Phase 35B

## Purpose
This phase chooses the exact first implementation shape for the review outcome packaging workflow defined in Phase 35B.

This phase is docs-only. It does not implement package generation.

## Chosen first implementation shape
The first implementation should produce a deterministic paired local package:

- one markdown handoff summary
- one JSON handoff payload

Both should be written under a bounded local package directory for a single reviewed run.

## Why this shape
This shape is the best first step because it is:
- deterministic
- easy to inspect manually
- easy to diff in tests
- consistent with the current local artifact-file workflow
- useful for both human review and structured downstream consumption

## Rejected first-step alternatives
Not chosen for first implementation:
- ZIP packaging
- browser download flow
- remote upload/export
- multi-run packaging
- async/background packaging
- package registries or DB-backed tracking

## Proposed output location
For a reviewed run id like:

- `theme_ctx_strong.analysis_success_export`

the package should be written to a deterministic local directory, such as:

- `<target_root>/<run_id>.package/`

## Proposed package files
Inside the package directory:

- `handoff_summary.md`
- `handoff_payload.json`

## Required content for handoff_summary.md
The markdown summary should include:
- run id
- run status
- export kind
- markdown artifact path
- json artifact path
- operator review metadata path
- review status
- operator decision
- review notes summary
- reviewer identity
- local-only handoff note

## Required content for handoff_payload.json
The JSON payload should include:
- run id
- run status
- export kind
- markdown artifact path
- json artifact path
- operator review metadata path
- review status
- operator decision
- review notes summary
- reviewer identity
- package version marker
- package creation timestamp or deterministic marker

## Required readiness rules
A run should only be packageable when:
- markdown artifact exists
- json artifact exists
- operator review metadata companion exists
- operator review metadata is readable
- if review status is `decided`, operator decision is present

## Operator-visible expectations
The future implementation should clearly show:
- which run is being packaged
- whether packaging is allowed
- where the package was written
- which files were created
- that packaging remains local-only

## Boundaries
- no `src/polymarket_arb/*` changes
- no production trading/execution
- no DB, queue, scheduling, notification, inbox, or background-job work
- no external integrations
- no screenshot/evidence modifications
- no broad orchestration workflow in first implementation

## Exit criteria
- first implementation shape is explicit
- output location is explicit
- required files are explicit
- required fields are explicit
- readiness rules are explicit
- no runtime behavior has changed
