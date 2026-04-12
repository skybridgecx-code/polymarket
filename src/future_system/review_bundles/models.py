"""Canonical deterministic in-memory bundles for operator-facing analysis review output."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.review_packets.models import AnalysisReviewPacketEnvelope
from future_system.runtime.models import (
    AnalysisRunFailureStage,
    AnalysisRunResultEnvelope,
    AnalysisRunStatus,
)

ReviewBundleKind = Literal["analysis_success_bundle", "analysis_failure_bundle"]


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


class AnalysisSuccessReviewBundle(BaseModel):
    """Deterministic in-memory review bundle for successful runtime outcomes."""

    bundle_kind: Literal["analysis_success_bundle"]
    status: Literal["success"]
    theme_id: str
    runtime_result: AnalysisRunResultEnvelope
    review_packet: AnalysisReviewPacketEnvelope
    rendered_text: str
    rendered_markdown: str
    run_flags: list[str] = Field(default_factory=list)
    bundle_summary: str

    @field_validator(
        "theme_id",
        "rendered_text",
        "rendered_markdown",
        "bundle_summary",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @model_validator(mode="after")
    def _validate_bundle_alignment(self) -> Self:
        if self.runtime_result.status != "success":
            raise ValueError("runtime_result.status must be 'success' for success bundles.")
        if self.review_packet.status != "success":
            raise ValueError("review_packet.status must be 'success' for success bundles.")

        success = self.runtime_result.success
        if success is None:
            raise ValueError("runtime_result.success must be present for success bundles.")

        if self.theme_id != success.theme_id:
            raise ValueError("theme_id must match runtime_result.success.theme_id.")
        if self.theme_id != self.review_packet.review_packet.theme_id:
            raise ValueError("theme_id must match review_packet.review_packet.theme_id.")
        if self.run_flags != success.run_flags:
            raise ValueError("run_flags must match runtime_result.success.run_flags.")
        return self


class AnalysisFailureReviewBundle(BaseModel):
    """Deterministic in-memory review bundle for failed runtime outcomes."""

    bundle_kind: Literal["analysis_failure_bundle"]
    status: Literal["failed"]
    theme_id: str
    failure_stage: AnalysisRunFailureStage
    runtime_result: AnalysisRunResultEnvelope
    review_packet: AnalysisReviewPacketEnvelope
    rendered_text: str
    rendered_markdown: str
    run_flags: list[str] = Field(default_factory=list)
    bundle_summary: str

    @field_validator(
        "theme_id",
        "rendered_text",
        "rendered_markdown",
        "bundle_summary",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")

    @model_validator(mode="after")
    def _validate_bundle_alignment(self) -> Self:
        if self.runtime_result.status != "failed":
            raise ValueError("runtime_result.status must be 'failed' for failure bundles.")
        if self.review_packet.status != "failed":
            raise ValueError("review_packet.status must be 'failed' for failure bundles.")

        failure = self.runtime_result.failure
        if failure is None:
            raise ValueError("runtime_result.failure must be present for failure bundles.")

        if self.theme_id != failure.theme_id:
            raise ValueError("theme_id must match runtime_result.failure.theme_id.")
        if self.theme_id != self.review_packet.review_packet.theme_id:
            raise ValueError("theme_id must match review_packet.review_packet.theme_id.")
        if self.failure_stage != failure.failure_stage:
            raise ValueError("failure_stage must match runtime_result.failure.failure_stage.")
        if self.run_flags != failure.run_flags:
            raise ValueError("run_flags must match runtime_result.failure.run_flags.")
        return self


AnalysisReviewBundle = AnalysisSuccessReviewBundle | AnalysisFailureReviewBundle


class AnalysisReviewBundleEnvelope(BaseModel):
    """Top-level deterministic envelope for successful or failed review bundles."""

    status: AnalysisRunStatus
    review_bundle: AnalysisReviewBundle

    @model_validator(mode="after")
    def _validate_bundle_status_consistency(self) -> Self:
        if self.status != self.review_bundle.status:
            raise ValueError(
                "status must match review_bundle.status for deterministic bundle output."
            )
        return self
