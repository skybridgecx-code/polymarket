# Phase 24B Layout/Accessibility Inventory

## Scope

Docs-only inventory of current local operator UI layout and accessibility surfaces.

No runtime behavior changes.

## Current Structure Inventory

### List Page

Current structure includes:

- `<h1>Local Review Runs</h1>`
- root status section with `<h2>Artifacts Root Status</h2>`
- trigger form section with `<h2>Create Local Review Run</h2>`
- run table under `<h2>Runs</h2>`
- optional issue table under `<h2>Run File Issues</h2>`

Form controls currently have labels for:

- `context_source`
- `target_subdirectory`
- `analyst_mode`

### Detail Page

Current structure includes:

- `<h1>Local Review Run Detail</h1>`
- outcome section
- run metadata section
- operator decision review section
- update decision form section
- artifact paths section
- artifact evidence section

### Update Decision Form

Current controls include:

- hidden `updated_at_epoch_ns`
- hidden `target_subdirectory`
- `review_status` select
- `operator_decision` select
- `review_notes_summary` textarea
- `reviewer_identity` input
- submit button `Save Local Decision`

### Error Page

Current error page includes:

- back link
- `<h1>` title
- bounded error message block

## Accessibility / Layout Gaps Identified

1. Page sections are readable but could benefit from clearer grouping around form and table areas.
2. Tables do not currently include captions.
3. Form helper copy exists, but controls do not use `aria-describedby` relationships.
4. Error block is visible, but does not expose an explicit ARIA role.
5. Update Decision form has labels, but hidden fields and helper text could be structured more clearly.
6. Root status and trigger error areas could be easier for operators to scan.
7. Artifact evidence sections are clear, but large content blocks could use stronger section framing.

## Recommended 24C Targets

For list page layout:

- add table captions for run list and run file issues
- add accessible helper IDs and `aria-describedby` for trigger form controls
- improve root status and trigger error semantics without behavior change
- preserve existing copy contract tests

## Recommended 24D Targets

For detail/edit page layout:

- add accessible helper IDs and `aria-describedby` for decision form controls
- improve form grouping with fieldset/legend if bounded
- add table/detail section structure only where it improves scanability
- keep POST/update behavior unchanged

## Recommended 24E Targets

For test hardening:

- assert table captions / form helper IDs / ARIA roles where added
- keep existing copy contract coverage
- keep behavior tests unchanged

## Boundaries

- no `src/polymarket_arb/*` changes
- no behavior changes in this phase
- no DB
- no queues/jobs/scheduling
- no notifications/delivery
- no production trading/execution
