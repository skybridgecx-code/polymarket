"""Canonical deterministic operator-review packets derived from runtime results."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.runtime.models import AnalysisRunFailureStage, AnalysisRunStatus

ReviewPacketKind = Literal["analysis_success", "analysis_failure"]


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list of strings.")

    normalized: list[str] = []
    for item in value:
        token = _normalize_required_text(item, field_name)
        if token in normalized:
            continue
        normalized.append(token)
    return normalized


def _validate_unit_interval(value: float, field_name: str) -> float:
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0.0, 1.0]; received {value}.")
    return value


class AnalysisSuccessReviewPacket(BaseModel):
    """Deterministic review packet for successful runtime outcomes."""

    packet_kind: Literal["analysis_success"]
    status: Literal["success"]
    theme_id: str
    run_flags: list[str] = Field(default_factory=list)
    summary_text: str
    runtime_summary: str
    candidate_posture: str
    reasoning_posture: str
    policy_decision: str
    decision_score: float
    readiness_score: float
    risk_penalty: float

    @field_validator(
        "theme_id",
        "summary_text",
        "runtime_summary",
        "candidate_posture",
        "reasoning_posture",
        "policy_decision",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @field_validator("decision_score", "readiness_score", "risk_penalty")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        return _validate_unit_interval(value, info.field_name)


class AnalysisFailureReviewPacket(BaseModel):
    """Deterministic review packet for failed runtime outcomes."""

    packet_kind: Literal["analysis_failure"]
    status: Literal["failed"]
    theme_id: str
    failure_stage: AnalysisRunFailureStage
    run_flags: list[str] = Field(default_factory=list)
    summary_text: str
    runtime_summary: str
    error_message: str

    @field_validator(
        "theme_id",
        "summary_text",
        "runtime_summary",
        "error_message",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")


AnalysisReviewPacket = AnalysisSuccessReviewPacket | AnalysisFailureReviewPacket


class AnalysisReviewPacketEnvelope(BaseModel):
    """Top-level deterministic envelope for successful or failed review packets."""

    status: AnalysisRunStatus
    review_packet: AnalysisReviewPacket

    @model_validator(mode="after")
    def _validate_packet_status_consistency(self) -> Self:
        if self.status != self.review_packet.status:
            raise ValueError(
                "status must match review_packet.status for deterministic review envelope output."
            )
        return self
