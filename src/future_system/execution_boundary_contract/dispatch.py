"""Deterministic local dispatch of validated handoff requests into cryp inbound transport tree."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from future_system.execution_boundary_contract.handoff_request_builder import (
    write_execution_boundary_handoff_request_from_package,
)
from future_system.execution_boundary_contract.validator import (
    validate_execution_boundary_handoff_request,
)
from future_system.review_outcome_packaging.writer import write_review_outcome_package


class ExecutionBoundaryDispatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result_kind: Literal["execution_boundary_dispatch_result"] = (
        "execution_boundary_dispatch_result"
    )
    status: Literal["dispatched_to_cryp_inbound", "dry_run_validated_only"]
    run_id: str
    correlation_id: str
    idempotency_key: str
    attempt_id: str
    dry_run: bool
    package_dir: str
    built_handoff_request_path: str
    resolved_inbound_handoff_request_path: str
    dispatch_receipt_path: str
    validation_status: Literal["passed"] = "passed"


class ExecutionBoundaryDispatchReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    receipt_kind: Literal["execution_boundary_dispatch_receipt"] = (
        "execution_boundary_dispatch_receipt"
    )
    status: Literal["dispatched_to_cryp_inbound"] = "dispatched_to_cryp_inbound"
    run_id: str
    correlation_id: str
    idempotency_key: str
    attempt_id: str
    dispatched_at_epoch_ns: int = Field(ge=0)
    package_dir: str
    built_handoff_request_path: str
    resolved_inbound_handoff_request_path: str


def _normalize_non_empty(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name}_empty")
    return normalized


def _normalize_attempt_id(value: str) -> str:
    attempt_id = _normalize_non_empty(value, field_name="attempt_id")
    if "/" in attempt_id or "\\" in attempt_id:
        raise ValueError("attempt_id_invalid_path_separator")
    if attempt_id in {".", ".."}:
        raise ValueError("attempt_id_invalid_relative_component")
    return attempt_id


def _default_attempt_id(*, epoch_ns: int) -> str:
    return f"attempt-{epoch_ns}"


def dispatch_execution_boundary_handoff_request(
    *,
    run_id: str,
    artifacts_root: Path,
    cryp_transport_root: Path,
    attempt_id: str | None = None,
    dry_run: bool = False,
    generated_attempt_epoch_ns: int | None = None,
    dispatched_at_epoch_ns: int | None = None,
) -> ExecutionBoundaryDispatchResult:
    normalized_run_id = _normalize_non_empty(run_id, field_name="run_id")
    resolved_artifacts_root = artifacts_root.resolve()
    resolved_cryp_transport_root = cryp_transport_root.resolve()

    package = write_review_outcome_package(
        run_id=normalized_run_id,
        markdown_artifact_path=resolved_artifacts_root / f"{normalized_run_id}.md",
        json_artifact_path=resolved_artifacts_root / f"{normalized_run_id}.json",
        operator_review_metadata_path=(
            resolved_artifacts_root / f"{normalized_run_id}.operator_review.json"
        ),
        target_root=resolved_artifacts_root,
    )
    package_dir = Path(package.paths.package_dir).resolve()
    built_handoff_request_path = write_execution_boundary_handoff_request_from_package(
        package_dir=package_dir
    ).resolve()

    payload = json.loads(built_handoff_request_path.read_text(encoding="utf-8"))
    validated = validate_execution_boundary_handoff_request(
        payload=payload,
        require_local_artifacts=True,
    )

    attempt_epoch_ns = generated_attempt_epoch_ns or time.time_ns()
    resolved_attempt_id = (
        _normalize_attempt_id(attempt_id)
        if attempt_id is not None
        else _default_attempt_id(epoch_ns=attempt_epoch_ns)
    )
    resolved_inbound_handoff_request_path = (
        resolved_cryp_transport_root
        / "inbound"
        / validated.correlation_id
        / resolved_attempt_id
        / "handoff_request.json"
    ).resolve()
    dispatch_receipt_path = (
        resolved_cryp_transport_root
        / "dispatch"
        / validated.correlation_id
        / resolved_attempt_id
        / "polymarket_arb_dispatch_receipt.json"
    ).resolve()

    if dry_run:
        return ExecutionBoundaryDispatchResult(
            status="dry_run_validated_only",
            run_id=normalized_run_id,
            correlation_id=validated.correlation_id,
            idempotency_key=validated.idempotency_key,
            attempt_id=resolved_attempt_id,
            dry_run=True,
            package_dir=str(package_dir),
            built_handoff_request_path=str(built_handoff_request_path),
            resolved_inbound_handoff_request_path=str(resolved_inbound_handoff_request_path),
            dispatch_receipt_path=str(dispatch_receipt_path),
        )

    resolved_inbound_handoff_request_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_inbound_handoff_request_path.write_text(
        f"{json.dumps(validated.model_dump(mode='json'), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )

    dispatch_receipt = ExecutionBoundaryDispatchReceipt(
        run_id=normalized_run_id,
        correlation_id=validated.correlation_id,
        idempotency_key=validated.idempotency_key,
        attempt_id=resolved_attempt_id,
        dispatched_at_epoch_ns=dispatched_at_epoch_ns or time.time_ns(),
        package_dir=str(package_dir),
        built_handoff_request_path=str(built_handoff_request_path),
        resolved_inbound_handoff_request_path=str(resolved_inbound_handoff_request_path),
    )
    dispatch_receipt_path.parent.mkdir(parents=True, exist_ok=True)
    dispatch_receipt_path.write_text(
        f"{json.dumps(dispatch_receipt.model_dump(mode='json'), indent=2, sort_keys=True)}\n",
        encoding="utf-8",
    )

    return ExecutionBoundaryDispatchResult(
        status="dispatched_to_cryp_inbound",
        run_id=normalized_run_id,
        correlation_id=validated.correlation_id,
        idempotency_key=validated.idempotency_key,
        attempt_id=resolved_attempt_id,
        dry_run=False,
        package_dir=str(package_dir),
        built_handoff_request_path=str(built_handoff_request_path),
        resolved_inbound_handoff_request_path=str(resolved_inbound_handoff_request_path),
        dispatch_receipt_path=str(dispatch_receipt_path),
    )


__all__ = [
    "ExecutionBoundaryDispatchReceipt",
    "ExecutionBoundaryDispatchResult",
    "dispatch_execution_boundary_handoff_request",
]
