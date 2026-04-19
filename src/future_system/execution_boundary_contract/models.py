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


__all__ = ["ExecutionBoundaryHandoffRequest"]
