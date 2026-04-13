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

Supported `--analyst-mode` values:

- `stub`
- `analyst_timeout`
- `analyst_transport`
- `reasoning_parse`

CLI output is deterministic JSON summary on stdout. On invalid input, CLI exits with code `2` and prints `review_artifacts_cli_error: ...` to stderr.

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
