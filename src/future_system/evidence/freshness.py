"""Deterministic freshness scoring helpers for evidence assembly."""

from __future__ import annotations

from datetime import UTC, datetime


def compute_freshness_score(*, snapshot_at: datetime, reference_time: datetime) -> float:
    """Score snapshot freshness using explicit bucket thresholds."""

    age_seconds = _age_seconds(snapshot_at=snapshot_at, reference_time=reference_time)

    if age_seconds <= 5 * 60:
        return 1.0
    if age_seconds <= 30 * 60:
        return 0.8
    if age_seconds <= 2 * 60 * 60:
        return 0.5
    return 0.2


def is_stale_snapshot(*, snapshot_at: datetime, reference_time: datetime) -> bool:
    """Return True when a snapshot is older than the final freshness bucket."""

    return _age_seconds(snapshot_at=snapshot_at, reference_time=reference_time) > 2 * 60 * 60


def _age_seconds(*, snapshot_at: datetime, reference_time: datetime) -> float:
    normalized_snapshot = _normalize_datetime(snapshot_at)
    normalized_reference = _normalize_datetime(reference_time)
    raw_age = (normalized_reference - normalized_snapshot).total_seconds()
    return max(0.0, raw_age)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
