"""Deterministic fixture-oriented parser for normalized crypto market snapshots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any, cast

from pydantic import ValidationError

from future_system.crypto_adapter.filters import filter_market_states_by_symbols
from future_system.crypto_adapter.models import (
    CryptoAdapterError,
    CryptoAdapterParseResult,
    CryptoMarketStatus,
    CryptoMarketType,
    NormalizedCryptoMarketState,
    normalize_crypto_symbol,
)


def parse_crypto_market_snapshots(
    payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    default_exchange: str | None = None,
) -> CryptoAdapterParseResult:
    """Parse raw fixture payload into deterministic normalized crypto market states."""

    records, payload_exchange = _extract_records_and_exchange(payload)

    market_states: list[NormalizedCryptoMarketState] = []
    skipped_records = 0
    flags: set[str] = set()

    for record in records:
        try:
            normalized = _normalize_record(
                record=record,
                default_exchange=default_exchange or payload_exchange,
            )
            market_states.append(normalized)
        except (ValueError, TypeError, ValidationError):
            skipped_records += 1

    if skipped_records > 0:
        flags.add("skipped_invalid_records")

    result_exchange = (
        default_exchange
        or payload_exchange
        or (market_states[0].exchange if market_states else "unknown")
    )

    return CryptoAdapterParseResult(
        exchange=result_exchange,
        market_states=market_states,
        skipped_records=skipped_records,
        flags=sorted(flags),
    )


class FixtureCryptoAdapter:
    """Tiny protocol-compatible adapter for deterministic fixture parsing."""

    def parse_raw_payload(
        self,
        payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
        *,
        default_exchange: str | None = None,
    ) -> CryptoAdapterParseResult:
        return parse_crypto_market_snapshots(payload, default_exchange=default_exchange)

    def filter_market_states(
        self,
        market_states: Sequence[NormalizedCryptoMarketState],
        *,
        allowed_symbols: Sequence[str] | None,
    ) -> list[NormalizedCryptoMarketState]:
        return filter_market_states_by_symbols(
            market_states=market_states,
            allowed_symbols=allowed_symbols,
        )


def _extract_records_and_exchange(
    payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
) -> tuple[list[Mapping[str, Any]], str | None]:
    payload_exchange: str | None = None

    if isinstance(payload, Mapping):
        payload_exchange = _coerce_optional_text(payload.get("exchange"))
        if "records" in payload:
            records_raw = payload["records"]
            if not isinstance(records_raw, Sequence) or isinstance(records_raw, str | bytes):
                raise CryptoAdapterError("payload['records'] must be a sequence of mappings.")
            records: list[Mapping[str, Any]] = []
            for item in records_raw:
                if not isinstance(item, Mapping):
                    raise CryptoAdapterError("payload records must be mappings.")
                records.append(item)
            return records, payload_exchange
        return [payload], payload_exchange

    if not isinstance(payload, Sequence) or isinstance(payload, str | bytes):
        raise CryptoAdapterError("payload must be a sequence of mappings or a mapping.")

    records = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise CryptoAdapterError("payload sequence items must be mappings.")
        records.append(item)
    return records, payload_exchange


def _normalize_record(
    *,
    record: Mapping[str, Any],
    default_exchange: str | None,
) -> NormalizedCryptoMarketState:
    market_type = _normalize_market_type(record.get("market_type", record.get("type")))
    base_asset = _coerce_required_text(record.get("base_asset", record.get("base")), "base_asset")
    quote_asset = _coerce_required_text(
        record.get("quote_asset", record.get("quote")),
        "quote_asset",
    )
    symbol = _normalize_symbol(
        symbol=record.get("symbol"),
        base_asset=base_asset,
        quote_asset=quote_asset,
        market_type=market_type,
    )
    bid_price = _coerce_optional_float(record.get("bid_price", record.get("bid")))
    ask_price = _coerce_optional_float(record.get("ask_price", record.get("ask")))
    mid_price = _coerce_optional_float(record.get("mid_price", record.get("mid")))
    computed_mid = mid_price
    if computed_mid is None and bid_price is not None and ask_price is not None:
        computed_mid = round((bid_price + ask_price) / 2.0, 8)

    exchange = _coerce_optional_text(record.get("exchange")) or default_exchange
    if exchange is None:
        raise ValueError("exchange is required either in record or default_exchange.")

    snapshot_at = _coerce_datetime(record.get("snapshot_at", record.get("timestamp")))
    status = _normalize_status(record.get("status"))

    return NormalizedCryptoMarketState(
        source="fixture",
        exchange=exchange,
        symbol=symbol,
        base_asset=base_asset,
        quote_asset=quote_asset,
        market_type=market_type,
        last_price=_coerce_optional_float(record.get("last_price", record.get("last"))),
        bid_price=bid_price,
        ask_price=ask_price,
        mid_price=computed_mid,
        volume_24h=_coerce_optional_float(record.get("volume_24h", record.get("volume"))),
        open_interest=_coerce_optional_float(record.get("open_interest")),
        funding_rate=_coerce_optional_float(record.get("funding_rate")),
        snapshot_at=snapshot_at,
        status=status,
    )


def _normalize_symbol(
    *,
    symbol: Any,
    base_asset: str,
    quote_asset: str,
    market_type: CryptoMarketType,
) -> str:
    if symbol is not None:
        return normalize_crypto_symbol(_coerce_required_text(symbol, "symbol"))
    if market_type == "perp":
        return normalize_crypto_symbol(f"{base_asset}-PERP")
    return normalize_crypto_symbol(f"{base_asset}-{quote_asset}")


def _normalize_market_type(value: Any) -> CryptoMarketType:
    raw = _coerce_required_text(value, "market_type").lower()
    if raw not in {"spot", "perp"}:
        raise ValueError("market_type must be 'spot' or 'perp'.")
    return cast(CryptoMarketType, raw)


def _normalize_status(value: Any) -> CryptoMarketStatus:
    if value is None:
        return "unknown"
    raw = _coerce_required_text(value, "status").lower()
    if raw not in {"active", "halted", "unknown"}:
        return "unknown"
    return cast(CryptoMarketStatus, raw)


def _coerce_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be a non-empty string.")
    return normalized


def _coerce_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    return _coerce_required_text(value, "value")


def _coerce_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("boolean values are not valid numeric inputs.")
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        return float(value.strip())
    raise ValueError("invalid numeric value type.")


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise ValueError("snapshot_at/timestamp must be an ISO datetime string.")
