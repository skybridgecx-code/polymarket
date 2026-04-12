"""Deterministic bounded scoring helpers for theme-linked news evidence."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime


def compute_news_freshness_score(*, published_at: datetime, reference_time: datetime) -> float:
    """Bucketed freshness score from published age using explicit reference time."""

    age_seconds = _age_seconds(published_at=published_at, reference_time=reference_time)
    if age_seconds <= 2 * 60 * 60:
        return 1.0
    if age_seconds <= 12 * 60 * 60:
        return 0.8
    if age_seconds <= 24 * 60 * 60:
        return 0.6
    if age_seconds <= 3 * 24 * 60 * 60:
        return 0.35
    return 0.15


def compute_news_trust_score(*, trust_scores: Sequence[float]) -> float:
    """Compute bounded aggregate trust as the mean of bounded record trust scores."""

    if not trust_scores:
        raise ValueError("trust_scores cannot be empty.")
    bounded = [clamp_unit(score) for score in trust_scores]
    return round(sum(bounded) / len(bounded), 3)


def compute_news_coverage_score(
    *,
    linked_entities: Sequence[str],
    observed_linked_entities: Sequence[str],
) -> float:
    """Compute bounded linked-entity coverage across matched news evidence."""

    linked_normalized = _normalize_tokens(linked_entities)
    if not linked_normalized:
        raise ValueError("linked_entities must include at least one entity.")

    observed_normalized = _normalize_tokens(observed_linked_entities)
    matched_count = len(linked_normalized & observed_normalized)
    return round(clamp_unit(matched_count / len(linked_normalized)), 3)


def clamp_unit(value: float) -> float:
    """Clamp numeric values into the closed unit interval."""

    return max(0.0, min(1.0, value))


def _normalize_tokens(values: Sequence[str]) -> set[str]:
    normalized: set[str] = set()
    for value in values:
        token = " ".join(value.split()).casefold().strip()
        if not token:
            continue
        normalized.add(token)
    return normalized


def _age_seconds(*, published_at: datetime, reference_time: datetime) -> float:
    published = _normalize_datetime(published_at)
    reference = _normalize_datetime(reference_time)
    return max(0.0, (reference - published).total_seconds())


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
