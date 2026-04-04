from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from polymarket_arb.models.raw import RawClobBook, RawClobFeeRate, RawGammaEvent


def _parse_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        return [value]
    return [str(value)]


def _parse_optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), tz=UTC)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return datetime.fromtimestamp(int(stripped) / 1000, tz=UTC)
        return datetime.fromisoformat(stripped.replace("Z", "+00:00"))
    raise TypeError(f"Unsupported datetime value: {value!r}")


class PriceLevel(BaseModel):
    price: Decimal
    size: Decimal


class NormalizedBook(BaseModel):
    token_id: str
    source: str
    fetched_at: datetime
    market_id: str | None
    book_hash: str | None
    book_timestamp: datetime | None
    bids: list[PriceLevel] = Field(default_factory=list)
    asks: list[PriceLevel] = Field(default_factory=list)
    best_bid: Decimal | None
    best_ask: Decimal | None
    midpoint: Decimal | None
    spread: Decimal | None
    min_order_size: Decimal | None
    tick_size: Decimal | None
    neg_risk: bool

    @classmethod
    def from_raw(cls, record: RawClobBook) -> NormalizedBook:
        payload = record.payload
        bids = sorted(
            [
                PriceLevel(price=Decimal(str(level["price"])), size=Decimal(str(level["size"])))
                for level in payload.get("bids", [])
                if isinstance(level, dict)
            ],
            key=lambda level: level.price,
            reverse=True,
        )
        asks = sorted(
            [
                PriceLevel(price=Decimal(str(level["price"])), size=Decimal(str(level["size"])))
                for level in payload.get("asks", [])
                if isinstance(level, dict)
            ],
            key=lambda level: level.price,
        )
        best_bid = bids[0].price if bids else None
        best_ask = asks[0].price if asks else None
        midpoint = None
        spread = None
        if best_bid is not None and best_ask is not None:
            midpoint = (best_bid + best_ask) / Decimal("2")
            spread = best_ask - best_bid

        min_order_size = (
            Decimal(str(payload["min_order_size"]))
            if payload.get("min_order_size") is not None
            else None
        )
        tick_size = (
            Decimal(str(payload["tick_size"]))
            if payload.get("tick_size") is not None
            else None
        )

        return cls(
            token_id=record.token_id,
            source=record.source,
            fetched_at=record.fetched_at,
            market_id=payload.get("market"),
            book_hash=payload.get("hash"),
            book_timestamp=_parse_optional_datetime(payload.get("timestamp")),
            bids=bids,
            asks=asks,
            best_bid=best_bid,
            best_ask=best_ask,
            midpoint=midpoint,
            spread=spread,
            min_order_size=min_order_size,
            tick_size=tick_size,
            neg_risk=bool(payload.get("neg_risk", False)),
        )


class NormalizedFeeRate(BaseModel):
    token_id: str
    source: str
    fetched_at: datetime
    base_fee_bps: int

    @classmethod
    def from_raw(cls, record: RawClobFeeRate) -> NormalizedFeeRate:
        payload = record.payload
        raw_base_fee = payload.get("base_fee")
        if raw_base_fee is None:
            raw_base_fee = payload.get("baseFee")
        base_fee_bps = int(str(raw_base_fee or 0))

        return cls(
            token_id=record.token_id,
            source=record.source,
            fetched_at=record.fetched_at,
            base_fee_bps=base_fee_bps,
        )


class NormalizedMarket(BaseModel):
    event_id: str
    market_id: str
    slug: str
    question: str
    outcomes: list[str]
    token_ids: list[str]
    active: bool
    closed: bool
    accepting_orders: bool
    neg_risk: bool
    source: str
    fetched_at: datetime

    @classmethod
    def from_gamma_payload(
        cls,
        *,
        event_id: str,
        payload: dict[str, Any],
        fetched_at: datetime,
        source: str,
    ) -> NormalizedMarket:
        return cls(
            event_id=event_id,
            market_id=str(payload["id"]),
            slug=str(payload.get("slug") or payload.get("question") or payload["id"]),
            question=str(payload.get("question") or ""),
            outcomes=_parse_string_list(payload.get("outcomes")),
            token_ids=_parse_string_list(payload.get("clobTokenIds")),
            active=bool(payload.get("active", False)),
            closed=bool(payload.get("closed", False)),
            accepting_orders=bool(payload.get("acceptingOrders", False)),
            neg_risk=bool(payload.get("negRisk", False)),
            source=source,
            fetched_at=fetched_at,
        )


class NormalizedEvent(BaseModel):
    event_id: str
    slug: str
    title: str
    active: bool
    closed: bool
    start_at: datetime | None
    end_at: datetime | None
    source: str
    fetched_at: datetime
    markets: list[NormalizedMarket] = Field(default_factory=list)

    @classmethod
    def from_raw(cls, record: RawGammaEvent) -> NormalizedEvent:
        payload = record.payload
        event_id = str(payload["id"])
        markets = [
            NormalizedMarket.from_gamma_payload(
                event_id=event_id,
                payload=market_payload,
                fetched_at=record.fetched_at,
                source=record.source,
            )
            for market_payload in payload.get("markets", [])
            if isinstance(market_payload, dict)
        ]
        open_markets = [
            market
            for market in markets
            if market.active and not market.closed and len(market.token_ids) > 0
        ]
        open_markets.sort(key=lambda market: (market.slug, market.market_id))

        return cls(
            event_id=event_id,
            slug=str(payload.get("slug") or event_id),
            title=str(payload.get("title") or payload.get("question") or event_id),
            active=bool(payload.get("active", False)),
            closed=bool(payload.get("closed", False)),
            start_at=_parse_optional_datetime(payload.get("startDate")),
            end_at=_parse_optional_datetime(payload.get("endDate")),
            source=record.source,
            fetched_at=record.fetched_at,
            markets=open_markets,
        )
