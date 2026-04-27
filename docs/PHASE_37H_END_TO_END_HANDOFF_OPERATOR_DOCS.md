# Phase 37H — End-to-End Handoff Operator Docs

## Phase Goal
Document the exact local end-to-end operator handoff path for the execution-boundary contract using shipped Phase 37A-37G2 behavior:

1. package reviewed artifacts
2. build full `handoff_request.json` envelope
3. process intake
4. inspect deterministic ack/reject output artifacts

No runtime behavior changes are introduced in this phase.

## End-to-End Operator Commands

### 1) Validate local tooling and tests
```bash
make validate
```

### 2) Package reviewed run artifacts
```bash
python -m future_system.cli.review_outcome_package \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --target-root .tmp/future-system-operator-ui-demo/packages
```

Expected package directory:
- `.tmp/future-system-operator-ui-demo/packages/theme_ctx_strong.analysis_success_export.package/`

Expected package files:
- `<package_dir>/handoff_payload.json`
- `<package_dir>/handoff_summary.md`

### 3) Build full handoff request envelope
Default output path:
```bash
python -m future_system.cli.execution_boundary_handoff_request \
  --package-dir .tmp/future-system-operator-ui-demo/packages/theme_ctx_strong.analysis_success_export.package
```

Optional explicit output path:
```bash
python -m future_system.cli.execution_boundary_handoff_request \
  --package-dir .tmp/future-system-operator-ui-demo/packages/theme_ctx_strong.analysis_success_export.package \
  --output-path .tmp/future-system-operator-ui-demo/execution_boundary_exports/theme_ctx_strong.analysis_success_export.handoff_request.json
```

Expected built envelope:
- default: `<package_dir>/handoff_request.json`
- explicit: `<output_path>`

### 4) Process intake and export deterministic ack/reject
```bash
python -m future_system.cli.execution_boundary_intake \
  --handoff-request-path /absolute/path/handoff_request.json \
  --export-root .tmp/future-system-operator-ui-demo/execution_boundary_exports
```

Optional strict local artifact checks:
```bash
python -m future_system.cli.execution_boundary_intake \
  --handoff-request-path /absolute/path/handoff_request.json \
  --export-root .tmp/future-system-operator-ui-demo/execution_boundary_exports \
  --require-local-artifacts
```

Expected export artifacts:
- accepted request: `<export_root>/<correlation_id>.execution_boundary_ack.json`
- rejected request: `<export_root>/<correlation_id>.execution_boundary_reject.json`

### 5) Dispatch directly into cryp canonical inbound tree (automated package -> handoff -> validate -> place)
```bash
python -m future_system.cli.execution_boundary_dispatch \
  --run-id theme_ctx_strong.analysis_success_export \
  --artifacts-root .tmp/future-system-operator-ui-demo/operator_runs \
  --cryp-transport-root /Users/muhammadaatif/cryp/.tmp/transport \
  --attempt-id attempt-000001
```

## Package Artifacts vs Full Handoff Request Envelope

Package artifacts (`review_outcome_package` output):
- `handoff_payload.json` (review outcome payload only)
- `handoff_summary.md` (human-readable summary)

Full handoff envelope (`execution_boundary_handoff_request` output):
- `handoff_request.json`
- includes:
  - `correlation_id`
  - `idempotency_key`
  - nested `handoff_payload`
  - nested `operator_review_metadata`
  - package and summary path context

Important:
- intake CLI requires the full envelope (`handoff_request.json`)
- intake CLI does not accept package payload-only file (`handoff_payload.json`)

## Expected CLI Success and Failure Behavior

### Builder CLI (`execution_boundary_handoff_request`)
Success:
- exit code `0`
- stdout JSON with:
  - `result_kind=execution_boundary_handoff_request_build_result`
  - `status=built`
  - `package_dir`
  - `handoff_request_path`

CLI/build failure:
- exit code `2`
- stderr prefixed with: `execution_boundary_handoff_request_cli_error:`
- typical causes:
  - missing `handoff_payload.json`
  - missing `handoff_summary.md`
  - invalid payload or companion metadata shape
  - run id / review-state mismatch between payload and companion metadata

### Intake CLI (`execution_boundary_intake`)
Accepted or rejected validation outcomes:
- exit code `0`
- stdout JSON with:
  - `result_kind=execution_boundary_intake_result`
  - `status=accepted` or `status=rejected`
- deterministic ack/reject artifact written under `--export-root`

CLI-level request loading/parsing failure:
- exit code `2`
- stderr prefixed with: `execution_boundary_intake_cli_error:`

## Workflow Placement
Shipped local operator path:

`validate -> prepare -> launch/review -> save local decision -> package -> build handoff_request.json -> intake -> cleanup`

## Boundaries Preserved
- local file-based workflow only
- no network calls
- no `cryp` runtime integration in this phase
- no production trading/execution behavior
- no auth/private-key/DB/queue/job/notification/scheduling expansion
- no `src/polymarket_arb/*` behavior changes

## Validation
```bash
make validate
```
