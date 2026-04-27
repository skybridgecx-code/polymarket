# Phase 35B — Review Outcome Packaging Contract

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-35b-review-outcome-packaging-contract`
- Phase: `35B — review outcome packaging contract`
- Source checkpoint: `main` after Phase 35A

## Purpose
This phase defines the next operator workflow after local review:
package a reviewed run into a bounded local output artifact that is easier to hand off, inspect, and reuse than the raw set of markdown/json/operator metadata files alone.

This phase is docs-only. It does not implement the workflow.

## Why this workflow
Current operator flow ends at:
- create local run
- review run detail
- update local decision metadata

That is useful, but it still leaves the operator with several local files and no single packaged output for handoff or final review.

## Proposed workflow
A local operator selects a reviewed run and generates a bounded review outcome package.

The package should summarize:
- run identity
- artifact locations
- operator review state
- operator decision
- review notes
- reviewer identity
- useful status/context for handoff

## Proposed inputs
Required inputs:
- existing run id
- existing review artifacts for that run
- existing companion operator review metadata file

Optional inputs:
- package target directory
- package label or handoff note
- package timestamp/version marker

## Proposed outputs
Primary output:
- one packaged local artifact for the reviewed run

Possible bounded shapes:
- single markdown handoff file
- single JSON handoff file
- paired markdown + JSON package
- local package directory with deterministic filenames

## Required operator-visible behavior
The future implementation should make these operator outcomes clear:
- which run is being packaged
- whether operator review metadata is present
- whether the run is ready to package
- where the package was written
- what files were included
- what decision/reviewer/notes were packaged

## Minimal contract expectations
A packaged review outcome should include:
- run id
- run status
- markdown artifact path
- json artifact path
- decision metadata path
- review status
- operator decision
- review notes summary
- reviewer identity
- timestamp or deterministic package marker
- clear indication that this is still a local artifact-file workflow

## Non-goals
- no remote upload
- no external delivery/integration
- no database persistence
- no queue/background processing
- no notification flow
- no production trading/execution behavior
- no `src/polymarket_arb/*` work

## Risks to avoid
- creating a vague export with unclear purpose
- introducing packaging shapes that are too flexible
- adding non-deterministic filenames without reason
- silently packaging incomplete review state
- broadening into full workflow orchestration too early

## Recommended next implementation sequence
- 35C package workflow scope lock and artifact shape choice
- 35D implementation bootstrap for local package generation
- 35E focused tests and manual smoke
- 35F closeout

## Exit criteria
- next workflow is concretely defined
- inputs and outputs are explicit
- operator-visible expectations are explicit
- non-goals are explicit
- no runtime behavior has changed
