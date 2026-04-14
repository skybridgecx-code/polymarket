# Phase 21A Editable Operator Decision Workflow Scope Lock

## Repo Checkpoint

- Repo: `polymarket-arb`
- Branch at scope lock creation: `phase-21a-editable-operator-decision-workflow-scope-lock`
- Prior checkpoint: `phase-20f-decision-workflow-closeout-checkpoint`
- Checkpoint status: local artifact-file workflow scope lock for editable operator decisions
  (not a production-readiness claim)

## Baseline Entering 21A

Phase 20A–20F established:

- deterministic operator review metadata contracts (`OperatorReviewDecisionRecord`)
- optional companion metadata initialization (`X.operator_review.json`) via CLI
- read-only UI rendering for decision metadata in list/detail views
- bounded malformed/out-of-root metadata read behavior
- deterministic test hardening across CLI -> artifact files -> UI read path

Current workflow is local file-based and read-only for operator decision metadata.

## Next Track Objective

Recommended next track name:

- `future_system editable local operator decision workflow`

Objective:

- add a bounded local UI edit flow for operator decisions backed only by
  `X.operator_review.json` companion files under configured artifacts root.

## Allowed Scope For Next Track

- `future_system`-scoped local UI form and POST handler behavior for decision metadata updates
- deterministic helper contracts for reading/updating/writing companion metadata files
- bounded path-safe file update semantics under configured artifacts root
- deterministic tests and docs for editable decision workflow behavior

## Editable Decision Fields (Proposed Contract)

Allowed user-editable fields:

- `review_status` (`pending` or `decided`)
- `operator_decision` (`approve` | `reject` | `needs_follow_up`) when `review_status=decided`
- `review_notes_summary` (optional non-empty text or cleared to `null`)
- `reviewer_identity` (optional non-empty text or cleared to `null`)

Non-editable/system-owned fields:

- `record_kind`, `record_version`
- `artifact` reference block (`run_id`, `theme_id`, `status`, `export_kind`, `failure_stage`,
  paths)
- `run_flags_snapshot`
- `decided_at_epoch_ns` / `updated_at_epoch_ns` assignment policy (if touched) must remain
  deterministic and validated by helper logic, not free-form raw UI input

## Validation Rules (Proposed)

- maintain existing `OperatorReviewDecisionRecord` invariants:
  - `pending` must not set `operator_decision`
  - `pending` must not set `decided_at_epoch_ns`
  - `decided` requires `operator_decision`
  - `updated_at_epoch_ns >= decided_at_epoch_ns` when both present
- reject malformed existing companion metadata for updates with bounded non-fatal UI error state
- reject update requests for invalid run IDs or out-of-root resolved paths
- reject writes when target companion path is not a regular file (including unsafe symlink
  behavior)

## Deterministic Update/Overwrite Behavior (Proposed)

- updates target exactly one companion file: `X.operator_review.json` for selected run `X`
- write path must resolve under configured artifacts root before any read/write
- updates are explicit replacements of validated metadata content for the selected run only
- no implicit updates to base artifact markdown/json files
- no cross-run writes; no recursive/global mutation behavior
- missing companion file behavior must be explicitly defined in a later phase (reject-only or
  explicit initialize-before-edit), not inferred implicitly

## Hard Out-Of-Scope Boundaries

- any changes under `src/polymarket_arb/*`
- DB persistence
- queues/background jobs/scheduling
- notifications/delivery/inbox workflows
- production trading/execution/order placement behavior
- remote orchestration or production-readiness claims

## Safety Boundaries

- local artifact-file workflow only
- strict run-id/path normalization and artifacts-root bounds checks
- malformed metadata remains bounded; should not break list/detail artifact visibility
- no hidden side effects beyond targeted companion file update

## Candidate Phases After 21A

1. **21B — Decision Update/Write Helper Contracts**  
   Define deterministic helper/models for validated companion metadata updates.

2. **21C — Operator UI Edit Form Rendering**  
   Add bounded edit form surface in run detail UI for allowed decision fields.

3. **21D — POST Handler / Update Flow**  
   Implement bounded POST update handling with explicit validation and file-write semantics.

4. **21E — Workflow Test Hardening**  
   Add integration-style tests locking edit/update invariants and error boundaries.

5. **21F — Closeout Checkpoint**  
   Document shipped editable workflow behavior, boundaries, and validation outcomes.

## Decision Gate

Choose one before implementation:

1. Stop at 21A and keep current read-only checkpoint behavior.
2. Start 21B–21F as a new bounded local track under this scope lock.
