"""Deterministic bounded scoring helpers for theme-linked crypto evidence."""

from __future__ import annotations

from datetime import UTC, datetime


def compute_crypto_freshness_score(*, snapshot_at: datetime, reference_time: datetime) -> float:
    """Bucketed freshness score with explicit reference time input."""

    age_seconds = _age_seconds(snapshot_at=snapshot_at, reference_time=reference_time)
    if age_seconds <= 5 * 60:
        return 1.0
    if age_seconds <= 30 * 60:
        return 0.8
    if age_seconds <= 2 * 60 * 60:
        return 0.5
    return 0.2


def is_crypto_stale(*, snapshot_at: datetime, reference_time: datetime) -> bool:
    """Return True when a crypto snapshot is older than the final freshness bucket."""

    return _age_seconds(snapshot_at=snapshot_at, reference_time=reference_time) > 2 * 60 * 60


def compute_crypto_liquidity_score(
    *,
    market_type: str,
    bid_price: float | None,
    ask_price: float | None,
    volume_24h: float | None,
    open_interest: float | None,
) -> float:
    """Compute bounded liquidity using spread, volume, and perp open interest."""

    if (
        bid_price is not None
        and ask_price is not None
        and ask_price >= bid_price
        and (ask_price + bid_price) > 0.0
    ):
        mid = (ask_price + bid_price) / 2.0
        relative_spread = (ask_price - bid_price) / mid
        spread_component = clamp_unit(1.0 - (relative_spread / 0.05))
    else:
        spread_component = 0.4

    volume_component = clamp_unit((volume_24h or 0.0) / 100_000.0)
    if market_type == "perp":
        open_interest_component = clamp_unit((open_interest or 0.0) / 10_000_000.0)
    else:
        open_interest_component = 0.5

    raw_score = (
        0.45 * spread_component
        + 0.35 * volume_component
        + 0.20 * open_interest_component
    )
    return round(clamp_unit(raw_score), 3)


def compute_crypto_coverage_score(*, matched_count: int, linked_count: int) -> float:
    """Compute bounded linked-symbol coverage from matched and linked counts."""

    if linked_count <= 0:
        raise ValueError("linked_count must be positive.")
    if matched_count <= 0:
        return 0.0
    return round(clamp_unit(matched_count / linked_count), 3)


def clamp_unit(value: float) -> float:
    """Clamp numeric values into the unit interval."""

    return max(0.0, min(1.0, value))


def _age_seconds(*, snapshot_at: datetime, reference_time: datetime) -> float:
    snapshot = _normalize_datetime(snapshot_at)
    reference = _normalize_datetime(reference_time)
    return max(0.0, (reference - snapshot).total_seconds())


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)

