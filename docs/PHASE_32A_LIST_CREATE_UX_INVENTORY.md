# Phase 32A — Local Review Runs List/Create UX Inventory

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-32a-list-create-ux-scope-lock`
- Phase: `32A — local review runs list/create UX inventory`
- Source checkpoint: current shipped local operator UI list/create flow

## Sources Reviewed
- `src/future_system/operator_ui/render_templates.py`
- `src/future_system/operator_ui/route_handlers.py`
- `src/future_system/operator_ui/artifact_reads.py`
- `tests/future_system/test_operator_ui_review_artifacts.py`
- `tests/future_system/test_operator_review_workflow_integration.py`
- `docs/FUTURE_SYSTEM_OPERATOR_UI_LOCAL_RUNBOOK.md`
- `docs/FUTURE_SYSTEM_LOCAL_OPERATOR_UI_RELEASE_INDEX.md`
- `evidence/local-operator-ui/notes.md`

## Current List/Create Page Sections
Based on `render_list_page(...)`, the current list/create surface includes:
- `Local Review Runs` page heading
- `Artifacts Root Status` section
- `Create Local Review Run` section
  - trigger form posting to `/runs/trigger`
- optional trigger-disabled message when root is unusable
- optional trigger error alert (`Trigger Error: ...`)
- `Runs` table with columns:
  - `Run`, `Theme ID`, `Status`, `Failure Stage`, `Decision Status`, `Updated`
- optional `Run File Issues` section with issue table

## Current Visible Labels/Text Relevant To Operator Comprehension
- `Local Review Runs`
- `Artifacts Root Status`
- root state labels:
  - `configured and readable`
  - `configured but missing`
  - `configured but unreadable/invalid`
  - `not configured`
- `Configured Value`
- `Create Local Review Run`
- `Context Source JSON Path`
- `Target Subdirectory`
- `Analyst Mode`
- `Run Analysis`
- helper copy:
  - context source must be an existing local `OpportunityContextBundle` JSON path
  - target subdirectory is relative under artifacts root and default isolates UI-triggered runs
  - `stub` gives deterministic success; other modes are failure modes
- `Runs`
- empty row copy: `No local review runs found.`
- `Run File Issues`
- trigger-disabled copy: `Triggering is unavailable until artifacts root configuration is fixed.`

## Current Create Form Fields
Current fields and transport in `render_list_page(...)`:
- `context_source` (text, required)
- `target_subdirectory` (text, required)
- `analyst_mode` (select from configured trigger choices)

Form behavior:
- submit destination: `POST /runs/trigger`
- submit button label: `Run Analysis`
- form controls are disabled when artifacts root is not usable
- last entered values are preserved in response rendering

## Current Artifact Root Status Behavior
From `render_list_page(...)`, `route_handlers.py`, and root status integration:
- root status is always rendered with:
  - status label
  - configured value
  - explanatory root message
- unusable root state disables trigger form and shows unavailability guidance
- unusable root state returns deterministic empty run history (`runs=[]`, `issues=[]`) instead of read attempts
- trigger attempts with unusable root return `422` and surface:
  - `Trigger Error: artifacts_root_unavailable: ...`

## Current Trigger Error Behavior
From `handle_trigger_run_request(...)` and list template rendering:
- invalid trigger inputs return `422` and render list page with alert:
  - `Trigger Error: Invalid trigger input: ...`
- root unavailable trigger attempts return `422` with:
  - `Trigger Error: artifacts_root_unavailable: ...`
- alert is rendered with `role="alert"` in list page
- successful trigger returns `303` redirect to created detail URL with encoded `target_subdirectory`

## Current Tests Covering List/Create Behavior
`tests/future_system/test_operator_ui_review_artifacts.py` currently covers list/create behavior including:
- list/create copy contract and accessibility descriptors
- run ordering and status/failure-stage rendering in runs table
- run form labels/help text (`Context Source JSON Path`, `Target Subdirectory`, `Analyst Mode`)
- explicit target subdirectory success and redirect behavior
- invalid target subdirectory rejection path
- invalid context source rejection path with trigger error rendering
- root status states:
  - configured/readable
  - configured/missing
  - configured/invalid
  - configured/unreadable
  - not configured
- trigger-disabled behavior and `artifacts_root_unavailable` handling
- run file issues rendering when files are invalid/incomplete

`tests/future_system/test_operator_review_workflow_integration.py` additionally exercises CLI→UI integration that affects list rendering:
- no metadata vs pending metadata states
- failure-stage preservation in list/detail
- malformed/out-of-root metadata bounded handling

## Safe Polish Opportunities (No Implementation In 32A)
- clarify list-page intro and operator intent before form interaction.
- improve root-status explanation so operators understand exactly what directory to configure.
- make context-source guidance more concrete for local demo workflows.
- make target-subdirectory semantics clearer for run discoverability vs isolation.
- clarify analyst-mode consequences in plain operator language.
- clarify expected outcomes after pressing `Run Analysis` (redirect/result expectations).
- make trigger error guidance easier to action without changing trigger logic.
- make no-runs state more instructive while preserving deterministic empty-state behavior.
