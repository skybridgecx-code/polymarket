"""Local file-based intake/export surface for Phase 37C handoff requests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from future_system.execution_boundary_contract.models import (
    ExecutionBoundaryIntakeAckArtifact,
    ExecutionBoundaryIntakeExportResult,
    ExecutionBoundaryIntakeRejectArtifact,
)
from future_system.execution_boundary_contract.validator import (
    validate_execution_boundary_handoff_request,
)


def load_execution_boundary_handoff_request_artifact(
    *, handoff_request_path: Path
) -> dict[str, object]:
    """Load one JSON handoff request artifact from disk."""

    try:
        payload = json.loads(handoff_request_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing_handoff_request_artifact: {handoff_request_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid_handoff_request_json: {handoff_request_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"invalid_handoff_request_object: {handoff_request_path}")
    return payload


def process_execution_boundary_handoff_request_artifact(
    *,
    handoff_request_path: Path,
    export_root: Path,
    require_local_artifacts: bool = False,
) -> ExecutionBoundaryIntakeExportResult:
    """Validate one handoff request and emit a deterministic local ack/reject artifact."""

    payload = load_execution_boundary_handoff_request_artifact(
        handoff_request_path=handoff_request_path
    )

    try:
        request = validate_execution_boundary_handoff_request(
            payload=payload,
            require_local_artifacts=require_local_artifacts,
        )
    except ValueError as exc:
        validation_error = str(exc)
        correlation_id = _optional_string(payload=payload, key="correlation_id")
        idempotency_key = _optional_string(payload=payload, key="idempotency_key")
        reject_identifier = correlation_id or handoff_request_path.stem
        reject_path = export_root / f"{reject_identifier}.execution_boundary_reject.json"

        reject_artifact = ExecutionBoundaryIntakeRejectArtifact(
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            reason_codes=_reason_codes_from_validation_error(validation_error),
            validation_error=validation_error,
            source_handoff_request_path=str(handoff_request_path),
        )
        _write_json_artifact(artifact_path=reject_path, artifact=reject_artifact)
        return ExecutionBoundaryIntakeExportResult(
            source_handoff_request_path=str(handoff_request_path),
            accepted=False,
            reject_artifact_path=str(reject_path),
        )

    ack_path = export_root / f"{request.correlation_id}.execution_boundary_ack.json"
    ack_artifact = ExecutionBoundaryIntakeAckArtifact(
        correlation_id=request.correlation_id,
        idempotency_key=request.idempotency_key,
        run_id=request.handoff_payload.run_id,
        source_handoff_request_path=str(handoff_request_path),
    )
    _write_json_artifact(artifact_path=ack_path, artifact=ack_artifact)
    return ExecutionBoundaryIntakeExportResult(
        source_handoff_request_path=str(handoff_request_path),
        accepted=True,
        ack_artifact_path=str(ack_path),
    )


def _optional_string(*, payload: Mapping[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if isinstance(value, str) and value:
        return value
    return None


def _reason_codes_from_validation_error(validation_error: str) -> list[str]:
    if validation_error.startswith("execution_boundary_contract_invalid_shape:"):
        return ["execution_boundary_contract_invalid_shape"]

    prefix = "execution_boundary_contract_invalid: "
    if validation_error.startswith(prefix):
        detail = validation_error[len(prefix) :]
        return [token.strip() for token in detail.split(", ") if token.strip()]

    return ["execution_boundary_contract_invalid"]


def _write_json_artifact(*, artifact_path: Path, artifact: BaseModel) -> None:
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        f"{json.dumps(artifact.model_dump(), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )


__all__ = [
    "load_execution_boundary_handoff_request_artifact",
    "process_execution_boundary_handoff_request_artifact",
]
