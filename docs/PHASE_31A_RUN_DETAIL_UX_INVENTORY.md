# Phase 31A — Run Detail UX Inventory

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-31a-run-detail-ux-improvement-scope-lock`
- Phase: `31A — run detail UX inventory`
- Source checkpoint: current shipped local operator UI detail flow

## Sources Reviewed
- `src/future_system/operator_ui/render_templates.py`
- `src/future_system/operator_ui/route_handlers.py`
- `src/future_system/operator_ui/artifact_reads.py`
- `tests/future_system/test_operator_ui_review_artifacts.py`
- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- `docs/FUTURE_SYSTEM_LOCAL_OPERATOR_UI_RELEASE_INDEX.md`
- `evidence/local-operator-ui/notes.md`

## Current Detail Page Sections
Based on `render_detail_page(...)`, current run detail page includes:
- back link: `Back to local review runs`
- optional trigger-created summary section:
  - heading: `Trigger Result Summary`
  - includes run id, theme id, run outcome, failure stage, target subdirectory, artifact directory
- `Local Review Run Detail` page heading
- `Outcome Summary` section
  - outcome label (`Success`/`Failure`)
  - status label
  - failure stage
  - failure explanation
- `Run Metadata` section
  - run id, theme id, status badge, failure stage, decision status, updated timestamp
- `Operator Decision Review` section
  - metadata view for decision status/decision/notes/reviewer/decided-at/updated-at
- `Update Decision` section
  - editable form when companion metadata exists
  - unavailable explanation when metadata is missing/invalid
- `Artifact Paths` section
  - target subdirectory, artifact directory, markdown/json/decision metadata paths, content sizes
- `Artifact Evidence` section
  - markdown evidence block
  - JSON evidence block
  - bounded truncation notices when large

## Current Visible Labels / Text Relevant To Operator Comprehension
Current detail-facing labels/text include:
- `Local Review Run Detail`
- `Outcome Summary`
- `Run Metadata`
- `Operator Decision Review`
- `Update Decision`
- `Decision Status`
- `Decision`
- `Decision Notes`
- `Reviewer`
- `Decided At (epoch ns)`
- `Updated At (epoch ns)`
- `Artifact Paths`
- `Target Subdirectory`
- `Artifact Directory`
- `Markdown Path`
- `JSON Path`
- `Decision Metadata Path`
- `Artifact Evidence`
- `Markdown Evidence`
- `JSON Evidence`
- `Save Local Decision`

## Current Empty / No-Metadata Behavior
When companion metadata is missing:
- decision status renders as `No review metadata`
- decision/notes/reviewer/epoch fields render as `none`
- update section remains visible but form is unavailable
- unavailable message:
  - `Decision form unavailable: this run does not have companion review metadata.`
  - `Generate the run with --initialize-operator-review before editing decisions.`

When companion metadata is malformed or path-invalid:
- detail still renders (bounded, non-fatal)
- operator review section shows metadata issue text (for example `operator_review_metadata_invalid...`)
- update section unavailable reason uses that issue text

## Current Update Form Fields
Current form fields in detail page:
- `review_status` (select: `pending` / `decided`)
- `operator_decision` (select: none/approve/reject/needs_follow_up)
- `review_notes_summary` (textarea)
- `reviewer_identity` (text input)
- `updated_at_epoch_ns` (hidden input, generated monotonic next value)
- `target_subdirectory` (hidden input; preserved when present in request context)

Form transport:
- POST endpoint: `/runs/{run_id}/operator-review/update`
- success redirect: `/runs/{run_id}?updated=1` (+ `target_subdirectory=...` when present)
- invalid update returns bounded `Decision Update Error` page

## Current Tests Covering Detail Page Behavior
`tests/future_system/test_operator_ui_review_artifacts.py` includes focused detail coverage for:
- detail copy contract and accessibility descriptors
- success/failure detail rendering with failure-stage context
- empty/no-review metadata behavior
- pending/decided operator review metadata rendering
- malformed/out-of-bounds metadata bounded behavior
- missing markdown / invalid JSON safe error behavior
- trigger-created detail summary behavior and target-subdirectory handling
- update form submission behavior:
  - decided update path
  - revert-to-pending path
  - missing metadata rejection
  - target-subdirectory redirect preservation
- large markdown/json bounded truncation rendering

## Safe Polish Opportunities (No Implementation In 31A)
- make root/config context more explicit on detail page for local operators.
- tighten hierarchy so run id + status + failure stage are easier to scan quickly.
- clarify difference between:
  - initialized review metadata
  - no review metadata
  - metadata invalid states
- improve update-form explanatory copy and save-outcome orientation.
- optionally surface clearer demo-context cues when artifacts come from demo launcher output.
- keep path-heavy metadata readable without removing deterministic evidence detail.
