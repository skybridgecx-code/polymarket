from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from polymarket_arb.models.raw import (
    RawClobBook,
    RawClobFeeRate,
    RawDataLeaderboardEntry,
    RawDataTopHolderGroup,
    RawDataUserActivity,
    RawGammaEvent,
)


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


def _parse_optional_decimal(value: Any) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _parse_optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    return int(str(value))


def _parse_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_wallet_address(value: Any) -> str | None:
    wallet = _parse_optional_string(value)
    if wallet is None:
        return None
    return wallet.lower()


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
    condition_id: str | None
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
            condition_id=_parse_optional_string(payload.get("conditionId")),
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


class NormalizedWalletSeed(BaseModel):
    source: str
    source_record_id: str
    source_reference: str
    discovered_at: datetime
    wallet_address: str
    seed_kind: str
    display_name: str | None
    pseudonym: str | None
    profile_image_url: str | None
    verified: bool | None
    leaderboard_rank: int | None
    leaderboard_volume: Decimal | None
    leaderboard_pnl: Decimal | None
    condition_id: str | None
    market_id: str | None
    market_slug: str | None
    event_slug: str | None
    token_id: str | None
    outcome: str | None
    outcome_index: int | None
    position_size: Decimal | None

    @classmethod
    def from_leaderboard_entry(cls, record: RawDataLeaderboardEntry) -> NormalizedWalletSeed:
        payload = record.payload
        wallet_address = _normalize_wallet_address(payload.get("proxyWallet"))
        if wallet_address is None:
            raise ValueError("Leaderboard entry is missing proxyWallet.")

        rank = _parse_optional_int(payload.get("rank"))
        return cls(
            source=record.source,
            source_record_id=(
                f"{record.source}:{record.time_period.lower()}:{record.order_by.lower()}:"
                f"{rank or 'na'}:{wallet_address}"
            ),
            source_reference=(
                f"/v1/leaderboard?timePeriod={record.time_period}&orderBy={record.order_by}"
            ),
            discovered_at=record.fetched_at,
            wallet_address=wallet_address,
            seed_kind="leaderboard",
            display_name=_parse_optional_string(payload.get("userName")),
            pseudonym=None,
            profile_image_url=_parse_optional_string(payload.get("profileImage")),
            verified=(
                bool(payload.get("verifiedBadge"))
                if payload.get("verifiedBadge") is not None
                else None
            ),
            leaderboard_rank=rank,
            leaderboard_volume=_parse_optional_decimal(payload.get("vol")),
            leaderboard_pnl=_parse_optional_decimal(payload.get("pnl")),
            condition_id=None,
            market_id=None,
            market_slug=None,
            event_slug=None,
            token_id=None,
            outcome=None,
            outcome_index=None,
            position_size=None,
        )

    @classmethod
    def from_top_holder_group(
        cls,
        *,
        record: RawDataTopHolderGroup,
        holder_payload: dict[str, Any],
        market: NormalizedMarket | None,
        event_slug: str | None,
    ) -> NormalizedWalletSeed:
        wallet_address = _normalize_wallet_address(holder_payload.get("proxyWallet"))
        token_id = _parse_optional_string(holder_payload.get("asset"))
        if wallet_address is None:
            raise ValueError("Top-holder payload is missing proxyWallet.")

        outcome_index = _parse_optional_int(holder_payload.get("outcomeIndex"))
        return cls(
            source=record.source,
            source_record_id=(
                f"{record.source}:{market.condition_id if market is not None else 'unknown'}:"
                f"{token_id or 'unknown'}:{wallet_address}:{outcome_index or 'na'}"
            ),
            source_reference=(
                "/holders?market="
                + ",".join(record.condition_ids)
            ),
            discovered_at=record.fetched_at,
            wallet_address=wallet_address,
            seed_kind="top_holder",
            display_name=_parse_optional_string(holder_payload.get("name")),
            pseudonym=_parse_optional_string(holder_payload.get("pseudonym")),
            profile_image_url=_parse_optional_string(
                holder_payload.get("profileImageOptimized") or holder_payload.get("profileImage")
            ),
            verified=(
                bool(holder_payload.get("verified"))
                if holder_payload.get("verified") is not None
                else None
            ),
            leaderboard_rank=None,
            leaderboard_volume=None,
            leaderboard_pnl=None,
            condition_id=market.condition_id if market is not None else None,
            market_id=market.market_id if market is not None else None,
            market_slug=market.slug if market is not None else None,
            event_slug=event_slug,
            token_id=token_id,
            outcome=(
                market.outcomes[outcome_index]
                if (
                    market is not None
                    and outcome_index is not None
                    and outcome_index < len(market.outcomes)
                )
                else None
            ),
            outcome_index=outcome_index,
            position_size=_parse_optional_decimal(holder_payload.get("amount")),
        )


class NormalizedWalletActivity(BaseModel):
    source: str
    source_record_id: str
    source_reference: str
    fetched_at: datetime
    activity_at: datetime | None
    wallet_address: str
    activity_type: str
    transaction_hash: str | None
    condition_id: str | None
    market_slug: str | None
    event_slug: str | None
    title: str | None
    token_id: str | None
    side: str | None
    outcome: str | None
    outcome_index: int | None
    size: Decimal | None
    usdc_size: Decimal | None
    price: Decimal | None

    @classmethod
    def from_raw(cls, record: RawDataUserActivity) -> NormalizedWalletActivity:
        payload = record.payload
        wallet_address = (
            _normalize_wallet_address(payload.get("proxyWallet"))
            or record.wallet_address.lower()
        )
        activity_at = _parse_optional_datetime(payload.get("timestamp"))
        transaction_hash = _parse_optional_string(payload.get("transactionHash"))
        condition_id = _parse_optional_string(payload.get("conditionId"))
        token_id = _parse_optional_string(payload.get("asset"))
        activity_type = str(payload.get("type") or "UNKNOWN").strip().upper()
        fallback_id = (
            f"{wallet_address}:{activity_type}:"
            f"{int(activity_at.timestamp()) if activity_at is not None else 'na'}:"
            f"{condition_id or token_id or 'na'}"
        )

        return cls(
            source=record.source,
            source_record_id=f"{record.source}:{transaction_hash or fallback_id}",
            source_reference=f"/activity?user={wallet_address}",
            fetched_at=record.fetched_at,
            activity_at=activity_at,
            wallet_address=wallet_address,
            activity_type=activity_type,
            transaction_hash=transaction_hash,
            condition_id=condition_id,
            market_slug=_parse_optional_string(payload.get("slug")),
            event_slug=_parse_optional_string(payload.get("eventSlug")),
            title=_parse_optional_string(payload.get("title")),
            token_id=token_id,
            side=_parse_optional_string(payload.get("side")),
            outcome=_parse_optional_string(payload.get("outcome")),
            outcome_index=_parse_optional_int(payload.get("outcomeIndex")),
            size=_parse_optional_decimal(payload.get("size")),
            usdc_size=_parse_optional_decimal(payload.get("usdcSize")),
            price=_parse_optional_decimal(payload.get("price")),
        )
