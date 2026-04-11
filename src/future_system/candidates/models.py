"""Canonical contracts for deterministic candidate signal construction and ranking."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

CandidatePosture = Literal["watch", "candidate", "high_conflict", "insufficient"]
CandidateReasonCode = Literal[
    "strong_cross_market_alignment",
    "weak_cross_market_alignment",
    "cross_market_conflict",
    "high_internal_divergence",
    "weak_liquidity",
    "stale_evidence",
    "weak_crypto_coverage",
    "missing_probability_inputs",
    "insufficient_comparison_confidence",
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
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided.")
    normalized = value.strip()
    return normalized or None


def _validate_unit_interval(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0.0, 1.0]; received {value}.")
    return value


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


class CandidateSignalPacket(BaseModel):
    """Canonical candidate output packet for one theme."""

    theme_id: str
    title: str | None = None
    posture: CandidatePosture
    candidate_score: float
    confidence_score: float
    conflict_score: float
    alignment: str
    primary_market_slug: str | None = None
    primary_symbol: str | None = None
    reason_codes: list[CandidateReasonCode] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    explanation: str

    @field_validator(
        "theme_id",
        "alignment",
        "explanation",
        mode="before",
    )
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("title", "primary_market_slug", mode="before")
    @classmethod
    def _normalize_optional_fields(cls, value: Any, info: Any) -> str | None:
        return _normalize_optional_text(value, info.field_name)

    @field_validator("primary_symbol", mode="before")
    @classmethod
    def _normalize_optional_symbol(cls, value: Any) -> str | None:
        normalized = _normalize_optional_text(value, "primary_symbol")
        if normalized is None:
            return None
        return normalized.upper()

    @field_validator("candidate_score", "confidence_score", "conflict_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated

    @field_validator("reason_codes", mode="before")
    @classmethod
    def _normalize_reason_codes(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("reason_codes must be a list of strings.")
        normalized = [_normalize_required_text(item, "reason_codes") for item in value]
        return _dedupe_preserving_order(normalized)

    @field_validator("flags", mode="before")
    @classmethod
    def _normalize_flags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("flags must be a list of strings.")
        normalized = [_normalize_required_text(item, "flags") for item in value]
        return _dedupe_preserving_order(normalized)


class CandidateBuildError(ValueError):
    """Raised when candidate construction cannot be computed from provided packets."""


class CandidateRankEntry(BaseModel):
    """Optional helper model representing one deterministic ranked candidate entry."""

    rank: int = Field(ge=1)
    signal: CandidateSignalPacket
