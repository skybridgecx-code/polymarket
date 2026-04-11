"""Canonical evidence packet models for deterministic theme evidence assembly."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

MarketStatus = Literal["active", "closed", "resolved", "unknown"]


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


def _validate_non_negative(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0:
        raise ValueError(f"{field_name} cannot be negative; received {value}.")
    return value


class NormalizedPolymarketMarketState(BaseModel):
    """Bounded normalized Polymarket snapshot used by evidence assembly."""

    market_slug: str | None = None
    event_slug: str | None = None
    condition_id: str | None = None
    question: str | None = None
    yes_bid: float | None = None
    yes_ask: float | None = None
    no_bid: float | None = None
    no_ask: float | None = None
    last_price_yes: float | None = None
    volume_24h: float | None = None
    depth_near_mid: float | None = None
    snapshot_at: datetime
    last_trade_at: datetime | None = None
    resolution_at: datetime | None = None
    status: MarketStatus

    @field_validator("market_slug", "event_slug", "condition_id", "question", mode="before")
    @classmethod
    def _normalize_optional_identifiers(cls, value: Any, info: Any) -> str | None:
        return _normalize_optional_text(value, info.field_name)

    @field_validator("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price_yes")
    @classmethod
    def _validate_probability_fields(cls, value: float | None, info: Any) -> float | None:
        return _validate_unit_interval(value, info.field_name)

    @field_validator("volume_24h", "depth_near_mid")
    @classmethod
    def _validate_non_negative_fields(cls, value: float | None, info: Any) -> float | None:
        return _validate_non_negative(value, info.field_name)

    @model_validator(mode="after")
    def _validate_identifiers(self) -> Self:
        if self.condition_id is None and self.market_slug is None and self.event_slug is None:
            raise ValueError(
                "NormalizedPolymarketMarketState must include at least one of "
                "condition_id, market_slug, or event_slug."
            )
        return self


class PolymarketMarketEvidence(BaseModel):
    """Evidence summary for one matched Polymarket market."""

    market_slug: str | None = None
    condition_id: str | None = None
    implied_yes_probability: float | None = None
    spread: float | None = None
    liquidity_score: float
    freshness_score: float
    flags: list[str] = Field(default_factory=list)
    is_primary: bool = False

    @field_validator("implied_yes_probability")
    @classmethod
    def _validate_implied_probability(cls, value: float | None) -> float | None:
        return _validate_unit_interval(value, "implied_yes_probability")

    @field_validator("spread")
    @classmethod
    def _validate_spread(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if value < 0.0 or value > 1.0:
            raise ValueError(f"spread must be within [0.0, 1.0]; received {value}.")
        return value

    @field_validator("liquidity_score", "freshness_score")
    @classmethod
    def _validate_unit_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class ThemeEvidencePacket(BaseModel):
    """Canonical assembled evidence packet for one linked theme."""

    theme_id: str
    primary_market_slug: str | None
    market_evidence: list[PolymarketMarketEvidence]
    aggregate_yes_probability: float | None
    liquidity_score: float
    freshness_score: float
    evidence_score: float
    flags: list[str] = Field(default_factory=list)
    explanation: str

    @field_validator("aggregate_yes_probability")
    @classmethod
    def _validate_aggregate_probability(cls, value: float | None) -> float | None:
        return _validate_unit_interval(value, "aggregate_yes_probability")

    @field_validator("liquidity_score", "freshness_score", "evidence_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class EvidenceAssemblyError(ValueError):
    """Raised when linked evidence cannot be assembled into a valid packet."""

