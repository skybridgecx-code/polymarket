# Phase 35C — Review Outcome Packaging Implementation Scope

## Purpose
This document constrains the first implementation of review outcome packaging so the next coding phase stays small and testable.

## In scope for first implementation
- package one reviewed run at a time
- local artifact-file workflow only
- deterministic local output directory
- deterministic markdown handoff summary
- deterministic JSON handoff payload
- reuse existing run artifacts and operator review metadata
- clear failure on missing/unreadable required inputs

## Out of scope for first implementation
- packaging multiple runs together
- any remote delivery target
- uploads, sync, or external sharing
- ZIP archives
- UI-heavy package browsing
- package history database
- async/background package generation
- approval workflow orchestration
- any `src/polymarket_arb/*` work

## Proposed future implementation inputs
- run id
- artifacts root
- optional package target root

## Proposed future implementation outputs
Package directory:
- `<target_root>/<run_id>.package/`

Files:
- `handoff_summary.md`
- `handoff_payload.json`

## Minimum failure cases
Implementation should fail clearly when:
- run artifacts are missing
- companion review metadata is missing
- companion review metadata is invalid
- package target path is outside allowed root, if a bounded root is enforced
- review status/decision state is inconsistent

## Recommended implementation order
### 35D
- add package builder/data shape
- add deterministic file writer
- add focused tests

### 35E
- add operator/manual smoke coverage
- add implementation closeout doc

## Manual test expectations
A future manual smoke should verify:
- package directory created
- markdown and JSON files created
- packaged fields match run + review metadata
- output paths are understandable
- missing metadata fails clearly

## Non-goals reminder
This workflow is still only a local handoff/package step.
It is not yet a broader operator workflow platform.
