"""Bounded protocol contract for deterministic news adapter behavior."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from future_system.news_adapter.models import (
    NewsAdapterParseResult,
    NewsRecordFilter,
    NormalizedNewsRecord,
)


@runtime_checkable
class NewsAdapterProtocol(Protocol):
    """Small adapter contract for parsing and deterministic exact-match filtering."""

    def parse_raw_payload(
        self,
        payload: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    ) -> NewsAdapterParseResult:
        """Parse raw payload records into normalized news records."""

    def filter_records(
        self,
        records: Sequence[NormalizedNewsRecord],
        *,
        record_filter: NewsRecordFilter | None = None,
    ) -> list[NormalizedNewsRecord]:
        """Return normalized news records filtered by exact normalized criteria."""
