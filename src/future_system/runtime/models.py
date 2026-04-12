"""Canonical deterministic models for end-to-end dry-run analysis runtime packets."""

from __future__ import annotations

from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.policy_engine.models import PolicyDecisionPacket
from future_system.reasoning_contracts.models import (
    ReasoningInputPacket,
    ReasoningOutputPacket,
    RenderedPromptPacket,
)

AnalysisRunStatus = Literal["success", "failed"]
AnalysisRunFailureStage = Literal["analyst_timeout", "analyst_transport", "reasoning_parse"]


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


class AnalysisRunPacket(BaseModel):
    """Canonical end-to-end dry-run runtime output packet."""

    theme_id: str
    status: AnalysisRunStatus
    context_bundle: OpportunityContextBundle
    reasoning_input: ReasoningInputPacket
    rendered_prompt: RenderedPromptPacket | dict[str, object] | None = None
    reasoning_output: ReasoningOutputPacket
    policy_decision: PolicyDecisionPacket
    run_flags: list[str] = Field(default_factory=list)
    run_summary: str

    @field_validator("theme_id", "run_summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")


class AnalysisRunFailurePacket(BaseModel):
    """Canonical deterministic runtime failure packet for operator-safe review."""

    theme_id: str
    status: Literal["failed"]
    failure_stage: AnalysisRunFailureStage
    run_flags: list[str] = Field(default_factory=list)
    run_summary: str
    error_message: str

    @field_validator("theme_id", "run_summary", "error_message", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("run_flags", mode="before")
    @classmethod
    def _normalize_run_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "run_flags")


class AnalysisRunResultEnvelope(BaseModel):
    """Top-level deterministic runtime result envelope for success or failure."""

    status: AnalysisRunStatus
    success: AnalysisRunPacket | None = None
    failure: AnalysisRunFailurePacket | None = None

    @model_validator(mode="after")
    def _validate_status_payload_consistency(self) -> Self:
        if self.status == "success":
            if self.success is None:
                raise ValueError("success payload is required when status='success'.")
            if self.failure is not None:
                raise ValueError("failure payload must be omitted when status='success'.")
            if self.success.status != "success":
                raise ValueError("success payload status must be 'success'.")
            return self

        if self.failure is None:
            raise ValueError("failure payload is required when status='failed'.")
        if self.success is not None:
            raise ValueError("success payload must be omitted when status='failed'.")
        if self.failure.status != "failed":
            raise ValueError("failure payload status must be 'failed'.")
        return self


class AnalysisRunError(ValueError):
    """Raised when dry-run analysis runtime cannot complete end-to-end pipeline."""

    def __init__(
        self,
        message: str,
        *,
        theme_id: str,
        failure_stage: AnalysisRunFailureStage | None = None,
        run_flags: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.theme_id = _normalize_required_text(theme_id, "theme_id")
        self.failure_stage = failure_stage
        self.run_flags = _normalize_string_list(run_flags, "run_flags")
