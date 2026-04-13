"""Deterministic contract models for local operator review decision metadata."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.review_exports.models import ReviewExportKind
from future_system.runtime.models import AnalysisRunFailureStage, AnalysisRunStatus

OperatorReviewStatus = Literal["pending", "decided"]
OperatorReviewDecision = Literal["approve", "reject", "needs_follow_up"]


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return _normalize_required_text(value, field_name)


def _normalize_non_negative_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
    return value


def _normalize_optional_non_negative_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    return _normalize_non_negative_int(value, field_name)


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


class OperatorReviewArtifactReference(BaseModel):
    """Bounded reference linking review metadata to one existing artifact run."""

    run_id: str
    theme_id: str
    status: AnalysisRunStatus
    export_kind: ReviewExportKind
    failure_stage: AnalysisRunFailureStage | None = None
    json_file_path: str | None = None
    markdown_file_path: str | None = None

    @field_validator("run_id", "theme_id", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("json_file_path", "markdown_file_path", mode="before")
    @classmethod
    def _normalize_optional_path_fields(cls, value: Any, info: Any) -> str | None:
        return _normalize_optional_text(value, info.field_name)

    @model_validator(mode="after")
    def _validate_status_stage_alignment(self) -> Self:
        if self.status == "success" and self.failure_stage is not None:
            raise ValueError("failure_stage must be None when status is success.")
        if self.status == "failed" and self.failure_stage is None:
            raise ValueError("failure_stage is required when status is failed.")
        return self


class OperatorReviewDecisionRecord(BaseModel):
    """Deterministic local file-safe operator review decision metadata record."""

    record_kind: Literal["operator_review_decision_record"] = "operator_review_decision_record"
    record_version: Literal[1] = 1
    artifact: OperatorReviewArtifactReference
    review_status: OperatorReviewStatus = "pending"
    operator_decision: OperatorReviewDecision | None = None
    review_notes_summary: str | None = None
    reviewer_identity: str | None = None
    decided_at_epoch_ns: int | None = None
    updated_at_epoch_ns: int | None = None
    run_flags_snapshot: list[str] = Field(default_factory=list)

    @field_validator("review_notes_summary", "reviewer_identity", mode="before")
    @classmethod
    def _normalize_optional_text_fields(cls, value: Any, info: Any) -> str | None:
        return _normalize_optional_text(value, info.field_name)

    @field_validator("decided_at_epoch_ns", "updated_at_epoch_ns", mode="before")
    @classmethod
    def _normalize_optional_timestamp_fields(cls, value: Any, info: Any) -> int | None:
        return _normalize_optional_non_negative_int(value, info.field_name)

    @field_validator("run_flags_snapshot", mode="before")
    @classmethod
    def _normalize_run_flags_snapshot(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags_snapshot")

    @model_validator(mode="after")
    def _validate_review_status_decision_alignment(self) -> Self:
        if self.review_status == "pending":
            if self.operator_decision is not None:
                raise ValueError("review_status 'pending' must not set operator_decision.")
            if self.decided_at_epoch_ns is not None:
                raise ValueError("review_status 'pending' must not set decided_at_epoch_ns.")
        elif self.operator_decision is None:
            raise ValueError("review_status 'decided' requires operator_decision.")

        if (
            self.decided_at_epoch_ns is not None
            and self.updated_at_epoch_ns is not None
            and self.updated_at_epoch_ns < self.decided_at_epoch_ns
        ):
            raise ValueError("updated_at_epoch_ns must be >= decided_at_epoch_ns.")
        return self


__all__ = [
    "OperatorReviewArtifactReference",
    "OperatorReviewDecision",
    "OperatorReviewDecisionRecord",
    "OperatorReviewStatus",
]
