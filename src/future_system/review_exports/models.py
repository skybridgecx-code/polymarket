"""Canonical deterministic payload models for exporting analysis review bundles."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.runtime.models import AnalysisRunFailureStage, AnalysisRunStatus

ReviewExportKind = Literal["analysis_success_export", "analysis_failure_export"]


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


def _normalize_json_payload(value: Any) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("json_payload must be a dict[str, object].")
    if not value:
        raise ValueError("json_payload must not be empty.")

    normalized: dict[str, object] = {}
    for key, item in value.items():
        normalized_key = _normalize_required_text(key, "json_payload.key")
        normalized[normalized_key] = item
    return normalized


class AnalysisSuccessReviewExportPayload(BaseModel):
    """Deterministic export payload package for successful review bundles."""

    export_kind: Literal["analysis_success_export"]
    status: Literal["success"]
    theme_id: str
    bundle_kind: Literal["analysis_success_bundle"]
    packet_kind: Literal["analysis_success"]
    run_flags: list[str] = Field(default_factory=list)
    json_payload: dict[str, object]
    markdown_document: str
    export_summary: str

    @field_validator("theme_id", "markdown_document", "export_summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @field_validator("json_payload", mode="before")
    @classmethod
    def _validate_json_payload(cls, value: Any) -> dict[str, object]:
        return _normalize_json_payload(value)


class AnalysisFailureReviewExportPayload(BaseModel):
    """Deterministic export payload package for failed review bundles."""

    export_kind: Literal["analysis_failure_export"]
    status: Literal["failed"]
    theme_id: str
    bundle_kind: Literal["analysis_failure_bundle"]
    packet_kind: Literal["analysis_failure"]
    failure_stage: AnalysisRunFailureStage
    run_flags: list[str] = Field(default_factory=list)
    json_payload: dict[str, object]
    markdown_document: str
    export_summary: str

    @field_validator("theme_id", "markdown_document", "export_summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @field_validator("json_payload", mode="before")
    @classmethod
    def _validate_json_payload(cls, value: Any) -> dict[str, object]:
        return _normalize_json_payload(value)


AnalysisReviewExportPayload = (
    AnalysisSuccessReviewExportPayload | AnalysisFailureReviewExportPayload
)


class AnalysisReviewExportPackage(BaseModel):
    """Top-level deterministic package containing export payloads and package metadata."""

    theme_id: str
    status: AnalysisRunStatus
    export_kind: ReviewExportKind
    run_flags: list[str] = Field(default_factory=list)
    payload: AnalysisReviewExportPayload
    cryp_external_confirmation_signal: dict[str, object] | None = None

    @field_validator("theme_id", mode="before")
    @classmethod
    def _normalize_theme_id(cls, value: Any) -> str:
        return _normalize_required_text(value, "theme_id")

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @field_validator("cryp_external_confirmation_signal", mode="before")
    @classmethod
    def _normalize_optional_cryp_signal(
        cls,
        value: Any,
    ) -> dict[str, object] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("cryp_external_confirmation_signal must be a dict.")
        normalized: dict[str, object] = {}
        for key, item in value.items():
            normalized_key = _normalize_required_text(
                key,
                "cryp_external_confirmation_signal.key",
            )
            normalized[normalized_key] = item
        return normalized

    @model_validator(mode="after")
    def _validate_package_alignment(self) -> Self:
        if self.status != self.payload.status:
            raise ValueError("status must match payload.status.")
        if self.export_kind != self.payload.export_kind:
            raise ValueError("export_kind must match payload.export_kind.")
        if self.theme_id != self.payload.theme_id:
            raise ValueError("theme_id must match payload.theme_id.")
        if self.run_flags != self.payload.run_flags:
            raise ValueError("run_flags must match payload.run_flags.")
        return self
