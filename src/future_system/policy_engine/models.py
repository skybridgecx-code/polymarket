"""Canonical deterministic contracts for policy decisions from context + reasoning."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

PolicyDecisionAction = Literal["allow", "hold", "deny"]
PolicyReasonCode = Literal[
    "strong_candidate_alignment",
    "reasoning_supportive",
    "weak_candidate_score",
    "weak_confidence",
    "high_conflict",
    "candidate_insufficient",
    "comparison_conflicted",
    "reasoning_high_conflict",
    "missing_information_significant",
    "insufficient_news_support",
    "stale_context",
    "bundle_incomplete",
    "reasoning_posture_deny",
    "reasoning_posture_insufficient",
]


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _validate_unit_interval(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0.0, 1.0]; received {value}.")
    return value


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


class PolicyDecisionPacket(BaseModel):
    """Canonical deterministic policy output packet."""

    theme_id: str
    decision: PolicyDecisionAction
    decision_score: float
    readiness_score: float
    risk_penalty: float
    reason_codes: list[PolicyReasonCode] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    summary: str

    @field_validator("theme_id", "summary", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("decision_score", "readiness_score", "risk_penalty")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated

    @field_validator("reason_codes", "flags", mode="before")
    @classmethod
    def _normalize_list_fields(cls, value: Any, info: Any) -> list[str]:
        return _normalize_string_list(value, info.field_name)


class PolicyDecisionError(ValueError):
    """Raised when deterministic policy decision cannot be computed."""
