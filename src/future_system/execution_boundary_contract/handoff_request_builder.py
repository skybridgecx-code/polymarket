"""Deterministic local builder for Phase 37A execution-boundary handoff requests."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from future_system.execution_boundary_contract.models import ExecutionBoundaryHandoffRequest
from future_system.operator_review_models.models import OperatorReviewDecisionRecord
from future_system.review_outcome_packaging.models import ReviewOutcomePackagePayload


def _read_json_dict(*, path: Path, missing_error: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{missing_error}: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_json_file: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"invalid_json_object: {path}")
    return payload


def build_execution_boundary_handoff_request_from_package(
    *, package_dir: Path
) -> ExecutionBoundaryHandoffRequest:
    """Build one full execution-boundary handoff request from a local package directory."""

    handoff_payload_path = package_dir / "handoff_payload.json"
    handoff_summary_path = package_dir / "handoff_summary.md"

    handoff_payload_raw = _read_json_dict(
        path=handoff_payload_path,
        missing_error="missing_handoff_payload",
    )
    try:
        handoff_payload = ReviewOutcomePackagePayload.model_validate(handoff_payload_raw)
    except ValidationError as exc:
        raise ValueError(f"invalid_handoff_payload_shape: {exc}") from exc

    if not handoff_summary_path.is_file():
        raise ValueError(f"missing_handoff_summary: {handoff_summary_path}")

    operator_review_metadata_path = Path(handoff_payload.operator_review_metadata_path)
    operator_review_raw = _read_json_dict(
        path=operator_review_metadata_path,
        missing_error="missing_operator_review_metadata",
    )
    try:
        operator_review_metadata = OperatorReviewDecisionRecord.model_validate(operator_review_raw)
    except ValidationError as exc:
        raise ValueError(f"invalid_operator_review_metadata_shape: {exc}") from exc

    run_id = handoff_payload.run_id
    if operator_review_metadata.artifact.run_id != run_id:
        raise ValueError("handoff_request_builder_run_id_mismatch")

    if operator_review_metadata.updated_at_epoch_ns is None:
        raise ValueError("handoff_request_builder_missing_updated_at_epoch_ns")

    if operator_review_metadata.operator_decision is None:
        raise ValueError("handoff_request_builder_missing_operator_decision")

    if handoff_payload.review_status != operator_review_metadata.review_status:
        raise ValueError("handoff_request_builder_review_status_mismatch")

    if handoff_payload.operator_decision != operator_review_metadata.operator_decision:
        raise ValueError("handoff_request_builder_operator_decision_mismatch")

    if handoff_payload.run_status != operator_review_metadata.artifact.status:
        raise ValueError("handoff_request_builder_run_status_mismatch")

    if handoff_payload.export_kind != operator_review_metadata.artifact.export_kind:
        raise ValueError("handoff_request_builder_export_kind_mismatch")

    correlation_id = run_id
    idempotency_key = (
        f"{run_id}:{operator_review_metadata.updated_at_epoch_ns}:"
        f"{operator_review_metadata.operator_decision}"
    )

    return ExecutionBoundaryHandoffRequest(
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
        handoff_payload=handoff_payload,
        operator_review_metadata=operator_review_metadata,
        package_artifact_path=str(package_dir),
        handoff_summary_path=str(handoff_summary_path),
        handoff_payload_path=str(handoff_payload_path),
    )


def write_execution_boundary_handoff_request_from_package(
    *,
    package_dir: Path,
    output_path: Path | None = None,
) -> Path:
    """Write one deterministic `handoff_request.json` from a local package directory."""

    request = build_execution_boundary_handoff_request_from_package(package_dir=package_dir)
    destination = output_path or (package_dir / "handoff_request.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        f"{json.dumps(request.model_dump(mode='json'), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )
    return destination


__all__ = [
    "build_execution_boundary_handoff_request_from_package",
    "write_execution_boundary_handoff_request_from_package",
]
