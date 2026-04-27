# Phase 37K — Cross-Repo Contract Drift Checklist (`polymarket-arb` <-> `cryp`)

## Phase Goal
Define a small docs-only checklist/gate that keeps producer and consumer local transport contract docs synchronized.

No runtime behavior changes are introduced in this phase.

## Canonical Source of Truth

The canonical contract source of truth is:

- `polymarket-arb/docs/PHASE_37I_LOCAL_TRANSPORT_WORKFLOW_CONTRACT.md`

The consumer-facing mirror is:

- `cryp/docs/PHASE_37J_LOCAL_TRANSPORT_CONSUMER_WORKFLOW_CONTRACT.md`

Rule:
- if 37I changes any transport contract detail, 37J must be reviewed and updated in the same bounded phase before closeout

## Cross-Repo Contract Surfaces That Must Match

The following must remain synchronized across 37I and 37J.

### 1) Canonical local transport paths

- `TRANSPORT_ROOT=<absolute/local/path>`
- inbound request path:
  - `<TRANSPORT_ROOT>/inbound/<correlation_id>/<attempt_id>/handoff_request.json`
- pickup receipt path:
  - `<TRANSPORT_ROOT>/pickup/<correlation_id>/<attempt_id>/cryp_pickup_receipt.json`
- response paths:
  - `<TRANSPORT_ROOT>/responses/<correlation_id>/<attempt_id>/<correlation_id>.execution_boundary_ack.json`
  - `<TRANSPORT_ROOT>/responses/<correlation_id>/<attempt_id>/<correlation_id>.execution_boundary_reject.json`
- archive path family:
  - `<TRANSPORT_ROOT>/archive/<correlation_id>/<attempt_id>/...`

### 2) Correlation and idempotency semantics

- `correlation_id` meaning and reuse
- `attempt_id` shape:
  - `<updated_at_epoch_ns>_<operator_decision>`
- authoritative idempotency tuple:
  - `<run_id>:<updated_at_epoch_ns>:<operator_decision>`
- duplicate attempt behavior:
  - same `<correlation_id>/<attempt_id>` is not a new request

### 3) Required pickup receipt fields

- `contract_version` (`"37A.v1"`)
- `producer_system` (`"polymarket-arb"`)
- `consumer_system` (`"cryp"`)
- `correlation_id`
- `idempotency_key`
- `pickup_status` (`"picked_up_for_local_execution_review"`)
- `picked_up_at_epoch_ns`
- `pickup_operator`
- `source_handoff_request_path`

### 4) Boundary response semantics

- exactly one boundary response artifact per attempt
- ack artifact kind:
  - `execution_boundary_intake_ack`
- reject artifact kind:
  - `execution_boundary_intake_reject`
- ack submission status semantics:
  - `accepted_for_local_execution_review`
- reject submission status semantics:
  - `rejected_for_local_execution_review`
- reject required fields:
  - `reason_codes`
  - `validation_error`

### 5) Boundary behavior and non-goals

- reject must not advance into runtime review/execution preparation
- ack remains bounded to local execution review only
- no network transport/auth/DB/queue/worker/scheduler additions
- no automatic cross-repo orchestration
- no production live execution expansion
- no replacement of existing `cryp` runtime guardrails

## Update-Together Rule

When any local transport contract change is proposed:

1. edit 37I first (canonical source)
2. immediately reconcile 37J in the same phase
3. if 37J does not require text changes, record explicit no-drift confirmation in the phase closeout notes
4. do not close the phase with only one side updated when contract semantics changed

## Pre-Close Checklist For Transport-Contract Edits

Before closing any future local-transport contract phase:

1. Confirm canonical doc and mirror doc are both reviewed:
   - `polymarket-arb/docs/PHASE_37I_LOCAL_TRANSPORT_WORKFLOW_CONTRACT.md`
   - `cryp/docs/PHASE_37J_LOCAL_TRANSPORT_CONSUMER_WORKFLOW_CONTRACT.md`
2. Confirm path templates are identical for inbound/pickup/responses/archive.
3. Confirm correlation/idempotency/duplicate semantics match exactly.
4. Confirm pickup receipt required fields match exactly.
5. Confirm ack/reject artifact naming and semantic status values match exactly.
6. Confirm non-goals and preserved boundaries remain aligned.
7. Run validation gates:
   - in `polymarket-arb`: `make validate`
   - in `cryp`: `make phase-finish`, then commit, then `make phase-close-check`

## Validation

```bash
make validate
```
