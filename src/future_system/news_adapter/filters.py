"""Deterministic exact-match filtering helpers for normalized news records."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from future_system.news_adapter.models import (
    NewsRecordFilter,
    NormalizedNewsRecord,
    normalize_news_list,
)


def filter_news_records(
    *,
    records: Sequence[NormalizedNewsRecord],
    publisher: str | None = None,
    entity: str | None = None,
    topic: str | None = None,
    is_official_source: bool | None = None,
    published_at_gte: datetime | None = None,
) -> list[NormalizedNewsRecord]:
    """Filter normalized news records by exact normalized criteria, preserving order."""

    record_filter = NewsRecordFilter(
        publisher=publisher,
        entity=entity,
        topic=topic,
        official_only=is_official_source,
        published_at_gte=published_at_gte,
    )
    return apply_news_record_filter(records=records, record_filter=record_filter)


def apply_news_record_filter(
    *,
    records: Sequence[NormalizedNewsRecord],
    record_filter: NewsRecordFilter | None,
) -> list[NormalizedNewsRecord]:
    """Apply a pre-validated filter object to normalized records in stable order."""

    if record_filter is None:
        return list(records)

    filtered: list[NormalizedNewsRecord] = []
    for record in records:
        if record_filter.publisher is not None and record.publisher != record_filter.publisher:
            continue

        if record_filter.entity is not None and record_filter.entity not in record.entities:
            continue

        if record_filter.topic is not None and record_filter.topic not in record.topics:
            continue

        if (
            record_filter.official_only is not None
            and record.is_official_source is not record_filter.official_only
        ):
            continue

        if (
            record_filter.published_at_gte is not None
            and record.published_at < record_filter.published_at_gte
        ):
            continue

        filtered.append(record)

    return filtered


def normalize_news_filters(values: Sequence[str] | None) -> list[str]:
    """Normalize filter tokens with deterministic case-insensitive dedupe."""

    if not values:
        return []
    return normalize_news_list(list(values))
