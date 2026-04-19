# Future System Operator UI Local Runbook

## Scope

This runbook documents the shipped local operator workflow for:

- generating review artifacts with `future_system` CLI
- launching and mounting the local operator UI
- inspecting run list/detail pages
- running the synchronous UI trigger flow

It is grounded in current code behavior in:

- `src/future_system/cli/review_artifacts.py`
- `src/future_system/operator_ui/*`

This runbook does not describe background workers, persistence, remote delivery, or any behavior not currently shipped.

## Recommended End-to-End Path (Primary)

Use this path for local operator handoff and demo use.

1. Validate launcher/tooling first:

```bash
make future-system-operator-ui-demo-validate
```

2. Prepare deterministic demo artifacts without starting Uvicorn:

```bash
make future-system-operator-ui-demo-prepare
```

Expected demo run id:
- `theme_ctx_strong.analysis_success_export`

Expected generated temp paths:
- `.tmp/future-system-operator-ui-demo/context_bundle.json`
- `.tmp/future-system-operator-ui-demo/operator_runs/`

3. Launch the UI:

```bash
make future-system-operator-ui-demo
```

If port `8000` is already in use:

```bash
PORT=8010 make future-system-operator-ui-demo
```

4. Open list and detail pages:
- List: `http://127.0.0.1:8000`
- Detail: `http://127.0.0.1:8000/runs/theme_ctx_strong.analysis_success_export`

5. Update local decision in detail page:
- Open `Update Decision`.
- Set `review_status` and optional decision/notes/reviewer fields.
- Select `Save Local Decision`.
- Confirm updated values render on detail page.

6. Confirm write scope:
- only companion metadata (`X.operator_review.json`) is rewritten
- run export markdown/json files remain unchanged

7. Package reviewed run outcome:

```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --target-root .tmp/future-system-operator-ui-demo/packages
```

Expected package directory:
- `.tmp/future-system-operator-ui-demo/packages/theme_ctx_strong.analysis_success_export.package/`

Expected package files:
- `handoff_summary.md`
- `handoff_payload.json`

8. Run local execution-boundary intake/export CLI:

```bash
python -m future_system.cli.execution_boundary_intake \
  --handoff-request-path /absolute/path/handoff_request.json \
  --export-root .tmp/future-system-operator-ui-demo/execution_boundary_exports
```

Optional strict local artifact path checks:

```bash
python -m future_system.cli.execution_boundary_intake \
  --handoff-request-path /absolute/path/handoff_request.json \
  --export-root .tmp/future-system-operator-ui-demo/execution_boundary_exports \
  --require-local-artifacts
```

Expected intake output files:
- accepted request: `<export_root>/<correlation_id>.execution_boundary_ack.json`
- rejected request: `<export_root>/<correlation_id>.execution_boundary_reject.json`

Important:
- `--handoff-request-path` must point to a full execution-boundary request envelope JSON.
- this is not the same file as package output `handoff_payload.json`.

9. Clean demo temp artifacts:

```bash
make future-system-operator-ui-demo-clean
```

If launcher startup reports missing multipart form dependency, install:

```bash
.venv/bin/python -m pip install python-multipart
```

If packaging CLI reports missing review metadata, confirm the run has:
- `<run_id>.operator_review.json`
- matching `artifact.run_id` for the run being packaged

If execution-boundary intake CLI reports `execution_boundary_intake_cli_error`, verify:
- handoff request JSON file exists and is valid JSON object
- request shape follows the Phase 37A/37B contract envelope

## Workflow Boundaries

- local artifact-file workflow only
- no production trading/execution behavior
- no DB/queues/jobs/notifications/scheduling behavior
- no `src/polymarket_arb/*` changes in this workflow

## Prerequisites

From repo root:

```bash
cd "/Users/muhammadaatif/polymarket-arb"
source .venv/bin/activate
```

You need:

- a valid `OpportunityContextBundle` JSON file
- a local artifacts directory you can read and write

## Artifacts Root Contract

The operator UI uses one artifacts root directory.

Configuration options:

- pass `artifacts_root` directly when constructing the app
- or set `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT`

Example:

```bash
export FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT="/absolute/path/review-artifacts"
```

Current root states shown in UI:

- `configured and readable`
- `configured but missing`
- `configured but unreadable/invalid`
- `not configured`

Root requirements:

- must be an existing directory
- must be readable, writable, and traversable

## Generate Artifacts With CLI

The CLI writes one markdown file and one JSON file per run:

```bash
python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/context_bundle.json \
  --target-directory /absolute/path/review-artifacts \
  --analyst-mode stub
```

Optional companion metadata initialization:

```bash
python -m future_system.cli.review_artifacts \
  --context-source /absolute/path/context_bundle.json \
  --target-directory /absolute/path/review-artifacts \
  --analyst-mode stub \
  --initialize-operator-review
```

With `--initialize-operator-review`, CLI also writes `X.operator_review.json` for generated run id
`X`, initialized as pending operator review metadata.

Supported `--analyst-mode` values:

- `stub`
- `analyst_timeout`
- `analyst_transport`
- `reasoning_parse`

CLI output is deterministic JSON summary on stdout. On invalid input, CLI exits with code `2` and prints `review_artifacts_cli_error: ...` to stderr.

If `--initialize-operator-review` is enabled and `X.operator_review.json` already exists, CLI
fails with a deterministic validation error and does not overwrite the existing companion metadata
file.

## Editable Operator Review Workflow

The editable decision workflow is local and file-based.

Prerequisite:

- the run must already have a companion metadata file named `X.operator_review.json`
- use `--initialize-operator-review` during CLI generation to create it automatically

Editable fields:

- `review_status`
- `operator_decision`
- `review_notes_summary`
- `reviewer_identity`

Manual flow:

1. Generate artifacts with companion review metadata:
   python -m future_system.cli.review_artifacts --context-source /absolute/path/context_bundle.json --target-directory /absolute/path/review-artifacts --analyst-mode stub --initialize-operator-review
2. Launch the operator UI with `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT` pointing at the same artifacts directory.
3. Open `http://127.0.0.1:8000/runs/X`.
4. Use Operator Review Edit Form to update the review metadata.
5. Submit the form.
6. Confirm the detail page redirects back and shows the updated values.
7. Confirm only `/absolute/path/review-artifacts/X.operator_review.json` changed.

Important behavior:

- update writes only `X.operator_review.json`
- base artifact `.json` and `.md` files are not modified
- missing companion metadata fails with `operator_review_metadata_missing`
- malformed companion metadata fails with a bounded operator error page
- target subdirectory context is preserved when provided

## Launch The Operator UI (Standalone)

Use the app factory export with Uvicorn factory mode:

```bash
export FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT="/absolute/path/review-artifacts"
python -m uvicorn future_system.operator_ui.app_entry:create_operator_ui_app --factory --reload
```

Open:

- `http://127.0.0.1:8000/`

Primary routes:

- `GET /`
- `POST /runs/trigger`
- `GET /runs/{run_id}`

## Mount The Operator UI Into Another FastAPI App

Primary mount helper:

- `future_system.operator_ui.mount_operator_ui_app`

Default mount path:

- `"/operator-ui"`

Example:

```python
from fastapi import FastAPI
from future_system.operator_ui import mount_operator_ui_app

app = FastAPI()
mount_operator_ui_app(
    parent_app=app,
    artifacts_root="/absolute/path/review-artifacts",
)
```

Custom mount path is supported and normalized (must start with `/`).

## CLI Artifacts vs UI Artifacts

Relationship between CLI generation and UI inspection:

- CLI writes artifacts to the `--target-directory` you provide.
- UI run list reads `*.json` files at the configured artifacts root (non-recursive).
- UI detail view reads matching `.json` and `.md` for a selected run.

Operator guidance:

- to inspect CLI-generated runs in list view, set UI artifacts root to the same directory where CLI wrote files
- if artifacts are stored in nested subdirectories, they are not discovered by list view unless you explicitly navigate using a run link that includes `target_subdirectory`

Important current behavior:

- UI trigger defaults `target_subdirectory` to `operator_runs`
- triggered runs are redirected to detail immediately
- those runs are not included in the top-level run list unless artifacts are written directly at the configured root

## UI Trigger Flow (Synchronous, Local)

Trigger form fields:

- `context_source` (required path to `.json` context bundle)
- `analyst_mode` (`stub`/`analyst_timeout`/`analyst_transport`/`reasoning_parse`)
- `target_subdirectory` (default `operator_runs`)

Flow:

1. Validate root status and trigger inputs.
2. Load `OpportunityContextBundle` from `context_source`.
3. Run synchronous analysis and artifact write.
4. Redirect to created run detail page.

Boundaries:

- writes are constrained under the configured artifacts root
- `target_subdirectory` must be relative and safe (no absolute paths, `..`, or unsafe segments)
- no background jobs are started

## Success/Failure Semantics

UI keeps success and failure distinct.

Failure-stage identity is explicit and preserved:

- `analyst_timeout`
- `analyst_transport`
- `reasoning_parse`

List and detail pages render status and failure-stage context directly from artifact files.

## Safe Troubleshooting

If list page shows root unavailable:

- verify `FUTURE_SYSTEM_REVIEW_ARTIFACTS_ROOT` or explicit `artifacts_root`
- verify directory exists and has read/write/execute permissions

If trigger returns `Invalid trigger input`:

- verify `context_source` exists, is a file, ends with `.json`, and validates as `OpportunityContextBundle`
- verify `target_subdirectory` is relative and contains only safe segments

If app startup fails with multipart/form-data error:

- install `python-multipart` in the active environment
- retry app startup after dependency installation

If list shows `Run Issues`:

- `json_invalid`: JSON file is malformed
- `json_fields_invalid`: JSON lacks required fields (`theme_id`, valid `status`, valid failure-stage semantics)
- `markdown_missing`: matching markdown file does not exist

If detail page errors:

- `artifact_run_not_found`: missing JSON file
- `artifact_markdown_missing`: missing markdown file
- `trigger_result_unavailable`: trigger wrote partial/unreadable output for the created run
