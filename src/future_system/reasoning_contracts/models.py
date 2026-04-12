"""Canonical deterministic contracts for reasoning input, prompt rendering, and output."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ReasoningRecommendedPosture = Literal[
    "watch",
    "candidate",
    "high_conflict",
    "deny",
    "insufficient",
]


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
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must contain only strings.")
        token = item.strip()
        if not token:
            continue
        normalized.append(token)
    return normalized


class ReasoningInputPacket(BaseModel):
    """Canonical reasoning input derived from one opportunity context bundle."""

    theme_id: str
    title: str | None = None
    candidate_posture: str
    comparison_alignment: str
    candidate_score: float
    confidence_score: float
    conflict_score: float
    bundle_flags: list[str] = Field(default_factory=list)
    operator_summary: str
    structured_facts: dict[str, object]
    prompt_version: str

    @field_validator(
        "theme_id",
        "candidate_posture",
        "comparison_alignment",
        "operator_summary",
        "prompt_version",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("title", mode="before")
    @classmethod
    def _normalize_title(cls, value: Any) -> str | None:
        return _normalize_optional_text(value, "title")

    @field_validator("candidate_score", "confidence_score", "conflict_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated

    @field_validator("bundle_flags", mode="before")
    @classmethod
    def _normalize_bundle_flags(cls, value: Any) -> list[str]:
        return _normalize_string_list(value, "bundle_flags")

    @field_validator("structured_facts", mode="before")
    @classmethod
    def _validate_structured_facts(cls, value: Any) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ValueError("structured_facts must be a dict[str, object].")
        if not value:
            raise ValueError("structured_facts must not be empty.")

        normalized: dict[str, object] = {}
        for key, item in value.items():
            normalized_key = _normalize_required_text(key, "structured_facts.key")
            normalized[normalized_key] = item
        return normalized


class ReasoningOutputPacket(BaseModel):
    """Strict validated reasoning output for downstream policy consumption."""

    theme_id: str
    thesis: str
    counter_thesis: str
    key_drivers: list[str]
    missing_information: list[str]
    uncertainty_notes: list[str]
    recommended_posture: ReasoningRecommendedPosture
    confidence_explanation: str
    analyst_flags: list[str] = Field(default_factory=list)

    @field_validator(
        "theme_id",
        "thesis",
        "counter_thesis",
        "confidence_explanation",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator(
        "key_drivers",
        "missing_information",
        "uncertainty_notes",
        "analyst_flags",
        mode="before",
    )
    @classmethod
    def _normalize_list_fields(cls, value: Any, info: Any) -> list[str]:
        return _normalize_string_list(value, info.field_name)

    @field_validator("key_drivers")
    @classmethod
    def _validate_key_drivers(cls, value: list[str]) -> list[str]:
        if len(value) < 1:
            raise ValueError("key_drivers must include at least one non-empty item.")
        return value


class RenderedPromptPacket(BaseModel):
    """Deterministically rendered prompt payload for future model invocation."""

    system_prompt: str
    user_prompt: str
    rendered_json_schema: dict[str, object] | None = None

    @field_validator("system_prompt", "user_prompt", mode="before")
    @classmethod
    def _normalize_prompt_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("rendered_json_schema", mode="before")
    @classmethod
    def _normalize_schema(cls, value: Any) -> dict[str, object] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            raise ValueError("rendered_json_schema must be a dict when provided.")
        return value


class ReasoningParseError(ValueError):
    """Raised when model-like output cannot be parsed into ReasoningOutputPacket."""
