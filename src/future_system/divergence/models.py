"""Canonical models for deterministic divergence detection over evidence packets."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

DivergencePosture = Literal["aligned", "mixed", "conflicted", "insufficient"]
MarketDisagreementSeverity = Literal["low", "medium", "high", "unknown"]


def _validate_unit_interval(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0.0, 1.0]; received {value}.")
    return value


class MarketDisagreement(BaseModel):
    """Per-market disagreement summary against packet aggregate probability."""

    market_slug: str | None = None
    condition_id: str | None = None
    implied_yes_probability: float | None = None
    distance_from_aggregate: float | None = None
    liquidity_score: float
    freshness_score: float
    flags: list[str] = Field(default_factory=list)
    severity: MarketDisagreementSeverity

    @field_validator("implied_yes_probability", "distance_from_aggregate")
    @classmethod
    def _validate_probability_fields(cls, value: float | None, info: Any) -> float | None:
        return _validate_unit_interval(value, info.field_name)

    @field_validator("liquidity_score", "freshness_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class ThemeDivergencePacket(BaseModel):
    """Canonical divergence output for one theme evidence packet."""

    theme_id: str
    primary_market_slug: str | None
    aggregate_yes_probability: float | None
    dispersion_score: float
    quality_penalty: float
    divergence_score: float
    posture: DivergencePosture
    market_disagreements: list[MarketDisagreement]
    flags: list[str] = Field(default_factory=list)
    explanation: str

    @field_validator("aggregate_yes_probability")
    @classmethod
    def _validate_aggregate_probability(cls, value: float | None) -> float | None:
        return _validate_unit_interval(value, "aggregate_yes_probability")

    @field_validator("dispersion_score", "quality_penalty", "divergence_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class DivergenceDetectionError(ValueError):
    """Raised when divergence cannot be computed from a provided evidence packet."""

