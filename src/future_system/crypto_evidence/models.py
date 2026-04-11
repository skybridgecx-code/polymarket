"""Canonical contracts for deterministic theme-scoped crypto evidence packets."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

ProxyRole = Literal["primary_proxy", "confirmation_proxy", "hedge_proxy", "context_only"]
DirectionalBias = Literal["up", "down", "mixed", "unknown"]
CryptoMarketType = Literal["spot", "perp"]


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


def _validate_non_negative(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0:
        raise ValueError(f"{field_name} cannot be negative; received {value}.")
    return value


class CryptoProxyEvidence(BaseModel):
    """Theme-scoped evidence for one linked normalized crypto proxy market."""

    symbol: str
    market_type: CryptoMarketType
    exchange: str
    role: ProxyRole
    direction_if_theme_up: DirectionalBias
    last_price: float | None = None
    mid_price: float | None = None
    funding_rate: float | None = None
    open_interest: float | None = None
    liquidity_score: float
    freshness_score: float
    flags: list[str] = Field(default_factory=list)
    is_primary: bool = False

    @field_validator("symbol", "exchange", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("last_price", "mid_price", "open_interest")
    @classmethod
    def _validate_non_negative_fields(cls, value: float | None, info: Any) -> float | None:
        return _validate_non_negative(value, info.field_name)

    @field_validator("funding_rate")
    @classmethod
    def _validate_funding_rate(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if value < -1.0 or value > 1.0:
            raise ValueError(f"funding_rate must be within [-1.0, 1.0]; received {value}.")
        return value

    @field_validator("liquidity_score", "freshness_score")
    @classmethod
    def _validate_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class ThemeCryptoEvidencePacket(BaseModel):
    """Canonical crypto evidence output packet for one linked theme."""

    theme_id: str
    primary_symbol: str | None
    proxy_evidence: list[CryptoProxyEvidence]
    matched_symbols: list[str]
    liquidity_score: float
    freshness_score: float
    coverage_score: float
    flags: list[str] = Field(default_factory=list)
    explanation: str

    @field_validator("theme_id", "explanation", mode="before")
    @classmethod
    def _normalize_required_fields(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("primary_symbol", mode="before")
    @classmethod
    def _normalize_optional_symbol(cls, value: Any) -> str | None:
        if value is None:
            return None
        return _normalize_required_text(value, "primary_symbol").upper()

    @field_validator("matched_symbols", mode="before")
    @classmethod
    def _normalize_matched_symbols(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("matched_symbols must be a list of strings.")
        return [_normalize_required_text(item, "matched_symbols").upper() for item in value]

    @field_validator("liquidity_score", "freshness_score", "coverage_score")
    @classmethod
    def _validate_packet_scores(cls, value: float, info: Any) -> float:
        validated = _validate_unit_interval(value, info.field_name)
        assert validated is not None
        return validated


class CryptoEvidenceAssemblyError(ValueError):
    """Raised when theme-linked crypto evidence cannot be assembled deterministically."""

