"""Canonical request metadata models for live analyst transport calls."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

LiveAnalystInputMode = Literal["reasoning_input", "rendered_prompt", "rendered_prompt_text"]


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


class LiveAnalystTransportRequest(BaseModel):
    """Deterministic transport request envelope passed to live model boundaries."""

    input_mode: LiveAnalystInputMode
    payload: dict[str, object]
    timeout_seconds: float
    model: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("payload", mode="before")
    @classmethod
    def _validate_payload(cls, value: Any) -> dict[str, object]:
        if not isinstance(value, dict):
            raise ValueError("payload must be a dict[str, object].")
        if not value:
            raise ValueError("payload must not be empty.")

        normalized: dict[str, object] = {}
        for key, item in value.items():
            normalized_key = _normalize_required_text(key, "payload.key")
            normalized[normalized_key] = item
        return normalized

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout_seconds(cls, value: float) -> float:
        if value <= 0.0:
            raise ValueError("timeout_seconds must be greater than 0.")
        return float(value)

    @field_validator("model", mode="before")
    @classmethod
    def _normalize_model(cls, value: Any) -> str | None:
        return _normalize_optional_text(value, "model")

    @field_validator("metadata", mode="before")
    @classmethod
    def _normalize_metadata(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError("metadata must be a dict[str, str].")

        normalized: dict[str, str] = {}
        for key, item in value.items():
            normalized_key = _normalize_required_text(key, "metadata.key")
            normalized_value = _normalize_required_text(item, "metadata.value")
            normalized[normalized_key] = normalized_value
        return normalized
