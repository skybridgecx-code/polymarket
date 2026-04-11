"""Canonical models for deterministic crypto adapter normalization."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, field_validator, model_validator

CryptoSource = Literal["fixture", "exchange"]
CryptoMarketType = Literal["spot", "perp"]
CryptoMarketStatus = Literal["active", "halted", "unknown"]


def normalize_crypto_symbol(value: str) -> str:
    """Normalize a crypto symbol to deterministic uppercase dash format."""

    normalized = value.strip().upper().replace("/", "-").replace("_", "-")
    return normalized


def _normalize_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _validate_non_negative(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if value < 0.0:
        raise ValueError(f"{field_name} cannot be negative; received {value}.")
    return value


class NormalizedCryptoMarketState(BaseModel):
    """Canonical normalized crypto market snapshot."""

    source: CryptoSource
    exchange: str
    symbol: str
    base_asset: str
    quote_asset: str
    market_type: CryptoMarketType
    last_price: float | None = None
    bid_price: float | None = None
    ask_price: float | None = None
    mid_price: float | None = None
    volume_24h: float | None = None
    open_interest: float | None = None
    funding_rate: float | None = None
    snapshot_at: datetime
    status: CryptoMarketStatus

    @field_validator("exchange", mode="before")
    @classmethod
    def _normalize_exchange(cls, value: Any) -> str:
        return _normalize_required_text(value, "exchange")

    @field_validator("symbol", mode="before")
    @classmethod
    def _normalize_symbol(cls, value: Any) -> str:
        normalized = normalize_crypto_symbol(_normalize_required_text(value, "symbol"))
        if not normalized:
            raise ValueError("symbol must be a non-empty string.")
        return normalized

    @field_validator("base_asset", "quote_asset", mode="before")
    @classmethod
    def _normalize_assets(cls, value: Any, info: Any) -> str:
        return _normalize_required_text(value, info.field_name).upper()

    @field_validator(
        "last_price",
        "bid_price",
        "ask_price",
        "mid_price",
        "volume_24h",
        "open_interest",
    )
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

    @model_validator(mode="after")
    def _validate_bid_ask_ordering(self) -> Self:
        if (
            self.bid_price is not None
            and self.ask_price is not None
            and self.ask_price < self.bid_price
        ):
            raise ValueError("ask_price must be greater than or equal to bid_price.")
        return self


class CryptoAdapterParseResult(BaseModel):
    """Deterministic parser result containing normalized crypto market states."""

    exchange: str
    market_states: list[NormalizedCryptoMarketState] = Field(default_factory=list)
    skipped_records: int = 0
    flags: list[str] = Field(default_factory=list)

    @field_validator("exchange", mode="before")
    @classmethod
    def _normalize_exchange(cls, value: Any) -> str:
        return _normalize_required_text(value, "exchange")

    @field_validator("skipped_records")
    @classmethod
    def _validate_skipped_records(cls, value: int) -> int:
        if value < 0:
            raise ValueError("skipped_records cannot be negative.")
        return value


class CryptoSymbolFilter(BaseModel):
    """Deterministic exact-match symbol filter input."""

    symbols: list[str] = Field(default_factory=list)

    @field_validator("symbols", mode="before")
    @classmethod
    def _normalize_symbols(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("symbols must be a list of strings.")
        normalized: list[str] = []
        for raw in value:
            symbol = normalize_crypto_symbol(_normalize_required_text(raw, "symbols"))
            normalized.append(symbol)
        return normalized


class CryptoAdapterError(ValueError):
    """Raised when raw payloads cannot be parsed into normalized crypto states."""
