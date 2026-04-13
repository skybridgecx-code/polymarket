"""Deterministic result models for top-level runtime-to-review entry composition."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.review_artifacts.models import (
    AnalysisFailureReviewArtifactFlowResult,
    AnalysisReviewArtifactFlowEnvelope,
    AnalysisSuccessReviewArtifactFlowResult,
)
from future_system.runtime.models import (
    AnalysisRunFailureStage,
    AnalysisRunResultEnvelope,
    AnalysisRunStatus,
)

ReviewEntryKind = Literal["analysis_success_review_entry", "analysis_failure_review_entry"]


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


class AnalysisSuccessReviewEntryResult(BaseModel):
    """Structured successful output for the top-level runtime-to-review entrypoint."""

    entry_kind: Literal["analysis_success_review_entry"]
    status: Literal["success"]
    theme_id: str
    target_directory: str
    runtime_result: AnalysisRunResultEnvelope
    artifact_flow: AnalysisReviewArtifactFlowEnvelope
    run_flags: list[str] = Field(default_factory=list)
    failure_stage: None = None
    entry_summary: str

    @field_validator("theme_id", "target_directory", "entry_summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @model_validator(mode="after")
    def _validate_alignment(self) -> Self:
        if self.runtime_result.status != "success":
            raise ValueError("runtime_result.status must be 'success'.")
        success_packet = self.runtime_result.success
        if success_packet is None:
            raise ValueError("runtime_result.success must be present for success entry results.")

        if self.artifact_flow.status != "success":
            raise ValueError("artifact_flow.status must be 'success'.")
        flow_result = self.artifact_flow.flow_result
        if not isinstance(flow_result, AnalysisSuccessReviewArtifactFlowResult):
            raise ValueError("artifact_flow.flow_result must be a success flow result.")

        if self.theme_id != success_packet.theme_id:
            raise ValueError("theme_id must match runtime_result.success.theme_id.")
        if self.theme_id != flow_result.theme_id:
            raise ValueError("theme_id must match artifact_flow.flow_result.theme_id.")

        if self.run_flags != success_packet.run_flags:
            raise ValueError("run_flags must match runtime_result.success.run_flags.")
        if self.run_flags != flow_result.run_flags:
            raise ValueError("run_flags must match artifact_flow.flow_result.run_flags.")

        if self.target_directory != flow_result.target_directory:
            raise ValueError(
                "target_directory must match artifact_flow.flow_result.target_directory."
            )
        return self


class AnalysisFailureReviewEntryResult(BaseModel):
    """Structured failed output for the top-level runtime-to-review entrypoint."""

    entry_kind: Literal["analysis_failure_review_entry"]
    status: Literal["failed"]
    theme_id: str
    target_directory: str
    runtime_result: AnalysisRunResultEnvelope
    artifact_flow: AnalysisReviewArtifactFlowEnvelope
    run_flags: list[str] = Field(default_factory=list)
    failure_stage: AnalysisRunFailureStage
    entry_summary: str

    @field_validator("theme_id", "target_directory", "entry_summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @model_validator(mode="after")
    def _validate_alignment(self) -> Self:
        if self.runtime_result.status != "failed":
            raise ValueError("runtime_result.status must be 'failed'.")
        failure_packet = self.runtime_result.failure
        if failure_packet is None:
            raise ValueError("runtime_result.failure must be present for failure entry results.")

        if self.artifact_flow.status != "failed":
            raise ValueError("artifact_flow.status must be 'failed'.")
        flow_result = self.artifact_flow.flow_result
        if not isinstance(flow_result, AnalysisFailureReviewArtifactFlowResult):
            raise ValueError("artifact_flow.flow_result must be a failure flow result.")

        if self.theme_id != failure_packet.theme_id:
            raise ValueError("theme_id must match runtime_result.failure.theme_id.")
        if self.theme_id != flow_result.theme_id:
            raise ValueError("theme_id must match artifact_flow.flow_result.theme_id.")

        if self.failure_stage != failure_packet.failure_stage:
            raise ValueError("failure_stage must match runtime_result.failure.failure_stage.")
        if self.failure_stage != flow_result.failure_stage:
            raise ValueError("failure_stage must match artifact_flow.flow_result.failure_stage.")

        if self.run_flags != failure_packet.run_flags:
            raise ValueError("run_flags must match runtime_result.failure.run_flags.")
        if self.run_flags != flow_result.run_flags:
            raise ValueError("run_flags must match artifact_flow.flow_result.run_flags.")

        if self.target_directory != flow_result.target_directory:
            raise ValueError(
                "target_directory must match artifact_flow.flow_result.target_directory."
            )
        return self


AnalysisReviewEntryResult = AnalysisSuccessReviewEntryResult | AnalysisFailureReviewEntryResult


class AnalysisReviewEntryEnvelope(BaseModel):
    """Top-level deterministic envelope for runtime entry-to-artifact entry output."""

    status: AnalysisRunStatus
    entry_result: AnalysisReviewEntryResult

    @model_validator(mode="after")
    def _validate_status_alignment(self) -> Self:
        if self.status != self.entry_result.status:
            raise ValueError("status must match entry_result.status.")
        return self


__all__ = [
    "AnalysisFailureReviewEntryResult",
    "AnalysisReviewEntryEnvelope",
    "AnalysisReviewEntryResult",
    "AnalysisSuccessReviewEntryResult",
    "ReviewEntryKind",
]
