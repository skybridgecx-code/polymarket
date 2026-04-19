# Phase 37E — Execution Boundary Intake CLI Operator Docs

## Phase Goal
Document the exact local operator path for the Phase 37D execution-boundary intake CLI so operators can run the handoff intake/export step consistently.

No runtime behavior changes are introduced in this phase.

## Operator Command
CLI entrypoint:

```bash
python -m future_system.cli.execution_boundary_intake \
  --handoff-request-path /absolute/path/handoff_request.json \
  --export-root /absolute/path/execution-boundary-exports
```

Optional strict file-presence validation:

```bash
python -m future_system.cli.execution_boundary_intake \
  --handoff-request-path /absolute/path/handoff_request.json \
  --export-root /absolute/path/execution-boundary-exports \
  --require-local-artifacts
```

## Required Arguments
- `--handoff-request-path`: path to one full handoff request envelope JSON (Phase 37A/37B schema shape).
- `--export-root`: directory where deterministic ack/reject intake artifacts are written.

## Deterministic Output Artifacts
Accepted request output:
- `<export_root>/<correlation_id>.execution_boundary_ack.json`

Rejected request output:
- `<export_root>/<correlation_id>.execution_boundary_reject.json`
- if `correlation_id` is missing in the request payload, fallback:
  `<export_root>/<handoff_request_filename_stem>.execution_boundary_reject.json`

## Expected CLI Behavior
- Accepted request:
  - exit code `0`
  - stdout JSON summary with `result_kind=execution_boundary_intake_result` and `status=accepted`
  - writes deterministic ack artifact
- Rejected (validation-failed) request:
  - exit code `0`
  - stdout JSON summary with `status=rejected`
  - writes deterministic reject artifact
- CLI-level request loading/parsing errors (for example missing file or invalid JSON object):
  - exit code `2`
  - stderr prefixed with `execution_boundary_intake_cli_error:`

## Workflow Placement
This step sits after local package creation and before cleanup in the local operator path:

1. `make future-system-operator-ui-demo-validate`
2. `make future-system-operator-ui-demo-prepare`
3. `make future-system-operator-ui-demo`
4. review list/detail pages and save local decision
5. `python -m future_system.cli.review_outcome_package ...`
6. `python -m future_system.cli.execution_boundary_intake ...`
7. `make future-system-operator-ui-demo-clean`

## Boundaries Preserved
- local file-based workflow only
- no `cryp` runtime integration in this phase
- no network calls
- no production trading/execution behavior
- no auth/private-key/DB/queue/job/notification/scheduling expansion

## Validation
```bash
make validate
```

