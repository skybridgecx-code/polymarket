# Phase 37A — Execution Boundary Contract (`polymarket-arb` -> `cryp`)

## Repo / Branch / Phase
- Repo: `polymarket-arb`
- Branch: `phase-37a-execution-boundary-contract`
- Phase: `37A — docs/design-only execution boundary contract`

## Purpose
Define one concrete handoff contract for moving an approved local review outcome package from `polymarket-arb` (producer) into `cryp` (consumer) for bounded execution review artifacts.

This phase is docs/design-only. No runtime behavior changes are introduced.

## 1) Producer / Consumer Systems
- Producer system: `polymarket-arb` (`future_system` local operator review + packaging CLI).
- Consumer system: `cryp` (bounded forward-runtime execution review artifacts and controls).
- Boundary rule: systems remain separate; no repo merge and no direct runtime coupling.

## 2) Canonical Artifact Names And Locations

### Producer-side handoff package (current shipped source)
- Package directory: `<target_root>/<run_id>.package/`
- Required files:
  - `handoff_payload.json`
  - `handoff_summary.md`
- Produced by:
  - `python -m future_system.cli.review_outcome_package --run-id <run_id> --artifacts-root <dir> [--target-root <dir>]`

### Producer-side source artifacts referenced by package payload
- `<artifacts_root>/<run_id>.md`
- `<artifacts_root>/<run_id>.json`
- `<artifacts_root>/<run_id>.operator_review.json`

### Consumer-side execution evidence surfaces (existing cryp artifact truth)
- `runs/<runtime_id>/sessions/<session_id>.live_transmission_request.json`
- `runs/<runtime_id>/sessions/<session_id>.live_transmission_result.json`
- `runs/<runtime_id>/sessions/<session_id>.live_transmission_state.json`
- `runs/<runtime_id>/live_transmission_decision.json`
- `runs/<runtime_id>/live_control_status.json`
- `runs/<runtime_id>/manual_control_state.json`
- `runs/<runtime_id>/reconciliation_report.json`
- `runs/<runtime_id>/forward_paper_history.jsonl`

## 3) Required Schema Fields (Handoff Request Contract)

### Required fields from `handoff_payload.json`
- `package_version` (`"v1"`)
- `local_only` (`true`)
- `package_marker` (`"deterministic_local_review_outcome_package"`)
- `run_id`
- `run_status`
- `export_kind`
- `markdown_artifact_path`
- `json_artifact_path`
- `operator_review_metadata_path`
- `review_status`
- `operator_decision`

### Required fields from companion metadata (`<run_id>.operator_review.json`)
- `record_kind` (`"operator_review_decision_record"`)
- `record_version` (`1`)
- `artifact.run_id`
- `artifact.status`
- `artifact.export_kind`
- `review_status`
- `operator_decision`
- `updated_at_epoch_ns`

## 4) Optional Schema Fields

### Optional fields from `handoff_payload.json`
- `review_notes_summary`
- `reviewer_identity`

### Optional fields from companion metadata
- `review_notes_summary`
- `reviewer_identity`
- `decided_at_epoch_ns`
- `run_flags_snapshot`
- `artifact.failure_stage`
- `artifact.json_file_path`
- `artifact.markdown_file_path`

## 5) Approval Status Required Before Handoff
- `handoff_payload.review_status == "decided"`
- `handoff_payload.operator_decision == "approve"`
- `handoff_payload.run_status == "success"`
- companion metadata validates and matches the same `run_id`
- companion metadata `updated_at_epoch_ns` is present and non-null

If any check fails, handoff is blocked.

## 6) Idempotency Key / Correlation ID Rules
- `correlation_id`: `<run_id>`
- `idempotency_key`: `<run_id>:<updated_at_epoch_ns>:<operator_decision>`
- consumer must treat repeated submissions with the same `idempotency_key` as duplicates and fail closed (no widened execution behavior).

## 7) Execution Acknowledgment Payload (Consumer -> Producer)
`execution_acknowledgment` payload must include:
- `contract_version` (`"37A.v1"`)
- `producer_system` (`"polymarket-arb"`)
- `consumer_system` (`"cryp"`)
- `correlation_id`
- `idempotency_key`
- `runtime_id`
- `session_id`
- `run_id` (consumer run id)
- `submission_status` (`"submitted"`)
- `ack_status` (`"accepted"` or `"duplicate"`)
- `request_id`
- `client_order_id`
- `intent_id`
- `venue`
- `observed_at`
- `state`
- `terminal`
- `summary`
- `reason_codes` (may be empty)
- `artifact_paths` (paths to request/result/state artifacts plus decision/control/reconciliation artifacts)

## 8) Failure / Reject Payload (Consumer -> Producer)
`execution_reject` payload must include:
- `contract_version` (`"37A.v1"`)
- `producer_system` (`"polymarket-arb"`)
- `consumer_system` (`"cryp"`)
- `correlation_id`
- `idempotency_key`
- `runtime_id`
- `session_id`
- `run_id` (consumer run id)
- `submission_status` (`"not_submitted"`, `"rejected"`, or `"error"`)
- `rejection_stage`:
  - `boundary_denied`
  - `adapter_rejected`
  - `adapter_error`
- `summary`
- `reason_codes` (non-empty on reject/error)
- `artifact_paths` (paths to decision/result/state/control/reconciliation evidence)

## 9) Evidence / Log Files Expected Back From `cryp`
- `*.live_transmission_request.json`
- `*.live_transmission_result.json`
- `*.live_transmission_state.json`
- `live_transmission_decision.json`
- `live_control_status.json`
- `manual_control_state.json`
- `reconciliation_report.json`
- `forward_paper_history.jsonl`

## 10) Operator Review Loop After Execution Attempt
1. Receive `execution_acknowledgment` or `execution_reject` with evidence paths.
2. Review cryp evidence against the matching `correlation_id` / `idempotency_key`.
3. Update local operator review metadata in `polymarket-arb` using the existing local detail-page workflow:
   - keep local-only file writes
   - record execution outcome context in `review_notes_summary` and/or reviewer identity updates.
4. Re-package only if operator intentionally creates a new reviewed state (`updated_at_epoch_ns` changes, yielding a new idempotency key).

## 11) Explicit Non-Goals / Boundary Rules
- no runtime behavior change in this phase
- no `src/polymarket_arb/*` changes
- no automatic execution trigger from `polymarket-arb`
- no direct network transport protocol implementation between repos in this phase
- no auth/private-key sharing between systems
- no DB/queue/jobs/notifications/scheduling expansion
- no unrestricted live trading authorization
- no replacement of existing cryp bounded live-control and transmission guardrails

## Validation
- `make validate` (in `polymarket-arb`)

## Next Recommended Phase
- Phase 37B should implement contract fixtures/validators only (still bounded, no repo merge), then Phase 37C can address transport mechanics if explicitly scoped.
