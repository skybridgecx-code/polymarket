"""Canonical contracts for deterministic Polymarket-vs-crypto comparison."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ComparisonDirection = Literal["bullish", "bearish", "mixed", "unknown"]
ComparisonAlignment = Literal["aligned", "weakly_aligned", "conflicted", "insufficient"]
EvidenceFamily = Literal["polymarket", "crypto"]


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


class EvidenceFamilySummary(BaseModel):
    """Normalized summary of one evidence family for cross-market comparison."""

    family: EvidenceFamily
    direction: ComparisonDirection
    strength_score: float
    freshness_score: float
    liquidity_score: float | None = None
    coverage_score: float | None = None
    flags: list[str] = Field(default_factory=list)

    @field_validator("strength_score", "freshness_score", "liquidity_score", "coverage_score")
    @classmethod
    def _validate_scores(cls, value: float | None, info: Any) -> float | None:
        return _validate_unit_interval(value, info.field_name)


class ThemeComparisonPacket(BaseModel):
    """Canonical comparison output for one theme across evidence families."""

    theme_id: str
    polymarket_summary: EvidenceFamilySummary
    crypto_summary: EvidenceFamilySummary
    alignment: ComparisonAlignment
    agreement_score: float
    confidence_score: float
    flags: list[str] = Field(default_factory=list)
    explanation: str

    @field_validator("theme_id", "explanation", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("agreement_score", "confidence_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class ComparisonError(ValueError):
    """Raised when comparison cannot be computed from provided evidence packets."""

