"""Deterministic models for the Phase 37A execution-boundary handoff request."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from future_system.operator_review_models import OperatorReviewDecisionRecord
from future_system.review_outcome_packaging.models import ReviewOutcomePackagePayload


class ExecutionBoundaryHandoffRequest(BaseModel):
    """Local-only handoff request envelope from polymarket-arb to cryp."""

    contract_version: Literal["37A.v1"] = "37A.v1"
    producer_system: Literal["polymarket-arb"] = "polymarket-arb"
    consumer_system: Literal["cryp"] = "cryp"
    correlation_id: str
    idempotency_key: str
    handoff_payload: ReviewOutcomePackagePayload
    operator_review_metadata: OperatorReviewDecisionRecord
    package_artifact_path: str | None = None
    handoff_summary_path: str | None = None
    handoff_payload_path: str | None = None
    notes: list[str] = Field(default_factory=list)


class ExecutionBoundaryIntakeAckArtifact(BaseModel):
    """Deterministic local acknowledgment artifact for a valid handoff request."""

    artifact_kind: Literal["execution_boundary_intake_ack"] = "execution_boundary_intake_ack"
    contract_version: Literal["37A.v1"] = "37A.v1"
    producer_system: Literal["polymarket-arb"] = "polymarket-arb"
    consumer_system: Literal["cryp"] = "cryp"
    correlation_id: str
    idempotency_key: str
    run_id: str
    submission_status: Literal["accepted_for_local_execution_review"] = (
        "accepted_for_local_execution_review"
    )
    reason_codes: list[str] = Field(default_factory=list)
    source_handoff_request_path: str


class ExecutionBoundaryIntakeRejectArtifact(BaseModel):
    """Deterministic local reject artifact for an invalid handoff request."""

    artifact_kind: Literal["execution_boundary_intake_reject"] = "execution_boundary_intake_reject"
    contract_version: Literal["37A.v1"] = "37A.v1"
    producer_system: Literal["polymarket-arb"] = "polymarket-arb"
    consumer_system: Literal["cryp"] = "cryp"
    correlation_id: str | None = None
    idempotency_key: str | None = None
    submission_status: Literal["rejected_for_local_execution_review"] = (
        "rejected_for_local_execution_review"
    )
    reason_codes: list[str] = Field(default_factory=list)
    validation_error: str
    source_handoff_request_path: str


class ExecutionBoundaryIntakeExportResult(BaseModel):
    """Result envelope describing where deterministic intake artifacts were written."""

    source_handoff_request_path: str
    accepted: bool
    ack_artifact_path: str | None = None
    reject_artifact_path: str | None = None


__all__ = [
    "ExecutionBoundaryHandoffRequest",
    "ExecutionBoundaryIntakeAckArtifact",
    "ExecutionBoundaryIntakeRejectArtifact",
    "ExecutionBoundaryIntakeExportResult",
]
