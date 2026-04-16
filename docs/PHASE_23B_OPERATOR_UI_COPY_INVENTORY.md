# Phase 23B Operator UI Copy Inventory

## Scope

Docs-only inventory of current local operator UI copy surfaces before making copy/UX changes.

No runtime behavior changes.

## Current Copy Surfaces

### List Page

File: `src/future_system/operator_ui/render_templates.py`

Current visible copy includes:

- `Review Artifacts`
- `Artifacts Root Status`
- `Trigger Run`
- `Runs`
- `Run Issues`
- `Triggering is unavailable until artifacts root configuration is fixed.`
- `Provide an existing OpportunityContextBundle JSON file path.`
- `Relative subdirectory under artifacts root; safe default isolates UI-triggered runs.`
- `Use stub for normal deterministic success or choose a failure mode.`

### Detail Page

Current visible copy includes:

- `Review Artifact Detail`
- `Trigger Result Summary`
- `Outcome Summary`
- `Run Metadata`
- `Failure Context`
- `Operator Review Metadata`
- `Operator Review Edit Form`
- `Artifact Paths`
- `Artifact Content`
- `Markdown Content`
- `JSON Content`

### Editable Decision Form

Current visible copy includes:

- `Operator Review Edit Form`
- `Update one local companion metadata file for this run.`
- `Review Status`
- `Operator Decision`
- `Required only when review status is decided.`
- `Review Notes Summary`
- `Reviewer Identity`
- `Update Review Decision`

### Error Pages

File: `src/future_system/operator_ui/route_handlers.py`

Current error titles include:

- `Run Read Error`
- `Trigger Result Unavailable`
- `Review Update Error`

Current error behavior surfaces raw bounded backend error messages such as:

- `artifacts_root_unavailable`
- `operator_review_metadata_missing`
- `operator_review_metadata_invalid`
- target subdirectory validation errors

### Status Labels / Metadata Labels

File: `src/future_system/operator_ui/artifact_reads.py`

Current status strings include:

- `pending`
- `decided`
- `no-review-metadata`
- `operator_review_metadata_invalid`

## Copy/UX Gaps Identified

1. `Review Artifacts` is technically accurate but vague for an operator.
2. `Trigger Run` does not clearly say it creates local review artifacts.
3. `no-review-metadata` is implementation-shaped and should be more operator-friendly.
4. `Operator Review Metadata` is accurate but could be clearer as `Operator Decision Review`.
5. `Update one local companion metadata file for this run.` is safe but too technical.
6. Error titles are bounded but could provide clearer recovery guidance.
7. The edit form should more clearly explain pending vs decided behavior.
8. Missing metadata should explain that the run must be generated with `--initialize-operator-review` before editing.
9. Form button copy should emphasize local-only update behavior.
10. Failure context is present but could be easier to scan.

## Recommended 23C Copy Targets

For list/detail read-only surfaces:

- rename page title/heading from `Review Artifacts` to clearer local-operator wording
- clarify root status wording
- clarify trigger form helper text
- improve empty-list and run-issue copy
- make `no-review-metadata` display as a friendly label while preserving internal value where needed

## Recommended 23D Copy Targets

For editable decision form/update surfaces:

- improve edit-form intro copy
- clarify pending/decided requirements
- improve submit button copy
- improve missing/malformed metadata error guidance
- preserve bounded raw error details where useful for debugging

## Boundaries

- no `src/polymarket_arb/*` changes
- no behavior changes in this phase
- no DB
- no queues/jobs/scheduling
- no notifications/delivery
- no production trading/execution
