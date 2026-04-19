"""Validation helpers for local Phase 37A execution-boundary handoff requests."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from pydantic import ValidationError

from future_system.execution_boundary_contract.models import ExecutionBoundaryHandoffRequest


def validate_execution_boundary_handoff_request(
    *,
    payload: Mapping[str, object],
    require_local_artifacts: bool = False,
) -> ExecutionBoundaryHandoffRequest:
    """Validate one local handoff request against Phase 37A contract rules."""

    try:
        request = ExecutionBoundaryHandoffRequest.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(f"execution_boundary_contract_invalid_shape: {exc}") from exc

    errors: list[str] = []
    handoff_payload = request.handoff_payload
    review_metadata = request.operator_review_metadata

    run_id = handoff_payload.run_id
    if request.correlation_id != run_id:
        errors.append("correlation_id_mismatch")

    updated_at_epoch_ns = review_metadata.updated_at_epoch_ns
    if updated_at_epoch_ns is None:
        errors.append("operator_review_updated_at_missing")
    else:
        expected_idempotency_key = (
            f"{run_id}:{updated_at_epoch_ns}:{review_metadata.operator_decision}"
        )
        if request.idempotency_key != expected_idempotency_key:
            errors.append("idempotency_key_mismatch")

    if handoff_payload.review_status != "decided":
        errors.append("handoff_payload_review_status_not_decided")
    if handoff_payload.operator_decision != "approve":
        errors.append("handoff_payload_operator_decision_not_approve")
    if handoff_payload.run_status != "success":
        errors.append("handoff_payload_run_status_not_success")

    if review_metadata.review_status != "decided":
        errors.append("operator_review_status_not_decided")
    if review_metadata.operator_decision != "approve":
        errors.append("operator_review_decision_not_approve")
    if review_metadata.artifact.status != "success":
        errors.append("operator_review_artifact_status_not_success")

    if review_metadata.artifact.run_id != run_id:
        errors.append("operator_review_run_id_mismatch")
    if review_metadata.artifact.export_kind != handoff_payload.export_kind:
        errors.append("operator_review_export_kind_mismatch")

    markdown_artifact_path = Path(handoff_payload.markdown_artifact_path)
    json_artifact_path = Path(handoff_payload.json_artifact_path)
    operator_review_metadata_path = Path(handoff_payload.operator_review_metadata_path)

    if markdown_artifact_path.name != f"{run_id}.md":
        errors.append("markdown_artifact_path_invalid_for_run")
    if json_artifact_path.name != f"{run_id}.json":
        errors.append("json_artifact_path_invalid_for_run")
    if operator_review_metadata_path.name != f"{run_id}.operator_review.json":
        errors.append("operator_review_metadata_path_invalid_for_run")

    if not (
        markdown_artifact_path.parent
        == json_artifact_path.parent
        == operator_review_metadata_path.parent
    ):
        errors.append("artifact_paths_not_colocated")

    if review_metadata.artifact.markdown_file_path is not None:
        if Path(review_metadata.artifact.markdown_file_path) != markdown_artifact_path:
            errors.append("artifact_markdown_file_path_mismatch")
    if review_metadata.artifact.json_file_path is not None:
        if Path(review_metadata.artifact.json_file_path) != json_artifact_path:
            errors.append("artifact_json_file_path_mismatch")

    if require_local_artifacts:
        for label, path in (
            ("markdown_artifact", markdown_artifact_path),
            ("json_artifact", json_artifact_path),
            ("operator_review_metadata", operator_review_metadata_path),
        ):
            if not path.is_file():
                errors.append(f"missing_local_file:{label}:{path}")

    if errors:
        detail = ", ".join(errors)
        raise ValueError(f"execution_boundary_contract_invalid: {detail}")

    return request


__all__ = ["validate_execution_boundary_handoff_request"]
