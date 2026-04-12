"""Canonical deterministic models for end-to-end dry-run analysis runtime packets."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from future_system.context_bundle.models import OpportunityContextBundle
from future_system.policy_engine.models import PolicyDecisionPacket
from future_system.reasoning_contracts.models import (
    ReasoningInputPacket,
    ReasoningOutputPacket,
    RenderedPromptPacket,
)

AnalysisRunStatus = Literal["success", "failed"]


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


class AnalysisRunError(ValueError):
    """Raised when dry-run analysis runtime cannot complete end-to-end pipeline."""
