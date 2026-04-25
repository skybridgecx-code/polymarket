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
SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSETS = tuple(SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP)

PolymarketExternalConfirmationSignalIntent = Literal[
    "bullish",
    "bearish",
    "neutral",
    "veto",
]

_POLYMARKET_INTENT_TO_REVIEWED_SIGNAL: dict[str, Literal["buy", "sell", "veto"]] = {
    "bullish": "buy",
    "bearish": "sell",
    "neutral": "veto",
    "veto": "veto",
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


def resolve_supported_cryp_confirmation_asset(
    *,
    asset_symbol: str | None,
    source_field: str,
) -> str:
    """Resolve the explicit structured asset source into a supported cryp base asset."""

    normalized_source_field = _normalize_source_field(source_field)
    if asset_symbol is None:
        raise ValueError(f"missing_cryp_confirmation_asset:{normalized_source_field}")
    if not isinstance(asset_symbol, str):
        raise ValueError(f"invalid_cryp_confirmation_asset:{normalized_source_field}")

    normalized_symbol = asset_symbol.strip().upper()
    if not normalized_symbol:
        raise ValueError(f"missing_cryp_confirmation_asset:{normalized_source_field}")

    for asset in SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSETS:
        if normalized_symbol == asset:
            return asset
        if normalized_symbol.startswith(f"{asset}-"):
            return asset
        if normalized_symbol in {f"{asset}USD", f"{asset}USDT"}:
            return asset

    supported = ",".join(SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSETS)
    raise ValueError(
        "unsupported_cryp_confirmation_asset:"
        f"{normalized_symbol}:source={normalized_source_field}:supported={supported}"
    )


def map_polymarket_intent_to_reviewed_signal(
    intent: str,
) -> Literal["buy", "sell", "veto"]:
    normalized_intent = intent.strip().lower() if isinstance(intent, str) else ""
    signal = _POLYMARKET_INTENT_TO_REVIEWED_SIGNAL.get(normalized_intent)
    if signal is None:
        supported = ",".join(_POLYMARKET_INTENT_TO_REVIEWED_SIGNAL)
        raise ValueError(
            f"unsupported_polymarket_confirmation_intent:{intent}:supported={supported}"
        )
    return signal


def _normalize_source_field(source_field: str) -> str:
    if not isinstance(source_field, str):
        raise ValueError("source_field_must_be_string")
    normalized = source_field.strip()
    if not normalized:
        raise ValueError("source_field_must_be_non_empty")
    return normalized


__all__ = [
    "PolymarketExternalConfirmationSignalIntent",
    "ReviewedPolymarketExternalConfirmationSignal",
    "SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSETS",
    "SUPPORTED_CRYP_EXTERNAL_CONFIRMATION_ASSET_MAP",
    "map_polymarket_intent_to_reviewed_signal",
    "resolve_supported_cryp_confirmation_asset",
]
