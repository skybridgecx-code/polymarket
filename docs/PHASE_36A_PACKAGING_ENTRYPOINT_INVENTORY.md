# Phase 36A — Packaging Entrypoint Inventory

## Current state
Current packaging flow exists as code and tests, but not yet as an operator-facing entrypoint.

Available implementation layer:
- `src/future_system/review_outcome_packaging/`
- deterministic local package directory
- `handoff_summary.md`
- `handoff_payload.json`

## Current gap
An operator cannot yet trigger packaging through a stable product-facing entrypoint.

## Entrypoint options considered

### 1. CLI first
Pros:
- bounded scope
- deterministic
- easy to test
- easy to document
- natural fit for local artifact-file workflow

Cons:
- less discoverable than UI
- requires terminal use

### 2. UI first
Pros:
- easier for operators who stay in the UI
- more discoverable

Cons:
- larger scope
- requires more UX work
- more coupling to current operator pages
- higher risk for first entrypoint

### 3. CLI then UI
Pros:
- keeps first step bounded
- leaves room for later operator UI action
- best long-term sequence

Cons:
- requires patience to avoid jumping straight to UI

## Recommended direction
Best next direction:
- **CLI first**
- then evaluate a later UI action only if operator demand remains clear

## Candidate CLI inputs
- `--run-id`
- `--artifacts-root`
- `--target-root` (optional)

## Candidate CLI outputs
- printed package directory
- printed created file paths
- non-zero exit on failure
- no remote side effects

## Candidate non-goals
- no upload/export target
- no browser download flow
- no multi-run packaging
- no packaging history service
- no async/background packaging
