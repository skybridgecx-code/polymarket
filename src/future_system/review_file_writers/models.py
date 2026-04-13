"""Deterministic result models for local writing of review export payloads."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, field_validator

from future_system.review_exports.models import ReviewExportKind
from future_system.runtime.models import AnalysisRunFailureStage, AnalysisRunStatus


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _normalize_non_negative_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative.")
    return value


class AnalysisSuccessReviewFileWriteResult(BaseModel):
    """Structured result for writing one successful review export payload package."""

    target_directory: str
    theme_id: str
    status: Literal["success"]
    export_kind: Literal["analysis_success_export"]
    failure_stage: None = None
    markdown_file_path: str
    json_file_path: str
    markdown_bytes_written: int
    json_bytes_written: int

    @field_validator(
        "target_directory",
        "theme_id",
        "markdown_file_path",
        "json_file_path",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("markdown_bytes_written", "json_bytes_written", mode="before")
    @classmethod
    def _normalize_byte_counts(cls, value: Any, info: Any) -> int:
        return _normalize_non_negative_int(value, info.field_name)


class AnalysisFailureReviewFileWriteResult(BaseModel):
    """Structured result for writing one failed review export payload package."""

    target_directory: str
    theme_id: str
    status: Literal["failed"]
    export_kind: Literal["analysis_failure_export"]
    failure_stage: AnalysisRunFailureStage
    markdown_file_path: str
    json_file_path: str
    markdown_bytes_written: int
    json_bytes_written: int

    @field_validator(
        "target_directory",
        "theme_id",
        "markdown_file_path",
        "json_file_path",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("markdown_bytes_written", "json_bytes_written", mode="before")
    @classmethod
    def _normalize_byte_counts(cls, value: Any, info: Any) -> int:
        return _normalize_non_negative_int(value, info.field_name)


AnalysisReviewFileWriteResult = (
    AnalysisSuccessReviewFileWriteResult | AnalysisFailureReviewFileWriteResult
)

__all__ = [
    "AnalysisFailureReviewFileWriteResult",
    "AnalysisReviewFileWriteResult",
    "AnalysisRunFailureStage",
    "AnalysisRunStatus",
    "AnalysisSuccessReviewFileWriteResult",
    "ReviewExportKind",
]
