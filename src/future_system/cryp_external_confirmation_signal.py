"""Shared reviewed signal model for Polymarket-to-cryp confirmation export."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP = {
    "BTC": "BTCUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
}


class ReviewedPolymarketExternalConfirmationSignal(BaseModel):
    """Bounded reviewed signal block carried by a packaged Polymarket artifact."""

    model_config = ConfigDict(extra="forbid")

    asset: str
    signal: Literal["buy", "sell", "veto"]
    confidence_adjustment: float = Field(ge=-0.5, le=0.5)
    rationale: str = Field(min_length=1)
    source_system: str = "polymarket-arb"
    supporting_tags: list[str] = Field(default_factory=list)
    observed_at_epoch_ns: int | None = Field(default=None, ge=0)
    correlation_id: str | None = None

    @field_validator("asset", "rationale", "source_system", mode="before")
    @classmethod
    def _normalize_required_text(cls, value: Any, info: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(f"{info.field_name}_must_be_string")
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{info.field_name}_must_be_non_empty")
        return normalized

    @field_validator("asset")
    @classmethod
    def _normalize_asset(cls, value: str) -> str:
        asset = value.upper()
        if asset not in SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP:
            supported = ",".join(sorted(SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP))
            raise ValueError(f"unsupported_crypto_asset:{asset}:supported={supported}")
        return asset

    @field_validator("supporting_tags", mode="before")
    @classmethod
    def _normalize_supporting_tags(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("supporting_tags_must_be_list")
        normalized: list[str] = []
        for raw in value:
            if not isinstance(raw, str):
                raise ValueError("supporting_tags_must_be_string")
            token = raw.strip()
            if not token or token in normalized:
                continue
            normalized.append(token)
        return normalized

    @field_validator("correlation_id", mode="before")
    @classmethod
    def _normalize_optional_correlation_id(cls, value: Any) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("correlation_id_must_be_string")
        normalized = value.strip()
        return normalized or None


__all__ = [
    "ReviewedPolymarketExternalConfirmationSignal",
    "SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP",
]
