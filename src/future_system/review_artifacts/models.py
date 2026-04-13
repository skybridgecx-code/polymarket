"""Deterministic result models for runtime-to-review local artifact composition flow."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.review_bundles.models import (
    AnalysisFailureReviewBundle,
    AnalysisReviewBundleEnvelope,
    AnalysisSuccessReviewBundle,
)
from future_system.review_exports.models import (
    AnalysisFailureReviewExportPayload,
    AnalysisReviewExportPackage,
    AnalysisSuccessReviewExportPayload,
)
from future_system.review_file_writers.models import (
    AnalysisFailureReviewFileWriteResult,
    AnalysisSuccessReviewFileWriteResult,
)
from future_system.runtime.models import (
    AnalysisRunFailureStage,
    AnalysisRunResultEnvelope,
    AnalysisRunStatus,
)

ReviewArtifactFlowKind = Literal[
    "analysis_success_artifact_flow",
    "analysis_failure_artifact_flow",
]


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


class AnalysisSuccessReviewArtifactFlowResult(BaseModel):
    """Structured output for successful runtime-to-review artifact composition flow."""

    flow_kind: Literal["analysis_success_artifact_flow"]
    status: Literal["success"]
    theme_id: str
    target_directory: str
    runtime_result: AnalysisRunResultEnvelope
    review_bundle: AnalysisReviewBundleEnvelope
    export_package: AnalysisReviewExportPackage
    file_write_result: AnalysisSuccessReviewFileWriteResult
    run_flags: list[str] = Field(default_factory=list)
    failure_stage: None = None
    flow_summary: str

    @field_validator("theme_id", "target_directory", "flow_summary", mode="before")
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
        success = self.runtime_result.success
        if success is None:
            raise ValueError("runtime_result.success must be present for success flow results.")

        if self.review_bundle.status != "success":
            raise ValueError("review_bundle.status must be 'success'.")
        bundle_payload = self.review_bundle.review_bundle
        if not isinstance(bundle_payload, AnalysisSuccessReviewBundle):
            raise ValueError("review_bundle.review_bundle must be a success bundle.")

        if self.export_package.status != "success":
            raise ValueError("export_package.status must be 'success'.")
        if not isinstance(self.export_package.payload, AnalysisSuccessReviewExportPayload):
            raise ValueError("export_package.payload must be a success export payload.")

        if self.file_write_result.status != "success":
            raise ValueError("file_write_result.status must be 'success'.")

        if self.theme_id != success.theme_id:
            raise ValueError("theme_id must match runtime_result.success.theme_id.")
        if self.theme_id != bundle_payload.theme_id:
            raise ValueError("theme_id must match review_bundle.review_bundle.theme_id.")
        if self.theme_id != self.export_package.theme_id:
            raise ValueError("theme_id must match export_package.theme_id.")
        if self.theme_id != self.file_write_result.theme_id:
            raise ValueError("theme_id must match file_write_result.theme_id.")

        if self.run_flags != success.run_flags:
            raise ValueError("run_flags must match runtime_result.success.run_flags.")
        if self.run_flags != bundle_payload.run_flags:
            raise ValueError("run_flags must match review_bundle.review_bundle.run_flags.")
        if self.run_flags != self.export_package.run_flags:
            raise ValueError("run_flags must match export_package.run_flags.")

        if self.target_directory != self.file_write_result.target_directory:
            raise ValueError("target_directory must match file_write_result.target_directory.")
        return self


class AnalysisFailureReviewArtifactFlowResult(BaseModel):
    """Structured output for failed runtime-to-review artifact composition flow."""

    flow_kind: Literal["analysis_failure_artifact_flow"]
    status: Literal["failed"]
    theme_id: str
    target_directory: str
    runtime_result: AnalysisRunResultEnvelope
    review_bundle: AnalysisReviewBundleEnvelope
    export_package: AnalysisReviewExportPackage
    file_write_result: AnalysisFailureReviewFileWriteResult
    run_flags: list[str] = Field(default_factory=list)
    failure_stage: AnalysisRunFailureStage
    flow_summary: str

    @field_validator("theme_id", "target_directory", "flow_summary", mode="before")
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
        failure = self.runtime_result.failure
        if failure is None:
            raise ValueError("runtime_result.failure must be present for failure flow results.")

        if self.review_bundle.status != "failed":
            raise ValueError("review_bundle.status must be 'failed'.")
        bundle_payload = self.review_bundle.review_bundle
        if not isinstance(bundle_payload, AnalysisFailureReviewBundle):
            raise ValueError("review_bundle.review_bundle must be a failure bundle.")

        if self.export_package.status != "failed":
            raise ValueError("export_package.status must be 'failed'.")
        export_payload = self.export_package.payload
        if not isinstance(export_payload, AnalysisFailureReviewExportPayload):
            raise ValueError("export_package.payload must be a failure export payload.")

        if self.file_write_result.status != "failed":
            raise ValueError("file_write_result.status must be 'failed'.")

        if self.theme_id != failure.theme_id:
            raise ValueError("theme_id must match runtime_result.failure.theme_id.")
        if self.theme_id != bundle_payload.theme_id:
            raise ValueError("theme_id must match review_bundle.review_bundle.theme_id.")
        if self.theme_id != self.export_package.theme_id:
            raise ValueError("theme_id must match export_package.theme_id.")
        if self.theme_id != self.file_write_result.theme_id:
            raise ValueError("theme_id must match file_write_result.theme_id.")

        if self.failure_stage != failure.failure_stage:
            raise ValueError("failure_stage must match runtime_result.failure.failure_stage.")
        if self.failure_stage != bundle_payload.failure_stage:
            raise ValueError("failure_stage must match review_bundle.review_bundle.failure_stage.")
        if self.failure_stage != export_payload.failure_stage:
            raise ValueError("failure_stage must match export_package.payload.failure_stage.")
        if self.failure_stage != self.file_write_result.failure_stage:
            raise ValueError("failure_stage must match file_write_result.failure_stage.")

        if self.run_flags != failure.run_flags:
            raise ValueError("run_flags must match runtime_result.failure.run_flags.")
        if self.run_flags != bundle_payload.run_flags:
            raise ValueError("run_flags must match review_bundle.review_bundle.run_flags.")
        if self.run_flags != self.export_package.run_flags:
            raise ValueError("run_flags must match export_package.run_flags.")

        if self.target_directory != self.file_write_result.target_directory:
            raise ValueError("target_directory must match file_write_result.target_directory.")
        return self


AnalysisReviewArtifactFlowResult = (
    AnalysisSuccessReviewArtifactFlowResult | AnalysisFailureReviewArtifactFlowResult
)


class AnalysisReviewArtifactFlowEnvelope(BaseModel):
    """Top-level deterministic envelope for runtime-to-review artifact flow output."""

    status: AnalysisRunStatus
    flow_result: AnalysisReviewArtifactFlowResult

    @model_validator(mode="after")
    def _validate_status_alignment(self) -> Self:
        if self.status != self.flow_result.status:
            raise ValueError("status must match flow_result.status.")
        return self


__all__ = [
    "AnalysisFailureReviewArtifactFlowResult",
    "AnalysisReviewArtifactFlowEnvelope",
    "AnalysisReviewArtifactFlowResult",
    "AnalysisSuccessReviewArtifactFlowResult",
    "ReviewArtifactFlowKind",
]
