# Phase 35B — Review Outcome Packaging Operator Flow

## Current end state
Today the operator can:
- create a local review run
- inspect list and detail pages
- initialize and update local operator review metadata
- stop with local artifact files on disk

## Proposed next operator flow
1. Open a reviewed run.
2. Confirm operator review metadata is present.
3. Confirm review status and operator decision are final enough for packaging.
4. Trigger local packaging for that run.
5. Receive a bounded output artifact path.
6. Use that package for local handoff/review/archive.

## Candidate readiness rules
A run may be considered ready to package when:
- review metadata companion file exists
- review status is present
- operator decision is present if the review is decided
- run artifact files are present and readable

## Candidate package contents
### Core identity
- run id
- theme id if available
- export kind
- status

### Artifact references
- markdown artifact path
- json artifact path
- operator review metadata path

### Review outcome
- review status
- operator decision
- review notes summary
- reviewer identity

### Handoff summary
- short operator-facing summary block
- package creation time or deterministic marker
- local-only usage note

## Safe first implementation shape
Recommended first implementation:
- deterministic paired output:
  - one markdown handoff summary
  - one JSON handoff payload

Reason:
- easy to inspect
- easy to test
- easy to diff
- consistent with current artifact-file workflow

## Explicit non-goals for first implementation
- no ZIP bundling
- no browser download flow
- no external storage target
- no multi-run packaging
- no async/background packaging
- no approval orchestration
